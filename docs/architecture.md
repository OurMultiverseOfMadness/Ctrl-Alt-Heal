# Ctrl-Alt-Heal Architecture Documentation

This document provides an overview of the architecture for the Ctrl-Alt-Heal application, a serverless, AI-powered "Care Companion" agent.

## High-Level Architecture

The application is designed around a central AI agent that leverages a collection of tools to perform specific tasks. It's a serverless architecture where an AWS Lambda function acts as the main entry point, processing webhooks from Telegram.

```mermaid
graph TD
    subgraph User
        A[Telegram User]
    end

    subgraph AWS Cloud
        B[API Gateway]
        C[Lambda Function: main.handler]
        D[DynamoDB]
        E[Amazon Bedrock]
        F[AWS Secrets Manager]
    end

    subgraph External APIs
        G[Google Calendar API]
        H[DuckDuckGo Search]
    end

    A -- sends message --> B
    B -- triggers --> C
    C -- manages history --> D
    C -- invokes --> Agent

    subgraph Agent Logic
        Agent[Care Companion Agent]
        Tools[Tools]
    end

    Agent -- uses --> Tools
    Tools -- Prescription Extraction --> E
    Tools -- Save/Load Credentials --> F
    Tools -- Calendar Events --> G
    Tools -- Web Search --> H

    Agent -- generates response --> C
    C -- sends response via Telegram API --> A
```

## Data Models

We use Pydantic `BaseModel`s to define our core data types. This provides strong data validation, serialization, and a clear structure.

```mermaid
classDiagram
    class ConversationHistory {
        +String user_id
        +List~Message~ history
        +Dict~String, Any~ state
    }

    class Message {
        +String role
        +String content
    }

    class User {
        +String user_id
        +String first_name
        +String timezone
        +String language
    }

    class Identity {
        +String provider
        +String provider_user_id
        +String user_id
    }

    class Prescription {
        +String name
        +String dosage
        +String frequency
    }

    User "1" -- "1..*" Identity : has
    ConversationHistory "1" -- "1" User : belongs to
    ConversationHistory "1" *-- "0..*" Message : contains
```

## Data Tracking Across DynamoDB Tables

We track user data across all DynamoDB tables using a single, consistent identifier: the internal `user_id`. This `user_id` acts as a foreign key, linking all of a user's records together.

```mermaid
graph TD
    subgraph User
        U[Internal User<br>user_id: abc-123]
    end

    subgraph DynamoDB
        T0[Identities Table]
        T1[Users Table]
        T2[History Table]
        T3[Prescriptions Table]
    end

    U -- "PK: 'telegram#54321'" --> T0
    U -- "PK: 'abc-123'" --> T1
    U -- "PK: 'abc-123'" --> T2
    U -- "PK: 'USER#abc-123'" --> T3

    T0 -- "Returns user_id 'abc-123'" --> U
    T1 -- "Data for user 'abc-123'" --> R1["{ user_id: 'abc-123', ... }"]
    T2 -- "Data for user 'abc-123'" --> R2["{ user_id: 'abc-123', history: [...] }"]
    T3 -- "Data for user 'abc-123'" --> R3["{ pk: 'USER#abc-123', ... }"]

    style U fill:#D6EAF8
    style T0 fill:#D1F2EB
    style T1 fill:#D1F2EB
    style T2 fill:#D1F2EB
    style T3 fill:#D1F2EB
```

## User Identity: Find-or-Create Workflow

The creation and storage of our internal `user_id` is a critical process that happens automatically the very first time a new user sends a message to our bot.

```mermaid
graph TD
    A[Start: Message Received from Telegram] --> B{Extract Telegram chat_id};
    B --> C{Find user_id in Identities table<br>using chat_id};
    C -->|Found| D[Use existing internal user_id];
    C -->|Not Found| E[Create New User in Users Table<br>(with auto-generated UUID)];
    E --> G[Create New Record in Identities Table<br>(Link chat_id to user_id)];
    G --> D;
    D --> H[Proceed with Agent Logic...];

    style E fill:#D5F5E3
    style G fill:#D5F5E3
```

## Agent Context Retrieval Flow

Once the handler has the internal `user_id`, it uses that single ID to fetch all the necessary context for the agent. User-specific details (like timezone) are retrieved on-demand by the tools when they are needed.

```mermaid
sequenceDiagram
    participant Telegram
    participant Lambda Handler (main.py)
    participant IdentitiesStore
    participant UsersStore
    participant HistoryStore
    participant Agent

    Telegram->>Lambda Handler (main.py): Sends Message (with chat_id)
    Lambda Handler (main.py)->>IdentitiesStore: find_user_id_by_identity(chat_id)
    IdentitiesStore-->>Lambda Handler (main.py): Returns internal_user_id

    Lambda Handler (main.py)->>HistoryStore: get_history(internal_user_id)
    HistoryStore-->>Lambda Handler (main.py): Returns ConversationHistory object

    Lambda Handler (main.py)->>Agent: Initializes Agent with history
    Lambda Handler (main.py)->>Agent: agent.invoke(message)

    Note over Agent: Agent decides to call a tool,<br/>e.g., create_google_calendar_event_tool

    Agent-->>Lambda Handler (main.py): Returns tool_call (with internal_user_id)

    Lambda Handler (main.py)->>UsersStore: Tool logic calls get_user(internal_user_id)
    UsersStore-->>Lambda Handler (main.py): Returns User object (with timezone, etc.)

    Note over Lambda Handler (main.py): Tool executes using user details
```

This is a living document and should be updated as the application evolves.

### Deployment

The entire application infrastructure is defined as code using the AWS Cloud Development Kit (CDK) in the `cdk/` directory. This allows for automated, repeatable, and version-controlled deployments.

The infrastructure is divided into three logical stacks:
-   **`DatabaseStack`**: Provisions all five DynamoDB tables (`Users`, `Identities`, `History`, `Prescriptions`, `FHIR`).
-   **`LambdaStack`**: Creates the main Python Lambda function, a Lambda Layer for its dependencies, and the necessary IAM Role with permissions to access the databases and other AWS services.
-   **`ApiGatewayStack`**: Sets up the public HTTP API Gateway that receives webhooks from Telegram and triggers the Lambda function.

#### Deployment Prerequisites
1.  **AWS CDK Toolkit**: Must be installed globally (`npm install -g aws-cdk`).
2.  **AWS Credentials**: Your environment must be configured with AWS credentials that have permission to create the necessary resources. This is typically done via the AWS CLI (`aws configure`).

#### How to Deploy
1.  Navigate to the CDK directory: `cd cdk`
2.  Activate the CDK's virtual environment: `source .venv/bin/activate`
3.  Install CDK Python dependencies: `pip install -r requirements.txt`
4.  Bootstrap your AWS environment (only needs to be done once per account/region): `cdk bootstrap --profile YOUR_PROFILE_NAME`
5.  Deploy all stacks: `cdk deploy --all --profile YOUR_PROFILE_NAME`

After a successful deployment, the CDK will output the API Gateway endpoint URL, which can then be set as the webhook for the Telegram bot.
