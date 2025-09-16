# Interface Layer

This directory contains all external communication interfaces and adapters.

## Components

### Telegram Integration
- **`telegram_client.py`** - Core Telegram Bot API client
- **`telegram_sender.py`** - Message sending and file delivery
- **`download.py`** - File download and processing utilities

### HTTP Interface
- **`http/`** - HTTP API handlers and middleware

### Telegram Handlers
- **`handlers/router.py`** - Message routing and processing
- **`middlewares/`** - Request/response middleware

## Key Features

### Telegram Bot Integration
- **Message Processing**: Handle text, images, and file uploads
- **File Management**: Download, process, and send files
- **Error Handling**: Robust error recovery and user feedback
- **Rate Limiting**: Prevent API abuse and ensure reliability

### HTTP API
- **RESTful Endpoints**: Clean API design for external integrations
- **Request Validation**: Type-safe request handling
- **Response Formatting**: Consistent response structures
- **Authentication**: Secure API access control

### File Handling
- **Multi-format Support**: Images, PDFs, and documents
- **S3 Integration**: Secure file storage and retrieval
- **Processing Pipeline**: Automated file processing workflows

## Architecture

The interface layer follows the Adapter pattern:
- **Abstractions**: Interface-based design for testability
- **Implementations**: Service-specific adapters
- **Error Handling**: Comprehensive error management
- **Performance**: Optimized for high-throughput scenarios
