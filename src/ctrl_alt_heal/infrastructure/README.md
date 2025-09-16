# Infrastructure Layer

This directory contains all external service integrations and data persistence implementations.

## Components

- **`bedrock.py`** - Amazon Bedrock AI service integration
- **`fhir_store.py`** - FHIR-compliant healthcare data storage
- **`history_store.py`** - Conversation history management
- **`identities_store.py`** - User identity and authentication management
- **`logger.py`** - Infrastructure logging utilities
- **`prescriptions_store.py`** - Medical prescription data management
- **`secrets.py`** - AWS Secrets Manager integration
- **`secrets_store.py`** - Secure credential management
- **`users_store.py`** - User profile and data management

## Key Features

### AWS Integration
- **DynamoDB**: NoSQL database for user data, conversations, and prescriptions
- **S3**: File storage for uploaded images and documents
- **Secrets Manager**: Secure credential and API key management
- **Bedrock**: AI model integration for natural language processing

### Data Models
- **FHIR Compliance**: Industry-standard healthcare data format
- **User Profiles**: Comprehensive user information management
- **Conversation History**: Optimized chat history storage
- **Prescriptions**: Medical prescription data with validation

### Security
- **Encryption**: Data encryption at rest and in transit
- **Access Control**: Role-based access to sensitive data
- **Audit Logging**: Comprehensive audit trails
- **Input Validation**: Data sanitization and validation

## Architecture

The infrastructure layer follows the Repository pattern:
- **Abstractions**: Interface-based design for testability
- **Implementations**: AWS service-specific implementations
- **Error Handling**: Robust error management and recovery
- **Performance**: Optimized queries and caching strategies
