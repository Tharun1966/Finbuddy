# FinBuddy - Smart Personal Finance Assistant

FinBuddy is an intelligent personal finance platform that combines AI-powered insights with workflow automation to help users make data-driven financial decisions. Get smart budgeting recommendations, automate recurring financial tasks, and visualize your financial progress through an interactive interface.

## 🎯 Key Features

- 🔐 **Secure Authentication**: Advanced login and registration with encrypted passwords
- 💰 **Smart Budgeting Insights**: AI-powered budget recommendations and optimization
- 📊 **Data-Driven Analytics**: Interactive charts, visualizations, and spending analysis
- 💡 **Intelligent Financial Advice**: Personalized recommendations based on your spending patterns
- 🤖 **Automated Workflows**: n8n integration for recurring financial tasks and notifications
- 🎯 **Financial Goal Tracking**: Set, monitor, and achieve financial objectives
- 📈 **Predictive Analytics**: Forecast spending trends and identify savings opportunities
- 📱 **Responsive Dashboard**: Real-time insights and metrics
- 🔄 **Multi-channel Notifications**: Email, SMS, and in-app alerts via n8n workflows

## Project Structure

```
chatbot/
├── app.py                 # Main Flask application
├── finbuddy.py           # AI chatbot logic and financial terms
├── requirements.txt      # Python dependencies
├── Procfile              # Deployment configuration
├── README.md             # This file
├── templates/
│   ├── index.html        # Home page
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   └── dashboard.html    # User dashboard
├── instance/             # Instance-specific files (database, config)
└── __pycache__/          # Python cache files
```

## Requirements

- Python 3.11+
- Flask 2.3.3
- SQLAlchemy 3.0.5
- Flask-Login 0.6.2
- Pandas & NumPy for data analysis
- Plotly/Chart.js for visualizations
- n8n (for workflow automation - optional but recommended)
- Additional dependencies listed in `requirements.txt`

## Installation

1. **Clone/Navigate to the project directory:**
   ```bash
   cd c:\Users\adapa\OneDrive\Documents\Finbuddy\chatbot\chatbot
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Access the application:**
   - Open your browser and navigate to: `http://127.0.0.1:5000`
   - Or access from network: `http://10.160.110.142:5000`

## Usage

### Getting Started

1. **Home Page**: Visit the home page to see login and registration options
2. **Register**: Create a new account with username, email, and password
3. **Login**: Sign in with your credentials
4. **Dashboard**: View your financial overview and access tools

### Features Overview

- **Budget Overview**: See your total income and expenses at a glance
- **Analytics**: Analyze spending patterns and trends
- **Financial Advice**: Get AI-powered recommendations based on your finances
- **Settings**: Customize your account and preferences

## API Endpoints

### Authentication
- `GET /` - Home page
- `GET /login` - Login page
- `POST /login` - Login (JSON)
- `GET /register` - Register page
- `POST /register` - Register (JSON)
- `GET /logout` - Logout

### User
- `GET /dashboard` - Dashboard (requires login)

### Smart Insights
- `GET /api/insights/overview` - Budget overview and key metrics
- `GET /api/insights/recommendations` - Smart budgeting recommendations
- `GET /api/insights/spending-analysis` - Detailed spending analysis
- `POST /api/insights/add-expense` - Add expense transaction
- `POST /api/insights/add-income` - Add income transaction
- `GET /api/insights/trends` - Spending trends and forecasts
- `GET /api/insights/goals` - Financial goals and progress
- `POST /api/insights/create-goal` - Create new financial goal

## Form Submission

All forms submit JSON data via JavaScript. Example:

```javascript
fetch('/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ 
    username: 'user123',
    password: 'password123'
  })
})
```

## 🧠 Smart Budgeting Insights

FinBuddy provides intelligent insights using machine learning and data analysis:

### Insight Categories

1. **Budget Optimization**
   - Analyze spending patterns and identify areas to cut costs
   - Recommend optimal budget allocations
   - Detect unusual spending spikes

2. **Spending Analysis**
   - Categorize expenses automatically
   - Track spending by category over time
   - Compare your spending against averages

3. **Financial Forecasting**
   - Predict future spending trends
   - Estimate savings potential
   - Identify seasonal spending patterns

4. **Goal Achievement**
   - Calculate timeline to financial goals
   - Suggest monthly savings targets
   - Track progress with visual indicators

5. **Smart Recommendations**
   - Get AI-powered advice based on your habits
   - Receive alerts about unusual transactions
   - Get tips on improving financial health

## 🤖 n8n Workflow Automation

Automate your financial workflows and get multi-channel notifications:

### Supported Workflows

1. **Expense Alerts**
   - Notify when spending exceeds budget
   - Send weekly spending summaries
   - Alert on large transactions

2. **Recurring Transactions**
   - Auto-categorize recurring expenses
   - Schedule bill reminders
   - Track subscription services

3. **Goal Notifications**
   - Celebrate goal milestones
   - Monthly progress reports
   - Motivation messages

4. **Data Backups**
   - Automatic data exports
   - Cloud backup integration
   - Report generation

### Setup n8n Integration

1. **Install n8n**:
   ```bash
   npm install -g n8n
   n8n
   ```

2. **Access n8n UI**: `http://localhost:5678`

3. **Create Workflows**: Use pre-built FinBuddy templates
   - Configure API credentials
   - Map data fields
   - Set notification channels

4. **Connect to FinBuddy**:
   - Set `N8N_WEBHOOK_URL` in `.env`
   - Configure API keys for integrations
   - Enable webhook triggers

### Notification Channels

- Email notifications via SendGrid/SMTP
- SMS alerts via Twilio
- Slack messages
- Discord webhooks
- In-app notifications

## 📊 Interactive Data Visualization

The dashboard includes:

- **Budget vs. Actual**: Real-time comparison charts
- **Spending Breakdown**: Pie and donut charts by category
- **Trend Analysis**: Line graphs showing spending over time
- **Goal Progress**: Visual progress bars and milestones
- **Cash Flow**: Waterfall charts showing income vs. expenses

## Configuration

The application uses the following environment variables (optional):
- `SECRET_KEY`: Flask session secret (auto-generated if not set)
- `DATABASE_URL`: Database connection string (defaults to SQLite)

Create a `.env` file in the project root to set these:
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///finbuddy.db

# n8n Integration
N8N_WEBHOOK_URL=http://localhost:5678/webhook/finbuddy
N8N_API_KEY=your-n8n-api-key
ENABLE_AUTOMATION=true

# Notification Settings
SENDGRID_API_KEY=your-sendgrid-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
SLACK_WEBHOOK_URL=your-slack-webhook
```

## Database

The application uses SQLite by default, storing data in `finbuddy.db`. The database includes:
- Users table with authentication
- Financial records and transactions
- User preferences and settings

## Security Features

- ✅ Password hashing with Werkzeug
- ✅ CSRF protection with Flask-WTF
- ✅ Session management with Flask-Login
- ✅ Secure cookies (HTTPOnly, SameSite)
- ✅ Input validation on all forms
- ✅ SQL injection prevention with SQLAlchemy ORM

## Logging

Application logs are stored in:
- `app.log` - Main application logs
- `finbuddy.log` - FinBuddy AI logs

Check these files for debugging and monitoring.

## Development

### Running in Debug Mode

To run with debug features enabled:
```python
app.run(debug=True)
```

### Troubleshooting

**Templates not found error:**
- Ensure the `templates/` folder exists with all HTML files

**Login/Register returns 500 error:**
- Check server logs in `app.log`
- Ensure Content-Type is set to 'application/json'

**Database connection error:**
- Delete `finbuddy.db` to reset the database
- Ensure write permissions in the project directory

## Deployment

For production deployment, use a production WSGI server:

```bash
gunicorn app:app
```

Configuration for Heroku is included in the `Procfile`.

## Technologies Used

- **Backend**: Flask, SQLAlchemy, Flask-Login
- **Frontend**: Bootstrap 5, HTML, CSS, JavaScript
- **Data Analysis**: Pandas, NumPy, Scikit-Learn
- **Visualizations**: Plotly, Chart.js, D3.js
- **Database**: SQLite (development), PostgreSQL (production)
- **Security**: Werkzeug, Flask-WTF
- **AI/ML**: Spacy, Scikit-Learn, statistical analysis
- **Automation**: n8n, Celery (for background tasks)
- **Notifications**: SendGrid, Twilio, Slack
- **Server**: Gunicorn (production), Flask development server
- **Testing**: Pytest, unittest
- **Deployment**: Docker, Heroku, AWS

## License

This project is provided as-is for educational and personal use.

## Support

For issues or questions:
1. Check the logs in `app.log` and `finbuddy.log`
2. Review the error messages displayed in the browser
3. Ensure all dependencies are installed with the correct versions

---

**Version**: 1.0.0  
**Last Updated**: March 31, 2026
