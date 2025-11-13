# AWS Free Tier Deployment Guide

## AWS Services We'll Use (All Free Tier Eligible)

### 1. **EC2 Instance** (Free for 12 months)
- t2.micro instance (1 vCPU, 1 GB RAM)
- 750 hours/month free
- Perfect for your FastAPI application

### 2. **RDS PostgreSQL** (Free for 12 months)
- db.t3.micro instance
- 20 GB storage
- 750 hours/month free

### 3. **ElastiCache Redis** (Free for 12 months)
- cache.t3.micro node
- 750 hours/month free

### 4. **Application Load Balancer** (Optional)
- For SSL/HTTPS support
- 750 hours/month free

## Deployment Options

### Option A: AWS App Runner (Easiest)
- Fully managed container service
- Auto-scaling and load balancing
- Direct GitHub integration
- $0.25/month for minimal usage

### Option B: EC2 + Docker (Most Control)
- Full control over environment
- Can run multiple services
- Completely free on t2.micro

### Option C: AWS Lightsail (Simplest)
- $3.50/month (not free tier, but very cheap)
- Pre-configured with everything needed

## Quick Start - Option A (App Runner)

### Prerequisites
1. AWS Account with Free Tier
2. AWS CLI installed
3. Docker (we already have Dockerfile)

### Step 1: Install AWS CLI
```bash
# On macOS
brew install awscli
# or
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
```

### Step 2: Configure AWS CLI
```bash
aws configure
# Enter your:
# - AWS Access Key ID
# - AWS Secret Access Key  
# - Default region (e.g., us-east-1)
# - Output format (json)
```

### Step 3: Create RDS PostgreSQL Database
```bash
# Create DB subnet group
aws rds create-db-subnet-group \
    --db-subnet-group-name fulfil-db-subnet-group \
    --db-subnet-group-description "Subnet group for Fulfil DB" \
    --subnet-ids subnet-12345 subnet-67890

# Create PostgreSQL instance
aws rds create-db-instance \
    --db-instance-identifier fulfil-postgres \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username postgres \
    --master-user-password YourSecurePassword123! \
    --allocated-storage 20 \
    --vpc-security-group-ids sg-12345 \
    --db-subnet-group-name fulfil-db-subnet-group \
    --publicly-accessible
```

### Step 4: Create ElastiCache Redis
```bash
# Create Redis cluster
aws elasticache create-cache-cluster \
    --cache-cluster-id fulfil-redis \
    --cache-node-type cache.t3.micro \
    --engine redis \
    --num-cache-nodes 1
```

### Step 5: Create App Runner Service
```bash
# Create apprunner.yaml
cat > apprunner.yaml << 'EOF'
version: 1.0
runtime: python3
build:
  commands:
    build:
      - echo "Build started on $(date)"
      - pip install -r requirements.txt
run:
  runtime-version: 3.11
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000
  network:
    port: 8000
    env: PORT
  env:
    - name: DATABASE_URL
      value: "postgresql://postgres:YourSecurePassword123!@fulfil-postgres.xxxxx.us-east-1.rds.amazonaws.com:5432/postgres"
    - name: REDIS_URL
      value: "redis://fulfil-redis.xxxxx.cache.amazonaws.com:6379"
    - name: ENVIRONMENT
      value: "production"
EOF
```

## Quick Start - Option B (EC2 + Docker)

### Step 1: Launch EC2 Instance
```bash
# Create key pair
aws ec2 create-key-pair --key-name fulfil-key --query 'KeyMaterial' --output text > fulfil-key.pem
chmod 400 fulfil-key.pem

# Launch t2.micro instance (Ubuntu 22.04)
aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --count 1 \
    --instance-type t2.micro \
    --key-name fulfil-key \
    --security-groups default \
    --user-data file://user-data.sh
```

### Step 2: Create User Data Script
```bash
cat > user-data.sh << 'EOF'
#!/bin/bash
apt-get update
apt-get install -y docker.io docker-compose-plugin git

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Start Docker
systemctl start docker
systemctl enable docker

# Clone your repo
cd /home/ubuntu
git clone https://github.com/RatikArora/Product-Importer.git
cd Product-Importer

# Create production environment file
cat > .env << 'ENVEOF'
DATABASE_URL=postgresql://postgres:password@localhost:5432/fulfil_db
REDIS_URL=redis://localhost:6379
ENVIRONMENT=production
ENVEOF

# Start with Docker Compose
docker-compose up -d
ENVEOF
```

## Current Project Compatibility

Your project is already AWS-ready because:

✅ **Docker Support**: You have `Dockerfile` and `docker-compose.yml`
✅ **Environment Variables**: All configuration via env vars
✅ **Database Agnostic**: Works with any PostgreSQL instance
✅ **Redis Compatible**: Standard Redis connection
✅ **Production Ready**: FastAPI + Uvicorn + Nginx ready

## Cost Estimation (Free Tier)

| Service | Free Tier Limit | Monthly Cost After |
|---------|----------------|-------------------|
| EC2 t2.micro | 750 hours/month (always free) | $8.50/month |
| RDS db.t3.micro | 750 hours/month | $12/month |
| ElastiCache t3.micro | 750 hours/month | $15/month |
| **Total** | **FREE for 12 months** | **~$35/month after** |

## Next Steps

1. **Choose deployment option** (App Runner recommended for simplicity)
2. **Get AWS credentials** from AWS Console → IAM → Access Keys
3. **Set up AWS CLI** and configure credentials
4. **Deploy databases first** (RDS + ElastiCache)
5. **Deploy application** using chosen method
6. **Configure custom domain** (optional, Route 53 has free tier too)

Would you like me to help you with any of these steps? The AWS approach will be much more reliable than Railway/Render!