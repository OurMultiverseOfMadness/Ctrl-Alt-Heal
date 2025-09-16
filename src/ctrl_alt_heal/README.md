# Ctrl-Alt-Heal Application Package

This is the main application package for Ctrl-Alt-Heal, an AI-powered healthcare companion that helps patients understand and adhere to their doctor's instructions.

## Package Structure

### Core Components

- **`agent/`** - AI agent implementation using Amazon Bedrock Nova model
- **`api/`** - API handlers and request validation
- **`config/`** - Configuration management and settings
- **`core/`** - Core services (dependency injection, caching, logging, health monitoring)
- **`domain/`** - Domain models and business entities
- **`infrastructure/`** - External service integrations (AWS, databases)
- **`interface/`** - External communication interfaces (Telegram, HTTP)
- **`tools/`** - AI agent tools for healthcare-specific tasks
- **`utils/`** - Shared utility functions and helpers

### Main Application

- **`fargate_app.py`** - FastAPI application running on AWS Fargate

## Key Features

- **Multi-modal AI Processing**: Handles text, images, and PDFs for prescription extraction
- **Medication Management**: Automated scheduling and reminder system
- **FHIR Compliance**: Industry-standard healthcare data format
- **Telegram Integration**: User-friendly chat interface
- **AWS Integration**: Scalable cloud infrastructure

## Architecture Principles

- **Clean Architecture**: Clear separation of concerns
- **Dependency Injection**: Testable and maintainable code
- **Type Safety**: Comprehensive type hints throughout
- **Error Handling**: Robust error management and recovery
- **Health Monitoring**: Real-time system health tracking

## Development

The package is designed for maintainability with comprehensive test coverage, structured logging, and clear documentation.
