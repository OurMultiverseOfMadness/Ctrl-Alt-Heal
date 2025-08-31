# Ctrl-Alt-Heal Architecture Diagram

## System Overview

```mermaid
graph TB
    %% External Users
    User[👤 Telegram User] --> TG[📱 Telegram Bot API]

    %% API Gateway Layer
    TG --> AGW[🌐 API Gateway<br/>HTTPS Endpoints]

    %% Load Balancer
    AGW --> ALB[⚖️ Application Load Balancer<br/>Health Checks]

    %% Fargate Service
    ALB --> Fargate[🐳 Fargate Service<br/>FastAPI Application]

    %% Agent Layer
    Fargate --> Agent[🤖 Care Companion Agent<br/>AWS Strands + Bedrock]

    %% Tools Layer
    Agent --> Tools[🛠️ Tool Registry<br/>13+ Specialized Tools]

    %% Infrastructure Services
    Tools --> DynamoDB[(🗄️ DynamoDB Tables)]
    Tools --> S3[(📦 S3 Buckets)]
    Tools --> Secrets[(🔐 Secrets Manager)]
    Tools --> Bedrock[🧠 Amazon Bedrock<br/>Claude 3.5 Sonnet]

    %% External APIs
    Tools --> Serper[🔍 Serper API<br/>Web Search]
    Tools --> TelegramAPI[📡 Telegram API<br/>File Sending]

    %% Data Flow Styling
    classDef external fill:#e1f5fe
    classDef aws fill:#ffeb3b
    classDef compute fill:#4caf50
    classDef storage fill:#2196f3
    classDef api fill:#ff9800

    class User,TG external
    class AGW,ALB,Fargate,Agent,Bedrock aws
    class Tools compute
    class DynamoDB,S3,Secrets storage
    class Serper,TelegramAPI api
```

## Detailed Component Architecture

```mermaid
graph TB
    %% User Interaction Flow
    subgraph "External Layer"
        User[👤 Telegram User]
        TG[📱 Telegram Bot API]
    end

    %% AWS Infrastructure
    subgraph "AWS Infrastructure"
        subgraph "API & Load Balancing"
            AGW[🌐 API Gateway<br/>• HTTPS Endpoints<br/>• CORS Support<br/>• Request Routing]
            ALB[⚖️ Application Load Balancer<br/>• Health Checks (/health)<br/>• Target Group<br/>• Security Groups]
        end

        subgraph "Compute Layer"
            subgraph "ECS Fargate"
                Fargate[🐳 Fargate Service<br/>• FastAPI Application<br/>• Uvicorn Server<br/>• Container Health]

                subgraph "Application Components"
                    Webhook[📥 Webhook Handler<br/>• Telegram Integration<br/>• Async Processing]
                    ChatAPI[💬 Chat Endpoints<br/>• Direct API Access<br/>• Streaming Responses]
                    AgentCore[🤖 Agent Orchestrator<br/>• Message Routing<br/>• Session Management]
                end
            end
        end

        subgraph "AI & Agent Layer"
            StrandsAgent[🧠 AWS Strands Agent<br/>• Care Companion (Cara)<br/>• Claude 3.5 Sonnet<br/>• System Prompt]

            subgraph "Tool Registry"
                PrescriptionTools[💊 Prescription Tools<br/>• Extraction<br/>• Scheduling<br/>• ICS Generation]
                UserTools[👤 User Tools<br/>• Profile Management<br/>• Identity Linking]
                MedicalTools[🏥 Medical Tools<br/>• Web Search<br/>• FHIR Storage]
                TimezoneTools[🌍 Timezone Tools<br/>• Detection<br/>• Calendar Integration]
                MediaTools[🖼️ Media Tools<br/>• Image Analysis<br/>• Description]
            end
        end

        subgraph "Data Layer"
            subgraph "DynamoDB Tables"
                Users[(👥 User Profiles<br/>• user_id PK)]
                Identities[(🔐 External Identities<br/>• identity_key PK)]
                Conversations[(💬 Conversation History<br/>• user_id PK, session_id SK)]
                Prescriptions[(💊 Medical Prescriptions<br/>• user_id PK, prescription_id SK)]
                FHIR[(🏥 FHIR Resources<br/>• user_id PK, resource_id SK)]
            end

            subgraph "S3 Storage"
                Uploads[(📁 User Uploads<br/>• Images, Files)]
                Assets[(📦 System Assets<br/>• System Prompt, Config)]
            end

            subgraph "Secrets Management"
                TelegramSecret[(🤖 Telegram Bot Token)]
                SerperSecret[(🔍 Serper API Key)]
            end
        end

        subgraph "AI Services"
            Bedrock[🧠 Amazon Bedrock<br/>• Claude 3.5 Sonnet<br/>• Model Inference]
        end
    end

    %% External Services
    subgraph "External APIs"
        SerperAPI[🔍 Serper API<br/>• Web Search<br/>• Medical Information]
        TelegramAPI[📡 Telegram API<br/>• Message Sending<br/>• File Uploads]
    end

    %% Network & Security
    subgraph "Network Layer"
        VPC[🌐 VPC<br/>• Private Subnets<br/>• Security Groups<br/>• NAT Gateway]
    end

    %% Data Flow Connections
    User --> TG
    TG --> AGW
    AGW --> ALB
    ALB --> Fargate

    Fargate --> Webhook
    Fargate --> ChatAPI
    Fargate --> AgentCore

    AgentCore --> StrandsAgent
    StrandsAgent --> PrescriptionTools
    StrandsAgent --> UserTools
    StrandsAgent --> MedicalTools
    StrandsAgent --> TimezoneTools
    StrandsAgent --> MediaTools

    %% Tool to Data Connections
    PrescriptionTools --> Prescriptions
    PrescriptionTools --> FHIR
    UserTools --> Users
    UserTools --> Identities
    MedicalTools --> Conversations
    TimezoneTools --> Users

    %% Media Processing
    MediaTools --> Uploads
    MediaTools --> Assets

    %% External API Connections
    MedicalTools --> SerperAPI
    PrescriptionTools --> TelegramAPI
    UserTools --> TelegramAPI

    %% AI Service Connections
    StrandsAgent --> Bedrock

    %% Secrets Access
    Fargate --> TelegramSecret
    Fargate --> SerperSecret

    %% Network Connections
    Fargate --> VPC
    ALB --> VPC

    %% Styling
    classDef external fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef aws fill:#ffeb3b,stroke:#f57f17,stroke-width:2px
    classDef compute fill:#4caf50,stroke:#2e7d32,stroke-width:2px
    classDef storage fill:#2196f3,stroke:#1565c0,stroke-width:2px
    classDef api fill:#ff9800,stroke:#e65100,stroke-width:2px
    classDef network fill:#9c27b0,stroke:#6a1b9a,stroke-width:2px

    class User,TG external
    class AGW,ALB,Fargate,Webhook,ChatAPI,AgentCore,StrandsAgent,Bedrock aws
    class PrescriptionTools,UserTools,MedicalTools,TimezoneTools,MediaTools compute
    class Users,Identities,Conversations,Prescriptions,FHIR,Uploads,Assets,TelegramSecret,SerperSecret storage
    class SerperAPI,TelegramAPI api
    class VPC network
```

## Data Flow Architecture

```mermaid
sequenceDiagram
    participant User as 👤 Telegram User
    participant TG as 📱 Telegram API
    participant AGW as 🌐 API Gateway
    participant ALB as ⚖️ Load Balancer
    participant Fargate as 🐳 Fargate Service
    participant Agent as 🤖 Care Agent
    participant Tools as 🛠️ Tools
    participant DB as 🗄️ DynamoDB
    participant S3 as 📦 S3
    participant Bedrock as 🧠 Bedrock
    participant Serper as 🔍 Serper API

    %% Message Flow
    User->>TG: Send message/image
    TG->>AGW: Webhook POST
    AGW->>ALB: Route request
    ALB->>Fargate: Forward to service

    %% Async Processing
    Fargate->>Fargate: Create async task
    Fargate->>TG: Return 200 OK immediately

    %% Agent Processing
    Fargate->>Agent: Process message
    Agent->>DB: Get user profile
    Agent->>DB: Get conversation history

    %% Tool Execution
    Agent->>Tools: Execute relevant tools

    alt Image Upload
        Tools->>S3: Store image
        Tools->>Bedrock: Analyze image
        Tools->>DB: Extract & store prescription
    else Text Message
        Tools->>Serper: Search medical info
        Tools->>DB: Update user data
    end

    %% Response Generation
    Tools->>Agent: Return tool results
    Agent->>Bedrock: Generate response
    Agent->>DB: Save conversation
    Agent->>TG: Send response to user
```

## Security Architecture

```mermaid
graph TB
    subgraph "Security Layers"
        subgraph "Network Security"
            VPC[🌐 VPC Isolation]
            SG_ALB[🛡️ ALB Security Group<br/>• Port 80/443 from API Gateway]
            SG_Fargate[🛡️ Fargate Security Group<br/>• Port 8000 from ALB]
            NAT[🌐 NAT Gateway<br/>• Outbound Internet Access]
        end

        subgraph "Application Security"
            IAM_Role[🔑 IAM Role<br/>• Least Privilege Access]
            Secrets[🔐 Secrets Manager<br/>• Encrypted API Keys]
            SSL[🔒 SSL/TLS<br/>• HTTPS Encryption]
        end

        subgraph "Data Security"
            DDB_Encryption[🔐 DynamoDB Encryption<br/>• At Rest & In Transit]
            S3_Encryption[🔐 S3 Encryption<br/>• Server-Side Encryption]
            KMS[🔑 KMS Keys<br/>• Key Management]
        end
    end

    subgraph "Access Control"
        API_Key[🔑 API Gateway Keys<br/>• Rate Limiting]
        User_Auth[👤 User Authentication<br/>• Telegram Chat ID Validation]
        Session_Mgmt[💬 Session Management<br/>• Conversation History]
    end

    %% Connections
    VPC --> SG_ALB
    VPC --> SG_Fargate
    VPC --> NAT

    SG_ALB --> IAM_Role
    SG_Fargate --> IAM_Role

    IAM_Role --> Secrets
    IAM_Role --> DDB_Encryption
    IAM_Role --> S3_Encryption

    DDB_Encryption --> KMS
    S3_Encryption --> KMS

    API_Key --> User_Auth
    User_Auth --> Session_Mgmt

    %% Styling
    classDef security fill:#ff5722,stroke:#d84315,stroke-width:2px
    classDef network fill:#3f51b5,stroke:#283593,stroke-width:2px
    classDef data fill:#009688,stroke:#00695c,stroke-width:2px
    classDef access fill:#795548,stroke:#5d4037,stroke-width:2px

    class IAM_Role,Secrets,SSL,KMS security
    class VPC,SG_ALB,SG_Fargate,NAT network
    class DDB_Encryption,S3_Encryption data
    class API_Key,User_Auth,Session_Mgmt access
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "CDK Stacks"
        subgraph "Database Stack"
            DB_Stack[🗄️ DatabaseStack<br/>• DynamoDB Tables<br/>• S3 Buckets<br/>• IAM Roles]
        end

        subgraph "Secrets Stack"
            Secrets_Stack[🔐 SecretsStack<br/>• Telegram Token<br/>• Serper API Key]
        end

        subgraph "Fargate Stack"
            Fargate_Stack[🐳 FargateStack<br/>• ECS Cluster<br/>• Fargate Service<br/>• Application Load Balancer<br/>• ECR Repository]
        end

        subgraph "API Gateway Stack"
            API_Stack[🌐 ApiGatewayStack<br/>• REST API<br/>• Routes<br/>• Integration]
        end
    end

    subgraph "Deployment Order"
        Step1[1️⃣ Deploy Database]
        Step2[2️⃣ Deploy Secrets]
        Step3[3️⃣ Deploy Fargate]
        Step4[4️⃣ Deploy API Gateway]
    end

    subgraph "Docker Pipeline"
        Build[🔨 Build Image]
        Push[📤 Push to ECR]
        Deploy[🚀 Deploy to Fargate]
    end

    %% Dependencies
    Step1 --> Step2
    Step2 --> Step3
    Step3 --> Step4

    Build --> Push
    Push --> Deploy

    DB_Stack --> Step1
    Secrets_Stack --> Step2
    Fargate_Stack --> Step3
    API_Stack --> Step4

    %% Styling
    classDef stack fill:#ff9800,stroke:#e65100,stroke-width:2px
    classDef step fill:#4caf50,stroke:#2e7d32,stroke-width:2px
    classDef pipeline fill:#2196f3,stroke:#1565c0,stroke-width:2px

    class DB_Stack,Secrets_Stack,Fargate_Stack,API_Stack stack
    class Step1,Step2,Step3,Step4 step
    class Build,Push,Deploy pipeline
```

## Current Infrastructure Status

### ✅ **Deployed Components**
- **4 CDK Stacks**: All CREATE_COMPLETE/UPDATE_COMPLETE
- **1 Fargate Service**: 1/1 tasks running (ACTIVE)
- **1 API Gateway**: HTTPS endpoints accessible
  - **Base URL**: `https://x2ungeyw8c.execute-api.ap-southeast-1.amazonaws.com/production/`
  - **Webhook URL**: `https://x2ungeyw8c.execute-api.ap-southeast-1.amazonaws.com/production/webhook`
- **5 DynamoDB Tables**: All operational with proper schema
- **2 S3 Buckets**: User uploads and system assets
- **2 Secrets**: Telegram bot token and Serper API key

### 🔧 **Key Features**
- **Multi-modal Processing**: Text + Image support
- **Persistent Sessions**: User profiles and conversation history
- **Healthcare Standards**: FHIR-compliant data storage
- **Calendar Integration**: ICS file generation
- **Timezone Management**: Automatic detection and handling
- **Medical Information**: Web search integration

### 🚀 **Scalability**
- **Auto-scaling**: Fargate service can scale based on demand
- **Load Balancing**: ALB distributes traffic across tasks
- **Container-based**: Easy deployment and updates
- **Serverless**: No server management required

This architecture provides a robust, scalable, and secure foundation for the Ctrl-Alt-Heal healthcare assistant application.

## 🎯 **Current Deployment Status**

### **Infrastructure Health**
- ✅ **All CDK Stacks**: Successfully deployed and operational
- ✅ **Fargate Service**: Running with 1/1 tasks (ACTIVE status)
- ✅ **API Gateway**: All endpoints responding correctly
- ✅ **Database**: All tables operational with proper schema
- ✅ **Secrets**: Securely stored and accessible
- ✅ **Telegram Integration**: Webhook configured and functional

### **Recent Improvements**
- 🔧 **Schema Alignment**: Fixed DynamoDB schema mismatches
- 🔧 **FhirStore Consolidation**: Removed duplicate implementations
- 🔧 **Error Handling**: Enhanced session management and error recovery
- 🔧 **Docker Optimization**: Fixed architecture compatibility issues

### **System Capabilities**
- 🚀 **Multi-modal Processing**: Text and image support
- 🚀 **Healthcare Standards**: FHIR-compliant data storage
- 🚀 **Calendar Integration**: ICS file generation
- 🚀 **Timezone Management**: Automatic detection and handling
- 🚀 **Medical Information**: Web search integration
- 🚀 **Persistent Sessions**: User profiles and conversation history
