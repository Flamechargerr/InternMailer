# Gmail App Password Setup Instructions

## Important: You need to set up an App Password to send emails via PowerShell

### Step 1: Enable 2-Step Verification
1. Go to your Google Account settings: https://myaccount.google.com/
2. Click on "Security" in the left sidebar
3. Under "Signing in to Google", click on "2-Step Verification"
4. Follow the prompts to enable 2-Step Verification if not already enabled

### Step 2: Generate App Password
1. Once 2-Step Verification is enabled, go back to Security settings
2. Under "Signing in to Google", click on "App passwords"
3. Select "Mail" from the dropdown
4. Select "Windows Computer" as the device
5. Click "Generate"
6. Google will show you a 16-character password (like: abcd efgh ijkl mnop)
7. **Copy this password** - you'll need it for the PowerShell script

### Step 3: Use the App Password
- When the PowerShell script asks for your password, use the 16-character App Password
- NOT your regular Gmail password

## Alternative: Using Gmail SMTP with OAuth2
If you prefer not to use App Passwords, you can also:
1. Use OAuth2 authentication (more complex setup)
2. Use a third-party email service like SendGrid or Mailgun

## Security Note
- App Passwords are more secure than "Less secure app access"
- Each App Password is unique to the application
- You can revoke App Passwords anytime from your Google Account settings

## Troubleshooting
- If emails aren't sending, check that 2-Step Verification is enabled
- Make sure you're using the App Password, not your regular password
- Check that you're not exceeding Gmail's sending limits (100 emails/day for free accounts)

## Gmail Sending Limits
- Free Gmail accounts: ~100 emails per day
- Google Workspace accounts: ~2000 emails per day
- Consider spacing out emails to avoid rate limiting
