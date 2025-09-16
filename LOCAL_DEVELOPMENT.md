# Local Development Guide

This guide explains how to run Ctrl-Alt-Heal locally for development and testing.

## 🚀 **Quick Local Setup**

### Prerequisites

- **Python 3.12+**
- **Docker** (optional, for LocalStack)
- **ngrok** (optional, for webhook testing)

### 1. **Basic Local Setup**

```bash
# Clone and set up the project
git clone https://github.com/your-username/Ctrl-Alt-Heal.git
cd Ctrl-Alt-Heal

# Set up Python environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up local development environment
python scripts/setup_local_dev.py
```

### 2. **Configure Local Environment**

```bash
# Copy and edit local environment file
cp .env.local .env

# Edit .env with your actual values
nano .env  # or your preferred editor
```

**Required for local development:**
- `TELEGRAM_BOT_TOKEN` - Your actual Telegram bot token
- `SERPER_API_KEY` - Your actual Serper API key

**Optional for local development:**
- AWS credentials (only needed if you want to use real Bedrock instead of mock mode)

### 3. **Start Local Server**

```bash
# Start the local development server
python scripts/local_webhook.py
```

The server will be available at:
- **Main API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs
- **Webhook Endpoint**: http://localhost:8000/webhook

## 🤖 **Mock Mode (No AWS Required)**

The application supports **mock mode** for local development without requiring AWS Bedrock access:

### **How Mock Mode Works**

When `MOCK_AWS_SERVICES=true` in your environment:
- **Mock AI Agent**: Returns predefined responses instead of using Bedrock
- **Mock Prescription Extraction**: Returns sample prescription data
- **Mock Image Description**: Returns sample image descriptions
- **Real Telegram API**: Still uses actual Telegram for testing

### **Enable Mock Mode**

```bash
# In your .env file
MOCK_AWS_SERVICES=true
LOCAL_DEVELOPMENT=true
```

### **Mock Mode Benefits**

- ✅ **No AWS setup required** - Works without Bedrock access
- ✅ **Fast development** - No API calls to AWS
- ✅ **Predictable responses** - Consistent mock data for testing
- ✅ **Cost-free** - No AWS charges during development

## 🐳 **Local AWS Services (Optional)**

For complete local development without AWS dependencies:

### **Using LocalStack**

```bash
# Start LocalStack (DynamoDB, S3, Secrets Manager)
docker run -d \
  --name localstack \
  -p 4566:4566 \
  -p 8000:8000 \
  -e SERVICES=dynamodb,s3,secretsmanager \
  localstack/localstack

# Create local tables
python scripts/setup_local_dev.py
```

### **Using Docker Compose**

```yaml
# docker-compose.local.yml
version: '3.8'
services:
  localstack:
    image: localstack/localstack
    ports:
      - "4566:4566"
      - "8000:8000"
    environment:
      - SERVICES=dynamodb,s3,secretsmanager
      - DEBUG=1
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock"
```

```bash
# Start local services
docker-compose -f docker-compose.local.yml up -d
```

## 📱 **Telegram Webhook Testing**

### **Using ngrok**

```bash
# Install ngrok
# Download from https://ngrok.com/download

# Start local server
python scripts/local_webhook.py

# In another terminal, expose with ngrok
ngrok http 8000

# Set Telegram webhook
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-ngrok-url.ngrok.io/webhook"}'
```

### **Testing the Bot**

1. Send a message to your Telegram bot
2. Check the local server logs for incoming requests
3. Verify responses are sent back to Telegram

## 🧪 **Testing**

### **Run Tests**

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest --cov=src/ctrl_alt_heal --cov-report=html

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v
```

### **Test API Endpoints**

```bash
# Health check
curl http://localhost:8000/health

# Test webhook endpoint
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"message": {"text": "Hello", "chat": {"id": 123}}}'
```

## 🔧 **Development Workflow**

### **Code Changes**

The local server runs with auto-reload enabled, so changes to Python files will automatically restart the server.

### **Environment Variables**

- **`.env`** - Main environment file (copy from `env.example`)
- **`.env.local`** - Local development overrides (created by setup script)

### **Logging**

Local development uses DEBUG level logging by default. Check the console output for detailed logs.

## 🐛 **Troubleshooting**

### **Common Issues**

#### **Import Errors**
```bash
# Ensure src is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

#### **AWS Credentials**
```bash
# Configure AWS CLI
aws configure

# Test Bedrock access
aws bedrock list-foundation-models --region ap-southeast-1
```

#### **Port Already in Use**
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn ctrl_alt_heal.fargate_app:app --port 8001
```

#### **LocalStack Issues**
```bash
# Check LocalStack status
docker ps | grep localstack

# Restart LocalStack
docker restart localstack

# Check LocalStack logs
docker logs localstack
```

### **Getting Help**

- **Issues**: Create a GitHub issue
- **Documentation**: Check the [docs/](./docs/) directory
- **Development Guide**: See [docs/development.md](./docs/development.md)

## 🚀 **Production vs Local**

| Feature | Local Development | Production |
|---------|------------------|------------|
| **Database** | LocalStack DynamoDB | AWS DynamoDB |
| **Storage** | LocalStack S3 | AWS S3 |
| **Secrets** | LocalStack Secrets Manager | AWS Secrets Manager |
| **AI Model** | AWS Bedrock (real) | AWS Bedrock |
| **Telegram** | Real Telegram API | Real Telegram API |
| **Logging** | Console output | CloudWatch |

## 📋 **Next Steps**

1. **Set up your environment** using the setup script
2. **Configure your API keys** in the environment file
3. **Start the local server** and test basic functionality
4. **Set up webhook testing** with ngrok
5. **Run the test suite** to verify everything works
6. **Start developing** with confidence!

Happy coding! 🎉
