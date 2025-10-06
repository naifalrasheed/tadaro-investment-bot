# 🚨 URGENT HOTFIX DEPLOYMENT COMMANDS

## Container Successfully Built: `tadaro-investment-bot:pro-610-hotfix`

### CRITICAL FIXES INCLUDED:
✅ **TwelveData Pro 610 API Key Fixed** - Your $79/month subscription will now work
✅ **Gunicorn Timeout: 120s → 300s** - No more worker timeouts
✅ **Performance Optimizations** - All batch processing improvements included

---

## STEP 1: Push Container to AWS ECR

```bash
# Navigate to the project directory
cd "/mnt/c/Users/alras/OneDrive/AI Agent Bot/investment_bot/src"

# Configure AWS credentials (if not already done)
aws configure
# Use Account: 593793060843
# Region: us-east-1
# AWS Access Key ID: [from your AWS Access Key file]
# AWS Secret Access Key: [from your AWS Access Key file]

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 593793060843.dkr.ecr.us-east-1.amazonaws.com

# Create ECR repository (if it doesn't exist)
aws ecr create-repository --repository-name tadaro-investment-bot --region us-east-1

# Tag the image for ECR
docker tag tadaro-investment-bot:pro-610-hotfix 593793060843.dkr.ecr.us-east-1.amazonaws.com/tadaro-investment-bot:pro-610-hotfix

# Push to ECR
docker push 593793060843.dkr.ecr.us-east-1.amazonaws.com/tadaro-investment-bot:pro-610-hotfix
```

---

## STEP 2: Update App Runner Service

```bash
# Get the App Runner service ARN
aws apprunner list-services --region us-east-1

# Update App Runner to use the new container (replace SERVICE-ARN with actual ARN)
aws apprunner update-service \
    --service-arn "arn:aws:apprunner:us-east-1:593793060843:service/tadaro-investment-bot/SERVICE-ID" \
    --source-configuration '{
        "ImageRepository": {
            "ImageIdentifier": "593793060843.dkr.ecr.us-east-1.amazonaws.com/tadaro-investment-bot:pro-610-hotfix",
            "ImageConfiguration": {
                "Port": "8000"
            },
            "ImageRepositoryType": "ECR"
        },
        "AutoDeploymentsEnabled": false
    }' \
    --region us-east-1
```

---

## STEP 3: Apply Database Schema Fix

```bash
# Connect to production PostgreSQL and run this SQL:
psql "$DATABASE_URL" -f production_database_fix.sql

# OR execute the SQL directly:
psql "$DATABASE_URL" -c "
DO \$\$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'stock_analysis'
        AND column_name = 'date'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE stock_analysis ADD COLUMN date TIMESTAMP DEFAULT NOW();
        RAISE NOTICE 'Added date column to stock_analysis table';
    END IF;
END \$\$;

UPDATE stock_analysis SET date = NOW() WHERE date IS NULL;
CREATE INDEX IF NOT EXISTS idx_stock_analysis_date ON stock_analysis(date DESC);
"
```

---

## STEP 4: Verify Deployment

After deployment, test these critical fixes:

1. **TwelveData API Working**: Stock analysis should show "Data Source: TwelveData"
2. **No Worker Timeouts**: Naif model should complete in <2 minutes
3. **Database Saves Working**: No more "column date does not exist" errors
4. **Real Data**: Application should stop using mock data

### Test URLs:
- **App Runner URL**: https://4thsn8tmbf.us-east-1.awsapprunner.com
- **Stock Analysis Test**: https://4thsn8tmbf.us-east-1.awsapprunner.com/analyze
- **Naif Model Test**: https://4thsn8tmbf.us-east-1.awsapprunner.com/naif-model

---

## EXPECTED RESULTS AFTER DEPLOYMENT:

### BEFORE (Current Issues):
❌ TwelveData API Error 401
❌ Worker timeout after 120 seconds
❌ Database error: column "date" does not exist
❌ Using mock data for analysis

### AFTER (With Hotfix):
✅ TwelveData Pro 610 API working (600 req/min)
✅ Worker timeout increased to 300 seconds
✅ Database saves working properly
✅ Real financial data analysis

---

## TROUBLESHOOTING:

If App Runner deployment fails:
1. Check App Runner logs in AWS Console
2. Verify ECR image was pushed successfully
3. Ensure App Runner service has ECR permissions

If database fix fails:
1. Verify DATABASE_URL environment variable
2. Check PostgreSQL connection permissions
3. Run the SQL manually in AWS RDS console

---

**PRIORITY**: Deploy immediately to restore your $79/month TwelveData subscription functionality!