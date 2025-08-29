"""Tests for string utilities."""

from ctrl_alt_heal.utils.string_utils import (
    sanitize_filename,
    normalize_timezone_string,
    clean_message_text,
    clean_xml_tags,
    split_message_for_telegram,
    normalize_medication_name,
    extract_medication_name_from_filename,
)


class TestStringUtils:
    """Test string utility functions."""

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Test normal filename
        result = sanitize_filename("My Medication")
        assert result == "My_Medication"

        # Test with invalid characters
        result = sanitize_filename("file<name>with:invalid/chars")
        assert result == "file_name_with_invalid_chars"

        # Test with multiple spaces
        result = sanitize_filename("  multiple   spaces  ")
        assert result == "multiple_spaces"

        # Test empty string
        result = sanitize_filename("")
        assert result == "unnamed"

        # Test None
        result = sanitize_filename(None)
        assert result == "unnamed"

    def test_normalize_timezone_string(self):
        """Test timezone string normalization."""
        # Test with Z suffix
        result = normalize_timezone_string("2024-01-15T14:30:45Z")
        assert result == "2024-01-15T14:30:45+00:00"

        # Test without Z suffix
        result = normalize_timezone_string("2024-01-15T14:30:45+00:00")
        assert result == "2024-01-15T14:30:45+00:00"

        # Test empty string
        result = normalize_timezone_string("")
        assert result == ""

        # Test None
        result = normalize_timezone_string(None)
        assert result is None

    def test_clean_message_text(self):
        """Test message text cleaning."""
        # Test with extra whitespace
        result = clean_message_text("  multiple    spaces  ")
        assert result == "multiple spaces"

        # Test with newlines
        result = clean_message_text("line1\nline2\nline3")
        assert result == "line1 line2 line3"

        # Test with tabs
        result = clean_message_text("tab1\ttab2\ttab3")
        assert result == "tab1 tab2 tab3"

        # Test empty string
        result = clean_message_text("")
        assert result == ""

        # Test None
        result = clean_message_text(None)
        assert result == ""

    def test_clean_xml_tags(self):
        """Test XML tag cleaning."""
        # Test with XML tags
        result = clean_xml_tags(
            "<thinking>This is a thought</thinking><response>This is a response</response>"
        )
        assert result == "This is a thoughtThis is a response"

        # Test with nested tags
        result = clean_xml_tags("<outer><inner>content</inner></outer>")
        assert result == "content"

        # Test without tags
        result = clean_xml_tags("Plain text without tags")
        assert result == "Plain text without tags"

        # Test empty string
        result = clean_xml_tags("")
        assert result == ""

    def test_split_message_for_telegram(self):
        """Test message splitting for Telegram."""
        # Test short message
        result = split_message_for_telegram("Short message")
        assert result == ["Short message"]

        # Test long message
        long_message = "A" * 10000  # Longer than 2 * max_length
        result = split_message_for_telegram(long_message)
        assert len(result) > 1
        assert all(len(chunk) <= 4096 for chunk in result)

        # Test with custom max length
        short_message = "A" * 150  # Longer than 2 * max_length
        result = split_message_for_telegram(short_message, max_length=50)
        assert len(result) > 1
        assert all(len(chunk) <= 50 for chunk in result)

        # Test with sentences
        sentences = "First sentence. Second sentence. Third sentence."
        result = split_message_for_telegram(sentences, max_length=20)
        assert len(result) > 1

        # Test empty message
        result = split_message_for_telegram("")
        assert result == []

    def test_normalize_medication_name(self):
        """Test medication name normalization."""
        # Test normal name
        result = normalize_medication_name("Aspirin 100mg")
        assert result == "aspirin 100mg"

        # Test with common terms
        result = normalize_medication_name("Aspirin TAB 100mg")
        assert result == "aspirin 100mg"

        # Test with extra whitespace
        result = normalize_medication_name("  Aspirin   100mg  ")
        assert result == "aspirin 100mg"

        # Test empty string
        result = normalize_medication_name("")
        assert result == ""

    def test_extract_medication_name_from_filename(self):
        """Test extracting medication name from filename."""
        # Test with timestamp
        result = extract_medication_name_from_filename(
            "Aspirin_reminders_20240115_143045.ics"
        )
        assert result == "Aspirin"

        # Test with suffix
        result = extract_medication_name_from_filename("Aspirin_schedule.ics")
        assert result == "Aspirin"

        # Test with underscores
        result = extract_medication_name_from_filename("Vitamin_D_reminders.ics")
        assert result == "Vitamin D"

        # Test without extension
        result = extract_medication_name_from_filename("Aspirin_reminders")
        assert result == "Aspirin"

        # Test empty string
        result = extract_medication_name_from_filename("")
        assert result == ""
