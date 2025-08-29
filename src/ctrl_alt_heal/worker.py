import json
from typing import Any

import boto3
import requests
from ctrl_alt_heal.agent.care_companion import get_agent, set_chat_id_for_file_sending
from ctrl_alt_heal.tools.medication_ics_tool import (
    set_chat_id_for_file_sending as set_ics_chat_id,
)
from ctrl_alt_heal.domain.models import ConversationHistory, Identity, Message, User
from ctrl_alt_heal.infrastructure.history_store import HistoryStore
from ctrl_alt_heal.infrastructure.identities_store import IdentitiesStore
from ctrl_alt_heal.infrastructure.secrets import get_secret
from ctrl_alt_heal.interface.telegram_sender import (
    get_telegram_file_path,
    send_telegram_message,
    send_telegram_file,
)
from ctrl_alt_heal.infrastructure.users_store import UsersStore
from ctrl_alt_heal.tools.registry import tool_registry
from datetime import UTC, datetime
import logging
import uuid
from strands import Agent
from ctrl_alt_heal.config import settings
from ctrl_alt_heal.utils.session_utils import (
    should_create_new_session,
    create_new_session,
    update_session_timestamp,
    get_session_status,
)
from ctrl_alt_heal.utils.constants import SESSION_TIMEOUT_MINUTES

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")


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
    if isinstance(agent_response_obj, dict) and "tool_calls" in agent_response_obj:
        tool_calls = agent_response_obj["tool_calls"]
        tool_results = []
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["tool_call_id"]

            # The agent sometimes forgets the user_id, so we add it back in
            if "user_id" not in tool_args:
                tool_args["user_id"] = user.user_id

            # Get the tool function from the registry
            tool_function = tool_registry.get(tool_name)

            if tool_function:
                try:
                    # Execute the tool
                    result = tool_function(**tool_args)

                    # Log medication scheduling errors
                    if tool_name == "set_medication_schedule":
                        if isinstance(result, dict) and result.get("status") == "error":
                            logger.warning(
                                f"set_medication_schedule failed: {result.get('message')}"
                            )
                            if result.get("needs_timezone"):
                                logger.warning("Tool indicates user needs timezone set")
                    # Format the result for the agent
                    # For prescription extraction, provide a more natural response format
                    if tool_name == "prescription_extraction" and isinstance(
                        result, dict
                    ):
                        if result.get("status") == "success":
                            # Format success response more naturally
                            content = f"SUCCESS: {result.get('message', 'Prescription extracted successfully')}. "
                            if result.get("prescriptions"):
                                content += (
                                    f"Found {result.get('count', 0)} medication(s): "
                                )
                                for i, med in enumerate(result["prescriptions"], 1):
                                    content += f"{i}. {med.get('name', 'Unknown')} - {med.get('dosage', 'Not specified')}, {med.get('frequency', 'Not specified')}. "

                            tool_results.append(
                                {"tool_result_id": tool_call_id, "content": content}
                            )
                        else:
                            # Format error response
                            content = f"ERROR: {result.get('message', 'Failed to extract prescription')}"

                            tool_results.append(
                                {"tool_result_id": tool_call_id, "content": content}
                            )
                    # Handle medication schedule creation with automatic ICS generation
                    elif tool_name in [
                        "set_medication_schedule",
                        "auto_schedule_medication",
                    ] and isinstance(result, dict):
                        if result.get("status") == "success" and result.get(
                            "ics_content"
                        ):
                            # Send the automatically generated ICS file to the user
                            ics_content = result["ics_content"]
                            filename = result.get(
                                "ics_filename",
                                f"medication_reminders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics",
                            )
                            caption = result.get(
                                "ics_caption",
                                "Here's your medication reminder calendar file!",
                            )

                            send_telegram_file(chat_id, ics_content, filename, caption)

                            # Format success response for the agent
                            content = f"SUCCESS: {result.get('message', 'Medication schedule created successfully')}. ICS file automatically sent to user."
                            tool_results.append(
                                {"tool_result_id": tool_call_id, "content": content}
                            )
                        else:
                            # Schedule created but no ICS file (fallback case)
                            content = f"SUCCESS: {result.get('message', 'Medication schedule created successfully')}"
                            tool_results.append(
                                {"tool_result_id": tool_call_id, "content": content}
                            )
                    # Handle ICS file generation
                    elif tool_name in [
                        "generate_medication_ics",
                        "generate_single_medication_ics",
                    ] and isinstance(result, dict):
                        if result.get("status") == "success" and result.get(
                            "ics_content"
                        ):
                            # Send the ICS file to the user
                            ics_content = result["ics_content"]
                            filename = f"medication_reminders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
                            caption = result.get(
                                "message",
                                "Here's your medication reminder calendar file!",
                            )

                            send_telegram_file(chat_id, ics_content, filename, caption)

                            # Format success response for the agent
                            content = f"SUCCESS: {result.get('message', 'ICS file generated successfully')}. File sent to user."
                            tool_results.append(
                                {"tool_result_id": tool_call_id, "content": content}
                            )
                        else:
                            # Format error response
                            content = f"ERROR: {result.get('message', 'Failed to generate ICS file')}"
                            tool_results.append(
                                {"tool_result_id": tool_call_id, "content": content}
                            )
                    else:
                        # Default JSON formatting for other tools
                        tool_results.append(
                            {
                                "tool_result_id": tool_call_id,
                                "content": json.dumps(result),
                            }
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

        # Emergency: Check for infinite loop
        if len(tool_results) > 10:
            logger.error(
                f"EMERGENCY: Too many tool calls detected ({len(tool_results)}). Stopping to prevent infinite loop."
            )
            final_message = "I apologize, but I'm experiencing technical difficulties. Please try again in a moment."
            history.history.append(Message(role="assistant", content=final_message))
            HistoryStore().save_history(history)
            send_telegram_message(chat_id, final_message)
            return

        next_response = agent(tool_results=tool_results)
        # Process the next response, which could be another tool call or a final message
        process_agent_response(next_response, agent, user, history, chat_id)

    else:
        # No more tool calls, we have the final response
        final_message = str(agent_response_obj)

        # Debug: Check if agent promised to create reminders but didn't call tools
        response_lower = final_message.lower()
        if any(
            phrase in response_lower
            for phrase in [
                "i'll create",
                "creating",
                "i'll set up",
                "setting up",
                "i'll schedule",
                "scheduling",
                "i'll make",
            ]
        ) and any(
            med_phrase in response_lower
            for med_phrase in ["reminder", "medication", "schedule", "remind"]
        ):
            logger.warning(
                f"Agent promised to create medication reminders but didn't call set_medication_schedule tool. Response: {final_message}"
            )
            logger.warning(
                "This suggests the agent is not following the system prompt instructions to use tools for medication scheduling."
            )

        # Fallback: If agent describes creating calendar files but didn't call tools, call the tool automatically
        if (
            any(
                phrase in response_lower
                for phrase in [
                    "i've created a calendar file",
                    "created a calendar file",
                    "calendar file with reminders",
                    "calendar files and import them",
                ]
            )
            and "generate_medication_ics" not in response_lower
        ):
            logger.warning(
                "Agent described creating calendar files but didn't call generate_medication_ics tool. Calling it automatically."
            )

            try:
                # Import the tool and call it directly
                from ctrl_alt_heal.tools.medication_ics_tool import (
                    generate_medication_ics_tool,
                )

                result = generate_medication_ics_tool(
                    user_id=user.user_id,
                    prescription_name=None,  # Generate for all medications
                    reminder_minutes=15,
                    include_notes=True,
                )

                if result.get("status") == "success":
                    # The tool will automatically send the file via Telegram
                    pass
                else:
                    logger.error(
                        f"Fallback ICS generation failed: {result.get('message')}"
                    )

            except Exception as e:
                logger.error(f"Error in fallback ICS generation: {e}")

        # Clean up XML-like tags from the response
        if "</thinking>" in final_message:
            final_message = final_message.split("</thinking>")[-1].strip()

        # Remove <response> tags if present
        if "<response>" in final_message and "</response>" in final_message:
            final_message = (
                final_message.replace("<response>", "")
                .replace("</response>", "")
                .strip()
            )

        # Remove any other XML-like tags that might be present
        import re

        # More comprehensive cleaning of thinking tags and other unwanted content
        final_message = re.sub(
            r"<thinking>.*?</thinking>", "", final_message, flags=re.DOTALL
        )
        final_message = re.sub(r"<thinking>.*", "", final_message, flags=re.DOTALL)
        final_message = re.sub(r"<[^>]+>", "", final_message).strip()

        # Clean up any extra whitespace and empty lines
        final_message = re.sub(r"\n\s*\n\s*\n", "\n\n", final_message)
        final_message = final_message.strip()

        # If the message is empty after cleaning, provide a default response
        if not final_message:
            final_message = "I apologize, but I couldn't generate a proper response. Please try asking your question again."

        history.history.append(Message(role="assistant", content=final_message))
        # Update session timestamp to keep it active
        history = update_session_timestamp(history)
        HistoryStore().save_history(history)
        send_telegram_message(chat_id, final_message)


def handle_text_message(
    message: dict[str, Any], chat_id: str, user: User, history: ConversationHistory
) -> None:
    """Handles an incoming text message."""
    text = message.get("text", "")
    history.history.append(Message(role="user", content=text))
    # Update session timestamp to keep it active
    history = update_session_timestamp(history)

    # Set chat ID for automatic file sending in tool wrappers
    set_chat_id_for_file_sending(chat_id)
    set_ics_chat_id(chat_id)

    agent = get_agent(user, history)

    # Use agent() to execute tools directly
    response_obj = agent()

    # Process the agent's response
    process_agent_response(response_obj, agent, user, history, chat_id)


def handle_photo_message(
    message: dict[str, Any], chat_id: str, user: User, history: ConversationHistory
) -> None:
    """Handles photo messages by uploading to S3 and invoking the agent."""

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

    history.history.append(Message(role="user", content=agent_prompt))
    # Update session timestamp to keep it active
    history = update_session_timestamp(history)

    # Set chat ID for automatic file sending in tool wrappers
    set_chat_id_for_file_sending(chat_id)
    set_ics_chat_id(chat_id)

    # Invoke the agent
    agent = get_agent(user, history)
    agent_response_obj = agent()

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

        # Check if we should create a new session based on inactivity
        should_create, reason = should_create_new_session(
            conversation_history, SESSION_TIMEOUT_MINUTES
        )

        if should_create:
            logger.info(f"Creating new session: {reason}")
            conversation_history = create_new_session(user.user_id)
        else:
            logger.info(
                "Continuing existing session - updating timestamp to keep it active"
            )
            conversation_history = update_session_timestamp(conversation_history)

        # Save the session immediately to persist the changes
        history_store.save_history(conversation_history)

        # Log session status for debugging
        session_status = get_session_status(conversation_history)
        logger.info(f"Session status: {session_status['reason']}")

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
