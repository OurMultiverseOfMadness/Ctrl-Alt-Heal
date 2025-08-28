import json
from typing import Any

import boto3
import requests
from ctrl_alt_heal.agent.care_companion import get_agent
from ctrl_alt_heal.domain.models import ConversationHistory, Identity, Message, User
from ctrl_alt_heal.infrastructure.history_store import HistoryStore
from ctrl_alt_heal.infrastructure.identities_store import IdentitiesStore
from ctrl_alt_heal.infrastructure.secrets import get_secret
from ctrl_alt_heal.interface.telegram_sender import (
    get_telegram_file_path,
    send_telegram_message,
)
from ctrl_alt_heal.infrastructure.users_store import UsersStore
from ctrl_alt_heal.tools.registry import tool_registry
from datetime import UTC, datetime, timedelta
import logging
import uuid
from strands import Agent
from ctrl_alt_heal.config import settings

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")

SESSION_TIMEOUT_MINUTES = 30  # Define session timeout


def process_agent_response(
    agent_response_obj: Any,
    agent: Agent,
    user: User,
    history: ConversationHistory,
    chat_id: str,
):
    """
    Processes the agent's response, handling tool calls recursively and sending the final message.
    """
    logger.info(
        f"--- Processing agent response. Raw response object: {agent_response_obj} ---"
    )
    if isinstance(agent_response_obj, dict) and "tool_calls" in agent_response_obj:
        logger.info("Tool call(s) detected in agent response.")
        tool_calls = agent_response_obj["tool_calls"]
        tool_results = []
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["tool_call_id"]

            logger.info(
                f"Executing tool call: ID='{tool_call_id}', Name='{tool_name}', Args='{tool_args}'"
            )

            # The agent sometimes forgets the user_id, so we add it back in
            if "user_id" not in tool_args:
                logger.info("Injecting 'user_id' into tool arguments.")
                tool_args["user_id"] = user.user_id

            # Get the tool function from the registry
            tool_function = tool_registry.get(tool_name)

            if tool_function:
                try:
                    # Execute the tool
                    logger.info(f"Executing tool: '{tool_name}'...")
                    result = tool_function(**tool_args)
                    logger.info(
                        f"Tool '{tool_name}' executed successfully. Result: {result}"
                    )
                    # Format the result for the agent
                    tool_results.append(
                        {"tool_result_id": tool_call_id, "content": json.dumps(result)}
                    )
                except Exception as e:
                    logger.error(f"Error executing tool {tool_name}: {e}")
                    tool_results.append(
                        {"tool_result_id": tool_call_id, "content": f"Error: {str(e)}"}
                    )
            else:
                logger.warning(f"Tool '{tool_name}' not found in registry.")
                tool_results.append(
                    {
                        "tool_result_id": tool_call_id,
                        "content": f"Error: Tool '{tool_name}' not found.",
                    }
                )

        # Send tool results back to the agent
        logger.info(f"Sending tool results back to agent: {tool_results}")
        next_response = agent(tool_results=tool_results)
        logger.info(f"Received next response from agent: {next_response}")
        # Process the next response, which could be another tool call or a final message
        process_agent_response(next_response, agent, user, history, chat_id)

    else:
        # No more tool calls, we have the final response
        logger.info("No tool calls detected. Processing as final response.")
        final_message = str(agent_response_obj)
        if "</thinking>" in final_message:
            final_message = final_message.split("</thinking>")[-1].strip()

        history.history.append(Message(role="assistant", content=final_message))
        HistoryStore().save_history(history)
        logger.info("Agent generated response. Preparing to send to Telegram.")
        send_telegram_message(chat_id, final_message)
        logger.info("Finished sending message to Telegram.")


def handle_text_message(
    message: dict[str, Any], chat_id: str, user: User, history: ConversationHistory
) -> None:
    """Handles an incoming text message."""
    text = message.get("text", "")
    history.history.append(Message(role="user", content=text))

    agent = get_agent(user, history)
    response_obj = agent()

    # Process the agent's response
    process_agent_response(response_obj, agent, user, history, chat_id)


def handle_photo_message(
    message: dict[str, Any], chat_id: str, user: User, history: ConversationHistory
) -> None:
    """Handles photo messages by uploading to S3 and invoking the agent."""
    logger.info("Photo message detected. Uploading to S3 and invoking agent.")
    photo = message["photo"][-1]
    file_id = photo["file_id"]

    file_path = get_telegram_file_path(file_id)
    if not file_path:
        send_telegram_message(
            chat_id,
            "Sorry, I couldn't download the image from Telegram. Please try again.",
        )
        return

    telegram_bot_token = get_secret(settings.telegram_secret_name).get("value")
    file_url = f"https://api.telegram.org/file/bot{telegram_bot_token}/{file_path}"
    response = requests.get(file_url)
    if response.status_code != 200:
        send_telegram_message(
            chat_id, "Sorry, I had trouble downloading the image. Please try again."
        )
        return
    image_bytes = response.content

    bucket_name = settings.uploads_bucket_name
    s3_key = f"uploads/{user.user_id}/{str(uuid.uuid4())}.jpg"
    s3_client.put_object(Bucket=bucket_name, Key=s3_key, Body=image_bytes)
    logger.info(f"Image uploaded to S3: s3://{bucket_name}/{s3_key}")

    # Create a simple, structured prompt instructing the agent to analyze the image.
    # The agent's system prompt will guide it to use the correct tools in sequence.
    args_json = json.dumps(
        {
            "s3_bucket": bucket_name,
            "s3_key": s3_key,
            "user_id": user.user_id,
        }
    )
    agent_prompt = (
        "The user has uploaded an image. Analyze it and take the appropriate next action. "
        f"The image details are: {args_json}"
    )

    logger.info(f"Invoking agent with prompt: {agent_prompt}")

    history.history.append(Message(role="user", content=agent_prompt))

    # Invoke the agent
    agent = get_agent(user, history)
    agent_response_obj = agent()
    logger.info(f"Raw agent response: {agent_response_obj}")

    # Process the agent's response
    process_agent_response(agent_response_obj, agent, user, history, chat_id)


def handler(event: dict[str, Any], _context: Any) -> None:
    """AWS Lambda handler for processing SQS messages."""
    logger.info("--- WORKER LAMBDA INVOCATION ---")
    for record in event["Records"]:
        body = json.loads(record["body"])
        message = body.get("message", {})
        chat = message.get("chat", {})
        from_user = message.get("from", {})  # Extract user info from 'from' field
        chat_id = str(chat.get("id"))

        # --- Find or create user ---
        identities_store = IdentitiesStore()
        users_store = UsersStore()
        user_id = identities_store.find_user_id_by_identity("telegram", chat_id)
        user = None
        if user_id:
            user = users_store.get_user(user_id)

        if user:
            now = datetime.now(UTC).isoformat()
            # Update user info from both chat and from fields (prefer from field for user details)
            user.first_name = from_user.get("first_name") or chat.get("first_name")
            user.last_name = from_user.get("last_name") or chat.get("last_name")
            user.username = from_user.get("username") or chat.get("username")
            # Extract language if available and not already set
            if not user.language and from_user.get("language_code"):
                user.language = from_user.get("language_code")
            user.updated_at = now
            users_store.upsert_user(user)
        else:
            now = datetime.now(UTC).isoformat()
            user = User(
                first_name=from_user.get("first_name") or chat.get("first_name"),
                last_name=from_user.get("last_name") or chat.get("last_name"),
                username=from_user.get("username") or chat.get("username"),
                language=from_user.get("language_code"),  # Set language from Telegram
                created_at=now,
                updated_at=now,
            )
            users_store.upsert_user(user)
            user_id = user.user_id
            identity = Identity(
                pk=f"telegram#{chat_id}",
                provider="telegram",
                provider_user_id=chat_id,
                user_id=user_id,
                created_at=now,
            )
            identities_store.link_identity(identity)

        # --- Session Management ---
        history_store = HistoryStore()
        conversation_history = history_store.get_latest_history(user.user_id)

        if conversation_history:
            last_updated_time = datetime.fromisoformat(
                conversation_history.last_updated
            )
            if datetime.now(UTC) - last_updated_time > timedelta(
                minutes=SESSION_TIMEOUT_MINUTES
            ):
                logger.info("Session timed out. Creating a new session.")
                conversation_history = ConversationHistory(user_id=user.user_id)
            else:
                logger.info("Continuing existing session.")
        else:
            logger.info("No existing session found. Creating a new one.")
            conversation_history = ConversationHistory(user_id=user.user_id)

        # Update timestamp and save immediately to keep session alive
        conversation_history.last_updated = datetime.now(UTC).isoformat()
        history_store.save_history(conversation_history)

        # --- Route to appropriate handler ---
        if "text" in message:
            handle_text_message(message, chat_id, user, conversation_history)
        elif "photo" in message:
            handle_photo_message(message, chat_id, user, conversation_history)
        else:
            logger.info("Received a message that is not text or a photo. Ignoring.")
            send_telegram_message(
                chat_id, "I can only process text messages and photos at the moment."
            )
