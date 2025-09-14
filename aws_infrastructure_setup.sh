#!/bin/bash
# AWS Infrastructure Setup for Tadaro.ai Investment Bot
# Run these commands in your Windows PowerShell with AWS CLI configured

echo "Starting AWS Infrastructure Setup for tadaro.ai..."
echo "Account: 593793060843, Region: us-east-1"

# 1. Create VPC and Security Group
echo "Step 1: Creating VPC and Security Groups..."
aws ec2 create-vpc --cidr-block 10.0.0.0/16 --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=tadaro-vpc},{Key=Project,Value=investment-bot}]' --region us-east-1

# Get VPC ID (you'll need to replace VPC_ID with actual ID from above command)
# VPC_ID=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=tadaro-vpc" --query 'Vpcs[0].VpcId' --output text --region us-east-1)

# Create Internet Gateway
aws ec2 create-internet-gateway --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=tadaro-igw},{Key=Project,Value=investment-bot}]' --region us-east-1

# Create Security Group for App Runner
aws ec2 create-security-group --group-name tadaro-app-sg --description "Security group for Tadaro Investment Bot App Runner" --vpc-id VPC_ID --region us-east-1

# Create Security Group for RDS
aws ec2 create-security-group --group-name tadaro-rds-sg --description "Security group for Tadaro RDS PostgreSQL" --vpc-id VPC_ID --region us-east-1

# Configure Security Group Rules
aws ec2 authorize-security-group-ingress --group-id SG_ID --protocol tcp --port 443 --cidr 0.0.0.0/0 --region us-east-1
aws ec2 authorize-security-group-ingress --group-id SG_ID --protocol tcp --port 80 --cidr 0.0.0.0/0 --region us-east-1

echo "Step 2: Creating Route 53 Hosted Zone..."
# Create Route 53 Hosted Zone
aws route53 create-hosted-zone --name tadaro.ai --caller-reference tadaro-$(date +%s)

echo "Step 3: Requesting SSL Certificate..."
# Request SSL Certificate
aws acm request-certificate --domain-name tadaro.ai --domain-name *.tadaro.ai --validation-method DNS --region us-east-1

echo "Step 4: Creating RDS Subnet Group..."
# Create DB Subnet Group (you'll need subnet IDs)
aws rds create-db-subnet-group --db-subnet-group-name tadaro-db-subnet-group --db-subnet-group-description "DB subnet group for Tadaro Investment Bot" --subnet-ids subnet-12345 subnet-67890 --region us-east-1

echo "Step 5: Creating RDS PostgreSQL Instance..."
# Create RDS PostgreSQL Instance
aws rds create-db-instance \
    --db-instance-identifier tadaro-prod-db \
    --db-instance-class db.t4g.micro \
    --engine postgres \
    --engine-version 15.7 \
    --master-username tadaro_admin \
    --master-user-password "TadaroSecure2025!" \
    --allocated-storage 20 \
    --vpc-security-group-ids sg-rds-id \
    --db-subnet-group-name tadaro-db-subnet-group \
    --backup-retention-period 7 \
    --storage-encrypted \
    --region us-east-1 \
    --tags Key=Name,Value=tadaro-prod-db Key=Project,Value=investment-bot

echo "Step 6: Setting up App Runner Service..."
# App Runner will be configured after containerization

echo "AWS Infrastructure setup commands prepared!"
echo "Next steps:"
echo "1. Run these commands in your PowerShell"
echo "2. Update GoDaddy DNS with Route 53 name servers"
echo "3. Validate SSL certificate via DNS"
echo "4. Configure database connection strings"

# Store important values
echo "Save these values for application configuration:"
echo "DB_HOST: tadaro-prod-db.amazonaws.com (will be provided after RDS creation)"
echo "DB_NAME: tadaro_prod"
echo "DB_USER: tadaro_admin"
echo "DB_PASSWORD: TadaroSecure2025!"