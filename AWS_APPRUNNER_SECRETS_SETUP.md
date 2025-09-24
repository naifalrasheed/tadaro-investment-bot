# AWS App Runner Secrets Manager Configuration

## Current Issue
The TwelveData analyzer now supports AWS Secrets Manager, but AWS App Runner needs to be configured to reference the secret properly.

## AWS App Runner Environment Variable Configuration

### Option 1: Reference Secret in AWS App Runner (Recommended)
1. Go to AWS App Runner Console
2. Select your service: `tadaro-investment-bot`
3. Go to **Configuration** → **Environment variables**
4. Update `TWELVEDATA_API_KEY` to reference the secret:

**Format for Secrets Manager Reference:**
```
Name: TWELVEDATA_API_KEY
Value: arn:aws:secretsmanager:us-east-1:593793060843:secret:tadaro-investment-bot/twelvedata-api-key:SecretString
```

**Alternative JSON format:**
```
Name: TWELVEDATA_API_KEY
Value: {"secret": "tadaro-investment-bot/twelvedata-api-key", "field": ""}
```

### Option 2: Direct Secret Access (Automatic Fallback)
If the environment variable is not set, the application will automatically try to access:
- Secret Name: `tadaro-investment-bot/twelvedata-api-key`
- Region: `us-east-1`
- Account: `593793060843`

## IAM Role Configuration
Ensure your App Runner service has these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": "arn:aws:secretsmanager:us-east-1:593793060843:secret:tadaro-investment-bot/twelvedata-api-key*"
        }
    ]
}
```

## Testing the Configuration

### Test 1: Run Windows Batch Tests
```cmd
cd "C:\Users\alras\OneDrive\AI Agent Bot\investment_bot\src"
test_api_windows.bat
```

### Test 2: Test AWS Secrets Manager
```cmd
test_aws_secrets.bat
```

### Test 3: Verify Deployment
```cmd
verify_deployment.bat
```

## Expected Behavior After Configuration

### Success Logs:
```
INFO: API key loaded from environment variable
INFO: TwelveData API Key configured (ending in ****XXXX)
INFO: TwelveData Pro 610 API initialized successfully
INFO: TwelveData API key validation successful
INFO: Selected single data source: twelvedata from X available sources
```

### Failure Logs (if not configured):
```
ERROR: TWELVEDATA_API_KEY not found. Configure it either as:
1. Environment variable: TWELVEDATA_API_KEY=your_key
2. AWS Secrets Manager reference in AWS App Runner
3. Direct AWS Secrets Manager: tadaro-investment-bot/twelvedata-api-key
```

## Verification Steps

1. **Check App Logs**: Look for "API key loaded from" messages
2. **Test Stock Analysis**: Data source should show "TwelveData (Real-time)"
3. **No 401 Errors**: Should not see authentication failures
4. **Single Source Data**: Should see "Priority Selection" badge, not "Reconciled Data"

## Troubleshooting

### If Still Getting Alpha Vantage Data:
- Check environment variable configuration in App Runner
- Verify secret exists in Secrets Manager
- Check IAM permissions for the service role

### If Getting 401 Errors:
- Verify API key value in Secrets Manager
- Test API key directly with batch files
- Check TwelveData subscription status

### If Getting Import Errors:
- Ensure boto3 is in requirements.txt (should be added automatically)
- Check Python version compatibility

## API Key Format
TwelveData API keys should be:
- 32 characters long
- Alphanumeric characters
- Example format: `4420a6f49fbf468c843c102571ec7329`

## Security Notes
- Never commit API keys to version control
- Use Secrets Manager for production
- Environment variables acceptable for development
- The application will never log full API keys (only last 4 digits)