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

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8+
- Telegram Bot Token
- Amazon Bedrock access
- AWS credentials configured

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/Ctrl-Alt-Heal.git
   cd Ctrl-Alt-Heal
   ```

2. **Create and activate a virtual environment, then install dependencies**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **CDK (infra) setup and deploy**
   ```bash
   cd infra/cdk
   npm install
   AWS_PROFILE=your-sso-profile npm run cdk -- bootstrap
   AWS_PROFILE=your-sso-profile npm run deploy
   ```

5. **Set Telegram webhook**
   ```bash
   export TELEGRAM_BOT_TOKEN=...   # or store in Secrets Manager as provisioned by CDK
   export TELEGRAM_WEBHOOK_SECRET=...
   export WEBHOOK_URL="https://<api-id>.execute-api.<region>.amazonaws.com/telegram/webhook"
   python scripts/set_telegram_webhook.py
   ```

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
├── src/
│   ├── bot/              # Telegram bot implementation
│   ├── ai/               # AI processing modules
│   ├── services/         # Core services (scheduling, knowledge base, etc.)
│   ├── models/           # Data models and FHIR schemas
│   └── utils/            # Utility functions
├── tests/                # Test suite
├── docs/                 # Documentation
├── config/               # Configuration files
└── requirements.txt      # Python dependencies
```

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Linting
flake8 src/

# Type checking
mypy src/

# Formatting
black src/
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
