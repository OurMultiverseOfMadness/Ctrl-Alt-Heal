# Ctrl-Alt-Heal 🤖💊

> An AI-powered recovery companion that helps patients understand and adhere to their doctor's instructions through intelligent reminders, medication tracking, and proactive support.

## 🌟 Overview

Ctrl-Alt-Heal is an intelligent Telegram bot designed to bridge the gap between patients and their healthcare providers. Many patients struggle with understanding and following their doctor's instructions, leading to suboptimal treatment outcomes. Our AI companion addresses this challenge by providing clear communication, automated reminders, and proactive support throughout the recovery journey.

## 🔗 Quick Links

### 📚 **Documentation**
- **[📖 Complete Documentation](./docs/README.md)** - Full documentation index
- **[🏗️ Architecture Guide](./docs/architecture.md)** - System design and architecture
- **[🔧 Development Guide](./docs/development.md)** - Setup and development workflow
- **[📊 Core Services](./docs/core-services.md)** - Core infrastructure documentation
- **[📋 Data Models](./docs/data-models.md)** - Data model documentation

### 💻 **Local Development**
- **[🚀 Local Development Guide](./LOCAL_DEVELOPMENT.md)** - Complete local setup guide
- **[⚙️ Environment Configuration](./env.example)** - Example environment file
- **[🔧 Setup Scripts](./scripts/README.md)** - Development and deployment scripts

### 🏗️ **Infrastructure & Deployment**
- **[☁️ CDK Infrastructure](./cdk/README.md)** - Infrastructure as Code documentation
- **[📦 CDK Stacks](./cdk/stacks/README.md)** - AWS resource definitions
- **[🚀 Deployment Guide](./cdk/DEPLOYMENT.md)** - Step-by-step deployment instructions

### 🧪 **Testing & Quality**
- **[🧪 Test Suite](./tests/README.md)** - Comprehensive test documentation
- **[✅ Quality Checks](./scripts/run_quality_checks.sh)** - Automated quality assurance
- **[🔍 Git Status Check](./scripts/check_git_status.sh)** - Pre-commit validation

### 📁 **Source Code Structure**
- **[🤖 AI Agent System](./src/ctrl_alt_heal/agent/README.md)** - AI agent implementation
- **[🔧 Core Services](./src/ctrl_alt_heal/core/README.md)** - Core infrastructure services
- **[🏗️ Infrastructure Layer](./src/ctrl_alt_heal/infrastructure/README.md)** - AWS integrations
- **[🛠️ AI Tools](./src/ctrl_alt_heal/tools/README.md)** - AI agent tools and utilities
- **[💬 Interface Layer](./src/ctrl_alt_heal/interface/README.md)** - Telegram and API interfaces
- **[🔧 Utilities](./src/ctrl_alt_heal/utils/README.md)** - Helper functions and utilities

## 🚀 Key Features

### 📋 **Smart Prescription Processing**
- **Multi-modal AI**: Extracts medication information from images, PDFs, and text
- **Intelligent Parsing**: Automatically identifies dosage, frequency, and duration
- **FHIR Compliance**: Stores patient records in industry-standard FHIR format

### ⏰ **Automated Reminders & Tracking**
- **Medication Reminders**: Timely notifications for medication intake
- **Treatment Adherence**: Ensures completion of prescribed medication courses
- **Progress Monitoring**: Tracks patient compliance and recovery milestones

### 🏥 **Appointment Management**
- **Smart Scheduling**: Facilitates follow-up appointment booking
- **Doctor Preference**: Prioritizes scheduling with the same healthcare provider
- **Calendar Integration**: Seamless appointment management

### 💬 **Proactive Patient Support**
- **Well-being Check-ins**: Periodic health status monitoring
- **Clear Communication**: Simplifies complex medical instructions
- **Familiar Interface**: Chat Apps reduces cognitive burden

### 🧠 **Knowledge Base Integration**
- **Medication Database**: Comprehensive drug information and interactions
- **Patient Records**: Secure FHIR-compliant data storage
- **Contextual Support**: Relevant medical information retrieval

## 🏗️ Architecture

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram Bot  │    │  Amazon Bedrock │    │   Multi-modal   │
│   (Interface)   │◄──►│   (LLM Engine)  │◄──►│   AI Processor  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Scheduling     │    │   Knowledge     │    │  Appointment    │
│   Service       │    │    Base         │    │   Service       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technology Stack

- **AI Engine**: Amazon Bedrock with Nova model
- **Chat Interface**: Telegram Bot API
- **Multi-modal AI**: Image and PDF processing capabilities
- **Data Storage**: FHIR-compliant patient records
- **Scheduling**: Automated reminder system
- **Knowledge Base**: Medical information retrieval service
- **Infrastructure**: AWS Fargate with Application Load Balancer
- **API Gateway**: External HTTPS access
- **Container**: Docker with Python 3.12

## 🏆 Hackathon Submission

This repository is submitted for a hackathon and contains:

- **Complete Application Code**: Full AI-powered healthcare companion
- **Infrastructure as Code**: AWS CDK deployment scripts
- **Comprehensive Documentation**: Detailed setup and usage instructions
- **Test Suite**: 400+ tests with 95%+ coverage
- **Open Source**: MIT License for community use

### Repository Structure
- **`src/`** - Main application source code with README files in each directory
- **`cdk/`** - AWS infrastructure definitions
- **`tests/`** - Comprehensive test suite
- **`docs/`** - Complete documentation
- **`scripts/`** - Utility scripts for development and deployment

## 🚀 **Quick Start**

### Prerequisites

#### **Development Tools**
- **Python 3.12+**
- **Node.js 18+** (for CDK)
- **Docker** (for container builds)
- **Git**

#### **AWS Account Setup**
- **AWS Account** with billing enabled
- **AWS CLI** configured with appropriate permissions
- **Amazon Bedrock access** enabled in ap-southeast-1 region
- **IAM permissions** for: ECS, ECR, DynamoDB, S3, Secrets Manager, API Gateway, CloudFormation

#### **External Services**
- **Telegram Bot Token** (create via @BotFather)
- **Serper API Key** (sign up at serper.dev)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/Ctrl-Alt-Heal.git
   cd Ctrl-Alt-Heal
   ```

2. **Set up development environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Configure environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration values
   ```

4. **Install CDK dependencies**
   ```bash
   cd cdk
   npm install
   cd ..
   ```

### AWS Account Setup

1. **Enable Amazon Bedrock**
   ```bash
   # Navigate to AWS Console > Bedrock > Model access
   # Request access to: Amazon Nova Lite (APAC)
   # Region: ap-southeast-1 (Singapore)
   ```

2. **Configure AWS CLI**
   ```bash
   aws configure
   # Enter your AWS Access Key ID, Secret Access Key, and region
   ```

3. **Create Telegram Bot**
   ```bash
   # Message @BotFather on Telegram
   # Use /newbot command
   # Save the bot token for later
   ```

4. **Get Serper API Key**
   ```bash
   # Visit https://serper.dev
   # Sign up for free account
   # Get your API key from dashboard
   ```

### Deployment

1. **Deploy Infrastructure (One Command)**
   ```bash
   # Deploy everything to AWS
   ./deploy-fargate.sh --profile your-aws-profile
   ```

   This script will:
   - ✅ Bootstrap CDK (if needed)
   - ✅ Deploy all AWS resources (DynamoDB, S3, ECR, ECS, API Gateway)
   - ✅ Build and push Docker image
   - ✅ Deploy Fargate service
   - ✅ Provide API Gateway URLs

2. **Configure Secrets**
   ```bash
   # Set up Telegram bot token
   python scripts/update_telegram_secret.py your_telegram_bot_token

   # Set up Serper API key
   python scripts/update_serper_secret.py your_serper_api_key
   ```

3. **Configure Telegram Webhook**
   ```bash
   # Get the webhook URL from deployment output
   # Set webhook via Telegram API
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://your-api-gateway-url/webhook"}'
   ```

4. **Test Deployment**
   ```bash
   # Send a message to your Telegram bot
   # Check CloudWatch logs for any errors
   aws logs describe-log-groups --log-group-name-prefix "/aws/ecs/ctrl-alt-heal"
   ```

## 💻 **Local Development**

For development and testing, you can run the application locally:

### **Quick Local Setup**

```bash
# Set up local development environment
python scripts/setup_local_dev.py

# Start local server
python scripts/local_webhook.py
```

**Local server will be available at:**
- **API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs
- **Webhook**: http://localhost:8000/webhook

**Mock Mode**: The local setup includes mock AI responses, so you don't need AWS Bedrock access for basic development and testing.

### **Telegram Webhook Testing**

```bash
# Expose local server with ngrok
ngrok http 8000

# Set webhook to your ngrok URL
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-ngrok-url.ngrok.io/webhook"}'
```

**See [LOCAL_DEVELOPMENT.md](./LOCAL_DEVELOPMENT.md) for complete local development guide.**

### Environment Configuration

The deployment supports multiple environments with **no hardcoded account IDs**:

```bash
# Development
export ENVIRONMENT=dev
export AWS_REGION=ap-southeast-1

# Production
export ENVIRONMENT=prod
export AWS_REGION=ap-southeast-1

# Deploy
cd cdk && ./deploy.sh
```

**The deployment automatically detects your AWS account and region.**

### AI Model Configuration

The application uses **Amazon Nova Lite** in the APAC region for optimal performance:

```bash
# Default Bedrock models (already configured)
BEDROCK_MODEL_ID=apac.amazon.nova-lite-v1:0
BEDROCK_MULTIMODAL_MODEL_ID=apac.amazon.nova-lite-v1:0
```

**Features:**
- ✅ **APAC Optimized**: Designed for Asia-Pacific users
- ✅ **Cost Effective**: Nova Lite provides excellent value
- ✅ **Multimodal**: Handles text and image processing
- ✅ **Healthcare Focused**: Optimized for medical conversations

### Development

```bash
# Run comprehensive quality checks (source files only)
./scripts/run_quality_checks.sh

# Run individual checks
pytest tests/ -v                    # Run tests
pre-commit run --files src/ tests/ *.py *.md *.yaml *.yml *.json *.toml *.sh  # Linting and formatting
mypy src/ --ignore-missing-imports --exclude '.*/(venv|\.venv|node_modules|\.git|\.pytest_cache|\.mypy_cache|\.ruff_cache|__pycache__|build|dist|packaging|lambda_layer|cdk/lambda_layer|infra/lambda_layers)/.*'  # Type checking

# Check git status before committing
./scripts/check_git_status.sh

# Run with coverage
pytest --cov=src/ctrl_alt_heal --cov-report=html
```

## 📚 **Documentation**

**📌 See the [Quick Links](#-quick-links) section above for easy navigation to all documentation.**

For comprehensive documentation, see the [docs/](./docs/) directory:

- **[📖 Documentation Index](./docs/README.md)** - Complete documentation overview
- **[🏗️ Architecture Guide](./docs/architecture.md)** - System design and architecture
- **[🔧 Development Guide](./docs/development.md)** - Setup and development workflow
- **[📊 Core Services](./docs/core-services.md)** - Core infrastructure documentation
- **[📋 Data Models](./docs/data-models.md)** - Data model documentation

## 📱 Usage

### For Patients

1. **Start a conversation** with the bot on Telegram
2. **Upload prescription** images or PDFs for processing
3. **Receive automated reminders** for medication and appointments
4. **Get support** through natural language interactions
5. **Track progress** and adherence to treatment plans

### For Healthcare Providers

- **FHIR Records**: Access standardized patient data
- **Adherence Reports**: Monitor patient compliance
- **Communication**: Seamless patient follow-up
- **Administrative Relief**: Reduced manual tracking

## 🔧 Configuration

### Environment Variables

The application uses environment variables for configuration. A comprehensive example file is provided:

```bash
# Copy the example environment file
cp env.example .env

# Edit with your actual values
nano .env  # or your preferred editor
```

**Key Environment Variables:**
- `AWS_REGION` - AWS region (default: ap-southeast-1)
- `BEDROCK_MODEL_ID` - Amazon Bedrock model (default: apac.amazon.nova-lite-v1:0)
- `TELEGRAM_SECRET_NAME` - AWS Secrets Manager secret name for Telegram bot token
- `SERPER_SECRET_NAME` - AWS Secrets Manager secret name for Serper API key
- `UPLOADS_BUCKET_NAME` - S3 bucket for file uploads
- `ASSETS_BUCKET_NAME` - S3 bucket for application assets

**Security Note:** Sensitive values (API keys, tokens) are stored in AWS Secrets Manager, not as environment variables.

See `env.example` for the complete list of configuration options.

### Virtual environment (recommended)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### AWS SSO profile usage
- Login once:
```bash
aws sso login --profile your-sso-profile
```
- Use with CDK:
```bash
AWS_PROFILE=your-sso-profile npm run deploy
# or
npm run deploy -- --profile your-sso-profile
```

## 🧪 Testing Instructions

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest --cov=src/ctrl_alt_heal --cov-report=html

# Run specific test categories
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only

# Run quality checks
./scripts/run_quality_checks.sh
```

### Test Coverage
- **400+ Tests**: Comprehensive test suite covering all components
- **95%+ Coverage**: High code coverage ensuring reliability
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **Mocking**: External dependencies properly mocked

## 🧪 Development

### Project Structure

```
Ctrl-Alt-Heal/
├── src/ctrl_alt_heal/          # Main application code
│   ├── agent/                  # AI agent implementation
│   ├── api/                    # API handlers and validators
│   ├── core/                   # Core services (DI, caching, logging, etc.)
│   ├── domain/                 # Data models and domain logic
│   ├── infrastructure/         # External service integrations
│   ├── interface/              # Interface implementations
│   ├── tools/                  # AI agent tools
│   └── utils/                  # Utility functions
├── tests/                      # Test suite (400+ tests)
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── fixtures/               # Test data and fixtures
├── cdk/                        # Infrastructure as Code
├── docs/                       # Comprehensive documentation
├── scripts/                    # Utility scripts
└── config/                     # Configuration files
```


### Code Quality

```bash
# Linting
flake8 src/ tests/

# Type checking
mypy src/

# Formatting
black src/ tests/

# Security scanning
bandit -r src/

# Pre-commit hooks
pre-commit install
pre-commit run --all-files
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏥 Healthcare Compliance

- **HIPAA Compliant**: Patient data protection and privacy
- **FHIR Standard**: Industry-standard healthcare data format
- **Secure Communication**: End-to-end encryption for patient interactions
- **Audit Trails**: Comprehensive logging for compliance

## 🛡️ **Enterprise Features**

### **Security & Robustness**
- **Advanced Security**: Input sanitization, rate limiting, and audit logging
- **Circuit Breaker Pattern**: Resilient AWS service integration
- **Health Monitoring**: Real-time system health and performance tracking
- **Error Handling**: Comprehensive error management and recovery

### **Code Quality & Architecture**
- **Dependency Injection**: Clean, testable, and maintainable architecture
- **Multi-layer Caching**: Optimized performance with intelligent caching
- **Structured Logging**: JSON logging with correlation IDs and performance tracking
- **Configuration Management**: Dynamic feature flags and environment management

### **Testing & Quality Assurance**
- **Comprehensive Testing**: 417+ tests with 95%+ coverage
- **Code Quality**: Zero linting errors, comprehensive type checking
- **Security Scanning**: Automated security vulnerability detection
- **Performance Monitoring**: Real-time performance metrics and alerting

## 🆘 Support

- **Documentation**: [Wiki](https://github.com/your-username/Ctrl-Alt-Heal/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-username/Ctrl-Alt-Heal/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/Ctrl-Alt-Heal/discussions)

## 🔧 **Troubleshooting**

### Common Issues

#### **Bedrock Access Denied**
```bash
# Check if Bedrock is enabled in your region
aws bedrock list-foundation-models --region ap-southeast-1

# Enable Bedrock access in AWS Console
# Go to: Bedrock > Model access > Request model access
```

#### **Docker Build Fails**
```bash
# Ensure Docker is running
docker --version

# Check available disk space
df -h

# Clean up Docker cache
docker system prune -a
```

#### **CDK Bootstrap Issues**
```bash
# Bootstrap CDK manually
cdk bootstrap aws://ACCOUNT-ID/ap-southeast-1

# Check CDK version
cdk --version
```

#### **Telegram Webhook Not Working**
```bash
# Check webhook status
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"

# Delete webhook and set again
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/deleteWebhook"
```

#### **Fargate Service Not Starting**
```bash
# Check ECS service status
aws ecs describe-services --cluster ctrl-alt-heal-cluster --services ctrl-alt-heal-service

# Check CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix "/aws/ecs/ctrl-alt-heal"
```

### Getting Help

- **Issues**: Create a GitHub issue with deployment logs
- **Documentation**: Check the [docs/](./docs/) directory
- **AWS Support**: For AWS-specific issues

## 🙏 Acknowledgments

- Amazon Bedrock team for the Nova model
- Telegram for the bot platform
- FHIR community for healthcare standards
- Open source contributors

---

**⚠️ Medical Disclaimer**: This application is designed to assist with medication adherence and healthcare communication but should not replace professional medical advice. Always consult with healthcare providers for medical decisions.

**Made with ❤️ for better healthcare outcomes**

### Local development with ngrok (webhook testing)

1) Start a local webhook server that calls the Lambda handler

```bash
pip install fastapi uvicorn
```

Create `scripts/local_webhook.py` with:

```python
from __future__ import annotations
from fastapi import FastAPI, Request, Response
from src.ctrl_alt_heal.apps.telegram_webhook_lambda.handler import handler as lambda_handler

app = FastAPI()

@app.post("/telegram/webhook")
async def webhook(req: Request) -> Response:
    body = await req.body()
    event = {
        "headers": {k: v for k, v in req.headers.items()},
        "body": body.decode("utf-8"),
        "isBase64Encoded": False,
    }
    result = lambda_handler(event, None)
    return Response(content=result.get("body", "ok"), status_code=result.get("statusCode", 200))
```

Run it:

```bash
uvicorn scripts.local_webhook:app --host 0.0.0.0 --port 8080 --reload
```

2) Expose it with ngrok

```bash
ngrok http 8080
# Copy the https URL printed, e.g. https://abcd-1234.ngrok-free.app
```

3) Point Telegram to your ngrok URL

```bash
export TELEGRAM_BOT_TOKEN=...
export TELEGRAM_WEBHOOK_SECRET=...
export WEBHOOK_URL="https://abcd-1234.ngrok-free.app/telegram/webhook"
python scripts/set_telegram_webhook.py
```

Notes:
- The same handler logic runs locally and in Lambda (secret header is validated if provided).
- Stop ngrok or server when done; re-run the webhook script if the URL changes.
