#!/bin/bash
# Emergency Deployment Script for TwelveData API & Mock Data Fixes
# Run this script after Docker build completes

set -e

echo "========================================="
echo "🚨 EMERGENCY DEPLOYMENT SCRIPT"
echo "========================================="
echo ""
echo "This script will:"
echo "✅ Tag the emergency fix container for ECR"
echo "✅ Push container to AWS ECR"
echo "✅ Update App Runner service with new container"
echo "✅ Monitor deployment status"
echo ""

# Configuration
ECR_REGISTRY="593793060843.dkr.ecr.us-east-1.amazonaws.com"
ECR_REPOSITORY="tadaro-investment-bot"
IMAGE_TAG="emergency-real-data"
SERVICE_ARN="arn:aws:apprunner:us-east-1:593793060843:service/tadaro-investment-bot/d8c7ae08baca472bbd2fb0db0d960c51"
REGION="us-east-1"
PRODUCTION_URL="https://4thsn8tmbf.us-east-1.awsapprunner.com"

# Step 1: Verify Docker image exists
echo "Step 1: Verifying Docker image exists..."
if docker images | grep -q "tadaro-investment-bot:emergency-real-data"; then
    echo "✅ Docker image 'tadaro-investment-bot:emergency-real-data' found"
else
    echo "❌ Docker image not found. Please run:"
    echo "   docker build -t tadaro-investment-bot:emergency-real-data ."
    exit 1
fi

# Step 2: Login to ECR
echo ""
echo "Step 2: Logging into AWS ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

if [ $? -eq 0 ]; then
    echo "✅ Successfully logged into ECR"
else
    echo "❌ Failed to login to ECR"
    exit 1
fi

# Step 3: Tag image for ECR
echo ""
echo "Step 3: Tagging image for ECR..."
docker tag tadaro-investment-bot:emergency-real-data $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG

if [ $? -eq 0 ]; then
    echo "✅ Image tagged successfully"
else
    echo "❌ Failed to tag image"
    exit 1
fi

# Step 4: Push to ECR
echo ""
echo "Step 4: Pushing to ECR..."
docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG

if [ $? -eq 0 ]; then
    echo "✅ Container pushed to ECR successfully"
else
    echo "❌ Failed to push to ECR"
    exit 1
fi

# Step 5: Update App Runner service
echo ""
echo "Step 5: Updating App Runner service..."
aws apprunner update-service \
    --service-arn "$SERVICE_ARN" \
    --source-configuration "{
        \"ImageRepository\": {
            \"ImageIdentifier\": \"$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG\",
            \"ImageConfiguration\": {
                \"Port\": \"8000\"
            },
            \"ImageRepositoryType\": \"ECR\"
        },
        \"AutoDeploymentsEnabled\": false
    }" \
    --region $REGION

if [ $? -eq 0 ]; then
    echo "✅ App Runner service update initiated"
else
    echo "❌ Failed to update App Runner service"
    exit 1
fi

# Step 6: Monitor deployment status
echo ""
echo "Step 6: Monitoring deployment status..."
echo "Waiting for service to update..."

check_deployment() {
    local max_attempts=20
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        echo "Attempt $attempt/$max_attempts: Checking deployment status..."

        STATUS=$(aws apprunner describe-service \
            --service-arn "$SERVICE_ARN" \
            --region $REGION \
            --query "Service.Status" \
            --output text)

        echo "Current Status: $STATUS"

        case $STATUS in
            "RUNNING")
                echo ""
                echo "========================================="
                echo "🎉 EMERGENCY DEPLOYMENT SUCCESSFUL!"
                echo "========================================="
                echo ""
                echo "✅ TwelveData Pro 610 API key now active"
                echo "✅ Mock data system completely disabled"
                echo "✅ Real financial data sources only"
                echo ""
                echo "🧪 TEST YOUR FIX:"
                echo "URL: $PRODUCTION_URL/analyze"
                echo "Test Symbol: MSFT"
                echo ""
                echo "Expected Results:"
                echo "• Data Source: 'TwelveData' (not Alpha Vantage)"
                echo "• Real MSFT price (~$518)"
                echo "• Accurate 52-week high/low"
                echo "• No mock data messages in logs"
                echo ""
                return 0
                ;;
            "CREATE_FAILED"|"UPDATE_FAILED")
                echo ""
                echo "❌ DEPLOYMENT FAILED!"
                echo "Status: $STATUS"
                echo ""
                echo "Please check AWS Console for detailed error logs:"
                echo "https://console.aws.amazon.com/apprunner/home?region=us-east-1"
                return 1
                ;;
            "OPERATION_IN_PROGRESS")
                echo "⏳ Deployment in progress, waiting 30 seconds..."
                sleep 30
                ;;
            *)
                echo "⏳ Status: $STATUS, waiting 30 seconds..."
                sleep 30
                ;;
        esac

        attempt=$((attempt + 1))
    done

    echo ""
    echo "⚠️  Deployment monitoring timed out after $max_attempts attempts"
    echo "Please check deployment status manually:"
    echo "aws apprunner describe-service --service-arn '$SERVICE_ARN' --region $REGION"
    return 1
}

# Run deployment monitoring
check_deployment

# Final instructions
echo ""
echo "========================================="
echo "📋 POST-DEPLOYMENT CHECKLIST"
echo "========================================="
echo ""
echo "1. Test the fix:"
echo "   curl '$PRODUCTION_URL/analyze' -d 'symbol=MSFT'"
echo ""
echo "2. Verify TwelveData usage in logs:"
echo "   aws logs tail /aws/apprunner/tadaro-investment-bot --region $REGION"
echo ""
echo "3. Check for these success indicators:"
echo "   ✅ 'Data Source: TwelveData' in responses"
echo "   ✅ No 401 TwelveData API errors"
echo "   ✅ No 'Using mock data' messages"
echo "   ✅ Real financial metrics displayed"
echo ""
echo "4. If issues persist, check the documentation:"
echo "   cat EMERGENCY_FIX_DOCUMENTATION.md"
echo ""
echo "🎯 Emergency deployment complete!"