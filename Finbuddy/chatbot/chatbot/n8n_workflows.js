/**
 * FinBuddy n8n Integration Configuration
 * 
 * Setup Guide for Automating Financial Workflows
 * 
 * Prerequisites:
 * - n8n installed and running (http://localhost:5678)
 * - FinBuddy API is accessible
 * - API keys configured in environment variables
 */

// Sample n8n Workflow Configurations

// ============ 1. Weekly Spending Summary Workflow ============
// Triggers every Sunday at 9 AM
// Sends email summary of weekly spending
const weeklySpendingWorkflow = {
  name: "Weekly Spending Summary",
  nodes: [
    {
      name: "Schedule",
      type: "n8n-nodes-base.cron",
      parameters: {
        cronExpression: "0 9 * * 0" // Every Sunday at 9 AM
      }
    },
    {
      name: "Get User ID",
      type: "n8n-nodes-base.code",
      parameters: {
        jsCode: "return [{ json: { userId: $input.first().json.userId } }]"
      }
    },
    {
      name: "Fetch Spending Overview",
      type: "n8n-nodes-base.httpRequest",
      parameters: {
        url: "http://localhost:5000/api/insights/overview?days=7",
        method: "GET",
        authentication: "bearerToken",
        options: {
          headers: {
            Authorization: "Bearer YOUR_API_TOKEN"
          }
        }
      }
    },
    {
      name: "Format Email",
      type: "n8n-nodes-base.code",
      parameters: {
        jsCode: `
          const data = $input.first().json;
          return [{
            json: {
              subject: "Your Weekly Spending Summary",
              body: \`
                <h2>Weekly Spending Summary</h2>
                <p>Total Spent: ₹\${data.total_spending}</p>
                <p>Daily Average: ₹\${data.daily_average}</p>
                <h3>Breakdown by Category:</h3>
                <ul>
                  \${Object.entries(data.category_breakdown)
                    .map(([cat, amt]) => \`<li>\${cat}: ₹\${amt}</li>\`)
                    .join('')}
                </ul>
              \`
            }
          }]
        `
      }
    },
    {
      name: "Send Email",
      type: "n8n-nodes-base.sendGrid",
      parameters: {
        authentication: "sendGridApi",
        to: "$input.first().json.userEmail",
        subject: "$input.first().json.subject",
        text: "$input.first().json.body"
      }
    }
  ]
};

// ============ 2. Budget Alert Workflow ============
// Triggers when spending exceeds 80% of budget
// Sends notification to user
const budgetAlertWorkflow = {
  name: "Budget Alert Notification",
  nodes: [
    {
      name: "Check Budget Status",
      type: "n8n-nodes-base.httpRequest",
      parameters: {
        url: "http://localhost:5000/api/insights/recommendations",
        method: "GET"
      }
    },
    {
      name: "Filter High Spending",
      type: "n8n-nodes-base.code",
      parameters: {
        jsCode: `
          const recs = $input.first().json.recommendations;
          const alerts = recs.filter(r => r.type === 'increase_budget');
          return alerts.length > 0 ? [{ json: { alerts } }] : [];
        `
      }
    },
    {
      name: "Send Slack Message",
      type: "n8n-nodes-base.slack",
      parameters: {
        authentication: "slackApi",
        channel: "#finbuddy-alerts",
        text: "⚠️ Budget Alert: You're spending more than budgeted in some categories."
      }
    }
  ]
};

// ============ 3. Recurring Expense Tracking Workflow ============
// Tracks subscription and recurring payments
// Sends monthly reminder of recurring expenses
const recurringExpenseWorkflow = {
  name: "Recurring Expense Tracker",
  nodes: [
    {
      name: "Monthly Trigger",
      type: "n8n-nodes-base.cron",
      parameters: {
        cronExpression: "0 0 1 * *" // First day of every month
      }
    },
    {
      name: "Get Recurring Expenses",
      type: "n8n-nodes-base.httpRequest",
      parameters: {
        url: "http://localhost:5000/api/insights/overview?category=subscriptions",
        method: "GET"
      }
    },
    {
      name: "Create Expense Record",
      type: "n8n-nodes-base.code",
      parameters: {
        jsCode: `
          const data = $input.first().json;
          // Auto-create monthly recurring expense entries
          return [{
            json: {
              entries: data.recurring_items.map(item => ({
                amount: item.amount,
                category: 'subscriptions',
                description: \`Monthly: \${item.name}\`,
                date: new Date().toISOString()
              }))
            }
          }]
        `
      }
    }
  ]
};

// ============ 4. Goal Progress Notification Workflow ============
// Checks financial goal progress
// Sends encouragement or suggestions
const goalProgressWorkflow = {
  name: "Financial Goal Progress Update",
  nodes: [
    {
      name: "Daily Check",
      type: "n8n-nodes-base.cron",
      parameters: {
        cronExpression: "0 9 * * *" // Daily at 9 AM
      }
    },
    {
      name: "Get Goal Progress",
      type: "n8n-nodes-base.httpRequest",
      parameters: {
        url: "http://localhost:5000/api/insights/goals",
        method: "GET"
      }
    },
    {
      name: "Evaluate Progress",
      type: "n8n-nodes-base.code",
      parameters: {
        jsCode: `
          const goals = $input.first().json.goals;
          const messages = goals.map(goal => {
            if (goal.on_track) {
              return \`✅ Goal '\${goal.purpose}': You're on track! \${goal.progress_percentage.toFixed(1)}% complete.\`;
            } else {
              return \`⚠️ Goal '\${goal.purpose}': Increase savings by ₹\${goal.daily_required_savings.toFixed(2)}/day to stay on track.\`;
            }
          });
          return [{ json: { messages } }]
        `
      }
    },
    {
      name: "Send Notification",
      type: "n8n-nodes-base.discord",
      parameters: {
        authentication: "discordWebhook",
        content: "$input.first().json.messages.join('\\n')"
      }
    }
  ]
};

// ============ 5. Data Backup Workflow ============
// Daily backup of financial data
// Exports to cloud storage
const dataBackupWorkflow = {
  name: "Daily Financial Data Backup",
  nodes: [
    {
      name: "Daily Trigger",
      type: "n8n-nodes-base.cron",
      parameters: {
        cronExpression: "0 2 * * *" // Daily at 2 AM
      }
    },
    {
      name: "Export User Data",
      type: "n8n-nodes-base.httpRequest",
      parameters: {
        url: "http://localhost:5000/api/insights/overview",
        method: "GET"
      }
    },
    {
      name: "Format as CSV",
      type: "n8n-nodes-base.code",
      parameters: {
        jsCode: `
          const data = $input.first().json;
          const csv = "Category,Amount\\n" + 
            Object.entries(data.category_breakdown)
              .map(([cat, amt]) => \`\${cat},\${amt}\`)
              .join('\\n');
          return [{ json: { filename: \`backup_\${new Date().toISOString()}.csv\`, content: csv } }]
        `
      }
    },
    {
      name: "Upload to Google Drive",
      type: "n8n-nodes-base.googleDrive",
      parameters: {
        authentication: "googleDriveOAuth2",
        operation: "upload",
        file: "$input.first().json.content",
        filename: "$input.first().json.filename",
        folderId: "YOUR_GOOGLE_DRIVE_FOLDER_ID"
      }
    }
  ]
};

// ============ 6. Anomaly Alert Workflow ============
// Detects unusual spending patterns
// Alerts user to potential fraud or errors
const anomalyAlertWorkflow = {
  name: "Spending Anomaly Detection",
  nodes: [
    {
      name: "Real-time Trigger",
      type: "n8n-nodes-base.webhook",
      parameters: {
        httpMethod: "POST",
        path: "finbuddy/expense-created"
      }
    },
    {
      name: "Detect Anomalies",
      type: "n8n-nodes-base.httpRequest",
      parameters: {
        url: "http://localhost:5000/api/insights/anomalies",
        method: "GET"
      }
    },
    {
      name: "Filter Recent Anomalies",
      type: "n8n-nodes-base.code",
      parameters: {
        jsCode: `
          const anomalies = $input.first().json.anomalies;
          const critical = anomalies.filter(a => a.severity === 'high');
          return critical.length > 0 ? [{ json: { alerts: critical } }] : [];
        `
      }
    },
    {
      name: "Send SMS Alert",
      type: "n8n-nodes-base.twilio",
      parameters: {
        authentication: "twilioApi",
        to: "$input.first().json.userPhone",
        message: "🚨 Unusual spending detected. Please verify this transaction."
      }
    }
  ]
};

// ============ 7. Savings Suggestion Workflow ============
// Weekly savings opportunity reminders
// Based on spending patterns
const savingsSuggestionWorkflow = {
  name: "Weekly Savings Opportunities",
  nodes: [
    {
      name: "Weekly Trigger",
      type: "n8n-nodes-base.cron",
      parameters: {
        cronExpression: "0 10 * * 1" // Every Monday at 10 AM
      }
    },
    {
      name: "Calculate Savings Potential",
      type: "n8n-nodes-base.httpRequest",
      parameters: {
        url: "http://localhost:5000/api/insights/savings-potential",
        method: "GET"
      }
    },
    {
      name: "Format Suggestions",
      type: "n8n-nodes-base.code",
      parameters: {
        jsCode: `
          const data = $input.first().json.data;
          const tips = data.reduction_tips.map(tip =>
            \`💡 \${tip.category.toUpperCase()}: \${tip.tip} (Save ₹\${tip.savings.toFixed(2)}/month)\`
          ).join('\\n');
          
          return [{
            json: {
              subject: "Weekly Savings Opportunities",
              body: \`
                <h2>Here's how you can save more:</h2>
                <p><strong>Potential Monthly Savings: ₹\${data.potential_monthly_savings.toFixed(2)}</strong></p>
                <pre>\${tips}</pre>
              \`
            }
          }]
        `
      }
    },
    {
      name: "Send Email",
      type: "n8n-nodes-base.sendGrid",
      parameters: {
        to: "$input.first().json.userEmail",
        subject: "$input.first().json.subject",
        html: "$input.first().json.body"
      }
    }
  ]
};

// ============ Environment Variables Required ============
const envVars = {
  SENDGRID_API_KEY: "your-sendgrid-api-key",
  SLACK_WEBHOOK_URL: "your-slack-webhook-url",
  DISCORD_WEBHOOK_URL: "your-discord-webhook-url",
  TWILIO_ACCOUNT_SID: "your-twilio-account-sid",
  TWILIO_AUTH_TOKEN: "your-twilio-auth-token",
  GOOGLE_DRIVE_FOLDER_ID: "your-google-drive-folder-id",
  FINBUDDY_API_TOKEN: "your-finbuddy-api-token",
  FINBUDDY_API_URL: "http://localhost:5000"
};

module.exports = {
  weeklySpendingWorkflow,
  budgetAlertWorkflow,
  recurringExpenseWorkflow,
  goalProgressWorkflow,
  dataBackupWorkflow,
  anomalyAlertWorkflow,
  savingsSuggestionWorkflow,
  envVars
};
