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
        with pytest.raises(
            ValueError,
            match="name can only contain lowercase letters, hyphens, and single spaces between words",
        ):
            validate_general_text_field("tomato!", "name")

    def test_numbers_raise_error(self):
        """Test numbers raise ValueError."""
        with pytest.raises(
            ValueError,
            match="name can only contain lowercase letters, hyphens, and single spaces between words",
        ):
            validate_general_text_field("tomato123", "name")

    def test_underscore_raises_error(self):
        """Test underscore raises ValueError."""
        with pytest.raises(
            ValueError,
            match="name can only contain lowercase letters, hyphens, and single spaces between words",
        ):
            validate_general_text_field("cherry_tomato", "name")

    def test_period_raises_error(self):
        """Test period raises ValueError."""
        with pytest.raises(
            ValueError,
            match="name can only contain lowercase letters, hyphens, and single spaces between words",
        ):
            validate_general_text_field("tomato.variety", "name")

    def test_starting_with_hyphen_raises_error(self):
        """Test string starting with hyphen raises ValueError."""
        with pytest.raises(
            ValueError,
            match="name can only contain lowercase letters, hyphens, and single spaces between words",
        ):
            validate_general_text_field("-tomato", "name")

    def test_ending_with_hyphen_raises_error(self):
        """Test string ending with hyphen raises ValueError."""
        with pytest.raises(
            ValueError,
            match="name can only contain lowercase letters, hyphens, and single spaces between words",
        ):
            validate_general_text_field("tomato-", "name")

    def test_starting_with_space_strips_correctly(self):
        """Test string starting with space is stripped correctly."""
        result = validate_general_text_field(" tomato", "name")
        assert result == "tomato"

    def test_ending_with_space_strips_correctly(self):
        """Test string ending with space is stripped correctly."""
        result = validate_general_text_field("tomato ", "name")
        assert result == "tomato"

    def test_consecutive_hyphens_raise_error(self):
        """Test consecutive hyphens raise ValueError."""
        with pytest.raises(
            ValueError,
            match="name can only contain lowercase letters, hyphens, and single spaces between words",
        ):
            validate_general_text_field("sweet--potato", "name")

    def test_mixed_consecutive_separators_raise_error(self):
        """Test mixed consecutive separators raise ValueError."""
        with pytest.raises(
            ValueError,
            match="name can only contain lowercase letters, hyphens, and single spaces between words",
        ):
            validate_general_text_field("sweet- potato", "name")

    def test_custom_field_name_in_error(self):
        """Test that custom field name appears in error message."""
        with pytest.raises(ValueError, match="plant_name cannot be empty"):
            validate_general_text_field("", "plant_name")

    def test_unicode_characters_raise_error(self):
        """Test unicode characters raise ValueError."""
        with pytest.raises(
            ValueError,
            match="name can only contain lowercase letters, hyphens, and single spaces between words",
        ):
            validate_general_text_field("tomaté", "name")

    def test_accented_characters_raise_error(self):
        """Test accented characters raise ValueError."""
        with pytest.raises(
            ValueError,
            match="name can only contain lowercase letters, hyphens, and single spaces between words",
        ):
            validate_general_text_field("jalapeño", "name")


class TestValidateNotesField:
    """Test cases for validate_notes_field function."""

    def test_empty_string_returns_empty(self):
        """Test empty string returns empty string."""
        result = validate_notes_field("", "notes")
        assert result == ""

    def test_none_value_returns_none(self):
        """Test None value returns None."""
        result = validate_notes_field(None, "notes")
        assert result is None

    def test_valid_simple_text(self):
        """Test simple text passes through unchanged."""
        text = "This is a simple note."
        result = validate_notes_field(text, "notes")
        assert result == text

    def test_special_characters_allowed(self):
        """Test that special characters are allowed in notes."""
        text = "Note with special chars: !@#$%^&*()+={}[]|\\:;\"'<>?,./"
        result = validate_notes_field(text, "notes")
        assert result == text

    def test_numbers_allowed(self):
        """Test that numbers are allowed in notes."""
        text = "Plant 123 needs watering on day 45 at 2:30 PM."
        result = validate_notes_field(text, "notes")
        assert result == text

    def test_unicode_characters_allowed(self):
        """Test that unicode characters are allowed in notes."""
        text = "Unicode test: 🌱 植物 tomaté jalapeño"
        result = validate_notes_field(text, "notes")
        assert result == text

    def test_newlines_and_tabs_allowed(self):
        """Test that newlines and tabs are allowed in notes."""
        text = "Line 1\nLine 2\n\tIndented line"
        result = validate_notes_field(text, "notes")
        assert result == text

    def test_mixed_case_preserved(self):
        """Test that mixed case is preserved in notes."""
        text = "MixedCase Text Is Preserved"
        result = validate_notes_field(text, "notes")
        assert result == text

    def test_leading_trailing_spaces_trimmed(self):
        """Test that leading and trailing spaces are trimmed."""
        result = validate_notes_field("  Some notes  ", "notes")
        assert result == "Some notes"

    def test_internal_spaces_preserved(self):
        """Test that internal spaces are preserved."""
        text = "Multiple   internal   spaces"
        result = validate_notes_field(text, "notes")
        assert result == text

    def test_default_max_length_500(self):
        """Test that default max length is 500 characters."""
        text = "a" * 500
        result = validate_notes_field(text, "notes")
        assert result == text

    def test_exceeds_default_max_length_raises_error(self):
        """Test that exceeding default max length raises error."""
        text = "a" * 501
        # Implementation uses wording "cannot exceed" rather than "cannot be longer than"
        with pytest.raises(ValueError, match="notes cannot exceed 500 characters"):
            validate_notes_field(text, "notes")

    def test_custom_max_length(self):
        """Test custom max length parameter."""
        text = "a" * 100
        result = validate_notes_field(text, "notes", max_length=100)
        assert result == text

    def test_exceeds_custom_max_length_raises_error(self):
        """Test that exceeding custom max length raises error."""
        text = "a" * 101
        with pytest.raises(ValueError, match="notes cannot exceed 100 characters"):
            validate_notes_field(text, "notes", max_length=100)

    def test_max_length_after_trimming(self):
        """Test that max length is checked after trimming."""
        text = "  " + "a" * 500 + "  "  # 504 chars total, 500 after trimming
        result = validate_notes_field(text, "notes")
        assert result == "a" * 500

    def test_max_length_after_trimming_raises_error(self):
        """Test that max length error is raised after trimming."""
        text = "  " + "a" * 501 + "  "  # 505 chars total, 501 after trimming
        with pytest.raises(ValueError, match="notes cannot exceed 500 characters"):
            validate_notes_field(text, "notes")

    def test_custom_field_name_in_error(self):
        """Test that custom field name appears in error message."""
        text = "a" * 501
        with pytest.raises(
            ValueError, match="description cannot exceed 500 characters"
        ):
            validate_notes_field(text, "description")

    def test_whitespace_only_trimmed_to_empty(self):
        """Test that whitespace-only string is trimmed to empty."""
        result = validate_notes_field("   \n\t   ", "notes")
        assert result == ""


class TestValidateTextField:
    """Test cases for validate_text_field function (Pydantic validator wrapper)."""

    def test_valid_input_passes_through(self):
        """Test that valid input passes through unchanged."""
        result = validate_text_field("tomato", "name")
        assert result == "tomato"

    def test_invalid_input_raises_error(self):
        """Test that invalid input raises appropriate error."""
        with pytest.raises(ValueError, match="name can only contain lowercase letters"):
            validate_text_field("tomato123", "name")

    def test_normalization_works(self):
        """Test that input normalization works."""
        result = validate_text_field("TOMATO", "name")
        assert result == "tomato"

    def test_default_field_name(self):
        """Test default field name when not provided."""
        result = validate_text_field("tomato")
        assert result == "tomato"

    def test_custom_field_name(self):
        """Test custom field name in error messages."""
        with pytest.raises(
            ValueError, match="plant_name can only contain lowercase letters"
        ):
            validate_text_field("tomato!", "plant_name")

    def test_cls_parameter_unused_but_required(self):
        """Test that cls parameter is required by Pydantic but unused."""
        # Direct call without cls argument
        result = validate_text_field("tomato", "name")
        assert result == "tomato"

    def test_complex_valid_case(self):
        """Test complex valid case with multiple words and hyphens."""
        result = validate_text_field("LONG-GRAIN Brown Rice", "variety")
        assert result == "long-grain brown rice"

    def test_special_characters_error_message(self):
        """Test that special characters produce appropriate error message."""
        with pytest.raises(
            ValueError,
            match="name can only contain lowercase letters, hyphens, and single spaces between words",
        ):
            validate_text_field("tomato@variety", "name")
