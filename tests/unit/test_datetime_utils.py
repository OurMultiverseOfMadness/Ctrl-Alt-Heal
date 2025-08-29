"""Tests for datetime utilities."""

from datetime import datetime, UTC, timedelta

from ctrl_alt_heal.utils.datetime_utils import (
    get_current_utc_iso,
    generate_timestamp_filename,
    format_datetime_for_display,
    parse_iso_datetime,
    is_datetime_recent,
    get_time_difference_minutes,
)


class TestDateTimeUtils:
    """Test datetime utility functions."""

    def test_get_current_utc_iso(self):
        """Test getting current UTC time as ISO string."""
        result = get_current_utc_iso()

        # Should be a valid ISO format string
        assert isinstance(result, str)
        assert "T" in result
        assert "+" in result or "Z" in result

        # Should be parseable
        parsed = datetime.fromisoformat(result.replace("Z", "+00:00"))
        assert isinstance(parsed, datetime)

    def test_generate_timestamp_filename(self):
        """Test generating timestamped filenames."""
        # Test with prefix only
        result = generate_timestamp_filename("test")
        assert result.startswith("test_")
        assert len(result) > len("test_")

        # Test with prefix and suffix
        result = result = generate_timestamp_filename("test", "suffix")
        assert result.startswith("test_")
        assert result.endswith("_suffix")

        # Test with empty suffix
        result = generate_timestamp_filename("test", "")
        assert result.startswith("test_")
        assert not result.endswith("_")

    def test_format_datetime_for_display(self):
        """Test formatting datetime for display."""
        dt = datetime(2024, 1, 15, 14, 30, 45)

        # Test default format
        result = format_datetime_for_display(dt)
        assert "2024-01-15 14:30:45" in result

        # Test custom format
        result = format_datetime_for_display(dt, "%Y-%m-%d")
        assert result == "2024-01-15"

    def test_parse_iso_datetime(self):
        """Test parsing ISO datetime strings."""
        # Test valid ISO string
        iso_str = "2024-01-15T14:30:45+00:00"
        result = parse_iso_datetime(iso_str)
        assert result == datetime(2024, 1, 15, 14, 30, 45, tzinfo=UTC)

        # Test with Z suffix
        iso_str = "2024-01-15T14:30:45Z"
        result = parse_iso_datetime(iso_str)
        assert result == datetime(2024, 1, 15, 14, 30, 45, tzinfo=UTC)

        # Test invalid string
        result = parse_iso_datetime("invalid")
        assert result is None

        # Test empty string
        result = parse_iso_datetime("")
        assert result is None

    def test_is_datetime_recent(self):
        """Test checking if datetime is recent."""
        now = datetime.now(UTC)

        # Test recent datetime
        recent_dt = now - timedelta(minutes=10)
        assert is_datetime_recent(recent_dt, 30) is True

        # Test old datetime
        old_dt = now - timedelta(minutes=40)
        assert is_datetime_recent(old_dt, 30) is False

        # Test custom threshold
        recent_dt = now - timedelta(minutes=5)
        assert is_datetime_recent(recent_dt, 10) is True

    def test_get_time_difference_minutes(self):
        """Test getting time difference in minutes."""
        dt1 = datetime(2024, 1, 15, 14, 0, 0, tzinfo=UTC)
        dt2 = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        result = get_time_difference_minutes(dt1, dt2)
        assert result == 30

        # Test reverse order
        result = get_time_difference_minutes(dt2, dt1)
        assert result == -30

        # Test same time
        result = get_time_difference_minutes(dt1, dt1)
        assert result == 0
