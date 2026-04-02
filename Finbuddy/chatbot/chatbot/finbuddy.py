import re
import datetime
import json
import logging
import sqlite3
from collections import defaultdict
from threading import Lock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('finbuddy.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FinBuddy:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(FinBuddy, cls).__new__(cls)
            return cls._instance

    def __init__(self, user_name=None):
        if not hasattr(self, 'initialized'):
            try:
                # User information
                self.user_name = user_name
                
                # Initialize database
                self.init_database()

                # Financial terms dictionary with expanded explanations
                self.financial_terms = {
                    "sip": {
                        "definition": "Systematic Investment Plan - a way to invest a fixed amount regularly in mutual funds.",
                        "benefits": ["Rupee cost averaging", "Disciplined investing", "Long-term wealth creation"],
                        "example": "Investing ₹5000 monthly in a mutual fund"
                    },
                    "emi": {
                        "definition": "Equated Monthly Installment - the fixed payment you make each month for a loan.",
                        "components": ["Principal amount", "Interest", "Total payment"],
                        "example": "Monthly payment of ₹15000 for a home loan"
                    },
                    "apr": {
                        "definition": "Annual Percentage Rate - the yearly interest rate on a loan including fees.",
                        "importance": "Helps compare different loan offers",
                        "example": "A loan with 10% APR means you pay 10% interest per year"
                    },
                    "fd": {
                        "definition": "Fixed Deposit - a savings account where you put money for a fixed time period.",
                        "features": ["Fixed interest rate", "Guaranteed returns", "Low risk"],
                        "example": "Investing ₹100000 for 1 year at 6% interest"
                    },
                    "rd": {
                        "definition": "Recurring Deposit - like an FD, but you add money every month.",
                        "benefits": ["Regular savings", "Higher interest than savings account", "Flexible amounts"],
                        "example": "Saving ₹5000 monthly for 12 months"
                    }
                }

                # Financial categories with subcategories
                self.categories = {
                    "food": ["groceries", "dining", "coffee", "snacks"],
                    "transport": ["fuel", "public_transport", "maintenance", "taxis"],
                    "housing": ["rent", "mortgage", "utilities", "maintenance"],
                    "entertainment": ["movies", "games", "subscriptions", "events"],
                    "shopping": ["clothes", "electronics", "household", "personal_care"],
                    "health": ["medical", "fitness", "insurance", "medicines"],
                    "education": ["tuition", "books", "courses", "supplies"],
                    "savings": ["emergency_fund", "investments", "retirement", "goals"]
                }

                # Conversation state and context
                self.state = "greeting" if not user_name else "ready"
                self.conversation_history = []
                self.user_preferences = {}
                self.temp_data = {}
                self.initialized = True
                logger.info(f"FinBuddy AI initialized for user: {user_name}")
            except Exception as e:
                logger.error(f"Error initializing FinBuddy AI: {str(e)}")
                raise

    def get_db_connection(self):
        """Get a new database connection for the current thread"""
        conn = sqlite3.connect('finbuddy.db')
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """Initialize SQLite database with required tables"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    location TEXT,
                    payment_method TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    category TEXT NOT NULL,
                    subcategory TEXT,
                    amount REAL NOT NULL,
                    period TEXT DEFAULT 'monthly',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS savings_goals (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    amount REAL NOT NULL,
                    target_date TIMESTAMP NOT NULL,
                    purpose TEXT,
                    current_amount REAL DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    message TEXT NOT NULL,
                    scheduled_time TIMESTAMP NOT NULL,
                    is_recurring BOOLEAN DEFAULT 0,
                    frequency TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_triggered TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    category TEXT NOT NULL,
                    preference TEXT NOT NULL,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("FinBuddy AI database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing FinBuddy AI database: {str(e)}")
            raise

    def analyze_sentiment(self, text):
        """Analyze the sentiment of user input using simple keyword matching"""
        positive_words = {'good', 'great', 'excellent', 'happy', 'like', 'love', 'thanks', 'thank'}
        negative_words = {'bad', 'poor', 'terrible', 'hate', 'dislike', 'angry', 'upset'}
        
        words = text.lower().split()
        sentiment_score = sum(1 for word in words if word in positive_words) - sum(1 for word in words if word in negative_words)
        
        return 'positive' if sentiment_score > 0 else 'negative' if sentiment_score < 0 else 'neutral'

    def extract_entities(self, text):
        """Extract relevant entities from user input using regex and keyword matching"""
        entities = {
            'amount': None,
            'category': None,
            'date': None,
            'purpose': None
        }
        
        # Extract amount
        amount_pattern = r'₹?(\d+(?:,\d+)*(?:\.\d+)?)'
        amount_match = re.search(amount_pattern, text)
        if amount_match:
            entities['amount'] = float(amount_match.group(1).replace(',', ''))
        
        # Extract category and subcategory
        text_lower = text.lower()
        for category, subcategories in self.categories.items():
            if category in text_lower:
                entities['category'] = category
                for subcategory in subcategories:
                    if subcategory in text_lower:
                        entities['subcategory'] = subcategory
                        break
                break
        
        # Extract date
        date_patterns = {
            'today': datetime.datetime.now(),
            'tomorrow': datetime.datetime.now() + datetime.timedelta(days=1),
            'yesterday': datetime.datetime.now() - datetime.timedelta(days=1)
        }
        for date_key, date_value in date_patterns.items():
            if date_key in text_lower:
                entities['date'] = date_value
                break
        
        return entities

    def get_recommendations(self, user_id):
        """Generate personalized financial recommendations"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get recent expenses
            cursor.execute("""
                SELECT category, SUM(amount) as total
                FROM expenses
                WHERE user_id = ? AND date >= date('now', '-30 days')
                GROUP BY category
            """, (user_id,))
            recent_expenses = dict(cursor.fetchall())
            
            # Get budgets
            cursor.execute("""
                SELECT category, amount
                FROM budgets
                WHERE user_id = ?
            """, (user_id,))
            budgets = dict(cursor.fetchall())
            
            # Get savings goals
            cursor.execute("""
                SELECT purpose, amount, current_amount
                FROM savings_goals
                WHERE user_id = ? AND status = 'active'
            """, (user_id,))
            savings_goals = cursor.fetchall()
            
            recommendations = []
            
            # Analyze spending patterns
            for category, spent in recent_expenses.items():
                budget = budgets.get(category, 0)
                if budget > 0:
                    percentage = (spent / budget) * 100
                    if percentage > 90:
                        recommendations.append(f"⚠️ You're close to your {category} budget limit. Consider reducing expenses in this category.")
                    elif percentage < 50:
                        recommendations.append(f"✅ You're doing well with your {category} budget. You've only used {percentage:.1f}% of your budget.")
            
            # Analyze savings goals
            for goal in savings_goals:
                purpose, target, current = goal
                progress = (current / target) * 100
                if progress < 50:
                    recommendations.append(f"📈 Consider increasing your savings for {purpose}. Current progress: {progress:.1f}%")
            
            conn.close()
            return recommendations
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []

    def process_message(self, message):
        """Process incoming user message with enhanced AI capabilities"""
        try:
            message = message.lower().strip()
            logger.info(f"Processing message: {message}")

            # Add message to conversation history
            self.conversation_history.append({"role": "user", "content": message})

            # Analyze sentiment
            sentiment = self.analyze_sentiment(message)
            
            # Extract entities
            entities = self.extract_entities(message)

            # Handle conversation states
            if self.state == "greeting":
                self.user_name = message
                self.state = "ready"
                logger.info(f"User registered: {self.user_name}")
                response = f"Nice to meet you, {self.user_name}! I'm your AI financial assistant. I can help you with:\n"
                response += "1. Tracking expenses and budgets\n"
                response += "2. Setting and monitoring savings goals\n"
                response += "3. Providing financial insights and recommendations\n"
                response += "4. Explaining financial terms and concepts\n"
                response += "5. Setting reminders for financial tasks\n\n"
                response += "What would you like to do first?"
                self.conversation_history.append({"role": "assistant", "content": response})
                return response

            # Handle different intents with improved pattern matching
            if entities['amount'] is not None:
                if any(word in message for word in ["spent", "paid", "expense", "cost"]):
                    response = self.handle_expense(message, entities)
                elif any(word in message for word in ["budget", "limit"]):
                    response = self.handle_budget(message, entities)
                elif "save" in message and any(word in message for word in ["by", "until"]):
                    response = self.handle_savings_goal(message, entities)
                else:
                    response = "I noticed you mentioned an amount. Would you like to:\n"
                    response += "1. Log this as an expense?\n"
                    response += "2. Set it as a budget?\n"
                    response += "3. Create a savings goal with this amount?"

            elif any(word in message for word in ["how", "status", "spending", "report"]):
                response = self.get_status()
                # Add personalized recommendations
                recommendations = self.get_recommendations(1)  # Replace 1 with actual user_id
                if recommendations:
                    response += "\n\n📊 Personalized Recommendations:\n"
                    for rec in recommendations:
                        response += f"• {rec}\n"

            elif any(term in message for term in self.financial_terms.keys()):
                response = self.explain_term(message)

            elif "remind" in message or "reminder" in message:
                response = self.handle_reminder(message, entities)

            elif "savings" in message or "save" in message:
                response = "To create a savings goal, please specify:\n"
                response += "1. The amount you want to save\n"
                response += "2. The target date\n"
                response += "3. The purpose of saving\n\n"
                response += "For example: 'I want to save ₹50000 for a new laptop by December'"

            else:
                # Use simple keyword matching for intent recognition
                intents = {
                    "log expense": ["spend", "paid", "cost", "expense"],
                    "set budget": ["budget", "limit", "maximum"],
                    "create savings goal": ["save", "savings", "goal"],
                    "check status": ["how", "status", "spending", "report"],
                    "set reminder": ["remind", "reminder", "alert"],
                    "explain term": ["what", "explain", "mean"]
                }
                
                matched_intent = None
                max_matches = 0
                
                for intent, keywords in intents.items():
                    matches = sum(1 for keyword in keywords if keyword in message)
                    if matches > max_matches:
                        max_matches = matches
                        matched_intent = intent
                
                if max_matches > 0:
                    response = f"I think you want to {matched_intent}. "
                    if matched_intent == "log expense":
                        response += "Please specify the amount and category. For example: 'I spent ₹500 on food'"
                    elif matched_intent == "set budget":
                        response += "Please specify the category and amount. For example: 'Set my food budget to ₹5000'"
                    elif matched_intent == "create savings goal":
                        response += "Please specify the amount, target date, and purpose. For example: 'Save ₹50000 for a laptop by December'"
                    elif matched_intent == "check status":
                        response += "I'll show you your current financial status."
                        response += self.get_status()
                    elif matched_intent == "set reminder":
                        response += "Please specify what you want to be reminded about and when. For example: 'Remind me to pay rent tomorrow'"
                    elif matched_intent == "explain term":
                        response += "Please specify which financial term you'd like to know about. For example: 'What is SIP?'"
                else:
                    response = "I'm not sure what you mean. You can:\n"
                    response += "1. Log expenses (e.g., 'I spent ₹500 on food')\n"
                    response += "2. Set budgets (e.g., 'Set my food budget to ₹5000')\n"
                    response += "3. Create savings goals (e.g., 'Save ₹50000 for a laptop by December')\n"
                    response += "4. Set reminders (e.g., 'Remind me to pay rent tomorrow')\n"
                    response += "5. Ask about financial terms (e.g., 'What is SIP?')"

            # Add response to conversation history
            self.conversation_history.append({"role": "assistant", "content": response})
            return response

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return "I encountered an error while processing your message. Please try again."

    def handle_expense(self, message, entities):
        """Handle expense logging with enhanced features"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            amount = entities['amount']
            category = entities['category'] or "other"
            subcategory = entities.get('subcategory')
            date = entities['date'] or datetime.datetime.now()

            # Save to database
            cursor.execute(
                """
                INSERT INTO expenses 
                (user_id, amount, category, subcategory, date, notes) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (1, amount, category, subcategory, date, message)  # Replace 1 with actual user_id
            )
            conn.commit()

            # Get spending insights
            cursor.execute(
                """
                SELECT SUM(amount) as total
                FROM expenses
                WHERE user_id = ? AND category = ? AND date >= date('now', '-30 days')
                """,
                (1, category)  # Replace 1 with actual user_id
            )
            monthly_total = cursor.fetchone()[0] or 0

            # Get budget if exists
            cursor.execute(
                "SELECT amount FROM budgets WHERE user_id = ? AND category = ?",
                (1, category)  # Replace 1 with actual user_id
            )
            budget = cursor.fetchone()
            budget_amount = budget[0] if budget else None

            conn.close()

            response = f"Got it—₹{amount} under '{category}'"
            if subcategory:
                response += f" ({subcategory})"
            response += f" on {date.strftime('%Y-%m-%d')}."

            if budget_amount:
                percentage = (monthly_total / budget_amount) * 100
                response += f"\n\n📊 Monthly {category} spending: ₹{monthly_total}/₹{budget_amount} ({percentage:.1f}%)"
                if percentage > 90:
                    response += "\n⚠️ You're close to your budget limit for this category!"
                elif percentage < 50:
                    response += "\n✅ You're doing well with your budget!"

            return response

        except Exception as e:
            logger.error(f"Error handling expense: {str(e)}")
            return "Sorry, I encountered an error while processing your expense. Please try again."

    def handle_budget(self, message, entities):
        """Handle budget setting"""
        amount_match = re.search(r'₹(\d+)', message)
        if not amount_match:
            return "I couldn't find the budget amount. Please include the amount with ₹ symbol."

        amount = int(amount_match.group(1))

        # Try to extract category
        categories = ["food", "groceries", "dining", "coffee", "transport", "entertainment", "shopping"]
        category = None

        for cat in categories:
            if cat in message:
                category = cat
                break

        if not category:
            return "For which category would you like to set this budget?"

        # Save to database
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO budgets (category, amount) VALUES (?, ?)",
            (category, amount)
        )
        conn.commit()
        conn.close()

        return f"Great! I've set your {category} budget to ₹{amount}. I'll let you know when you reach 75% of that."

    def handle_savings_goal(self, message, entities):
        """Handle savings goal creation"""
        amount_match = re.search(r'₹(\d+)', message)
        if not amount_match:
            return "I couldn't find the savings amount. Please include the amount with ₹ symbol."

        amount = int(amount_match.group(1))

        # Extract date (simplified)
        date_match = re.search(r'by ([a-zA-Z]+ \d+)', message)
        target_date = date_match.group(1) if date_match else "the end of the year"

        # Extract purpose
        purpose = "your goal"
        purpose_match = re.search(r'for ([a-zA-Z ]+)', message)
        if purpose_match:
            purpose = purpose_match.group(1).strip()

        # Save to database
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO savings_goals (amount, target_date, purpose) VALUES (?, ?, ?)",
            (amount, target_date, purpose)
        )
        conn.commit()
        conn.close()

        return f"I've set up your goal to save ₹{amount} for {purpose} by {target_date}. Would you like weekly reminders?"

    def handle_reminder(self, message, entities):
        """Handle reminder creation"""
        # Extract date/time
        date_match = re.search(r'(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)', message.lower())
        if not date_match:
            return "When would you like to be reminded?"

        scheduled_time = datetime.datetime.now()
        day = date_match.group(1)
        if day == "tomorrow":
            scheduled_time = scheduled_time + datetime.timedelta(days=1)
        # Add more date parsing logic as needed

        # Extract message
        reminder_text = message.split("remind")[-1].strip()
        if not reminder_text:
            return "What would you like to be reminded about?"

        # Check if recurring
        is_recurring = any(word in message for word in ["daily", "weekly", "monthly"])
        frequency = None
        if is_recurring:
            if "daily" in message:
                frequency = "daily"
            elif "weekly" in message:
                frequency = "weekly"
            elif "monthly" in message:
                frequency = "monthly"

        # Save to database
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reminders (message, scheduled_time, is_recurring, frequency) VALUES (?, ?, ?, ?)",
            (reminder_text, scheduled_time, is_recurring, frequency)
        )
        conn.commit()
        conn.close()

        return f"I'll remind you about '{reminder_text}' at {scheduled_time.strftime('%Y-%m-%d %H:%M')}"

    def get_status(self):
        """Get current month's spending status with enhanced insights"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            current_month = datetime.datetime.now().strftime("%Y-%m")

            # Get total spent this month
            cursor.execute(
                """
                SELECT SUM(amount) 
                FROM expenses 
                WHERE user_id = ? AND date LIKE ?
                """,
                (1, f"{current_month}%")  # Replace 1 with actual user_id
            )
            total_spent = cursor.fetchone()[0] or 0

            # Get category-wise spending
            cursor.execute(
                """
                SELECT category, subcategory, SUM(amount) as total
                FROM expenses 
                WHERE user_id = ? AND date LIKE ?
                GROUP BY category, subcategory
                """,
                (1, f"{current_month}%")  # Replace 1 with actual user_id
            )
            category_spending = defaultdict(lambda: defaultdict(float))
            for row in cursor.fetchall():
                category_spending[row['category']][row['subcategory']] = row['total']

            # Get budgets
            cursor.execute(
                "SELECT category, amount FROM budgets WHERE user_id = ?",
                (1,)  # Replace 1 with actual user_id
            )
            budgets = dict(cursor.fetchall())

            # Get savings goals
            cursor.execute(
                """
                SELECT purpose, amount, current_amount
                FROM savings_goals
                WHERE user_id = ? AND status = 'active'
                """,
                (1,)  # Replace 1 with actual user_id
            )
            savings_goals = cursor.fetchall()

            conn.close()

            # Format the response
            response = f"📊 Financial Status for {current_month}\n\n"
            response += f"Total spent this month: ₹{total_spent}\n\n"

            # Category-wise breakdown
            response += "Category-wise spending:\n"
            for category, subcategories in category_spending.items():
                category_total = sum(subcategories.values())
                budget = budgets.get(category, 0)
                
                response += f"\n{category.title()}:\n"
                for subcategory, amount in subcategories.items():
                    response += f"  • {subcategory}: ₹{amount}\n"
                
                if budget > 0:
                    percentage = (category_total / budget) * 100
                    response += f"  Total: ₹{category_total}/₹{budget} ({percentage:.1f}%)\n"
                    if percentage > 90:
                        response += "  ⚠️ Close to budget limit!\n"
                    elif percentage < 50:
                        response += "  ✅ Good progress!\n"
                else:
                    response += f"  Total: ₹{category_total} (no budget set)\n"

            # Savings goals
            if savings_goals:
                response += "\nSavings Goals:\n"
                for goal in savings_goals:
                    purpose, target, current = goal
                    progress = (current / target) * 100
                    response += f"• {purpose}: ₹{current}/₹{target} ({progress:.1f}%)\n"

            # Add insights
            if total_spent > sum(budgets.values()) * 0.9 and budgets:
                response += "\n⚠️ You're close to your total budget for the month. Consider cutting back on some expenses."
            elif budgets:
                response += "\n✅ You're doing well with your budgets so far!"

            return response

        except Exception as e:
            logger.error(f"Error getting status: {str(e)}")
            return "Sorry, I encountered an error while fetching your status. Please try again."

    def explain_term(self, message):
        """Explain financial terms with enhanced information"""
        for term, info in self.financial_terms.items():
            if term in message.lower():
                response = f"📚 {term.upper()}:\n"
                response += f"Definition: {info['definition']}\n"
                
                if 'benefits' in info:
                    response += "\nBenefits:\n"
                    for benefit in info['benefits']:
                        response += f"• {benefit}\n"
                
                if 'components' in info:
                    response += "\nComponents:\n"
                    for component in info['components']:
                        response += f"• {component}\n"
                
                if 'features' in info:
                    response += "\nFeatures:\n"
                    for feature in info['features']:
                        response += f"• {feature}\n"
                
                if 'example' in info:
                    response += f"\nExample: {info['example']}"
                
                return response

        return "I don't have information about that financial term. You can ask me about SIP, EMI, APR, FD, or RD."

    def __del__(self):
        """Cleanup when the object is destroyed"""
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
                logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

# Simple command-line interface to test the chatbot
def main():
    print("Welcome to FinBuddy AI, your intelligent financial assistant!")
    print("What's your name?")

    user_input = input("> ")
    chatbot = FinBuddy()

    print(chatbot.process_message(user_input))

    while True:
        user_input = input("> ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Thank you for using FinBuddy AI! Goodbye!")
            break

        response = chatbot.process_message(user_input)
        print(response)

if __name__ == "__main__":
    main()