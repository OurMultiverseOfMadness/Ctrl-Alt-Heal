"""Telegram message formatting utilities for robust message handling."""

from __future__ import annotations

import re
from typing import List, Dict, Any
from enum import Enum

from ctrl_alt_heal.utils.constants import TELEGRAM_API


class TelegramParseMode(Enum):
    """Telegram parse modes for message formatting."""

    MARKDOWN_V2 = "MarkdownV2"
    HTML = "HTML"
    MARKDOWN = "Markdown"  # Legacy, deprecated
    PLAIN_TEXT = "text"


class TelegramFormatter:
    """Handles Telegram message formatting and parsing."""

    def __init__(self, parse_mode: TelegramParseMode = TelegramParseMode.HTML):
        """
        Initialize the formatter.

        Args:
            parse_mode: Telegram parse mode to use for formatting
        """
        self.parse_mode = parse_mode

    def format_message(self, text: str) -> Dict[str, Any]:
        """
        Format a message for Telegram API.

        Args:
            text: Raw message text

        Returns:
            Formatted message payload
        """
        if self.parse_mode == TelegramParseMode.PLAIN_TEXT:
            return {"text": text}

        formatted_text = self._apply_formatting(text)

        return {"text": formatted_text, "parse_mode": self.parse_mode.value}

    def _apply_formatting(self, text: str) -> str:
        """
        Apply formatting based on the parse mode.

        Args:
            text: Raw text to format

        Returns:
            Formatted text
        """
        if self.parse_mode == TelegramParseMode.HTML:
            return self._format_html(text)
        elif self.parse_mode == TelegramParseMode.MARKDOWN_V2:
            return self._format_markdown_v2(text)
        elif self.parse_mode == TelegramParseMode.MARKDOWN:
            return self._format_markdown(text)
        else:
            return text

    def _format_html(self, text: str) -> str:
        """
        Format text as HTML for Telegram.

        Args:
            text: Raw text to format

        Returns:
            HTML formatted text
        """
        # Escape HTML special characters
        text = self._escape_html(text)

        # Convert markdown-style formatting to HTML
        # Bold: **text** -> <b>text</b>
        text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)

        # Italic: *text* -> <i>text</i>
        text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)

        # Code: `text` -> <code>text</code>
        text = re.sub(r"`(.*?)`", r"<code>\1</code>", text)

        # Code blocks: ```text``` -> <pre><code>text</code></pre>
        text = re.sub(
            r"```(.*?)```", r"<pre><code>\1</code></pre>", text, flags=re.DOTALL
        )

        # Links: [text](url) -> <a href="url">text</a>
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)

        # Line breaks: \n -> <br>
        text = text.replace("\n", "<br>")

        return text

    def _format_markdown_v2(self, text: str) -> str:
        """
        Format text as MarkdownV2 for Telegram.

        Args:
            text: Raw text to format

        Returns:
            MarkdownV2 formatted text
        """
        # Escape special characters for MarkdownV2
        special_chars = [
            "_",
            "*",
            "[",
            "]",
            "(",
            ")",
            "~",
            "`",
            ">",
            "#",
            "+",
            "-",
            "=",
            "|",
            "{",
            "}",
            ".",
            "!",
        ]

        for char in special_chars:
            text = text.replace(char, f"\\{char}")

        # Apply formatting (re-escape the content)
        # Bold: **text** -> *text*
        text = re.sub(r"\\\*\\\*(.*?)\\\*\\\*", r"*\1*", text)

        # Italic: *text* -> _text_
        text = re.sub(r"\\\*(.*?)\\\*", r"_\1_", text)

        # Code: `text` -> `text` (already escaped)
        text = re.sub(r"`(.*?)`", r"`\1`", text)

        # Links: [text](url) -> [text](url) (already escaped)

        return text

    def _format_markdown(self, text: str) -> str:
        """
        Format text as legacy Markdown for Telegram.

        Args:
            text: Raw text to format

        Returns:
            Markdown formatted text
        """
        # Legacy Markdown formatting (deprecated but still supported)
        # Bold: **text** -> *text*
        text = re.sub(r"\*\*(.*?)\*\*", r"*\1*", text)

        # Italic: *text* -> _text_
        text = re.sub(r"\*(.*?)\*", r"_\1_", text)

        # Code: `text` -> `text`
        # Links: [text](url) -> [text](url)

        return text

    def _escape_html(self, text: str) -> str:
        """
        Escape HTML special characters.

        Args:
            text: Text to escape

        Returns:
            Escaped text
        """
        html_escapes = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;",
        }

        for char, escape in html_escapes.items():
            text = text.replace(char, escape)

        return text

    def clean_formatting(self, text: str) -> str:
        """
        Remove formatting from text to get plain text.

        Args:
            text: Formatted text

        Returns:
            Plain text without formatting
        """
        # Remove markdown formatting
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # Bold
        text = re.sub(r"\*(.*?)\*", r"\1", text)  # Italic
        text = re.sub(r"`(.*?)`", r"\1", text)  # Code
        text = re.sub(r"```(.*?)```", r"\1", text, flags=re.DOTALL)  # Code blocks
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # Links

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Unescape HTML entities
        html_unescapes = {
            "&amp;": "&",
            "&lt;": "<",
            "&gt;": ">",
            "&quot;": '"',
            "&#39;": "'",
        }

        for escape, char in html_unescapes.items():
            text = text.replace(escape, char)

        return text.strip()

    def validate_formatting(self, text: str) -> bool:
        """
        Validate that the text can be properly formatted.

        Args:
            text: Text to validate

        Returns:
            True if formatting is valid, False otherwise
        """
        try:
            formatted = self._apply_formatting(text)
            return len(formatted) <= TELEGRAM_API["MAX_MESSAGE_LENGTH"]
        except Exception:
            return False

    def get_formatted_length(self, text: str) -> int:
        """
        Get the length of formatted text.

        Args:
            text: Text to measure

        Returns:
            Length of formatted text
        """
        formatted = self._apply_formatting(text)
        return len(formatted)


class MessageSplitter:
    """Handles intelligent message splitting for Telegram."""

    def __init__(self, max_length: int = TELEGRAM_API["MAX_MESSAGE_LENGTH"]):
        """
        Initialize the splitter.

        Args:
            max_length: Maximum length per message
        """
        self.max_length = max_length
        self.formatter = TelegramFormatter()

    def split_message(self, text: str, preserve_formatting: bool = True) -> List[str]:
        """
        Split a long message into multiple parts.

        Args:
            text: Text to split
            preserve_formatting: Whether to preserve formatting across splits

        Returns:
            List of message parts
        """
        if len(text) <= self.max_length:
            return [text]

        if preserve_formatting:
            return self._split_with_formatting(text)
        else:
            return self._split_plain_text(text)

    def _split_with_formatting(self, text: str) -> List[str]:
        """
        Split message while preserving formatting.

        Args:
            text: Text to split

        Returns:
            List of formatted message parts
        """
        self._original_text = text  # Store original text for fallback

        # First, try to split by paragraphs
        paragraphs = text.split("\n\n")
        if len(paragraphs) > 1:
            return self._split_by_paragraphs(paragraphs)

        # Then try to split by sentences
        sentences = re.split(r"(?<=[.!?])\s+", text)
        if len(sentences) > 1:
            return self._split_by_sentences(sentences)

        # Finally, split by words
        words = text.split()
        return self._split_by_words(words)

    def _split_by_paragraphs(self, paragraphs: List[str]) -> List[str]:
        """
        Split by paragraphs.

        Args:
            paragraphs: List of paragraphs

        Returns:
            List of message parts
        """
        parts = []
        current_part = ""

        for paragraph in paragraphs:
            if len(current_part) + len(paragraph) + 2 <= self.max_length:
                current_part += (
                    (paragraph + "\n\n") if current_part else paragraph + "\n\n"
                )
            else:
                if current_part:
                    parts.append(current_part.strip())
                current_part = paragraph + "\n\n"

        if current_part:
            parts.append(current_part.strip())

        return parts if len(parts) > 1 else [self._original_text]

    def _split_by_sentences(self, sentences: List[str]) -> List[str]:
        """
        Split by sentences.

        Args:
            sentences: List of sentences

        Returns:
            List of message parts
        """
        parts = []
        current_part = ""

        for sentence in sentences:
            if len(current_part) + len(sentence) + 1 <= self.max_length:
                current_part += (sentence + " ") if current_part else sentence + " "
            else:
                if current_part:
                    parts.append(current_part.strip())
                current_part = sentence + " "

        if current_part:
            parts.append(current_part.strip())

        return parts if len(parts) > 1 else [self._original_text]

    def _split_by_words(self, words: List[str]) -> List[str]:
        """
        Split by words.

        Args:
            words: List of words

        Returns:
            List of message parts
        """
        parts = []
        current_part = ""

        for word in words:
            if len(current_part) + len(word) + 1 <= self.max_length:
                current_part += (word + " ") if current_part else word + " "
            else:
                if current_part:
                    parts.append(current_part.strip())
                current_part = word + " "

        if current_part:
            parts.append(current_part.strip())

        return parts

    def _split_plain_text(self, text: str) -> List[str]:
        """
        Split plain text without preserving formatting.

        Args:
            text: Text to split

        Returns:
            List of message parts
        """
        # Simple character-based splitting
        parts = []
        for i in range(0, len(text), self.max_length):
            parts.append(text[i : i + self.max_length])

        return parts


class TelegramMessageBuilder:
    """Builds Telegram messages with proper formatting and validation."""

    def __init__(self, parse_mode: TelegramParseMode = TelegramParseMode.HTML):
        """
        Initialize the message builder.

        Args:
            parse_mode: Parse mode to use
        """
        self.formatter = TelegramFormatter(parse_mode)
        self.splitter = MessageSplitter()

    def build_message(self, text: str, split_long: bool = True) -> List[Dict[str, Any]]:
        """
        Build a Telegram message with proper formatting.

        Args:
            text: Message text
            split_long: Whether to split long messages

        Returns:
            List of message payloads
        """
        # Clean and validate the text
        text = self._clean_text(text)

        if not split_long:
            return [self.formatter.format_message(text)]

        # Split if needed
        parts = self.splitter.split_message(text, preserve_formatting=True)

        # Format each part
        messages = []
        for i, part in enumerate(parts):
            if len(parts) > 1:
                part = f"{part}\n\n*Part {i+1} of {len(parts)}*"

            formatted = self.formatter.format_message(part)
            messages.append(formatted)

        return messages

    def _clean_text(self, text: str) -> str:
        """
        Clean and prepare text for formatting.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)
        text = re.sub(r" +", " ", text)

        # Remove any XML-like tags that might interfere
        text = re.sub(r"<[^>]+>", "", text)

        return text.strip()

    def validate_message(self, text: str) -> bool:
        """
        Validate that a message can be sent.

        Args:
            text: Message text

        Returns:
            True if valid, False otherwise
        """
        return self.formatter.validate_formatting(text)
