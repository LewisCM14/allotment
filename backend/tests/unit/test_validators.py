"""
Unit tests for app/api/schemas/validators.py

Tests all validator functions to ensure they properly validate and normalize input
according to the general data integrity rules and notes field requirements.
"""

import pytest

from app.api.schemas.validators import (
    validate_general_text_field,
    validate_notes_field,
    validate_text_field,
)


class TestValidateGeneralTextField:
    """Test cases for validate_general_text_field function."""

    def test_valid_single_word_lowercase(self):
        """Test validation passes for a single lowercase word."""
        result = validate_general_text_field("tomato", "name")
        assert result == "tomato"

    def test_valid_single_word_uppercase_normalized(self):
        """Test uppercase input is normalized to lowercase."""
        result = validate_general_text_field("TOMATO", "name")
        assert result == "tomato"

    def test_valid_single_word_mixed_case_normalized(self):
        """Test mixed case input is normalized to lowercase."""
        result = validate_general_text_field("ToMaTo", "name")
        assert result == "tomato"

    def test_valid_multiple_words_with_spaces(self):
        """Test validation passes for multiple words separated by single spaces."""
        result = validate_general_text_field("cherry tomato", "name")
        assert result == "cherry tomato"

    def test_valid_multiple_words_with_hyphens(self):
        """Test validation passes for hyphenated words."""
        result = validate_general_text_field("sweet-potato", "name")
        assert result == "sweet-potato"

    def test_valid_mixed_separators(self):
        """Test validation passes for words with both spaces and hyphens."""
        result = validate_general_text_field("black-eyed peas", "name")
        assert result == "black-eyed peas"

    def test_valid_complex_name(self):
        """Test validation passes for complex valid names."""
        result = validate_general_text_field("long-grain brown rice", "name")
        assert result == "long-grain brown rice"

    def test_leading_trailing_spaces_stripped(self):
        """Test leading and trailing spaces are stripped."""
        result = validate_general_text_field("  tomato  ", "name")
        assert result == "tomato"

    def test_uppercase_with_spaces_normalized(self):
        """Test uppercase input with spaces is properly normalized."""
        result = validate_general_text_field("  CHERRY TOMATO  ", "name")
        assert result == "cherry tomato"

    def test_empty_string_raises_error(self):
        """Test empty string raises ValueError."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            validate_general_text_field("", "name")

    def test_whitespace_only_raises_error(self):
        """Test whitespace-only string raises ValueError after stripping."""
        with pytest.raises(
            ValueError,
            match="name can only contain lowercase letters, hyphens, and single spaces between words",
        ):
            validate_general_text_field("   ", "name")

    def test_consecutive_spaces_raises_error(self):
        """Test consecutive spaces raise ValueError."""
        with pytest.raises(
            ValueError,
            match="name can only contain lowercase letters, hyphens, and single spaces between words",
        ):
            validate_general_text_field("cherry  tomato", "name")

    def test_multiple_consecutive_spaces_raises_error(self):
        """Test multiple consecutive spaces raise ValueError."""
        with pytest.raises(
            ValueError,
            match="name can only contain lowercase letters, hyphens, and single spaces between words",
        ):
            validate_general_text_field("cherry   tomato", "name")

    def test_special_characters_raise_error(self):
        """Test special characters raise ValueError."""
        invalid_chars = [
            "!",
            "@",
            "#",
            "$",
            "%",
            "^",
            "&",
            "*",
            "(",
            ")",
            "=",
            "+",
            "[",
            "]",
            "{",
            "}",
            "|",
            "\\",
            ":",
            ";",
            '"',
            "'",
            "<",
            ">",
            ",",
            ".",
            "?",
            "/",
            "~",
            "`",
        ]

        for char in invalid_chars:
            with pytest.raises(
                ValueError,
                match="can only contain lowercase letters, hyphens, and single spaces",
            ):
                validate_general_text_field(f"tomato{char}", "name")

    def test_numbers_raise_error(self):
        """Test numbers raise ValueError."""
        with pytest.raises(
            ValueError,
            match="can only contain lowercase letters, hyphens, and single spaces",
        ):
            validate_general_text_field("tomato123", "name")

    def test_underscore_raises_error(self):
        """Test underscore raises ValueError."""
        with pytest.raises(
            ValueError,
            match="can only contain lowercase letters, hyphens, and single spaces",
        ):
            validate_general_text_field("cherry_tomato", "name")

    def test_period_raises_error(self):
        """Test period raises ValueError."""
        with pytest.raises(
            ValueError,
            match="can only contain lowercase letters, hyphens, and single spaces",
        ):
            validate_general_text_field("mr.tomato", "name")

    def test_starting_with_hyphen_raises_error(self):
        """Test string starting with hyphen raises ValueError."""
        with pytest.raises(
            ValueError,
            match="can only contain lowercase letters, hyphens, and single spaces",
        ):
            validate_general_text_field("-tomato", "name")

    def test_ending_with_hyphen_raises_error(self):
        """Test string ending with hyphen raises ValueError."""
        with pytest.raises(
            ValueError,
            match="can only contain lowercase letters, hyphens, and single spaces",
        ):
            validate_general_text_field("tomato-", "name")

    def test_starting_with_space_strips_correctly(self):
        """Test string starting with space is stripped and passes validation."""
        result = validate_general_text_field(" tomato", "name")
        assert result == "tomato"

    def test_ending_with_space_strips_correctly(self):
        """Test string ending with space is stripped and passes validation."""
        result = validate_general_text_field("tomato ", "name")
        assert result == "tomato"

    def test_consecutive_hyphens_raise_error(self):
        """Test consecutive hyphens raise ValueError."""
        with pytest.raises(
            ValueError,
            match="can only contain lowercase letters, hyphens, and single spaces",
        ):
            validate_general_text_field("cherry--tomato", "name")

    def test_mixed_consecutive_separators_raise_error(self):
        """Test mixed consecutive separators raise ValueError."""
        with pytest.raises(
            ValueError,
            match="can only contain lowercase letters, hyphens, and single spaces",
        ):
            validate_general_text_field("cherry- tomato", "name")

    def test_custom_field_name_in_error(self):
        """Test custom field name appears in error message."""
        with pytest.raises(ValueError, match="custom_field cannot be empty"):
            validate_general_text_field("", "custom_field")

    def test_unicode_characters_raise_error(self):
        """Test unicode characters raise ValueError."""
        with pytest.raises(
            ValueError,
            match="can only contain lowercase letters, hyphens, and single spaces",
        ):
            validate_general_text_field("tomatö", "name")

    def test_accented_characters_raise_error(self):
        """Test accented characters raise ValueError."""
        with pytest.raises(
            ValueError,
            match="can only contain lowercase letters, hyphens, and single spaces",
        ):
            validate_general_text_field("café", "name")


class TestValidateNotesField:
    """Test cases for validate_notes_field function."""

    def test_empty_string_returns_empty(self):
        """Test empty string is returned as-is."""
        result = validate_notes_field("", "notes")
        assert result == ""

    def test_none_value_returns_none(self):
        """Test None value is returned as-is."""
        result = validate_notes_field(None, "notes")
        assert result is None

    def test_valid_simple_text(self):
        """Test simple text passes validation."""
        result = validate_notes_field("This is a simple note.", "notes")
        assert result == "This is a simple note."

    def test_special_characters_allowed(self):
        """Test special characters are allowed in notes."""
        text = "Note with special chars: !@#$%^&*()_+-=[]{}|;:,.<>?/~`"
        result = validate_notes_field(text, "notes")
        assert result == text

    def test_numbers_allowed(self):
        """Test numbers are allowed in notes."""
        text = "Plant spacing: 12-18 inches apart, pH 6.0-7.0"
        result = validate_notes_field(text, "notes")
        assert result == text

    def test_unicode_characters_allowed(self):
        """Test unicode characters are allowed in notes."""
        text = "Temperature: 20°C-25°C, café-style planting"
        result = validate_notes_field(text, "notes")
        assert result == text

    def test_newlines_and_tabs_allowed(self):
        """Test newlines and tabs are allowed in notes."""
        text = "Line 1\nLine 2\tTabbed content"
        result = validate_notes_field(text, "notes")
        assert result == text

    def test_mixed_case_preserved(self):
        """Test mixed case is preserved (not normalized to lowercase)."""
        text = "Plant NAME should be Capitalized"
        result = validate_notes_field(text, "notes")
        assert result == "Plant NAME should be Capitalized"

    def test_leading_trailing_spaces_trimmed(self):
        """Test leading and trailing spaces are trimmed."""
        text = "  This note has spaces  "
        result = validate_notes_field(text, "notes")
        assert result == "This note has spaces"

    def test_internal_spaces_preserved(self):
        """Test internal spaces including consecutive ones are preserved."""
        text = "This  has   multiple    spaces"
        result = validate_notes_field(text, "notes")
        assert result == "This  has   multiple    spaces"

    def test_default_max_length_500(self):
        """Test default maximum length is 500 characters."""
        text = "x" * 500
        result = validate_notes_field(text, "notes")
        assert result == text

    def test_exceeds_default_max_length_raises_error(self):
        """Test exceeding default max length raises ValueError."""
        text = "x" * 501
        with pytest.raises(ValueError, match="notes cannot exceed 500 characters"):
            validate_notes_field(text, "notes")

    def test_custom_max_length(self):
        """Test custom maximum length validation."""
        text = "x" * 100
        result = validate_notes_field(text, "notes", max_length=100)
        assert result == text

    def test_exceeds_custom_max_length_raises_error(self):
        """Test exceeding custom max length raises ValueError."""
        text = "x" * 101
        with pytest.raises(ValueError, match="notes cannot exceed 100 characters"):
            validate_notes_field(text, "notes", max_length=100)

    def test_max_length_after_trimming(self):
        """Test max length is checked after trimming whitespace."""
        # Create a string that's 500 chars after trimming but longer before
        text = "  " + "x" * 500 + "  "
        result = validate_notes_field(text, "notes", max_length=500)
        assert result == "x" * 500

    def test_max_length_after_trimming_raises_error(self):
        """Test max length error after trimming whitespace."""
        # Create a string that's 501 chars after trimming
        text = "  " + "x" * 501 + "  "
        with pytest.raises(ValueError, match="notes cannot exceed 500 characters"):
            validate_notes_field(text, "notes", max_length=500)

    def test_custom_field_name_in_error(self):
        """Test custom field name appears in error message."""
        text = "x" * 501
        with pytest.raises(
            ValueError, match="description cannot exceed 500 characters"
        ):
            validate_notes_field(text, "description")

    def test_whitespace_only_trimmed_to_empty(self):
        """Test whitespace-only string is trimmed to empty string."""
        result = validate_notes_field("   \t\n   ", "notes")
        assert result == ""


class TestValidateTextField:
    """Test cases for validate_text_field function (Pydantic validator wrapper)."""

    def test_valid_input_passes_through(self):
        """Test valid input passes through validate_text_field."""
        result = validate_text_field("tomato", "name")
        assert result == "tomato"

    def test_invalid_input_raises_error(self):
        """Test invalid input raises error through validate_text_field."""
        with pytest.raises(ValueError, match="name can only contain lowercase letters"):
            validate_text_field("tomato123", "name")

    def test_normalization_works(self):
        """Test normalization works through validate_text_field."""
        result = validate_text_field("  CHERRY TOMATO  ", "name")
        assert result == "cherry tomato"

    def test_default_field_name(self):
        """Test default field name is used when not provided."""
        with pytest.raises(ValueError, match="field cannot be empty"):
            validate_text_field("")

    def test_custom_field_name(self):
        """Test custom field name is used in error messages."""
        with pytest.raises(ValueError, match="family_name cannot be empty"):
            validate_text_field("", "family_name")

    def test_cls_parameter_unused_but_required(self):
        """Test cls parameter is no longer required (function simplified)."""
        # The cls parameter has been removed to simplify the function
        result = validate_text_field("tomato", "name")
        assert result == "tomato"

    def test_complex_valid_case(self):
        """Test complex valid case through validate_text_field."""
        result = validate_text_field("  LONG-GRAIN Brown Rice  ", "variety")
        assert result == "long-grain brown rice"

    def test_special_characters_error_message(self):
        """Test error message for special characters is informative."""
        with pytest.raises(
            ValueError,
            match="variety can only contain lowercase letters, hyphens, and single spaces",
        ):
            validate_text_field("rice@home", "variety")
