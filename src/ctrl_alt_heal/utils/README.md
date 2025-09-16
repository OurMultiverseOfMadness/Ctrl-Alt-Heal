# Utility Functions

This directory contains shared utility functions and helper modules used throughout the application.

## Components

### Core Utilities
- **`constants.py`** - Application constants and configuration values
- **`exceptions.py`** - Custom exception classes and error handling
- **`error_handling.py`** - Error handling decorators and utilities

### Data Processing
- **`datetime_utils.py`** - Date and time manipulation utilities
- **`string_utils.py`** - String processing and sanitization
- **`validation.py`** - Input validation and data validation utilities

### Session Management
- **`session_utils.py`** - User session management and timeout handling
- **`history_management.py`** - Conversation history optimization and management

### Time and Timezone
- **`time_parsing.py`** - Time parsing and validation utilities
- **`timezone_utils.py`** - Timezone detection and conversion
- **`timezone.py`** - Timezone-related utilities

### Communication
- **`telegram_formatter.py`** - Telegram message formatting and parsing

### Domain-Specific
- **`medication.py`** - Medication-related utility functions

## Key Features

### Data Validation
- **Type Safety**: Comprehensive type checking and validation
- **Input Sanitization**: Security-focused input cleaning
- **Error Handling**: Graceful error handling and recovery

### Performance Optimization
- **Caching**: Intelligent caching strategies
- **Memory Management**: Efficient memory usage patterns
- **Processing**: Optimized data processing algorithms

### Healthcare Compliance
- **Medical Data**: Healthcare-specific data processing
- **Privacy**: Privacy-focused data handling
- **Standards**: Compliance with healthcare data standards

## Architecture

All utilities follow consistent patterns:
- **Pure Functions**: Stateless, predictable functions
- **Type Hints**: Comprehensive type annotations
- **Documentation**: Clear docstrings and examples
- **Testing**: Comprehensive unit test coverage
