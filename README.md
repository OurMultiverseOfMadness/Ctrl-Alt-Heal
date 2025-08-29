# Ctrl-Alt-Heal 🤖💊

> An AI-powered recovery companion that helps patients understand and adhere to their doctor's instructions through intelligent reminders, medication tracking, and proactive support.

## 🌟 Overview

Ctrl-Alt-Heal is an intelligent Telegram bot designed to bridge the gap between patients and their healthcare providers. Many patients struggle with understanding and following their doctor's instructions, leading to suboptimal treatment outcomes. Our AI companion addresses this challenge by providing clear communication, automated reminders, and proactive support throughout the recovery journey.

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

## 🚀 **Quick Start**

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for CDK)
- **AWS CLI** with configured credentials
- **Docker** (for Lambda layer builds)
- **Telegram Bot Token**
- **Amazon Bedrock access** in ap-southeast-1 region

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/Ctrl-Alt-Heal.git
   cd Ctrl-Alt-Heal
   ```

2. **Set up development environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Install CDK dependencies**
   ```bash
   cd cdk
   npm install
   cd ..
   ```

### Deployment

1. **Build Lambda layer**
   ```bash
   ./build-layer.sh
   ```

2. **Deploy infrastructure (one command)**
   ```bash
   cd cdk
   ./deploy.sh
   cd ..
   ```

3. **Configure secrets**
   ```bash
   # Update secrets in AWS Secrets Manager
   aws secretsmanager update-secret \
     --secret-id "ctrl-alt-heal/dev/telegram/bot-token" \
     --secret-string '{"value": "your_telegram_bot_token"}'

   aws secretsmanager update-secret \
     --secret-id "ctrl-alt-heal/dev/serper/api-key" \
     --secret-string '{"api_key": "your_serper_api_key"}'
   ```

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
# Run tests
pytest

# Run with coverage
pytest --cov=src/ctrl_alt_heal --cov-report=html

# Code quality checks
flake8 src/ tests/
black src/ tests/
mypy src/
```

## 📚 **Documentation**

For comprehensive documentation, see the [docs/](./docs/) directory:

- **[📖 Documentation Index](./docs/README.md)** - Complete documentation overview
- **[🏗️ Architecture Guide](./docs/architecture.md)** - System design and architecture
- **[🔧 Development Guide](./docs/development.md)** - Setup and development workflow
- **[📊 Core Services](./docs/core-services.md)** - Core infrastructure documentation
- **[📋 Data Models](./docs/data-models.md)** - Data model documentation
- **[🔄 Refactoring History](./docs/refactoring-history.md)** - Complete refactoring journey

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

```env
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_WEBHOOK_SECRET=your_webhook_secret

# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-southeast-1

# Amazon Bedrock
BEDROCK_MODEL_ID=amazon.nova-1

# Database Configuration
DATABASE_URL=your_database_url

# FHIR Server
FHIR_SERVER_URL=your_fhir_server_url
```

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
│   ├── services/               # Business logic services
│   ├── tools/                  # AI agent tools
│   ├── utils/                  # Utility functions
│   └── worker.py               # Main Lambda handler
├── tests/                      # Test suite (417+ tests)
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── tools/                  # Tool-specific tests
├── cdk/                        # Infrastructure as Code
├── docs/                       # Comprehensive documentation
├── scripts/                    # Utility scripts
└── config/                     # Configuration files
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/ctrl_alt_heal --cov-report=html

# Run specific test categories
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
pytest tests/tools/             # Tool tests only

# Run with verbose output
pytest -v
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
