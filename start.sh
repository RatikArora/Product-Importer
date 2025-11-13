#!/bin/bash

# Product Importer - Development Setup Script
# Ratik Arora - Fulfil Assignment

set -e

echo "🚀 Setting up Product Importer for Fulfil Assignment..."
echo "👨‍💻 Developer: Ratik Arora"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file"
else
    echo "✅ .env file already exists"
fi

# Create uploads directory
mkdir -p uploads
echo "✅ Created uploads directory"

echo ""
echo "🐳 Starting services with Docker Compose..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are healthy
echo "🔍 Checking service health..."

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "⚠️  PostgreSQL is starting up..."
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "⚠️  Redis is starting up..."
fi

echo ""
echo "🎉 Product Importer is now running!"
echo ""
echo "📱 Access the application:"
echo "   🌐 Web Interface: http://localhost:8000"
echo "   📚 API Documentation: http://localhost:8000/docs"
echo "   🌸 Celery Flower: http://localhost:5555"
echo ""
echo "📊 Test with the provided CSV file:"
echo "   📁 File: products.csv (861,687 records)"
echo "   📈 Expected processing time: ~10-15 minutes"
echo ""
echo "🛑 To stop the application:"
echo "   docker-compose down"
echo ""
echo "🔧 To view logs:"
echo "   docker-compose logs -f"
echo ""
echo "🚀 Happy testing! - Ratik Arora"