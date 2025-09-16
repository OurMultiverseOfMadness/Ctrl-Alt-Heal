# AI Agent System

This directory contains the AI agent implementation that powers the healthcare companion functionality.

## Components

- **`care_companion.py`** - Main agent implementation using Amazon Bedrock Nova model
- **`system_prompt.txt`** - Healthcare-focused system prompt for the AI agent

## Key Features

- **Healthcare-Focused AI**: Specialized prompts for medical conversations
- **Multi-modal Processing**: Handles text, images, and PDFs
- **Tool Integration**: Connects to 22+ specialized healthcare tools
- **Conversation Management**: Maintains context and history
- **User Context**: Personalized interactions based on user profiles

## Architecture

The agent system uses:
- **Amazon Bedrock Nova Lite**: APAC-optimized AI model
- **Strands Agents Framework**: Tool orchestration and management
- **Context Management**: Optimized conversation history handling
- **Error Handling**: Robust error recovery and fallback mechanisms

## Tools Integration

The agent has access to specialized tools for:
- Prescription extraction and processing
- Medication scheduling and reminders
- User profile management
- Timezone detection and management
- Calendar integration (ICS generation)
- FHIR data management
- Web search capabilities
- Image description and analysis
