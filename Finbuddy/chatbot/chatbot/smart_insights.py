import re
import datetime
import json
import logging
import sqlite3
from collections import defaultdict
from threading import Lock
from statistics import mean, median, stdev

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


class SmartInsights:
    """Smart budgeting insights and recommendations engine"""
    
    def __init__(self):
        self.logger = logger
    
    def get_spending_overview(self, user_id, days=30):
        """Get spending overview for the specified period"""
        try:
            conn = sqlite3.connect('finbuddy.db')
            cursor = conn.cursor()
            
            start_date = datetime.datetime.now() - datetime.timedelta(days=days)
            
            # Get total spending
            cursor.execute("""
                SELECT SUM(amount) as total
                FROM expenses
                WHERE user_id = ? AND date >= ?
            """, (user_id, start_date))
            
            total_spending = cursor.fetchone()[0] or 0
            
            # Get spending by category
            cursor.execute("""
                SELECT category, SUM(amount) as total
                FROM expenses
                WHERE user_id = ? AND date >= ?
                GROUP BY category
                ORDER BY total DESC
            """, (user_id, start_date))
            
            category_spending = dict(cursor.fetchall())
            
            # Get daily average
            cursor.execute("""
                SELECT COUNT(DISTINCT DATE(date)) as days
                FROM expenses
                WHERE user_id = ? AND date >= ?
            """, (user_id, start_date))
            
            active_days = cursor.fetchone()[0] or 1
            daily_average = total_spending / active_days
            
            conn.close()
            
            return {
                'total_spending': total_spending,
                'daily_average': daily_average,
                'category_breakdown': category_spending,
                'period_days': days,
                'active_days': active_days
            }
        except Exception as e:
            self.logger.error(f"Error getting spending overview: {str(e)}")
            return None
    
    def get_smart_recommendations(self, user_id):
        """Generate AI-powered budget recommendations"""
        try:
            conn = sqlite3.connect('finbuddy.db')
            cursor = conn.cursor()
            
            # Get 90-day spending average by category
            start_date = datetime.datetime.now() - datetime.timedelta(days=90)
            
            cursor.execute("""
                SELECT category, SUM(amount) as total
                FROM expenses
                WHERE user_id = ? AND date >= ?
                GROUP BY category
            """, (user_id, start_date))
            
            spending_by_category = dict(cursor.fetchall())
            
            # Get current budgets
            cursor.execute("""
                SELECT category, amount
                FROM budgets
                WHERE user_id = ?
            """, (user_id,))
            
            budget_by_category = dict(cursor.fetchall())
            
            recommendations = []
            
            # Analyze each category
            for category, spending in spending_by_category.items():
                avg_monthly = spending / 3  # 90 days / 3 months
                current_budget = budget_by_category.get(category, 0)
                
                # Detect overspending
                if current_budget > 0:
                    if avg_monthly > current_budget * 1.2:
                        recommendations.append({
                            'type': 'increase_budget',
                            'category': category,
                            'suggested_budget': avg_monthly * 1.1,
                            'current_budget': current_budget,
                            'reason': f'Average spending exceeds budget by {((avg_monthly/current_budget - 1) * 100):.1f}%'
                        })
                    elif avg_monthly < current_budget * 0.5:
                        recommendations.append({
                            'type': 'reduce_budget',
                            'category': category,
                            'suggested_budget': avg_monthly * 1.1,
                            'current_budget': current_budget,
                            'reason': 'You\'re spending well below your budget - consider using savings for goals'
                        })
                else:
                    recommendations.append({
                        'type': 'set_budget',
                        'category': category,
                        'suggested_budget': avg_monthly * 1.1,
                        'reason': f'No budget set for {category} - spending averages {avg_monthly:.2f}/month'
                    })
            
            conn.close()
            return recommendations
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    def detect_spending_anomalies(self, user_id):
        """Detect unusual spending patterns"""
        try:
            conn = sqlite3.connect('finbuddy.db')
            cursor = conn.cursor()
            
            # Get last 30 days of spending
            start_date = datetime.datetime.now() - datetime.timedelta(days=30)
            
            cursor.execute("""
                SELECT category, amount, date
                FROM expenses
                WHERE user_id = ? AND date >= ?
                ORDER BY date DESC
            """, (user_id, start_date))
            
            expenses = cursor.fetchall()
            
            # Group by category and calculate statistics
            category_amounts = defaultdict(list)
            for category, amount, date_str in expenses:
                category_amounts[category].append(amount)
            
            anomalies = []
            
            for category, amounts in category_amounts.items():
                if len(amounts) >= 3:
                    try:
                        avg = mean(amounts)
                        std = stdev(amounts) if len(amounts) > 1 else 0
                        
                        # Find outliers (more than 2 standard deviations)
                        for i, amount in enumerate(amounts):
                            if std > 0 and abs(amount - avg) > 2 * std:
                                anomalies.append({
                                    'category': category,
                                    'amount': amount,
                                    'average': avg,
                                    'deviation': (amount - avg) / avg * 100 if avg > 0 else 0,
                                    'severity': 'high' if abs(amount - avg) > 3 * std else 'medium'
                                })
                    except:
                        pass
            
            conn.close()
            return anomalies
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {str(e)}")
            return []
    
    def calculate_savings_potential(self, user_id):
        """Calculate potential savings based on spending patterns"""
        try:
            conn = sqlite3.connect('finbuddy.db')
            cursor = conn.cursor()
            
            spending_overview = self.get_spending_overview(user_id, days=30)
            recommendations = self.get_smart_recommendations(user_id)
            
            current_spending = spending_overview['total_spending']
            potential_savings = 0
            reduction_tips = []
            
            for rec in recommendations:
                if rec['type'] in ['reduce_budget', 'increase_budget']:
                    savings = rec.get('current_budget', rec['suggested_budget']) - rec['suggested_budget']
                    if savings > 0:
                        potential_savings += savings
                        reduction_tips.append({
                            'category': rec['category'],
                            'current': rec.get('current_budget', rec['suggested_budget']),
                            'suggested': rec['suggested_budget'],
                            'savings': savings,
                            'tip': self._generate_saving_tip(rec['category'])
                        })
            
            conn.close()
            
            return {
                'current_monthly_spending': current_spending,
                'potential_monthly_savings': potential_savings,
                'savings_percentage': (potential_savings / current_spending * 100) if current_spending > 0 else 0,
                'reduction_tips': reduction_tips
            }
        except Exception as e:
            self.logger.error(f"Error calculating savings potential: {str(e)}")
            return None
    
    def _generate_saving_tip(self, category):
        """Generate saving tips for each category"""
        tips = {
            'food': 'Plan meals and buy in bulk to reduce food expenses',
            'transport': 'Consider public transport or carpooling to save on travel costs',
            'shopping': 'Set spending limits and avoid impulse purchases',
            'entertainment': 'Look for free or low-cost entertainment options',
            'housing': 'Review utility bills and look for ways to reduce consumption',
            'health': 'Use preventive care and generic medicines when possible',
            'education': 'Look for online courses and book discounts'
        }
        return tips.get(category, 'Review and optimize spending in this category')
    
    def get_goal_progress(self, user_id):
        """Get progress on financial goals"""
        try:
            conn = sqlite3.connect('finbuddy.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, purpose, amount, current_amount, target_date
                FROM savings_goals
                WHERE user_id = ? AND status = 'active'
            """, (user_id,))
            
            goals = cursor.fetchall()
            goal_progress = []
            
            for goal_id, purpose, target, current, target_date in goals:
                progress_percentage = (current / target * 100) if target > 0 else 0
                
                # Calculate days remaining
                target_dt = datetime.datetime.fromisoformat(target_date)
                days_remaining = (target_dt - datetime.datetime.now()).days
                
                # Calculate required daily savings
                amount_needed = target - current
                daily_required = amount_needed / days_remaining if days_remaining > 0 else 0
                
                goal_progress.append({
                    'id': goal_id,
                    'purpose': purpose,
                    'target_amount': target,
                    'current_amount': current,
                    'progress_percentage': progress_percentage,
                    'days_remaining': days_remaining,
                    'daily_required_savings': daily_required,
                    'on_track': daily_required <= (self.get_spending_overview(user_id)['daily_average'] * 0.1)
                })
            
            conn.close()
            return goal_progress
        except Exception as e:
            self.logger.error(f"Error getting goal progress: {str(e)}")
            return []
