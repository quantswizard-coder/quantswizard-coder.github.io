# 🚀 AWS Production Deployment Guide

## 📋 **Overview**

This guide covers deploying the Interactive Trading Simulator to AWS for production use. The application will run on AWS infrastructure with real Bitcoin market data and live trading simulations.

## 🏗️ **Architecture**

### **Production Stack:**
- **Frontend**: React app served via Nginx in Docker container
- **Backend**: FastAPI Python server with real market data integration
- **Load Balancer**: AWS Application Load Balancer for high availability
- **Infrastructure**: AWS CloudFormation for infrastructure as code
- **Containers**: Docker for consistent deployment across environments

### **AWS Services Used:**
- **EC2**: Virtual servers for application hosting
- **ALB**: Application Load Balancer for traffic distribution
- **VPC**: Virtual Private Cloud for network isolation
- **CloudFormation**: Infrastructure as code
- **Route 53**: DNS management (optional)
- **ACM**: SSL certificate management (optional)

## 🔧 **Prerequisites**

### **Local Development Environment:**
```bash
# Required tools
- AWS CLI v2
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- Git
```

### **AWS Account Setup:**
1. **AWS Account** with appropriate permissions
2. **IAM User** with deployment permissions
3. **EC2 Key Pair** for SSH access
4. **Domain Name** (optional, for custom domain)
5. **SSL Certificate** (optional, via AWS Certificate Manager)

### **AWS CLI Configuration:**
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter your default region (e.g., us-east-1)
# Enter output format (json)
```

## 🚀 **Deployment Process**

### **Step 1: Clone and Prepare Repository**
```bash
# Clone from GitHub
git clone https://github.com/quantswizard-coder/quantswizard-coder.github.io.git
cd quantswizard-coder.github.io

# Verify all files are present
ls -la aws-deployment/
```

### **Step 2: Configure Environment Variables**
```bash
# Backend production environment
cp backend/.env.production backend/.env
# Edit backend/.env with your production values

# Frontend production environment  
cp frontend/.env.production frontend/.env
# Edit frontend/.env with your production API URL
```

### **Step 3: Update Deployment Configuration**
```bash
# Edit aws-deployment/deploy.sh
nano aws-deployment/deploy.sh

# Update these variables:
DOMAIN_NAME="your-actual-domain.com"
KEY_PAIR_NAME="your-ec2-key-pair"
REGION="your-preferred-region"
```

### **Step 4: Run Deployment Script**
```bash
# Make script executable
chmod +x aws-deployment/deploy.sh

# Run deployment
./aws-deployment/deploy.sh
```

### **Step 5: Configure DNS (Optional)**
```bash
# Get Load Balancer DNS from CloudFormation output
aws cloudformation describe-stacks \
    --stack-name trading-simulator-stack \
    --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' \
    --output text

# Point your domain to this DNS name
```

## 🔍 **Manual Deployment Steps**

### **If you prefer manual deployment:**

#### **1. Build Docker Images**
```bash
# Backend
cd backend
docker build -t trading-simulator-backend:latest .

# Frontend
cd ../frontend
docker build -t trading-simulator-frontend:latest .
```

#### **2. Deploy Infrastructure**
```bash
cd aws-deployment

# Create CloudFormation stack
aws cloudformation create-stack \
    --stack-name trading-simulator-stack \
    --template-body file://cloudformation-template.yml \
    --parameters ParameterKey=DomainName,ParameterValue=your-domain.com \
                ParameterKey=KeyPairName,ParameterValue=your-key-pair \
    --capabilities CAPABILITY_IAM \
    --region us-east-1
```

#### **3. Start Services**
```bash
# Start with docker-compose
docker-compose up -d

# Check status
docker-compose ps
```

## 🔧 **Configuration Details**

### **Environment Variables:**

#### **Backend (.env.production):**
```env
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=https://your-domain.com
LOG_LEVEL=INFO
```

#### **Frontend (.env.production):**
```env
REACT_APP_API_URL=https://api.your-domain.com/api
REACT_APP_ENVIRONMENT=production
```

### **Docker Configuration:**
- **Backend**: Python 3.11 slim with FastAPI and dependencies
- **Frontend**: Multi-stage build with Node.js build and Nginx serve
- **Nginx**: Optimized for React SPA with API proxy

## 🔍 **Verification & Testing**

### **Health Checks:**
```bash
# Backend API health
curl https://api.your-domain.com/api/health

# Frontend accessibility
curl https://your-domain.com

# API endpoints
curl https://api.your-domain.com/api/strategies
curl https://api.your-domain.com/api/market-data/BTC-USD?days=7
```

### **Application Testing:**
1. **Access Frontend**: https://your-domain.com
2. **Test Strategy Tab**: Select and configure strategies
3. **Test Simulation Tab**: Create and run simulations
4. **Verify Real Data**: Confirm Bitcoin prices are current
5. **Check Performance**: Monitor response times and errors

## 📊 **Monitoring & Maintenance**

### **Application Logs:**
```bash
# View container logs
docker-compose logs -f backend
docker-compose logs -f frontend

# System logs
sudo journalctl -u docker
```

### **Performance Monitoring:**
- **CloudWatch**: AWS native monitoring
- **Application metrics**: Built into FastAPI backend
- **Health checks**: Automated endpoint monitoring

### **Updates & Maintenance:**
```bash
# Pull latest code
git pull origin main

# Rebuild and redeploy
./aws-deployment/deploy.sh

# Rolling updates
docker-compose up -d --no-deps backend
docker-compose up -d --no-deps frontend
```

## 🔒 **Security Considerations**

### **Production Security:**
- **HTTPS Only**: SSL certificates via AWS Certificate Manager
- **CORS Configuration**: Restricted to your domain
- **Security Headers**: Implemented in Nginx configuration
- **Container Security**: Non-root users in containers
- **Network Security**: VPC with security groups

### **API Security:**
- **Rate Limiting**: Implemented in FastAPI backend
- **Input Validation**: Pydantic models for all endpoints
- **Error Handling**: No sensitive information in error responses

## 🎯 **Production Features**

### **What Your Investment Partners Get:**
- **Real Bitcoin Data**: Live market data from Yahoo Finance
- **Professional Interface**: Investment-grade web application
- **6 Trading Strategies**: Sophisticated algorithmic strategies
- **Real-time Simulations**: Live backtesting with actual data
- **Performance Metrics**: Industry-standard analysis
- **High Availability**: Load-balanced, fault-tolerant deployment

### **Business Benefits:**
- **Professional Hosting**: Enterprise-grade AWS infrastructure
- **Scalability**: Auto-scaling capabilities
- **Reliability**: 99.9% uptime with proper configuration
- **Security**: Production-grade security measures
- **Monitoring**: Comprehensive logging and metrics

## 🆘 **Troubleshooting**

### **Common Issues:**
1. **Docker build fails**: Check Docker daemon and permissions
2. **AWS deployment fails**: Verify AWS credentials and permissions
3. **Health checks fail**: Check container logs and network connectivity
4. **API calls fail**: Verify CORS configuration and API URLs

### **Support:**
- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Comprehensive guides and API docs
- **Logs**: Detailed logging for troubleshooting

## 🎉 **Success!**

**Your Interactive Trading Simulator is now running on AWS with:**
- ✅ **Production-grade infrastructure**
- ✅ **Real Bitcoin market data**
- ✅ **Professional web interface**
- ✅ **High availability and scalability**
- ✅ **Enterprise security measures**

**Ready for professional investment partner demonstrations!** 🚀📈
