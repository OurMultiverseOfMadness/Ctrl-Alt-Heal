# Python Developer Assistant

This document provides instructions for the Python Developer Assistant.

## High-Level Instructions

- The primary goal of this project is to create a care companion agent that helps patients stick to their prescriptions and assists them in their recovery journey.
- The agent is built using the Strands SDK and is deployed as an AWS Lambda function.
- The agent interacts with users through a Telegram bot.

## Project Structure

The project is organized into the following structure:

```
src/ctrl_alt_heal/
├── agent/
│   └── care_companion.py
├── tools/
│   ├── prescription_extractor.py
│   ├── fhir_store.py
│   ├── calendar_tool.py
│   └── medication_info.py
├── services/
│   └── telegram_service.py
├── domain/
│   └── models.py
├── infrastructure/
│   ├── bedrock.py
│   ├── prescriptions_store.py
│   └── fhir_store.py
└── main.py
```

When making changes to the codebase, please adhere to this structure.
