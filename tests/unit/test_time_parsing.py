"""Tests for time parsing utilities."""

from ctrl_alt_heal.utils.time_parsing import (
    parse_natural_time_input,
    parse_natural_times_input,
    parse_frequency_to_times,
    validate_time_format,
    validate_time_range,
)
from ctrl_alt_heal.utils.timezone import (
    normalize_timezone_input,
    suggest_timezone_from_language,
)


class TestTimeParsing:
    """Test time parsing functionality."""

    def test_parse_natural_time_input_12_hour_format(self):
        """Test parsing 12-hour format times."""
        # Test cases that should work
        test_cases = [
            ("10am", "10:00"),
            ("2pm", "14:00"),
            ("8pm", "20:00"),
            ("12am", "00:00"),
            ("12pm", "12:00"),
            ("10:30am", "10:30"),
            ("2:45pm", "14:45"),
            ("11:59pm", "23:59"),
        ]

        for input_time, expected in test_cases:
            result = parse_natural_time_input(input_time)
            assert result == expected

    def test_parse_natural_time_input_24_hour_format(self):
        """Test parsing 24-hour format times."""
        test_cases = [
            ("10:00", "10:00"),
            ("14:30", "14:30"),
            ("23:59", "23:59"),
            ("00:00", "00:00"),
        ]

        for input_time, expected in test_cases:
            result = parse_natural_time_input(input_time)
            assert result == expected

    def test_parse_natural_time_input_invalid_formats(self):
        """Test that invalid time formats return None."""
        invalid_times = [
            "25:00",  # Invalid hour
            "10:60",  # Invalid minute
            "10am:30",  # Malformed
            "10:30am:45",  # Malformed
            "not a time",  # Not a time
            "",  # Empty string
            "13am",  # Invalid AM/PM
            "13pm",  # Invalid AM/PM
        ]

        for invalid_time in invalid_times:
            result = parse_natural_time_input(invalid_time)
            assert result is None

    def test_parse_frequency_to_times(self):
        """Test parsing frequency text to default times."""
        test_cases = [
            ("once daily", ["08:00"]),
            ("twice daily", ["08:00", "20:00"]),
            ("three times daily", ["08:00", "14:00", "20:00"]),
            ("four times daily", ["08:00", "12:00", "16:00", "20:00"]),
            ("morning", ["08:00"]),
            ("evening", ["20:00"]),
            ("night", ["20:00"]),
            ("afternoon", ["12:00"]),
            ("noon", ["12:00"]),
            ("", ["08:00"]),  # Default case
        ]

        for frequency, expected in test_cases:
            result = parse_frequency_to_times(frequency)
            assert result == expected

    def test_parse_natural_times_input_list(self):
        """Test parsing list of natural time inputs."""
        test_cases = [
            (["10am", "2pm", "8pm"], ["10:00", "14:00", "20:00"]),
            (["10:00", "14:00", "20:00"], ["10:00", "14:00", "20:00"]),
            (["9:30am", "3:45pm"], ["09:30", "15:45"]),
        ]

        for input_times, expected in test_cases:
            result = parse_natural_times_input(input_times)
            assert result == expected

    def test_parse_natural_times_input_string(self):
        """Test parsing comma-separated time string."""
        test_cases = [
            ("10am, 2pm, 8pm", ["10:00", "14:00", "20:00"]),
            ("10:00, 14:00, 20:00", ["10:00", "14:00", "20:00"]),
            ("9:30am, 3:45pm", ["09:30", "15:45"]),
        ]

        for input_string, expected in test_cases:
            result = parse_natural_times_input(input_string)
            assert result == expected

    def test_parse_natural_times_input_mixed_formats(self):
        """Test parsing mixed time formats."""
        test_cases = [
            (["10am", "14:00", "8pm"], ["10:00", "14:00", "20:00"]),
            (["9:30am", "15:45", "10pm"], ["09:30", "15:45", "22:00"]),
        ]

        for input_times, expected in test_cases:
            result = parse_natural_times_input(input_times)
            assert result == expected

    def test_parse_natural_times_input_with_invalid_times(self):
        """Test parsing with some invalid times."""
        test_cases = [
            (
                ["10am", "invalid", "8pm"],
                ["10:00", "20:00"],
            ),  # Should filter out invalid
            (["invalid", "2pm"], ["14:00"]),  # Should filter out invalid
            (["invalid"], ["08:00"]),  # Should return default when no valid times
        ]

        for input_times, expected in test_cases:
            result = parse_natural_times_input(input_times)
            assert result == expected


class TestTimezoneHandling:
    """Test timezone handling functionality."""

    def test_normalize_timezone_input(self):
        """Test normalizing timezone input strings."""
        test_cases = [
            ("EST", "America/New_York"),
            ("PST", "America/Los_Angeles"),
            ("UTC", "UTC"),
            ("UTC+5", "Etc/GMT-5"),
            ("UTC-5", "Etc/GMT+5"),
            ("SGT", "Asia/Singapore"),
            ("Pacific Time", "America/Los_Angeles"),
            ("Eastern Time", "America/New_York"),
            ("New York", "America/New_York"),
            ("Los Angeles", "America/Los_Angeles"),
            ("Singapore", "Asia/Singapore"),
        ]

        for input_tz, expected in test_cases:
            result = normalize_timezone_input(input_tz)
            assert result == expected

    def test_normalize_timezone_input_invalid(self):
        """Test normalizing invalid timezone inputs."""
        invalid_timezones = [
            "INVALID",
            "NOT_A_TIMEZONE",
            "",
            "123",
        ]

        for invalid_tz in invalid_timezones:
            result = normalize_timezone_input(invalid_tz)
            assert result is None

    def test_suggest_timezone_from_language(self):
        """Test suggesting timezone based on language."""
        test_cases = [
            ("en-US", "America/New_York"),
            ("en-GB", "Europe/London"),
            ("zh-CN", "Asia/Shanghai"),
            ("ja-JP", "Asia/Tokyo"),
            ("de-DE", "Europe/Berlin"),
            ("fr-FR", "Europe/Paris"),
            ("es-ES", "Europe/Madrid"),
            ("pt-BR", "America/Sao_Paulo"),
            ("en-AU", "Australia/Sydney"),
            ("en-CA", "America/Toronto"),
        ]

        for language, expected in test_cases:
            result = suggest_timezone_from_language(language)
            assert result == expected

    def test_suggest_timezone_from_language_unknown(self):
        """Test suggesting timezone for unknown language."""
        unknown_languages = [
            "xx-XX",
            "unknown",
            "",
            "invalid",
        ]

        for language in unknown_languages:
            result = suggest_timezone_from_language(language)
            assert result == "UTC"  # Should default to UTC


class TestTimeValidation:
    """Test time validation functionality."""

    def test_validate_time_format(self):
        """Test validating time format."""
        valid_times = [
            "00:00",
            "12:00",
            "23:59",
            "09:30",
            "14:45",
        ]

        for time_str in valid_times:
            result = validate_time_format(time_str)
            assert result is True

    def test_validate_time_format_invalid(self):
        """Test validating invalid time formats."""
        invalid_times = [
            "24:00",  # Hour > 23
            "12:60",  # Minute > 59
            "25:30",  # Hour > 23
            "10:61",  # Minute > 59
            "1:30",  # Missing leading zero
            "10:5",  # Missing leading zero
            "10am",  # Not 24-hour format
            "not a time",
            "",
        ]

        for time_str in invalid_times:
            result = validate_time_format(time_str)
            assert result is False

    def test_validate_time_range(self):
        """Test validating time is within valid range."""
        valid_times = [
            ("00:00", True),
            ("12:00", True),
            ("23:59", True),
            ("24:00", False),
            ("12:60", False),
            ("25:30", False),
        ]

        for time_str, expected in valid_times:
            result = validate_time_range(time_str)
            assert result == expected
