import json
from typing import Any

from ctrl_alt_heal.agent.care_companion import get_agent
from ctrl_alt_heal.domain.models import Identity, Message, User
from ctrl_alt_heal.infrastructure.history_store import HistoryStore
from ctrl_alt_heal.infrastructure.identities_store import IdentitiesStore
from ctrl_alt_heal.interface.telegram_sender import send_telegram_message
from ctrl_alt_heal.infrastructure.users_store import UsersStore
from ctrl_alt_heal.tools.registry import tool_registry
from datetime import UTC, datetime
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: dict[str, Any], _context: Any) -> None:
    """AWS Lambda handler for processing SQS messages."""
    logger.info("--- WORKER LAMBDA INVOCATION --- CODE VERSION: 2 ---")
    for record in event["Records"]:
        body = json.loads(record["body"])
        message = body.get("message", {})
        chat = message.get("chat", {})
        chat_id = str(chat.get("id"))
        text = message.get("text", "")

        if text:
            # Find or create user
            identities_store = IdentitiesStore()
            users_store = UsersStore()
            user_id = identities_store.find_user_id_by_identity("telegram", chat_id)

            if user_id:
                user = users_store.get_user(user_id)
                if user:
                    # Update user info
                    now = datetime.now(UTC).isoformat()
                    user.first_name = chat.get("first_name")
                    user.last_name = chat.get("last_name")
                    user.username = chat.get("username")
                    user.updated_at = now
                    users_store.upsert_user(user)
            else:
                # Create new user and identity
                now = datetime.now(UTC).isoformat()
                new_user = User(
                    first_name=chat.get("first_name"),
                    last_name=chat.get("last_name"),
                    username=chat.get("username"),
                    created_at=now,
                    updated_at=now,
                )
                users_store.upsert_user(new_user)
                user_id = new_user.user_id
                identity = Identity(
                    provider="telegram",
                    provider_user_id=chat_id,
                    user_id=user_id,
                    created_at=now,
                )
                identities_store.link_identity(identity)

            # Process message
            history_store = HistoryStore()
            conversation_history = history_store.get_history(user_id)

            agent = get_agent(conversation_history)
            response_obj = agent(text)
            response_str = str(response_obj)  # Explicitly convert to string

            conversation_history.history.append(Message(role="user", content=text))

            # The agent's response might be a string or a dict with tool calls
            if isinstance(response_obj, dict) and "tool_calls" in response_obj:
                for tool_call in response_obj["tool_calls"]:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    # Add user_id to tool args if not present
                    if "user_id" not in tool_args:
                        tool_args["user_id"] = user_id

                    tool_function = tool_registry.get(tool_name)
                    if tool_function:
                        tool_function(**tool_args)
                    else:
                        print(f"Warning: Tool '{tool_name}' not found in registry.")

                history_store.save_history(conversation_history)
            else:
                # This is a standard text response, clean it and send it
                if "</thinking>" in response_str:
                    final_message = response_str.split("</thinking>")[-1].strip()
                else:
                    final_message = response_str

                conversation_history.history.append(
                    Message(role="assistant", content=final_message)
                )
                history_store.save_history(conversation_history)

                logger.info("Agent generated response. Preparing to send to Telegram.")
                send_telegram_message(chat_id, final_message)
                logger.info("Finished sending message to Telegram.")
