This document outlines the folder structure of the Ctrl-Alt-Heal application.

### High-Level Structure

The project is organized into several key directories, separating the application logic from the infrastructure code.

```
.
├── cdk/               # AWS CDK Infrastructure-as-Code
├── docs/              # Project documentation
├── infra/             # Infrastructure-related files (e.g., Lambda Layers)
├── src/               # Main application source code
└── tests/             # Unit and integration tests
```

### Source Code (`src/`)

The core application logic resides in `src/ctrl_alt_heal/`.

```
src/ctrl_alt_heal/
├── agent/             # Defines the main Strands agent and its system prompt.
├── config.py          # Centralized Pydantic settings configuration.
├── domain/            # Core data models (e.g., User, Prescription, Identity).
├── infrastructure/    # Clients for external services (AWS, Google, Telegram).
├── tools/             # All tools available to the Strands agent.
└── main.py            # The AWS Lambda handler entry point.
```

*   **`agent/`**: Contains the definition for our main `care_companion` agent, including its initialization and the system prompt that defines its persona and capabilities.
*   **`config.py`**: Uses Pydantic's `BaseSettings` for a robust, centralized configuration system that loads settings from environment variables.
*   **`domain/`**: Holds the Pydantic data models that define the core concepts of our application, such as `User`, `Identity`, `Prescription`, and `ConversationHistory`.
*   **`infrastructure/`**: Contains all the modules responsible for interacting with external services. This includes our DynamoDB data stores (`UsersStore`, `IdentitiesStore`, etc.), the `TelegramClient`, and the `GoogleCalendarClient`.
*   **`tools/`**: Each file in this directory defines a specific capability for the agent (e.g., `google_calendar_tool.py`, `user_profile_tool.py`). The `registry.py` file provides a central mapping of all available tools.
*   **`main.py`**: The entry point for the application. This AWS Lambda handler processes incoming Telegram webhooks, manages user identity, invokes the agent, and dispatches tool calls.

### Infrastructure (`cdk/`)

The `cdk/` directory contains a complete AWS CDK application for deploying the entire infrastructure.

```
cdk/
├── stacks/            # Individual CDK stacks for each part of the infrastructure.
│   ├── api_gateway_stack.py
│   ├── database_stack.py
│   └── lambda_stack.py
├── app.py             # The main entry point for the CDK application.
├── cdk.json           # CDK configuration file.
└── requirements.txt   # Python dependencies for the CDK app itself.
```

This setup defines the DynamoDB tables, the Lambda function, the API Gateway, and the necessary IAM roles and permissions as code, allowing for repeatable and automated deployments.
