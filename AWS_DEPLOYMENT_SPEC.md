# AWS Deployment Specification
# Hospital Readmission Prediction System

**Project**: Care Insight - Hospital Readmission Prevention Platform  
**Version**: 1.0.0  
**Date**: August 12, 2026  
**Deployment Model**: Spec-Driven Development (SDD)  
**Target**: AWS Free Tier (12 months)  
**Cost**: $0/month

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Specification](#2-architecture-specification)
3. [Infrastructure Requirements](#3-infrastructure-requirements)
4. [Deployment Phases](#4-deployment-phases)
5. [Security Specifications](#5-security-specifications)
6. [Testing & Validation](#6-testing--validation)
7. [Monitoring & Maintenance](#7-monitoring--maintenance)
8. [Rollback & Disaster Recovery](#8-rollback--disaster-recovery)

---

## 1. Project Overview

### 1.1 System Description

**Backend Application**:
- **Framework**: FastAPI (Python 3.11)
- **ML Model**: Scikit-learn based readmission prediction (89% accuracy)
- **Model File**: best_model.pkl (~50 MB)
- **Database**: PostgreSQL 15
- **Dataset**: 40,000 patient records with predictions
- **Authentication**: JWT-based auth system
- **API Endpoints**: 25+ REST endpoints

**Frontend Application**:
- **Framework**: React 18 + TanStack Router
- **Build Tool**: Vite 5
- **UI Library**: Shadcn/ui + Tailwind CSS
- **State Management**: TanStack Query
- **Features**: Real-time dashboards, risk analysis, patient management

### 1.2 Current State

```
✅ Backend: Fully functional locally (port 8000)
✅ Frontend: Fully functional locally (port 3000)
✅ Database: PostgreSQL with 40K patients
✅ Git Repositories: 
   - Backend: github.com/vishwapandiyan/readmission_backend
   - Frontend: github.com/aisvamalar/care-insight-predict
✅ Database Dump: readmission_db_dump.sql (15 MB, compressed to 2.2 MB)
```

### 1.3 Deployment Goals

- [x] Deploy to AWS Free Tier (100% free for 12 months)
- [x] Zero downtime deployment capability
- [x] Auto-scaling and self-healing
- [x] HTTPS everywhere
- [x] Global CDN for frontend
- [x] Automated backups
- [x] Infrastructure as Code (Terraform)
- [x] CI/CD ready

---

## 2. Architecture Specification

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          USERS / CLIENTS                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │   CloudFront    │ (Global CDN)
                    │   + SSL/TLS     │
                    └────────┬────────┘
                             │
            ┌────────────────┴────────────────┐
            │                                  │
    ┌───────▼────────┐              ┌────────▼────────┐
    │   S3 Bucket    │              │  API Gateway    │
    │   (Frontend)   │              │   REST API      │
    └────────────────┘              └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │   ECS Cluster   │
                                    │  (EC2 t2.micro) │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │  Docker Container│
                                    │  FastAPI + ML   │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │  RDS PostgreSQL │
                                    │   (t3.micro)    │
                                    └─────────────────┘
```

### 2.2 AWS Services Mapping

| Component | AWS Service | Instance Type | Free Tier | Purpose |
|-----------|-------------|---------------|-----------|---------|
| **Database** | RDS PostgreSQL | t3.micro | 750 hrs/month | Patient data, predictions, users |
| **Backend Container** | ECS on EC2 | t2.micro | 750 hrs/month | FastAPI + ML model |
| **Container Registry** | ECR | - | 500 MB/month | Docker images |
| **API Gateway** | API Gateway | REST API | 1M requests/month | HTTP API endpoint |
| **Frontend Hosting** | S3 | Standard | 5 GB storage | Static files |
| **CDN** | CloudFront | - | 50 GB transfer | Global content delivery |
| **Networking** | VPC | - | Free | Network isolation |
| **Security** | Security Groups | - | Free | Firewall rules |
| **Permissions** | IAM | - | Free | Access control |
| **Monitoring** | CloudWatch | - | 5 GB logs/month | Logs and metrics |
| **DNS** | Route53 (optional) | - | $0.50/month | Custom domain |

### 2.3 Network Architecture

```
VPC (10.0.0.0/16)
│
├─── Public Subnet (10.0.1.0/24)
│    ├─── Internet Gateway
│    ├─── NAT Gateway (optional)
│    └─── EC2 Instance (ECS Host)
│         └─── Docker Container (FastAPI:8000)
│
└─── Private Subnet (10.0.2.0/24)
     └─── RDS PostgreSQL (port 5432)
          └─── Multi-AZ: No (to stay free)
```

---

## 3. Infrastructure Requirements

### 3.1 Resource Specifications

#### 3.1.1 Backend (ECS on EC2)

```yaml
Instance Type: t2.micro
vCPU: 1
Memory: 1 GB
Storage: 8 GB EBS (gp3)
OS: Amazon Linux 2023
Docker Version: 24.x
Container Resources:
  - Memory: 768 MB (reserve 256 MB for OS)
  - CPU: 0.5 vCPU
  - Health Check: /health endpoint every 30s
  - Restart Policy: Always
```

#### 3.1.2 Database (RDS PostgreSQL)

```yaml
Engine: PostgreSQL 15.4
Instance Type: db.t3.micro
vCPU: 2
Memory: 1 GB
Storage: 20 GB (gp3)
Backup Retention: 7 days
Multi-AZ: No (to stay in free tier)
Public Access: No (private subnet only)
Encryption: Yes (at rest and in transit)
Connection Pool: 100 connections
```

#### 3.1.3 API Gateway

```yaml
Type: REST API
Protocol: HTTPS only
CORS: Enabled for frontend origin
Throttling: 
  - Rate: 1000 requests/second
  - Burst: 2000 requests
Stages: 
  - dev
  - prod
Caching: Disabled (to stay in free tier)
```

#### 3.1.4 Frontend (S3 + CloudFront)

```yaml
S3:
  - Bucket: care-insight-frontend-prod
  - Static Website Hosting: Enabled
  - Versioning: Enabled
  - Encryption: AES-256
  
CloudFront:
  - Price Class: Use Only US, Canada, Europe
  - SSL Certificate: AWS Certificate Manager (free)
  - Compress: Yes
  - Cache TTL: 86400 seconds (1 day)
```

---

## 4. Deployment Phases

### Phase 1: Prerequisites & Setup

#### Task 1.1: Install Required Tools

**Acceptance Criteria**:
- [ ] AWS CLI v2 installed and configured
- [ ] Terraform v1.5+ installed
- [ ] Docker installed and running
- [ ] Git repositories cloned
- [ ] AWS credentials configured

**Commands**:
```bash
# Install AWS CLI
brew install awscli

# Install Terraform
brew install terraform

# Verify installations
aws --version    # Should be 2.x
terraform version # Should be 1.5+
docker --version  # Should be 20.x+

# Configure AWS credentials
aws configure
# AWS Access Key ID: [PROVIDED]
# AWS Secret Access Key: [PROVIDED]
# Default region: us-east-1
# Default output format: json
```

#### Task 1.2: Prepare Project Structure

**Acceptance Criteria**:
- [ ] Terraform directory created with all configurations
- [ ] Docker directory created with Dockerfile
- [ ] Scripts directory created with deployment scripts
- [ ] Documentation directory created

**Structure**:
```
Readmission system/
├── backend/                    # Backend application
├── terraform/                  # Infrastructure as Code
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── vpc.tf
│   ├── rds.tf
│   ├── ecs.tf
│   ├── ecr.tf
│   ├── api-gateway.tf
│   ├── s3-cloudfront.tf
│   ├── iam.tf
│   └── terraform.tfvars
├── docker/                     # Docker configuration
│   ├── Dockerfile
│   ├── .dockerignore
│   └── docker-compose.yml
├── scripts/                    # Deployment scripts
│   ├── 01-setup-aws.sh
│   ├── 02-build-and-push.sh
│   ├── 03-deploy-infrastructure.sh
│   ├── 04-deploy-backend.sh
│   ├── 05-restore-database.sh
│   ├── 06-deploy-frontend.sh
│   └── 99-destroy-all.sh
└── docs/                       # Documentation
    ├── DEPLOYMENT-GUIDE.md
    ├── ARCHITECTURE.md
    └── TROUBLESHOOTING.md
```

---

### Phase 2: Infrastructure Setup (Terraform)

#### Task 2.1: VPC and Networking

**Acceptance Criteria**:
- [ ] VPC created with CIDR 10.0.0.0/16
- [ ] Public subnet created (10.0.1.0/24)
- [ ] Private subnet created (10.0.2.0/24)
- [ ] Internet Gateway attached
- [ ] Route tables configured
- [ ] Security groups created

**Resources**:
```hcl
# VPC
resource "aws_vpc" "main"
resource "aws_subnet" "public"
resource "aws_subnet" "private"
resource "aws_internet_gateway" "main"
resource "aws_route_table" "public"
resource "aws_route_table_association" "public"

# Security Groups
resource "aws_security_group" "ecs"      # Port 8000 from API Gateway
resource "aws_security_group" "rds"      # Port 5432 from ECS only
resource "aws_security_group" "alb"      # Port 80/443 from anywhere (if needed)
```

#### Task 2.2: RDS Database

**Acceptance Criteria**:
- [ ] RDS PostgreSQL t3.micro created
- [ ] Database in private subnet
- [ ] Security group allows ECS access only
- [ ] Automated backups enabled (7 days)
- [ ] Database credentials stored in AWS Secrets Manager
- [ ] Encryption enabled

**Terraform Resource**:
```hcl
resource "aws_db_instance" "postgres" {
  identifier              = "readmission-db"
  engine                  = "postgres"
  engine_version          = "15.4"
  instance_class          = "db.t3.micro"
  allocated_storage       = 20
  storage_type            = "gp3"
  db_name                 = "readmission_db"
  username                = "dbadmin"
  password                = random_password.db_password.result
  vpc_security_group_ids  = [aws_security_group.rds.id]
  db_subnet_group_name    = aws_db_subnet_group.main.name
  backup_retention_period = 7
  skip_final_snapshot     = false
  final_snapshot_identifier = "readmission-db-final-snapshot"
  publicly_accessible     = false
  multi_az                = false  # Keep false for free tier
  storage_encrypted       = true
}
```

#### Task 2.3: ECR Repository

**Acceptance Criteria**:
- [ ] ECR repository created for backend
- [ ] Image scanning enabled
- [ ] Lifecycle policy configured (keep last 5 images)

#### Task 2.4: ECS Cluster and Service

**Acceptance Criteria**:
- [ ] ECS cluster created (EC2 launch type)
- [ ] EC2 t2.micro instance launched
- [ ] ECS task definition created
- [ ] ECS service created with 1 desired task
- [ ] Auto-restart on failure enabled
- [ ] Health check configured

**Task Definition**:
```json
{
  "family": "readmission-backend",
  "networkMode": "bridge",
  "containerDefinitions": [
    {
      "name": "fastapi",
      "image": "${ECR_REPO_URL}:latest",
      "memory": 768,
      "cpu": 512,
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://..."
        },
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/readmission-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

#### Task 2.5: API Gateway

**Acceptance Criteria**:
- [ ] REST API created
- [ ] Integration with ECS backend
- [ ] CORS configured for frontend origin
- [ ] Custom domain configured (optional)
- [ ] Throttling enabled
- [ ] Access logs enabled

**Routes**:
```
GET  /health          → ECS:8000/health
POST /api/v1/auth/*   → ECS:8000/api/v1/auth/*
GET  /api/v1/patients → ECS:8000/api/v1/patients
POST /api/v1/patients → ECS:8000/api/v1/patients
...all other routes
```

#### Task 2.6: S3 and CloudFront

**Acceptance Criteria**:
- [ ] S3 bucket created for frontend
- [ ] Static website hosting enabled
- [ ] Bucket policy allows CloudFront access only
- [ ] CloudFront distribution created
- [ ] SSL certificate created (ACM)
- [ ] HTTPS redirect enabled
- [ ] Compression enabled

---

### Phase 3: Application Deployment

#### Task 3.1: Dockerize Backend

**Acceptance Criteria**:
- [ ] Dockerfile created for FastAPI app
- [ ] Multi-stage build for optimization
- [ ] Image size < 500 MB
- [ ] ML model included in image
- [ ] Health check endpoint working
- [ ] Local test successful

**Dockerfile**:
```dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY backend/app ./app
COPY best_model.pkl .
COPY best_model_feature_importance.csv .
COPY model_metadata.csv .

# Set environment variables
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

#### Task 3.2: Build and Push to ECR

**Acceptance Criteria**:
- [ ] Docker image built successfully
- [ ] Image tagged with version and latest
- [ ] Image pushed to ECR
- [ ] Image scan completed (no critical vulnerabilities)

**Script**:
```bash
#!/bin/bash
# scripts/02-build-and-push.sh

# Get ECR login
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin ${ECR_REGISTRY}

# Build image
docker build -t readmission-backend:${VERSION} -f docker/Dockerfile .
docker tag readmission-backend:${VERSION} ${ECR_REPO}:${VERSION}
docker tag readmission-backend:${VERSION} ${ECR_REPO}:latest

# Push to ECR
docker push ${ECR_REPO}:${VERSION}
docker push ${ECR_REPO}:latest

echo "✅ Image pushed successfully"
```

#### Task 3.3: Deploy ECS Service

**Acceptance Criteria**:
- [ ] ECS service updated with new task definition
- [ ] Container starts successfully
- [ ] Health checks passing
- [ ] Logs visible in CloudWatch
- [ ] API Gateway can reach backend

#### Task 3.4: Restore Database

**Acceptance Criteria**:
- [ ] Database dump uploaded to S3 (temporary)
- [ ] Database restored from dump
- [ ] 40,000 patient records verified
- [ ] Users table verified (4 users)
- [ ] Database connections working from ECS

**Script**:
```bash
#!/bin/bash
# scripts/05-restore-database.sh

DB_HOST=$(terraform output -raw rds_endpoint)
DB_NAME="readmission_db"
DB_USER="dbadmin"
DB_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id readmission-db-password \
  --query SecretString --output text)

# Uncompress and restore
gunzip -c readmission_db_dump.sql.gz | \
  PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME

echo "✅ Database restored successfully"
```

#### Task 3.5: Build and Deploy Frontend

**Acceptance Criteria**:
- [ ] Environment variables updated with API Gateway URL
- [ ] Frontend built (npm run build)
- [ ] Build uploaded to S3
- [ ] CloudFront cache invalidated
- [ ] HTTPS working
- [ ] Frontend can communicate with backend

**Script**:
```bash
#!/bin/bash
# scripts/06-deploy-frontend.sh

cd ../frontendread/care-insight-predict

# Update API URL
API_URL=$(terraform output -raw api_gateway_url)
echo "VITE_API_BASE_URL=$API_URL" > .env.production

# Build
npm run build

# Deploy to S3
aws s3 sync dist/ s3://care-insight-frontend-prod/ --delete

# Invalidate CloudFront cache
DISTRIBUTION_ID=$(terraform output -raw cloudfront_distribution_id)
aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"

echo "✅ Frontend deployed successfully"
```

---

## 5. Security Specifications

### 5.1 Network Security

- [x] RDS in private subnet (no public access)
- [x] ECS in public subnet (minimal exposure)
- [x] Security groups with least privilege
- [x] No SSH keys (use Session Manager)
- [x] All traffic encrypted in transit (TLS 1.2+)

### 5.2 Data Security

- [x] RDS encryption at rest (AES-256)
- [x] Database credentials in AWS Secrets Manager
- [x] S3 bucket encryption (AES-256)
- [x] JWT tokens for API authentication
- [x] Password hashing with bcrypt

### 5.3 Access Control

- [x] IAM roles for ECS tasks (no hardcoded credentials)
- [x] S3 bucket accessible only via CloudFront
- [x] API Gateway with throttling
- [x] CloudWatch logs for audit trail

### 5.4 Security Groups

**ECS Security Group**:
```
Inbound:
  - Port 8000 from 0.0.0.0/0 (API Gateway uses public IPs)
Outbound:
  - Port 5432 to RDS security group
  - Port 443 to 0.0.0.0/0 (for external APIs)
```

**RDS Security Group**:
```
Inbound:
  - Port 5432 from ECS security group ONLY
Outbound:
  - None needed
```

---

## 6. Testing & Validation

### 6.1 Infrastructure Tests

**Test 1: VPC Connectivity**
```bash
# Test that EC2 can reach RDS
aws ssm start-session --target ${INSTANCE_ID}
# Inside instance:
telnet ${RDS_ENDPOINT} 5432
```

**Test 2: ECS Health**
```bash
# Check ECS task status
aws ecs describe-services \
  --cluster readmission-cluster \
  --services readmission-backend-service

# Expected: runningCount: 1, desiredCount: 1
```

**Test 3: Database Connectivity**
```bash
# Test from ECS task
aws ecs execute-command \
  --cluster readmission-cluster \
  --task ${TASK_ARN} \
  --container fastapi \
  --interactive \
  --command "psql -h ${RDS_ENDPOINT} -U dbadmin -d readmission_db -c 'SELECT COUNT(*) FROM patients;'"

# Expected: 40000
```

### 6.2 Application Tests

**Test 4: Backend Health Check**
```bash
curl -X GET https://api.your-domain.com/health
# Expected: {"status": "healthy", "version": "1.0.0"}
```

**Test 5: Authentication**
```bash
curl -X POST https://api.your-domain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
# Expected: {"access_token": "...", "token_type": "bearer"}
```

**Test 6: Patient List**
```bash
TOKEN="..." # from login
curl -X GET https://api.your-domain.com/api/v1/patients \
  -H "Authorization: Bearer $TOKEN"
# Expected: Array of patients
```

**Test 7: Frontend Access**
```bash
curl -I https://your-cloudfront-url.cloudfront.net
# Expected: HTTP/2 200, x-cache: Hit from cloudfront
```

### 6.3 Performance Tests

**Test 8: API Response Time**
```bash
time curl -X GET https://api.your-domain.com/api/v1/patients/stats/summary
# Expected: < 2 seconds
```

**Test 9: Frontend Load Time**
- Open Chrome DevTools
- Navigate to frontend URL
- Check Performance tab
- Expected: First Contentful Paint < 1.5s

### 6.4 Security Tests

**Test 10: HTTPS Enforcement**
```bash
curl -I http://your-cloudfront-url.cloudfront.net
# Expected: 301 redirect to HTTPS
```

**Test 11: CORS**
```bash
curl -X OPTIONS https://api.your-domain.com/api/v1/patients \
  -H "Origin: https://your-frontend-url.com" \
  -H "Access-Control-Request-Method: GET"
# Expected: Access-Control-Allow-Origin header present
```

---

## 7. Monitoring & Maintenance

### 7.1 CloudWatch Dashboards

**Dashboard 1: Infrastructure Health**
- ECS CPU Utilization (target: < 70%)
- ECS Memory Utilization (target: < 80%)
- RDS CPU Utilization (target: < 70%)
- RDS Free Storage Space (alert if < 2 GB)
- RDS Database Connections (alert if > 80)

**Dashboard 2: Application Metrics**
- API Gateway 4XX/5XX errors
- API Gateway latency (p50, p95, p99)
- ECS task count (should be 1)
- CloudFront requests and cache hit ratio

### 7.2 CloudWatch Alarms

**Alarm 1: ECS Task Stopped**
```
Metric: ecs:DesiredTaskCount - ecs:RunningTaskCount
Threshold: > 0 for 5 minutes
Action: SNS notification + Auto-restart
```

**Alarm 2: High CPU**
```
Metric: ECS CPU Utilization
Threshold: > 80% for 10 minutes
Action: SNS notification
```

**Alarm 3: Database Connections**
```
Metric: RDS DatabaseConnections
Threshold: > 80 for 5 minutes
Action: SNS notification
```

**Alarm 4: API Gateway Errors**
```
Metric: API Gateway 5XX Errors
Threshold: > 10 in 5 minutes
Action: SNS notification
```

### 7.3 Log Retention

- ECS logs: 7 days
- API Gateway logs: 7 days
- RDS logs: 7 days
- CloudTrail: 90 days

### 7.4 Backup Strategy

**RDS Backups**:
- Automated daily backups (7-day retention)
- Manual snapshot before major changes
- Backup window: 03:00-04:00 UTC

**Application Backups**:
- ECS task definition versions (keep all)
- ECR images (keep last 5)
- S3 versioning enabled (keep 30 days)

---

## 8. Rollback & Disaster Recovery

### 8.1 Rollback Procedures

**Scenario 1: Bad Backend Deployment**
```bash
# Rollback to previous task definition
aws ecs update-service \
  --cluster readmission-cluster \
  --service readmission-backend-service \
  --task-definition readmission-backend:PREVIOUS_VERSION

# Or rollback to previous image
aws ecs update-service \
  --cluster readmission-cluster \
  --service readmission-backend-service \
  --force-new-deployment
```

**Scenario 2: Bad Frontend Deployment**
```bash
# S3 versioning - restore previous version
aws s3api list-object-versions --bucket care-insight-frontend-prod
aws s3api copy-object \
  --copy-source care-insight-frontend-prod/index.html?versionId=PREVIOUS_VERSION \
  --bucket care-insight-frontend-prod \
  --key index.html

# Invalidate CloudFront
aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"
```

**Scenario 3: Database Issues**
```bash
# Restore from automated backup
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier readmission-db-restore \
  --db-snapshot-identifier rds:readmission-db-YYYY-MM-DD-HH-MM

# Or restore from manual snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier readmission-db-restore \
  --db-snapshot-identifier readmission-db-final-snapshot
```

### 8.2 Disaster Recovery

**RTO (Recovery Time Objective)**: 1 hour  
**RPO (Recovery Point Objective)**: 24 hours

**DR Procedure**:
1. Identify failure (monitoring alarms)
2. Assess impact (check CloudWatch dashboards)
3. Execute rollback or restore procedure
4. Verify recovery (run test suite)
5. Post-mortem analysis

---

## 9. Cost Optimization

### 9.1 Free Tier Usage Tracking

**Monthly Limits**:
- EC2: 750 hours (1 t2.micro = 720 hours) ✅
- RDS: 750 hours (1 t3.micro = 720 hours) ✅
- RDS Storage: 20 GB (using ~15 GB) ✅
- S3: 5 GB storage, 2000 PUT, 20000 GET ✅
- CloudFront: 50 GB transfer ✅
- API Gateway: 1M requests ✅

**Cost Alerts**:
- Alert at $5 spent
- Alert at $10 spent
- Billing anomaly detection enabled

### 9.2 Cost After Free Tier

**Estimated Monthly Costs (Month 13+)**:
```
EC2 t2.micro:           $8.50
RDS t3.micro:          $16.20
RDS Storage (20 GB):    $2.30
S3 Storage:             $0.10
CloudFront:             $0.85
API Gateway:            $0.35
CloudWatch:             $0.50
Data Transfer:          $0.90
──────────────────────────────
TOTAL:                ~$30.00/month
```

---

## 10. Success Criteria

### 10.1 Deployment Complete

- [x] All infrastructure deployed via Terraform
- [x] Backend running on ECS with health checks passing
- [x] Database restored with 40K patients
- [x] Frontend deployed and accessible via HTTPS
- [x] API Gateway routing traffic correctly
- [x] All tests passing
- [x] Monitoring dashboards configured
- [x] Cost tracking enabled

### 10.2 Acceptance Criteria

**Functional Requirements**:
- [ ] Users can login to frontend
- [ ] Dashboard shows real patient data
- [ ] Risk analysis displays correctly
- [ ] Patient search works
- [ ] Predictions are accurate
- [ ] All CRUD operations work

**Non-Functional Requirements**:
- [ ] Frontend loads in < 2 seconds
- [ ] API response time < 500ms (p95)
- [ ] 99% uptime
- [ ] Zero cost in first 12 months
- [ ] Auto-recovery from failures
- [ ] Logs available for debugging

---

## 11. Appendix

### 11.1 Environment Variables

**Backend (.env)**:
```env
DATABASE_URL=postgresql://dbadmin:PASSWORD@RDS_ENDPOINT:5432/readmission_db
JWT_SECRET_KEY=GENERATED_SECRET
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=production
DEBUG=False
```

**Frontend (.env.production)**:
```env
VITE_API_BASE_URL=https://api.your-domain.com
VITE_ENVIRONMENT=production
```

### 11.2 Useful Commands

```bash
# Check Terraform state
terraform show

# Get all outputs
terraform output

# SSH to ECS instance (via Session Manager)
aws ssm start-session --target ${INSTANCE_ID}

# View ECS logs
aws logs tail /ecs/readmission-backend --follow

# Check RDS status
aws rds describe-db-instances --db-instance-identifier readmission-db

# Invalidate CloudFront
aws cloudfront create-invalidation --distribution-id ID --paths "/*"

# Check API Gateway logs
aws logs tail /aws/apigateway/readmission-api --follow
```

### 11.3 Troubleshooting Guide

**Issue 1: ECS Task Fails to Start**
- Check CloudWatch logs: `/ecs/readmission-backend`
- Verify environment variables
- Check security group allows database access
- Verify Docker image is correct

**Issue 2: Cannot Connect to Database**
- Check RDS security group
- Verify database endpoint
- Check credentials in Secrets Manager
- Verify ECS security group has outbound rule

**Issue 3: Frontend Not Loading**
- Check CloudFront distribution status
- Verify S3 bucket has files
- Check browser console for errors
- Verify API_URL in frontend env

**Issue 4: API Gateway 502/504**
- Check ECS task is running
- Verify health check endpoint
- Check ECS security group allows traffic from API Gateway
- Review API Gateway integration settings

---

## 12. Next Steps

After successful deployment:

1. **Enable CI/CD**:
   - GitHub Actions for automated deployments
   - Deploy on merge to main branch

2. **Add Custom Domain**:
   - Register domain in Route53
   - Configure ACM certificate
   - Update CloudFront and API Gateway

3. **Enhance Monitoring**:
   - Set up X-Ray for distributed tracing
   - Add custom metrics for business KPIs
   - Configure SNS for alerts

4. **Performance Optimization**:
   - Enable API Gateway caching
   - Optimize database queries
   - Implement Redis cache (if needed)

5. **Security Hardening**:
   - Enable AWS WAF
   - Implement rate limiting
   - Add API key authentication
   - Regular security audits

---

**Deployment Checklist**: [See separate file: DEPLOYMENT_CHECKLIST.md]  
**Terraform Files**: [See terraform/ directory]  
**Scripts**: [See scripts/ directory]  
**Documentation**: [See docs/ directory]

---

**Document Version**: 1.0.0  
**Last Updated**: August 12, 2026  
**Status**: Ready for Implementation ✅
