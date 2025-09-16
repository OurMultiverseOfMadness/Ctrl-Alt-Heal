# Source Code Directory

This directory contains the main application source code for Ctrl-Alt-Heal, an AI-powered healthcare companion.

## Structure

- **`ctrl_alt_heal/`** - Main application package containing all core functionality

## Key Components

- **Agent System**: AI-powered care companion using Amazon Bedrock
- **Telegram Interface**: Bot integration for patient communication
- **Infrastructure**: AWS services integration (DynamoDB, S3, Secrets Manager)
- **Tools**: Specialized tools for prescription processing, medication scheduling, and more
- **Core Services**: Dependency injection, caching, logging, and health monitoring

## Architecture

The application follows a clean architecture pattern with clear separation of concerns:
- **Domain Models**: Core business entities and data structures
- **Infrastructure**: External service integrations and data persistence
- **Interface**: External communication (Telegram, HTTP APIs)
- **Tools**: AI agent tools for specific healthcare tasks
- **Utils**: Shared utility functions and helpers

## Development

All source code is organized in the `ctrl_alt_heal` package with comprehensive test coverage and type hints for maintainability.
