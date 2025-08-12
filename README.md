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

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the bot**
   ```bash
   python main.py
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

# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1

# Amazon Bedrock
BEDROCK_MODEL_ID=amazon.nova-1

# Database Configuration
DATABASE_URL=your_database_url

# FHIR Server
FHIR_SERVER_URL=your_fhir_server_url
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