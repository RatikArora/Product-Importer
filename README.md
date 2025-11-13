# Product Importer - CSV Processing System

A robust, scalable web application for importing and managing large CSV product datasets with real-time processing capabilities.

## 🚀 Live Demo

**Production Application**: http://35.170.77.201

*Currently deployed on AWS EC2 with full production infrastructure*

## 📋 Overview

This application was built as a technical assessment for **Fulfil.io** to demonstrate:

- **Full-stack development** with modern Python frameworks
- **Scalable architecture** for handling large datasets
- **Production deployment** with containerization
- **Real-time processing** with background task queues
- **Professional UI/UX** with responsive design

## 🎯 Key Features

### Core Functionality
- ✅ **CSV File Upload** - Drag & drop interface with file validation
- ✅ **Real-time Processing** - Background processing with progress tracking
- ✅ **Product Management** - Full CRUD operations with search and pagination
- ✅ **Bulk Operations** - Handle datasets with 100K+ records efficiently
- ✅ **Data Validation** - Robust error handling and data integrity checks

### Technical Highlights
- **Async Architecture** - FastAPI with async/await for high concurrency
- **Background Processing** - Celery task queue for non-blocking operations
- **Database Optimization** - Batch processing and connection pooling
- **Containerization** - Docker Compose for development and production
- **Production Ready** - AWS deployment with proper scaling

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern, fast Python web framework
- **SQLAlchemy** - Async ORM with PostgreSQL
- **Celery** - Distributed task queue for background processing
- **Redis** - Message broker and caching
- **Pandas** - Efficient data processing and validation

### Frontend
- **Bootstrap 5** - Responsive UI framework
- **JavaScript ES6** - Modern client-side functionality
- **Font Awesome** - Professional icon set

### Infrastructure
- **PostgreSQL** - Production database
- **Docker** - Containerization for all services
- **Nginx** - Reverse proxy and load balancer
- **AWS EC2** - Production hosting

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend UI   │────│   FastAPI Web   │────│   PostgreSQL    │
│   Bootstrap 5   │    │   Application   │    │   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              │
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Celery Worker  │────│     Redis       │
                       │  (Background)   │    │  Message Broker │
                       └─────────────────┘    └─────────────────┘
```

## 📊 Performance Capabilities

- **File Size**: Handles files up to 1GB
- **Record Volume**: Processed 361,343 products successfully
- **Processing Speed**: ~1,000-2,000 records per second
- **Concurrency**: Multiple simultaneous uploads supported
- **Memory Efficiency**: Chunked processing to handle large datasets

## 🚀 Quick Start

### Local Development

```bash
# Clone repository
git clone https://github.com/RatikArora/Product-Importer.git
cd Product-Importer

# Start services with Docker Compose
docker-compose up -d

# Access application
open http://localhost:8000
```

### Production Deployment

The application is production-ready with:
- **Docker Compose** configuration for easy deployment
- **Environment variables** for configuration
- **Health checks** and restart policies
- **Volume mounting** for data persistence

## 📱 User Interface

### Dashboard Features
- **Upload Interface** - Drag & drop with real-time validation
- **Progress Tracking** - Live updates during processing
- **Product Management** - Search, filter, and paginate results
- **Responsive Design** - Works on desktop, tablet, and mobile

### API Endpoints
- `POST /api/v1/upload/` - CSV file upload and processing
- `GET /api/v1/products/` - List products with pagination
- `GET /api/v1/products/{id}` - Get product details
- `PUT /api/v1/products/{id}` - Update product
- `DELETE /api/v1/products/{id}` - Delete product
- `GET /api/v1/health` - Health check endpoint

## 🔧 Configuration

### Environment Variables
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
REDIS_URL=redis://host:port/db
DEBUG=false
```

### Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
# Configure .env file
# Run migrations (if needed)

# Start development server
uvicorn app.main:app --reload
```

## 📈 Production Deployment Details

### Current Infrastructure (AWS EC2)
- **Instance Type**: t3.micro (AWS Free Tier)
- **OS**: Ubuntu 22.04 LTS
- **Services**: 5 containers orchestrated with Docker Compose
- **Database**: PostgreSQL 15 with persistent storage
- **Reverse Proxy**: Nginx for load balancing

### Monitoring & Health
- Health check endpoints for all services
- Automatic restart policies
- Structured logging
- Error tracking and reporting

## 🧪 Testing the Application

### Sample Data Processing
The application has been tested with:
- **361,343 product records** successfully imported
- **Large CSV files** (100MB+) processed without issues
- **Concurrent uploads** handled smoothly
- **Error recovery** and partial import capabilities

### Live Demo Instructions
1. Visit: http://35.170.77.201
2. Use the CSV upload feature with any product data
3. Monitor real-time processing progress
4. Browse and manage imported products
5. Test search and filtering capabilities

## 🏆 Technical Achievements

### Scalability
- **Async processing** for high concurrency
- **Background task queue** for non-blocking operations
- **Database connection pooling** for efficiency
- **Chunked processing** for large files

### Reliability
- **Error handling** with detailed logging
- **Data validation** at multiple levels
- **Transaction management** for data integrity
- **Graceful degradation** under load

### User Experience
- **Real-time feedback** during uploads
- **Progress indicators** for long-running tasks
- **Responsive design** across devices
- **Intuitive interface** for complex operations

## 📞 Contact & Links

- **GitHub Repository**: https://github.com/RatikArora/Product-Importer
- **Live Application**: http://35.170.77.201
- **Developer**: Ratik Arora
- **Email**: ratikarora007@gmail.com


---

*Built by Ratik Arora*
