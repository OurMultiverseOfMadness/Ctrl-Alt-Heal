### Folder Structure (DDD + AWS Strands + Lambda/Container)

Purpose: Keep business logic clean and testable while enabling both Lambda webhook and container long-polling deployments. Agents (AWS Strands) orchestrate tools that delegate to application use cases per bounded context.

```
src/ctrl_alt_heal/
  apps/
    telegram_webhook_lambda/     # API Gateway → Lambda handler
      handler.py                 # Webhook entrypoint (stateless, idempotent)
      di.py                      # Dependency wiring for Lambda (future)
    telegram_bot_service/        # Container service (long polling + scheduler)
      main.py                    # Process entrypoint
      di.py                      # Dependency wiring for service (future)
  agents/
    strands/
      agent.py                   # Strands agent shell
      registry.py                # Tool registry
      tools/                     # Tools that call application layer ports
  contexts/                      # Bounded contexts (pure domain, app, infra per context)
    prescriptions/
      domain/                    # Entities, value objects, services, events, repos (interfaces)
      application/               # Use cases, DTOs, commands/queries
      infrastructure/            # Bedrock adapters, persistence, http clients, mappers
    adherence/
      domain/; application/; infrastructure/
    patient_records/
      domain/; application/; infrastructure/  # FHIR client lives here
    appointments/
      domain/; application/; infrastructure/
    notifications/
      domain/; application/; infrastructure/
  interface/                      # Inbound adapters
    telegram/                     # Handlers map updates → use cases/agent intents
      handlers/
      middlewares/
    http/
  shared/                         # Shared kernel (only truly shared items)
    domain/                       # base_entity, value_objects, events
    application/                  # buses, errors
    infrastructure/               # logging, db utils, message bus
  config/
    settings.py                   # Environment-backed settings

infra/
  cdk/                            # IaC: API GW, Lambdas, DynamoDB, S3, permissions, Scheduler roles

events/                           # EventBridge Scheduler templates, Step Functions (if any)
tests/                            # Mirrors src by context and layer
docs/architecture/                # Architecture decisions, diagrams
```

Key rules:
- Domain layer has no dependencies on infra or external SDKs.
- Application layer defines ports (interfaces) that infra implements.
- Agents/tools call application use cases with validated inputs; no domain mutation in handlers.
- Webhook (Lambda) stays stateless and idempotent; containers can host long-polling + in-process schedulers when desired.
- EventBridge Scheduler triggers Lambdas for reminders; DynamoDB is the source of truth.
