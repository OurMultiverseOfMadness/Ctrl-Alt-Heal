from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

import boto3
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse, PlainTextResponse
from pydantic import BaseModel

from ctrl_alt_heal.agent.care_companion import get_agent
from ctrl_alt_heal.domain.models import ConversationHistory, Identity, Message, User
from ctrl_alt_heal.infrastructure.history_store import HistoryStore
from ctrl_alt_heal.infrastructure.identities_store import IdentitiesStore
from ctrl_alt_heal.infrastructure.secrets import get_secret
from ctrl_alt_heal.interface.telegram_sender import (
    get_telegram_file_path,
    send_telegram_message_with_retry,
    validate_telegram_chat_id,
)
from ctrl_alt_heal.infrastructure.users_store import UsersStore
from ctrl_alt_heal.utils.session_utils import (
    should_create_new_session,
    create_new_session,
    update_session_timestamp,
    get_session_status,
)
from ctrl_alt_heal.utils.constants import SESSION_TIMEOUT_MINUTES
from datetime import UTC, datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Ctrl-Alt-Heal Fargate API",
    description="Healthcare AI Agent running on Fargate",
    version="1.0.0",
)

# Initialize AWS clients
s3_client = boto3.client("s3")


# Pydantic models for API
class TelegramWebhook(BaseModel):
    update_id: int
    message: dict[str, Any] | None = None


class HealthCheck(BaseModel):
    status: str = "healthy"
    timestamp: str = datetime.now(UTC).isoformat()


@app.get("/health")
async def health_check() -> HealthCheck:
    """Health check endpoint for Fargate."""
    return HealthCheck()


@app.post("/webhook")
async def telegram_webhook(webhook: TelegramWebhook) -> JSONResponse:
    """Handle Telegram webhook messages."""
    try:
        if not webhook.message:
            return JSONResponse(content={"status": "no message"}, status_code=200)

        message = webhook.message
        chat = message.get("chat", {})
        chat_id = str(chat.get("id"))

        # Validate chat ID
        if not validate_telegram_chat_id(chat_id):
            logger.warning(f"Invalid chat ID: {chat_id}")
            return JSONResponse(content={"status": "invalid chat"}, status_code=400)

        # Process message asynchronously
        asyncio.create_task(process_message(message, chat_id))

        return JSONResponse(content={"status": "ok"}, status_code=200)

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return JSONResponse(content={"status": "error"}, status_code=500)


@app.post("/chat")
async def chat_endpoint(request: dict) -> PlainTextResponse:
    """Direct chat endpoint for testing and API access."""
    try:
        prompt = request.get("prompt", "")
        if not prompt:
            raise HTTPException(status_code=400, detail="No prompt provided")

        # Create a mock user for testing
        mock_user = User(
            user_id="test-user",
            first_name="Test",
            last_name="User",
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        # Create empty history
        history = ConversationHistory(user_id="test-user", history=[])

        # Get agent and process
        agent = get_agent(mock_user, history)
        response = agent(prompt)

        return PlainTextResponse(content=str(response))

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat-streaming")
async def chat_streaming_endpoint(request: dict) -> StreamingResponse:
    """Streaming chat endpoint for real-time responses."""
    try:
        prompt = request.get("prompt", "")
        if not prompt:
            raise HTTPException(status_code=400, detail="No prompt provided")

        # Create a mock user for testing
        mock_user = User(
            user_id="test-user",
            first_name="Test",
            last_name="User",
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        # Create empty history
        history = ConversationHistory(user_id="test-user", history=[])

        async def generate_response():
            agent = get_agent(mock_user, history)
            async for item in agent.stream_async(prompt):
                if "data" in item:
                    yield item["data"]

        return StreamingResponse(generate_response(), media_type="text/plain")

    except Exception as e:
        logger.error(f"Error in streaming chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_message(message: dict[str, Any], chat_id: str) -> None:
    """Process a Telegram message asynchronously."""
    try:
        # Extract user information from message
        from_user = message.get("from", {})

        # Find or create user
        identities_store = IdentitiesStore()
        users_store = UsersStore()
        user_id = identities_store.find_user_id_by_identity("telegram", chat_id)

        if user_id:
            user = users_store.get_user(user_id)
            if user:
                now = datetime.now(UTC).isoformat()
                user.first_name = from_user.get("first_name")
                user.last_name = from_user.get("last_name")
                user.username = from_user.get("username")
                user.updated_at = now
                users_store.upsert_user(user)
        else:
            now = datetime.now(UTC).isoformat()
            new_user = User(
                first_name=from_user.get("first_name"),
                last_name=from_user.get("last_name"),
                username=from_user.get("username"),
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
            user = new_user

        # Get conversation history and manage session
        history_store = HistoryStore()
        conversation_history = history_store.get_latest_history(user_id)

        # Debug: Log what we're loading
        if conversation_history:
            logger.info(
                f"Loaded history with {len(conversation_history.history)} messages"
            )
            for i, msg in enumerate(
                conversation_history.history[-3:]
            ):  # Show last 3 messages
                logger.info(f"  Loaded message {i}: {msg.role} - {msg.content[:50]}...")
        else:
            logger.info("No existing history found")

        # Check if we should create a new session based on inactivity
        should_create, reason = should_create_new_session(
            conversation_history, SESSION_TIMEOUT_MINUTES
        )

        if should_create:
            logger.info(f"Creating new session: {reason}")
            conversation_history = create_new_session(user_id)
        else:
            logger.info(
                "Continuing existing session - updating timestamp to keep it active"
            )
            if conversation_history is not None:
                conversation_history = update_session_timestamp(conversation_history)
            else:
                # If no history exists, create a new session
                logger.info("No existing history found, creating new session")
                conversation_history = create_new_session(user_id)

        # Save the session immediately to persist the changes
        history_store.save_history(conversation_history)

        # Log session status for debugging
        session_status = get_session_status(conversation_history)
        logger.info(f"Session status: {session_status['reason']}")

        # Ensure user exists before proceeding
        if not user:
            logger.error("Failed to create or retrieve user")
            send_telegram_message_with_retry(
                chat_id,
                "Sorry, I encountered an error setting up your profile. Please try again.",
            )
            return

        # Route to appropriate handler
        if "text" in message:
            await handle_text_message(message, chat_id, user, conversation_history)
        elif "photo" in message:
            await handle_photo_message(message, chat_id, user, conversation_history)
        else:
            logger.info("Received a message that is not text or a photo. Ignoring.")
            send_telegram_message_with_retry(
                chat_id, "I can only process text messages and photos at the moment."
            )

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        send_telegram_message_with_retry(
            chat_id,
            "Sorry, I encountered an error processing your message. Please try again.",
        )


async def handle_text_message(
    message: dict[str, Any], chat_id: str, user: User, history: ConversationHistory
) -> None:
    """Handle text messages."""
    text = message.get("text", "")
    history.history.append(Message(role="user", content=text))

    # Update session timestamp
    history = update_session_timestamp(history)

    # Set chat_id for file sending tools
    from ctrl_alt_heal.agent.care_companion import (
        set_chat_id_for_file_sending,
    )

    set_chat_id_for_file_sending(chat_id)

    # Get agent and process
    agent = get_agent(user, history)

    # Debug: Log the history being passed to the agent
    logger.info(f"History being passed to agent: {len(history.history)} messages")
    for i, msg in enumerate(history.history[-5:]):  # Show last 5 messages
        logger.info(f"  Message {i}: {msg.role} - {msg.content[:100]}...")

    response_obj = agent(text)

    # Process response
    await process_agent_response(response_obj, agent, user, history, chat_id)


async def handle_photo_message(
    message: dict[str, Any], chat_id: str, user: User, history: ConversationHistory
) -> None:
    """Handle photo messages."""
    logger.info("Photo message detected. Starting image processing workflow.")
    uploads_bucket = os.environ.get("UPLOADS_BUCKET_NAME")
    if not uploads_bucket:
        logger.error("UPLOADS_BUCKET_NAME environment variable not found.")
        send_telegram_message_with_retry(
            chat_id, "Sorry, there was a configuration error. Please try again later."
        )
        return

    # Get the file_id of the largest photo
    photo_array = message.get("photo", [])
    if not photo_array:
        logger.warning("Photo message received but no photo array found.")
        return
    file_id = photo_array[-1]["file_id"]

    # Get the file path from Telegram
    file_path = get_telegram_file_path(file_id)
    if not file_path:
        send_telegram_message_with_retry(
            chat_id, "Sorry, I couldn't download the image you sent. Please try again."
        )
        return

    # Download the image
    telegram_secret_name = os.environ.get("TELEGRAM_SECRET_NAME")
    if not telegram_secret_name:
        logger.error("TELEGRAM_SECRET_NAME environment variable not found.")
        send_telegram_message_with_retry(
            chat_id, "Sorry, there was a configuration error. Please try again later."
        )
        return
    secret_value = get_secret(telegram_secret_name)
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
        send_telegram_message_with_retry(
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
        send_telegram_message_with_retry(
            chat_id,
            "I'm having trouble saving your image right now. Please try again in a few minutes.",
        )
        return

    # Call the prescription extraction tool
    send_telegram_message_with_retry(
        chat_id,
        "Thanks! I've received your image. I'll start analyzing it for prescription details now. This might take a moment.",
    )

    # Import and call prescription extraction tool
    from ctrl_alt_heal.tools.prescription_extraction_tool import (
        prescription_extraction_tool,
    )

    extraction_result = prescription_extraction_tool(
        user_id=user.user_id,
        s3_bucket=uploads_bucket,
        s3_key=s3_key,
    )

    # Re-engage the agent with the results
    # Debug: Log the history being passed to the agent for image processing
    logger.info(
        f"(Image processing) History being passed to agent: {len(history.history)} messages"
    )
    for i, msg in enumerate(history.history[-5:]):  # Show last 5 messages
        logger.info(
            f"  (Image processing) Message {i}: {msg.role} - {msg.content[:100]}..."
        )

    # Set chat_id for file sending tools
    from ctrl_alt_heal.agent.care_companion import (
        set_chat_id_for_file_sending,
    )

    set_chat_id_for_file_sending(chat_id)

    agent = get_agent(user, history)

    if extraction_result.get("status") == "success":
        med_names = [
            p.get("name", "Unknown") for p in extraction_result.get("prescriptions", [])
        ]
        system_prompt = (
            f"The user just uploaded an image of a prescription. "
            f"I successfully extracted and saved the following new medications to their profile: {', '.join(med_names)}. "
            "Now, I need to confirm this with the user and ask a helpful follow-up question, like what they want to do next (e.g., set a reminder, learn about the medication)."
        )
    else:
        system_prompt = (
            "The user just uploaded an image of a prescription, but I couldn't seem to read any details from it. "
            "I should apologize for the trouble, let them know I couldn't read the image, and suggest they could try again with a clearer picture or just tell me the prescription details directly."
        )

    # Let the agent generate the final response
    agent_response_obj = agent(system_prompt)
    await process_agent_response(agent_response_obj, agent, user, history, chat_id)


async def process_agent_response(
    agent_response_obj: Any,
    agent: Any,
    user: User,
    history: ConversationHistory,
    chat_id: str,
) -> None:
    """Process the agent's response."""
    try:
        if isinstance(agent_response_obj, dict) and "tool_calls" in agent_response_obj:
            # Handle tool calls
            tool_calls = agent_response_obj["tool_calls"]
            tool_results = []

            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_call_id = tool_call["tool_call_id"]

                # Add user_id if missing
                if "user_id" not in tool_args:
                    tool_args["user_id"] = user.user_id

                # Set chat_id for file sending tools
                from ctrl_alt_heal.agent.care_companion import (
                    set_chat_id_for_file_sending,
                )

                set_chat_id_for_file_sending(chat_id)

                # Execute the actual tool
                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

                # Import and execute the specific tool
                tool_result: Any = None
                try:
                    if tool_name == "prescription_extraction_tool":
                        from ctrl_alt_heal.tools.prescription_extraction_tool import (
                            prescription_extraction_tool,
                        )

                        tool_result = prescription_extraction_tool(**tool_args)
                    elif tool_name == "search_tool":
                        from ctrl_alt_heal.tools.search_tool import search_tool

                        tool_result = search_tool(**tool_args)
                    elif tool_name == "fhir_data_tool":
                        from ctrl_alt_heal.tools.fhir_data_tool import fhir_data_tool

                        tool_result = fhir_data_tool(**tool_args)
                    elif tool_name == "calendar_ics_tool":
                        from ctrl_alt_heal.tools.calendar_tool import calendar_ics_tool

                        tool_result = calendar_ics_tool(**tool_args)
                    elif tool_name == "describe_image_tool":
                        from ctrl_alt_heal.tools.image_description_tool import (
                            describe_image_tool,
                        )

                        tool_result = describe_image_tool(**tool_args)
                    elif tool_name == "get_user_profile_tool":
                        from ctrl_alt_heal.tools.user_profile_tool import (
                            get_user_profile_tool,
                        )

                        tool_result = get_user_profile_tool(**tool_args)
                    elif tool_name == "update_user_profile_tool":
                        from ctrl_alt_heal.tools.user_profile_tool import (
                            update_user_profile_tool,
                        )

                        tool_result = update_user_profile_tool(**tool_args)
                    elif tool_name == "save_user_notes_tool":
                        from ctrl_alt_heal.tools.user_profile_tool import (
                            save_user_notes_tool,
                        )

                        tool_result = save_user_notes_tool(**tool_args)
                    elif tool_name == "find_user_by_identity_tool":
                        from ctrl_alt_heal.tools.identity_tool import (
                            find_user_by_identity_tool,
                        )

                        tool_result = find_user_by_identity_tool(**tool_args)
                    elif tool_name == "create_user_with_identity_tool":
                        from ctrl_alt_heal.tools.identity_tool import (
                            create_user_with_identity_tool,
                        )

                        tool_result = create_user_with_identity_tool(**tool_args)
                    elif tool_name == "get_or_create_user_tool":
                        from ctrl_alt_heal.tools.identity_tool import (
                            get_or_create_user_tool,
                        )

                        tool_result = get_or_create_user_tool(**tool_args)
                    elif tool_name == "detect_user_timezone_tool":
                        from ctrl_alt_heal.tools.timezone_tool import (
                            detect_user_timezone_tool,
                        )

                        tool_result = detect_user_timezone_tool(**tool_args)
                    elif tool_name == "suggest_timezone_from_language_tool":
                        from ctrl_alt_heal.tools.timezone_tool import (
                            suggest_timezone_from_language_tool,
                        )

                        tool_result = suggest_timezone_from_language_tool(**tool_args)
                    elif tool_name == "auto_detect_timezone_tool":
                        from ctrl_alt_heal.tools.timezone_tool import (
                            auto_detect_timezone_tool,
                        )

                        tool_result = auto_detect_timezone_tool(**tool_args)
                    elif tool_name == "auto_schedule_medication_tool":
                        from ctrl_alt_heal.tools.medication_schedule_tool import (
                            auto_schedule_medication_tool,
                        )

                        tool_result = auto_schedule_medication_tool(**tool_args)
                    elif tool_name == "set_medication_schedule_tool":
                        from ctrl_alt_heal.tools.medication_schedule_tool import (
                            set_medication_schedule_tool,
                        )

                        tool_result = set_medication_schedule_tool(**tool_args)
                    elif tool_name == "get_medication_schedule_tool":
                        from ctrl_alt_heal.tools.medication_schedule_tool import (
                            get_medication_schedule_tool,
                        )

                        tool_result = get_medication_schedule_tool(**tool_args)
                    elif tool_name == "clear_medication_schedule_tool":
                        from ctrl_alt_heal.tools.medication_schedule_tool import (
                            clear_medication_schedule_tool,
                        )

                        tool_result = clear_medication_schedule_tool(**tool_args)
                    elif tool_name == "get_user_prescriptions_tool":
                        from ctrl_alt_heal.tools.medication_schedule_tool import (
                            get_user_prescriptions_tool,
                        )

                        tool_result = get_user_prescriptions_tool(**tool_args)
                    elif tool_name == "show_all_medications_tool":
                        from ctrl_alt_heal.tools.medication_schedule_tool import (
                            show_all_medications_tool,
                        )

                        tool_result = show_all_medications_tool(**tool_args)
                    elif tool_name == "generate_medication_ics":
                        from ctrl_alt_heal.agent.care_companion import (
                            wrapped_generate_medication_ics_tool,
                        )

                        tool_result = wrapped_generate_medication_ics_tool(**tool_args)
                    elif tool_name == "generate_single_medication_ics":
                        from ctrl_alt_heal.agent.care_companion import (
                            wrapped_generate_single_medication_ics_tool,
                        )

                        tool_result = wrapped_generate_single_medication_ics_tool(
                            **tool_args
                        )
                    else:
                        logger.warning(f"Unknown tool: {tool_name}")
                        tool_result = {
                            "status": "error",
                            "message": f"Unknown tool: {tool_name}",
                        }

                    logger.info(
                        f"Tool {tool_name} executed successfully: {tool_result}"
                    )

                except Exception as tool_error:
                    logger.error(f"Error executing tool {tool_name}: {tool_error}")
                    tool_result = {"status": "error", "message": str(tool_error)}

                tool_results.append(
                    {"tool_result_id": tool_call_id, "content": json.dumps(tool_result)}
                )

            # Continue processing with tool results
            next_response = agent(tool_results=tool_results)
            await process_agent_response(next_response, agent, user, history, chat_id)

        else:
            # Handle final message
            response_str = str(agent_response_obj)
            logger.info("=== AGENT RESPONSE DEBUG ===")
            logger.info(f"Raw agent response: {response_str}")
            logger.info(f"Response type: {type(agent_response_obj)}")
            logger.info(f"Contains <br> tags: {'<br>' in response_str}")
            logger.info(f"Contains </thinking>: {'</thinking>' in response_str}")
            logger.info(f"Response length: {len(response_str)}")

            # Extract the actual message content from the agent response
            if "</thinking>" in response_str:
                # Split by </thinking> and take everything after it
                parts = response_str.split("</thinking>")
                if len(parts) > 1:
                    final_message = parts[-1].strip()
                    logger.info(
                        f"Extracted message after </thinking>: '{final_message}'"
                    )
                else:
                    final_message = response_str
                    logger.info("No content after </thinking>, using full response")
            else:
                final_message = response_str
                logger.info("No </thinking> tag found, using full response")

            # If the message is empty or only contains thinking, generate a fallback
            if not final_message or final_message.isspace():
                logger.warning("Agent response is empty, generating fallback message")
                final_message = (
                    "I'm processing your request. Please give me a moment to respond."
                )
            elif final_message.startswith("<thinking>") and final_message.endswith(
                "</thinking>"
            ):
                logger.warning(
                    "Agent response only contains thinking, generating fallback message"
                )
                final_message = (
                    "I'm processing your request. Please give me a moment to respond."
                )

            logger.info(f"Final message before formatting: {final_message}")
            logger.info("=== END AGENT RESPONSE DEBUG ===")

            # Clean HTML entities from the agent response (temporary fix)
            import html

            final_message = html.unescape(final_message)
            logger.info(f"After HTML unescaping: {final_message}")

            # Try different Telegram parse modes to handle formatting issues
            from ctrl_alt_heal.utils.telegram_formatter import (
                TelegramFormatter,
                TelegramParseMode,
            )
            import re

            logger.info("=== TELEGRAM FORMATTING DEBUG ===")
            logger.info(f"Original message: {final_message}")

            # Try different parse modes in order of preference
            parse_modes_to_try = [
                TelegramParseMode.HTML,  # Most forgiving - handles bullet points well
                TelegramParseMode.PLAIN_TEXT,  # Fallback - no formatting
            ]

            success = False
            selected_parse_mode = TelegramParseMode.PLAIN_TEXT  # Default fallback

            for parse_mode in parse_modes_to_try:
                try:
                    logger.info(f"Trying parse mode: {parse_mode.value}")
                    formatter = TelegramFormatter(parse_mode)

                    if parse_mode == TelegramParseMode.PLAIN_TEXT:
                        # For plain text, clean all formatting
                        cleaned_message = formatter.clean_formatting(final_message)
                        # Replace <br> with newlines
                        cleaned_message = re.sub(
                            r"<br\s*/?>", "\n", cleaned_message, flags=re.IGNORECASE
                        )
                        # Remove any remaining HTML tags
                        cleaned_message = re.sub(r"<[^>]+>", "", cleaned_message)
                        final_message = cleaned_message
                    else:
                        # For HTML mode, format properly
                        # First replace <br> tags with newlines
                        if "<br>" in final_message:
                            final_message = re.sub(
                                r"<br\s*/?>", "\n", final_message, flags=re.IGNORECASE
                            )

                        # Convert bullet points from - to • for better HTML compatibility
                        final_message = re.sub(
                            r"^\- ", "• ", final_message, flags=re.MULTILINE
                        )
                        final_message = re.sub(r"\n\- ", "\n• ", final_message)

                        final_message = formatter._apply_formatting(final_message)

                    logger.info(f"Formatted with {parse_mode.value}: {final_message}")
                    selected_parse_mode = parse_mode
                    success = True
                    break

                except Exception as e:
                    logger.warning(f"Failed with {parse_mode.value}: {e}")
                    continue

            if not success:
                logger.warning("All parse modes failed, using plain text fallback")
                # Ultimate fallback - strip all formatting
                final_message = re.sub(r"<[^>]+>", "", final_message)
                final_message = re.sub(
                    r"\*\*(.*?)\*\*", r"\1", final_message
                )  # Remove bold
                final_message = re.sub(
                    r"\*(.*?)\*", r"\1", final_message
                )  # Remove italic
                final_message = re.sub(r"`(.*?)`", r"\1", final_message)  # Remove code
                final_message = re.sub(
                    r"\[([^\]]+)\]\([^)]+\)", r"\1", final_message
                )  # Remove links

            logger.info(f"Final message to send: {final_message}")
            logger.info(f"Selected parse mode: {selected_parse_mode.value}")
            logger.info("=== END TELEGRAM FORMATTING DEBUG ===")

            history.history.append(Message(role="assistant", content=final_message))
            history_store = HistoryStore()
            history_store.save_history(history)

            # Debug: Log what we're saving
            logger.info(f"Saving history with {len(history.history)} messages")
            for i, msg in enumerate(history.history[-3:]):  # Show last 3 messages
                logger.info(f"  Saved message {i}: {msg.role} - {msg.content[:50]}...")

            logger.info("Agent generated response. Preparing to send to Telegram.")
            # Use the selected parse mode (HTML preferred, with plain text fallback)
            send_telegram_message_with_retry(
                chat_id, final_message, parse_mode=selected_parse_mode
            )
            logger.info("Finished sending message to Telegram.")

    except Exception as e:
        logger.error(f"Error processing agent response: {e}")
        send_telegram_message_with_retry(
            chat_id,
            "Sorry, I encountered an error processing your request. Please try again.",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
