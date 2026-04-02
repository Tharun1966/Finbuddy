# n8n Integration Setup Guide

This guide walks you through setting up n8n workflows with FinBuddy for automated financial management.

## What is n8n?

n8n is a fair-code, open-source workflow automation platform. It allows you to automate repetitive financial tasks and connect FinBuddy with other services like email, Slack, SMS, Google Drive, and more.

## Installation

### 1. Install n8n

```bash
# Using npm
npm install -g n8n

# Using Docker (recommended)
docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n
```

### 2. Start n8n

```bash
n8n
# or with Docker
docker run -d --name n8n -p 5678:5678 n8nio/n8n
```

### 3. Access n8n UI
Open your browser and go to: `http://localhost:5678`

## Setting Up FinBuddy Integration

### Step 1: Create API Credentials

In n8n:
1. Go to **Settings** → **Credentials**
2. Click **New**
3. Choose **HTTP Request**
4. Configure:
   - Name: `FinBuddy API`
   - Authentication: Bearer Token
   - Token: Your FinBuddy API token

### Step 2: Configure Notification Services

#### Email (SendGrid)
1. Create a SendGrid account and get API key
2. In n8n Settings → Credentials → SendGrid
3. Enter your SendGrid API key

#### SMS (Twilio)
1. Create a Twilio account
2. Get Account SID and Auth Token
3. In n8n Settings → Credentials → Twilio
4. Enter credentials

#### Slack
1. Create a Slack webhook or get an API token
2. In n8n Settings → Credentials → Slack
3. Enter webhook URL or API token

#### Discord
1. Create a Discord webhook in your server
2. Copy the webhook URL
3. Use in Discord node in workflows

## Pre-built Workflow Templates

### 1. Weekly Spending Summary

**Trigger:** Every Sunday at 9 AM  
**Action:** Send email with weekly spending breakdown

**Setup:**
1. Create new workflow
2. Add **Cron** node with trigger: `0 9 * * 0`
3. Add **FinBuddy API** node pointing to `/api/insights/overview?days=7`
4. Add **SendGrid** node to send summary email

### 2. Budget Alert Notifications

**Trigger:** Manual or scheduled check  
**Action:** Send alert when spending exceeds budget

**Setup:**
1. Add **Cron** node (daily check)
2. Add FinBuddy **API** node: `/api/insights/recommendations`
3. Add **Slack** node to send alerts

```
Budget Alert: You're spending more than budgeted in {{$node.FinBuddy.json.category}}.
Recommended budget: ₹{{$node.FinBuddy.json.suggested_budget}}
```

### 3. Recurring Expense Tracker

**Trigger:** First of every month  
**Action:** Create expense entries for subscriptions

**Setup:**
1. Add **Cron** node: `0 0 1 * *` (1st of month)
2. Query database for recurring items
3. Create expense entries automatically

### 4. Financial Goal Progress Reminder

**Trigger:** Daily at 9 AM  
**Action:** Get goal progress and send motivation/tips

**Setup:**
1. Add **Cron** node (daily)
2. Add FinBuddy API node: `/api/insights/goals`
3. Add conditional logic to send different messages
4. Send via SMS or email

### 5. Spending Anomaly Detection

**Trigger:** Real-time on expense creation  
**Action:** Alert if unusual spending detected

**Setup:**
1. Add **Webhook** node to receive expense events
2. Add FinBuddy API node: `/api/insights/anomalies`
3. Add **Twilio** (SMS) or **Slack** notification node

### 6. Data Backup to Google Drive

**Trigger:** Daily at 2 AM  
**Action:** Export and backup financial data

**Setup:**
1. Add **Cron** node: `0 2 * * *`
2. Add FinBuddy API node to get data
3. Convert to CSV format
4. Upload to Google Drive using **Google Drive** node

### 7. Savings Optimization Tips

**Trigger:** Every Wednesday  
**Action:** Send personalized savings tips

**Setup:**
1. Add **Cron** node (Wednesday 10 AM)
2. Add FinBuddy API node: `/api/insights/savings-potential`
3. Format response with tips
4. Send via email or Slack

## Advanced Configuration

### Webhook URL Configuration

To enable real-time triggers from FinBuddy:

1. In n8n, create a **Webhook** node
2. Copy the webhook URL
3. In FinBuddy `.env`, set:
   ```
   N8N_WEBHOOK_URL=<webhook-url-from-n8n>
   ```

### Conditional Logic Example

```javascript
// In n8n Code node
if ($input.first().json.savings_percentage > 20) {
  return [{ json: { message: "🎉 Excellent savings rate!" } }];
} else if ($input.first().json.savings_percentage > 10) {
  return [{ json: { message: "👍 Good job saving!" } }];
} else {
  return [{ json: { message: "💡 Try to save more" } }];
}
```

### Error Handling

All workflows should include error handling:

1. Add an **Error Trigger** node after HTTP requests
2. Configure fallback actions (e.g., send error notification)
3. Log errors for debugging

```javascript
// Email yourself on error
return [{
  json: {
    subject: "FinBuddy Workflow Error",
    body: "Error: " + $execution.lastNodeExecuted
  }
}];
```

## Monitoring & Debugging

### View Execution Logs
1. Go to **Executions** tab in n8n
2. See which workflows ran and their status
3. Debug failed executions

### Common Issues

| Issue | Solution |
|-------|----------|
| API 401 Unauthorized | Check API token in credentials |
| API Connection Failed | Ensure FinBuddy is running on port 5000 |
| Webhook Not Triggering | Verify webhook URL is correct and active |
| Email Not Sent | Check SendGrid API key and email limits |
| Slack Message Failed | Verify webhook URL or API token |

## Best Practices

1. **Test Workflows First**
   - Use test runs before activating
   - Check data mapping carefully

2. **Error Handling**
   - Add error nodes to all workflows
   - Include retry logic for API calls

3. **Performance**
   - Don't run checks too frequently
   - Consider using daily/weekly triggers instead of hourly

4. **Security**
   - Store API keys in n8n credentials, not in workflow
   - Use environment variables for sensitive data
   - Keep API tokens rotated

5. **Monitoring**
   - Check execution logs regularly
   - Set up notifications for workflow failures
   - Subscribe to n8n updates for new features

## Example n8n Workflow JSON

```json
{
  "name": "Weekly FinBuddy Summary",
  "nodes": [
    {
      "parameters": {
        "cronExpression": "0 9 * * 0"
      },
      "name": "Every Sunday 9am",
      "type": "n8n-nodes-base.cron",
      "typeVersion": 1,
      "position": [250, 300]
    },
    {
      "parameters": {
        "url": "http://localhost:5000/api/insights/overview?days=7",
        "authentication": "bearerToken",
        "options": {}
      },
      "name": "Get Weekly Spending",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.1,
      "position": [450, 300]
    }
  ],
  "connections": {
    "Every Sunday 9am": {
      "main": [
        [
          {
            "node": "Get Weekly Spending",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

## Support & Resources

- [n8n Documentation](https://docs.n8n.io)
- [FinBuddy API Documentation](./README.md#api-endpoints)
- [n8n Community](https://community.n8n.io)

## Troubleshooting

### Enable Debug Mode
Set in `.env`:
```
N8N_LOG_LEVEL=debug
```

### Test API Connection
```bash
curl -X GET http://localhost:5000/api/insights/overview \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Check n8n Logs
```bash
# Docker
docker logs n8n

# npm
# Check console output
```

---

For additional help or custom workflows, refer to the main README.md file.
