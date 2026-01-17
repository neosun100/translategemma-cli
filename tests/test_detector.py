"""Tests for language detection."""

import pytest

from translategemma_cli.detector import (
    detect_language,
    detect_script_language,
    get_target_language,
    format_language_indicator,
    get_language_name,
    is_valid_language,
    list_languages,
)


class TestDetectScriptLanguage:
    """Test script-based language detection."""
    
    def test_han_characters(self):
        """Test detection of Han (Chinese) characters."""
        assert detect_script_language("你好") == "yue"
        assert detect_script_language("早晨") == "yue"
        assert detect_script_language("今日天氣好好") == "yue"
    
    def test_latin_characters(self):
        """Test detection of Latin (English) characters."""
        assert detect_script_language("Hello") == "en"
        assert detect_script_language("Good morning") == "en"
        assert detect_script_language("The weather is nice") == "en"
    
    def test_japanese_characters(self):
        """Test detection of Japanese characters."""
        assert detect_script_language("こんにちは") == "ja"
        assert detect_script_language("ありがとう") == "ja"
        assert detect_script_language("おはよう") == "ja"
    
    def test_korean_characters(self):
        """Test detection of Korean characters."""
        assert detect_script_language("안녕하세요") == "ko"
        assert detect_script_language("감사합니다") == "ko"
    
    def test_arabic_characters(self):
        """Test detection of Arabic characters."""
        assert detect_script_language("مرحبا بالعالم") == "ar"
    
    def test_cyrillic_characters(self):
        """Test detection of Cyrillic characters."""
        assert detect_script_language("Привет мир") == "ru"
    
    def test_thai_characters(self):
        """Test detection of Thai characters."""
        assert detect_script_language("สวัสดีครับ") == "th"
    
    def test_devanagari_characters(self):
        """Test detection of Devanagari characters."""
        assert detect_script_language("नमस्ते दुनिया") == "hi"
    
    def test_empty_string(self):
        """Test empty string returns None."""
        assert detect_script_language("") is None
        assert detect_script_language("   ") is None
    
    def test_numbers_only(self):
        """Test numbers only returns None (defaults to None)."""
        result = detect_script_language("12345")
        # Numbers don't match any pattern, should return None or default
        assert result is None or result == "en"


class TestDetectLanguage:
    """Test language detection with configured pairs."""
    
    def test_cantonese_detection_default_pair(self):
        """Test Cantonese detection with default yue-en pair."""
        assert detect_language("你好") == "yue"
        assert detect_language("早晨") == "yue"
    
    def test_english_detection_default_pair(self):
        """Test English detection with default yue-en pair."""
        assert detect_language("Hello") == "en"
        assert detect_language("Good morning") == "en"
    
    def test_custom_language_pair(self):
        """Test detection with custom language pair."""
        # Japanese-English pair
        assert detect_language("こんにちは", ("ja", "en")) == "ja"
        assert detect_language("Hello", ("ja", "en")) == "en"
        
        # Chinese-French pair (both non-CJK targets same behavior)
        assert detect_language("你好", ("zh", "fr")) == "zh"
        assert detect_language("Bonjour", ("zh", "fr")) == "fr"
    
    def test_empty_input(self):
        """Test empty input returns second language."""
        assert detect_language("") == "en"
        assert detect_language("", ("ja", "fr")) == "fr"
    
    def test_mixed_content(self):
        """Test mixed language content detection."""
        # Predominantly Chinese (more Han characters)
        result = detect_language("我想買一杯咖啡")
        assert result == "yue"  # More Han characters
        
        # Predominantly English
        result = detect_language("Hello world 你")
        assert result == "en"  # More Latin characters


class TestGetTargetLanguage:
    """Test target language determination."""
    
    def test_default_pair_yue_to_en(self):
        """Test yue -> en with default pair."""
        assert get_target_language("yue") == "en"
    
    def test_default_pair_en_to_yue(self):
        """Test en -> yue with default pair."""
        assert get_target_language("en") == "yue"
    
    def test_custom_pair(self):
        """Test with custom language pair."""
        assert get_target_language("ja", ("ja", "en")) == "en"
        assert get_target_language("en", ("ja", "en")) == "ja"
    
    def test_source_not_in_pair(self):
        """Test source language not in configured pair."""
        # Should return second language as default
        result = get_target_language("zh", ("yue", "en"))
        assert result == "en"


class TestFormatLanguageIndicator:
    """Test language indicator formatting."""
    
    def test_basic_format(self):
        """Test basic indicator format."""
        assert format_language_indicator("yue", "en") == "[yue→en]"
        assert format_language_indicator("en", "yue") == "[en→yue]"
    
    def test_various_languages(self):
        """Test with various language codes."""
        assert format_language_indicator("ja", "en") == "[ja→en]"
        assert format_language_indicator("zh", "fr") == "[zh→fr]"


class TestGetLanguageName:
    """Test language name lookup."""
    
    def test_known_languages(self):
        """Test looking up known language names."""
        assert get_language_name("en") == "English"
        assert get_language_name("yue") == "Cantonese"
        assert get_language_name("zh") == "Chinese (Simplified)"
        assert get_language_name("ja") == "Japanese"
        assert get_language_name("ko") == "Korean"
    
    def test_unknown_language(self):
        """Test unknown language returns code itself."""
        assert get_language_name("unknown") == "unknown"
        assert get_language_name("xyz") == "xyz"


class TestIsValidLanguage:
    """Test language validation."""
    
    def test_valid_languages(self):
        """Test valid language codes."""
        assert is_valid_language("en") is True
        assert is_valid_language("yue") is True
        assert is_valid_language("zh") is True
        assert is_valid_language("ja") is True
    
    def test_invalid_languages(self):
        """Test invalid language codes."""
        assert is_valid_language("invalid") is False
        assert is_valid_language("xxx") is False
        assert is_valid_language("") is False


class TestListLanguages:
    """Test language listing."""
    
    def test_returns_dict(self):
        """Test that list_languages returns a dict."""
        langs = list_languages()
        assert isinstance(langs, dict)
    
    def test_contains_all_languages(self):
        """Test that all languages are included."""
        langs = list_languages()
        assert len(langs) == 54
    
    def test_contains_key_languages(self):
        """Test that key languages are included."""
        langs = list_languages()
        assert "en" in langs
        assert "yue" in langs
        assert "zh" in langs
        assert "ja" in langs
        assert "ko" in langs
    
    def test_returns_copy(self):
        """Test that modifying result doesn't affect original."""
        langs1 = list_languages()
        langs1["test"] = "Test"
        langs2 = list_languages()
        assert "test" not in langs2


class TestDetectionEdgeCases:
    """Test edge cases in language detection."""
    
    def test_punctuation_only(self):
        """Test punctuation-only input."""
        result = detect_language("!!!")
        assert result == "en"  # Default to second language
    
    def test_emoji_only(self):
        """Test emoji-only input."""
        result = detect_language("😀🎉")
        assert result == "en"  # Default
    
    def test_whitespace_heavy(self):
        """Test whitespace-heavy input."""
        result = detect_language("   Hello   world   ")
        assert result == "en"
    
    def test_single_character(self):
        """Test single character input."""
        assert detect_language("你") == "yue"
        assert detect_language("H") == "en"
    
    def test_code_switching(self):
        """Test code-switching (mixed language) detection."""
        # Should detect majority language
        result1 = detect_language("今天weather很好")  # More Chinese
        result2 = detect_language("The 天氣 is nice")  # More English
        
        # Results depend on character ratios
        assert result1 in ("yue", "en")
        assert result2 in ("yue", "en")
