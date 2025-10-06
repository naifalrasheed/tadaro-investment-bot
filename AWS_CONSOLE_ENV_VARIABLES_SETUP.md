# AWS CONSOLE ENVIRONMENT VARIABLES SETUP
**For GitHub Source App Runner Deployment**

---

## CRITICAL FIX REQUIRED

The `value-from` syntax is **NOT SUPPORTED** in GitHub source deployments. Environment variables must be configured manually in AWS Console.

---

## ENVIRONMENT VARIABLES TO ADD IN AWS CONSOLE

After creating the App Runner service, **manually add these environment variables**:

### **Step 1: Navigate to Service Configuration**
1. Open AWS App Runner Console
2. Select your new service: `tadaro-investment-bot-github`
3. Click **"Configuration"** tab
4. Click **"Edit"** in Environment variables section

### **Step 2: Add Required Environment Variables**

**Add these 7 environment variables manually:**

#### **API Keys (Critical for functionality)**
```
Name: TWELVEDATA_API_KEY
Value: 4420a6f49fbf468c843c102571ec7329

Name: ALPHA_VANTAGE_API_KEY
Value: [Get from AWS Secrets Manager]

Name: CLAUDE_API_KEY
Value: [Get from AWS Secrets Manager]
```

#### **Database & Security**
```
Name: DATABASE_URL
Value: [PostgreSQL connection string from Secrets Manager]

Name: SECRET_KEY
Value: [Flask secret key from Secrets Manager]

Name: FLASK_SECRET_KEY
Value: [Same as SECRET_KEY]
```

#### **Google OAuth**
```
Name: GOOGLE_CLIENT_SECRET
Value: [Google OAuth secret from Secrets Manager]

Name: GOOGLE_CLIENT_ID
Value: [Google OAuth client ID]
```

---

## HOW TO GET SECRET VALUES

### **Method 1: AWS CLI (If available)**
```bash
# TwelveData API Key
aws secretsmanager get-secret-value --secret-id "tadaro-investment-bot/twelvedata-api-key" --region us-east-1 --query "SecretString" --output text

# Database URL
aws secretsmanager get-secret-value --secret-id "tadaro-investment-bot/database-url" --region us-east-1 --query "SecretString" --output text

# Flask Secret Key
aws secretsmanager get-secret-value --secret-id "tadaro-investment-bot/flask-secret-key" --region us-east-1 --query "SecretString" --output text

# Claude API Key
aws secretsmanager get-secret-value --secret-id "tadaro-investment-bot/claude-api-key" --region us-east-1 --query "SecretString" --output text

# Alpha Vantage API Key
aws secretsmanager get-secret-value --secret-id "tadaro-investment-bot/ALPHA_VANTAGE_API_KEY" --region us-east-1 --query "SecretString" --output text

# Google Client Secret
aws secretsmanager get-secret-value --secret-id "tadaro-investment-bot/google-client-secret" --region us-east-1 --query "SecretString" --output text
```

### **Method 2: AWS Console**
1. Navigate to **AWS Secrets Manager**: https://console.aws.amazon.com/secretsmanager/home?region=us-east-1
2. Search for secrets starting with `tadaro-investment-bot/`
3. Click on each secret and **"Retrieve secret value"**
4. Copy the value to App Runner environment variables

---

## SIMPLIFIED DEPLOYMENT PROCESS

### **Option A: Basic Deployment (Recommended)**
1. **Fix apprunner.yaml**: ✅ Already fixed (removed value-from syntax)
2. **Create App Runner Service**: Use GitHub source with configuration file
3. **Add Environment Variables**: Manually in AWS Console after service creation
4. **Deploy**: Service will rebuild with environment variables

### **Option B: Known Working Values**
If you have access to these known working values:

```bash
# Critical Values (These are definitely needed)
TWELVEDATA_API_KEY=4420a6f49fbf468c843c102571ec7329
ENVIRONMENT=production
FLASK_ENV=production
PORT=8000

# Database (Check if RDS is still running)
DATABASE_URL=postgresql://username:password@host:5432/dbname

# Flask Security (Generate new if needed)
SECRET_KEY=[32-character random string]
FLASK_SECRET_KEY=[Same as SECRET_KEY]
```

---

## DEPLOYMENT STEPS (Updated)

### **Step 1: Commit Fixed apprunner.yaml**
```bash
git add apprunner.yaml
git commit -m "Fix apprunner.yaml: Remove value-from syntax for GitHub source deployment"
git push origin main
```

### **Step 2: Create App Runner Service (AWS Console)**
1. **Source**: GitHub repository
2. **Repository**: `https://github.com/naifalrasheed/tadaro-investment-bot`
3. **Branch**: `main`
4. **Configuration**: Use configuration file (apprunner.yaml)
5. **Service Name**: `tadaro-investment-bot-github`

### **Step 3: Add Environment Variables (After Service Creation)**
1. Wait for initial deployment to complete (may fail due to missing env vars)
2. Go to service **Configuration** tab
3. **Edit** environment variables
4. Add all 7+ variables listed above
5. **Save** - this will trigger automatic redeployment

### **Step 4: Monitor Deployment**
- Build should complete successfully
- Application should start without environment variable errors
- Test endpoints to verify weighted averaging is eliminated

---

## SUCCESS CRITERIA

### **After Environment Variables Added**:
- ✅ Service status: **RUNNING**
- ✅ Health endpoint: `https://[service-url]/health` returns **HTTP 200**
- ✅ **No weighted averaging** in logs or API responses
- ✅ **TwelveData integration** working (not 401 errors)
- ✅ **Database connection** successful
- ✅ **User authentication** functional

---

## TROUBLESHOOTING

### **If Build Fails:**
- Check **Logs** in App Runner console for specific error
- Ensure `apprunner.yaml` has no syntax errors
- Verify all required dependencies in `requirements.txt`

### **If Application Fails to Start:**
- **Missing environment variables**: Add them via Console
- **Database connection**: Verify DATABASE_URL is correct
- **API key issues**: Verify TWELVEDATA_API_KEY is valid

### **If Weighted Averaging Persists:**
- Check application logs for data source selection
- Verify latest code is deployed (commit with data_comparison_service fixes)
- Test endpoint: `/api/analyze/MSFT` should use priority-based selection

---

This approach will **bypass the value-from syntax limitation** and get your deployment working with manual environment variable configuration.