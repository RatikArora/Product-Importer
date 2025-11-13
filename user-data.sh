#!/bin/bash

# User data script for EC2 instance
# This script will run when the instance starts

set -e

echo "Starting deployment script..."

# Update system
apt-get update
apt-get upgrade -y

# Install Docker
apt-get install -y docker.io docker-compose-plugin curl git

# Install Docker Compose standalone
curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Start and enable Docker
systemctl start docker
systemctl enable docker

# Add ubuntu user to docker group
usermod -aG docker ubuntu

# Create application directory
mkdir -p /home/ubuntu/fulfil
cd /home/ubuntu/fulfil

# Clone repository
git clone https://github.com/RatikArora/Product-Importer.git .

# Create production environment file
cat > .env << 'EOF'
DATABASE_URL=postgresql://postgres:fulfil_secure_password_2024!@postgres:5432/fulfil_db
REDIS_URL=redis://redis:6379
ENVIRONMENT=production
EOF

# Create directories for volumes
mkdir -p uploads logs ssl

# Create simple init SQL file
cat > init.sql << 'EOF'
CREATE DATABASE IF NOT EXISTS fulfil_db;
EOF

# Set ownership
chown -R ubuntu:ubuntu /home/ubuntu/fulfil

# Build and start services
cd /home/ubuntu/fulfil
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to start
sleep 30

# Show status
docker-compose -f docker-compose.prod.yml ps

echo "Deployment completed!"
echo "Application should be available at http://$(curl -s ifconfig.me):8000"
echo "Nginx proxy available at http://$(curl -s ifconfig.me)"