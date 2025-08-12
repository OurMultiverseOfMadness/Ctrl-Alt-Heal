from __future__ import annotations

"""
This module is intended for long-running processes (e.g., App Runner, ECS Fargate, EC2).
Do not use this as an AWS Lambda entrypoint. For Lambda handlers, see:

- src.ctrl_alt_heal.apps.telegram_webhook_lambda.handler.handler
- src.ctrl_alt_heal.apps.reminders.send_reminder.handler
"""


def main() -> None:
    # Placeholder entrypoint for containerized long-polling bot.
    # Will initialize DI and start polling loop in future edits.
    print("Ctrl-Alt-Heal bot service placeholder running.")


if __name__ == "__main__":
    main()
