# AI Agent Tools

This directory contains specialized tools that the AI agent uses to perform healthcare-specific tasks.

## Tool Categories

### Prescription Processing
- **`prescription_extraction_tool.py`** - Extracts medication information from images and PDFs
- **`prescription_extractor.py`** - Core prescription parsing logic

### Medication Management
- **`medication_schedule_tool.py`** - Medication scheduling and reminder management
- **`medication_ics_tool.py`** - Calendar integration for medication reminders

### User Management
- **`user_profile_tool.py`** - User profile creation, updates, and management
- **`identity_tool.py`** - User identity linking and authentication

### Time and Scheduling
- **`timezone_tool.py`** - Timezone detection and management
- **`calendar_tool.py`** - Calendar integration and ICS generation

### Data and Search
- **`fhir_data_tool.py`** - FHIR-compliant healthcare data management
- **`search_tool.py`** - Web search capabilities for medical information
- **`image_description_tool.py`** - Image analysis and description

### Tool Registry
- **`registry.py`** - Tool registration and management system

## Key Features

### Multi-modal Processing
- **Image Analysis**: Extract text and information from prescription images
- **PDF Processing**: Parse complex prescription documents
- **Text Processing**: Handle natural language medication instructions

### Healthcare Compliance
- **FHIR Standards**: Industry-standard healthcare data format
- **Data Validation**: Comprehensive input validation and sanitization
- **Privacy Protection**: Secure handling of sensitive medical information

### Integration Capabilities
- **Calendar Systems**: ICS file generation for medication reminders
- **Search APIs**: Integration with medical information services
- **User Systems**: Comprehensive user profile and identity management

## Architecture

Each tool follows a consistent pattern:
- **Input Validation**: Type-safe input handling
- **Error Management**: Comprehensive error handling and recovery
- **Logging**: Structured logging for debugging and monitoring
- **Testing**: Comprehensive unit test coverage
