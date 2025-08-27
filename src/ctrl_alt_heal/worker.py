import json
import os
from typing import Any

import boto3
import requests
from ctrl_alt_heal.agent.care_companion import get_agent
from ctrl_alt_heal.domain.models import Identity, Message, User
from ctrl_alt_heal.infrastructure.history_store import HistoryStore
from ctrl_alt_heal.infrastructure.identities_store import IdentitiesStore
from ctrl_alt_heal.infrastructure.secrets import get_secret
from ctrl_alt_heal.interface.telegram_sender import (
    get_telegram_file_path,
    send_telegram_message,
)
from ctrl_alt_heal.infrastructure.users_store import UsersStore
from ctrl_alt_heal.tools.registry import tool_registry
from datetime import UTC, datetime
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")


def handle_text_message(message: dict[str, Any], chat_id: str, user: User) -> None:
    """Handles an incoming text message."""
    text = message.get("text", "")
    history_store = HistoryStore()
    conversation_history = history_store.get_history(user.user_id)

    agent = get_agent(user, conversation_history)
    response_obj = agent(text)
    response_str = str(response_obj)

    conversation_history.history.append(Message(role="user", content=text))

    if isinstance(response_obj, dict) and "tool_calls" in response_obj:
        for tool_call in response_obj["tool_calls"]:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            if "user_id" not in tool_args:
                tool_args["user_id"] = user.user_id
            tool_function = tool_registry.get(tool_name)
            if tool_function:
                tool_function(**tool_args)
            else:
                logger.warning(f"Tool '{tool_name}' not found in registry.")
        history_store.save_history(conversation_history)
    else:
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


def handle_photo_message(message: dict[str, Any], chat_id: str, user: User) -> None:
    """Handles an incoming photo message."""
    logger.info("Photo message detected. Starting image processing workflow.")
    uploads_bucket = os.environ["UPLOADS_BUCKET_NAME"]

    # Get the file_id of the largest photo
    photo_array = message.get("photo", [])
    if not photo_array:
        logger.warning("Photo message received but no photo array found.")
        return
    file_id = photo_array[-1]["file_id"]

    # Get the file path from Telegram
    file_path = get_telegram_file_path(file_id)
    if not file_path:
        send_telegram_message(
            chat_id, "Sorry, I couldn't download the image you sent. Please try again."
        )
        return

    # Download the image
    secret_value = get_secret(os.environ["TELEGRAM_SECRET_NAME"])
    token = secret_value.get("bot_token") or secret_value.get("value")
    download_url = f"https://api.telegram.org/file/bot{token}/{file_path}"

    try:
        logger.info("Downloading image from Telegram.")
        response = requests.get(download_url, timeout=30)
        response.raise_for_status()
        image_bytes = response.content
        logger.info("Image downloaded successfully.")
    except requests.RequestException as e:
        logger.error("Failed to download image from Telegram: %s", e)
        send_telegram_message(
            chat_id,
            "Sorry, I ran into an error trying to download your image. Please try again.",
        )
        return

    # Upload to S3
    s3_key = f"uploads/{user.user_id}/{file_id}.jpg"
    try:
        logger.info("Uploading image to S3 bucket: %s, key: %s", uploads_bucket, s3_key)
        s3_client.put_object(Bucket=uploads_bucket, Key=s3_key, Body=image_bytes)
        logger.info("Image uploaded to S3 successfully.")
    except Exception as e:
        logger.error("Failed to upload image to S3: %s", e)
        send_telegram_message(
            chat_id,
            "I'm having trouble saving your image right now. Please try again in a few minutes.",
        )
        return

    # Call the prescription extraction tool
    send_telegram_message(
        chat_id,
        "Thanks! I've received your image. I'll start analyzing it for prescription details now. This might take a moment.",
    )

    tool_function = tool_registry.get("prescription_extraction")
    if tool_function:
        extraction_result = tool_function(
            user_id=user.user_id,
            s3_bucket=uploads_bucket,
            s3_key=s3_key,
        )

        # Re-engage the agent with the results
        history_store = HistoryStore()
        conversation_history = history_store.get_history(user.user_id)
        agent = get_agent(user, conversation_history)

        if extraction_result.get("status") == "success":
            med_names = [
                p.get("name", "Unknown")
                for p in extraction_result.get("prescriptions", [])
            ]
            # This prompt is carefully worded to sound like the agent's own internal thought process.
            system_prompt = (
                f"The user just uploaded an image of a prescription. "
                f"I successfully extracted and saved the following new medications to their profile: {', '.join(med_names)}. "
                "Now, I need to confirm this with the user and ask a helpful follow-up question, like what they want to do next (e.g., set a reminder, learn about the medication)."
            )
        else:
            # This prompt frames the failure as a simple issue, not a persistent error.
            system_prompt = (
                "The user just uploaded an image of a prescription, but I couldn't seem to read any details from it. "
                "I should apologize for the trouble, let them know I couldn't read the image, and suggest they could try again with a clearer picture or just tell me the prescription details directly."
            )

        # Let the agent generate the final response
        agent_response_obj = agent(system_prompt)
        agent_response_str = str(agent_response_obj)
        if "</thinking>" in agent_response_str:
            final_message = agent_response_str.split("</thinking>")[-1].strip()
        else:
            final_message = agent_response_str

        send_telegram_message(chat_id, final_message)

    else:
        logger.error("Prescription extraction tool not found in registry.")
        send_telegram_message(
            chat_id,
            "Sorry, I can't analyze the prescription image right now because my tools are being updated.",
        )


def handler(event: dict[str, Any], _context: Any) -> None:
    """AWS Lambda handler for processing SQS messages."""
    logger.info("--- WORKER LAMBDA INVOCATION ---")
    for record in event["Records"]:
        body = json.loads(record["body"])
        message = body.get("message", {})
        chat = message.get("chat", {})
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
            user.first_name = chat.get("first_name")
            user.last_name = chat.get("last_name")
            user.username = chat.get("username")
            user.updated_at = now
            users_store.upsert_user(user)
        else:
            now = datetime.now(UTC).isoformat()
            user = User(
                first_name=chat.get("first_name"),
                last_name=chat.get("last_name"),
                username=chat.get("username"),
                created_at=now,
                updated_at=now,
            )
            users_store.upsert_user(user)
            user_id = user.user_id
            identity = Identity(
                provider="telegram",
                provider_user_id=chat_id,
                user_id=user_id,
                created_at=now,
            )
            identities_store.link_identity(identity)

        # --- Route to appropriate handler ---
        if "text" in message:
            handle_text_message(message, chat_id, user)
        elif "photo" in message:
            handle_photo_message(message, chat_id, user)
        else:
            logger.info("Received a message that is not text or a photo. Ignoring.")
            send_telegram_message(
                chat_id, "I can only process text messages and photos at the moment."
            )
