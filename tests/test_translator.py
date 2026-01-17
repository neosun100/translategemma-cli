"""Tests for translation engine."""

from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from translategemma_cli.translator import (
    Translator,
    get_translator,
    reset_translator,
    LANG_CODE_MAP,
)


class TestLangCodeMap:
    """Test language code mapping."""
    
    def test_cantonese_mapping(self):
        """Test Cantonese is mapped to zh-Hant-HK."""
        assert LANG_CODE_MAP["yue"] == "zh-Hant-HK"
    
    def test_traditional_chinese_mapping(self):
        """Test Traditional Chinese mapping."""
        assert LANG_CODE_MAP["zh-TW"] == "zh-Hant"
    
    def test_unmapped_languages_pass_through(self):
        """Test that unmapped languages use their original code."""
        translator = Translator()
        assert translator._map_lang_code("en") == "en"
        assert translator._map_lang_code("ja") == "ja"
        assert translator._map_lang_code("fr") == "fr"


class TestTranslator:
    """Test Translator class."""
    
    def test_initial_state(self):
        """Test translator initial state."""
        translator = Translator()
        
        assert translator.is_loaded is False
        assert translator.current_model_size is None
        assert translator.backend is None
        assert translator.get_force_target() is None
        assert translator.get_output_mode() == "direct"
    
    def test_set_force_target_valid(self):
        """Test setting valid force target."""
        translator = Translator()
        
        translator.set_force_target("en")
        assert translator.get_force_target() == "en"
        
        translator.set_force_target("ja")
        assert translator.get_force_target() == "ja"
    
    def test_set_force_target_none(self):
        """Test clearing force target."""
        translator = Translator()
        
        translator.set_force_target("en")
        translator.set_force_target(None)
        assert translator.get_force_target() is None
    
    def test_set_force_target_invalid(self):
        """Test setting invalid force target raises error."""
        translator = Translator()
        
        with pytest.raises(ValueError, match="Unsupported language"):
            translator.set_force_target("invalid_lang")
    
    def test_set_output_mode_direct(self):
        """Test setting direct output mode."""
        translator = Translator()
        
        translator.set_output_mode("direct")
        assert translator.get_output_mode() == "direct"
    
    def test_set_output_mode_explain(self):
        """Test setting explain output mode."""
        translator = Translator()
        
        translator.set_output_mode("explain")
        assert translator.get_output_mode() == "explain"
    
    def test_set_output_mode_invalid(self):
        """Test setting invalid output mode raises error."""
        translator = Translator()
        
        with pytest.raises(ValueError, match="Mode must be"):
            translator.set_output_mode("invalid")


class TestTranslatorFormatMessages:
    """Test message formatting."""
    
    def test_format_basic_message(self):
        """Test basic message formatting."""
        translator = Translator()
        
        messages = translator._format_messages("Hello", "en", "yue")
        
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"][0]["type"] == "text"
        assert messages[0]["content"][0]["text"] == "Hello"
        assert messages[0]["content"][0]["source_lang_code"] == "en"
        assert messages[0]["content"][0]["target_lang_code"] == "zh-Hant-HK"  # Mapped
    
    def test_format_with_cantonese_source(self):
        """Test formatting with Cantonese as source."""
        translator = Translator()
        
        messages = translator._format_messages("你好", "yue", "en")
        
        assert messages[0]["content"][0]["source_lang_code"] == "zh-Hant-HK"
        assert messages[0]["content"][0]["target_lang_code"] == "en"
    
    def test_format_with_unmapped_languages(self):
        """Test formatting with languages not in map."""
        translator = Translator()
        
        messages = translator._format_messages("Bonjour", "fr", "de")
        
        assert messages[0]["content"][0]["source_lang_code"] == "fr"
        assert messages[0]["content"][0]["target_lang_code"] == "de"


class TestTranslatorCleanResponse:
    """Test response cleaning."""
    
    def test_clean_special_tokens(self):
        """Test cleaning special tokens."""
        translator = Translator()
        
        text = "Hello<end_of_turn><eos>"
        result = translator._clean_special_tokens(text)
        
        assert "<end_of_turn>" not in result
        assert "<eos>" not in result
        assert "Hello" in result
    
    def test_clean_response_removes_explanations(self):
        """Test cleaning removes explanation text."""
        translator = Translator()
        
        text = """Hello
This phrase is a common greeting.
Note: In formal contexts, use "Good morning"."""
        
        result = translator._clean_response(text)
        
        assert result == "Hello"
        assert "This phrase" not in result
        assert "Note:" not in result
    
    def test_clean_response_removes_quotes(self):
        """Test cleaning removes surrounding quotes."""
        translator = Translator()
        
        # Straight quotes
        assert translator._clean_response('"Hello world"') == "Hello world"
        assert translator._clean_response("'Hello world'") == "Hello world"
        
        # CJK brackets
        assert translator._clean_response("「你好」") == "你好"
    
    def test_clean_response_removes_parenthetical(self):
        """Test cleaning removes parenthetical explanations."""
        translator = Translator()
        
        text = "你好 (Hello)"
        result = translator._clean_response(text)
        
        assert result == "你好"
        assert "(Hello)" not in result
    
    def test_clean_response_removes_bold(self):
        """Test cleaning removes markdown bold."""
        translator = Translator()
        
        text = "**Hello world**"
        result = translator._clean_response(text)
        
        assert "**" not in result
        assert "Hello world" in result
    
    def test_clean_response_empty_input(self):
        """Test cleaning empty input."""
        translator = Translator()
        
        assert translator._clean_response("") == ""
        assert translator._clean_response("   ") == ""
    
    def test_clean_response_given_context(self):
        """Test cleaning responses that start with 'Given the'."""
        translator = Translator()
        
        # Response with quoted translation
        text = 'Given the lack of context, the translation would be: "Hello"'
        result = translator._clean_response(text)
        assert result == "Hello"
    
    def test_clean_response_refusal_with_quote(self):
        """Test extracting translation from refusal response."""
        translator = Translator()
        
        text = 'This term is vulgar. A neutral translation would be "darn" or "damn".'
        result = translator._clean_response(text)
        assert "darn" in result or "damn" in result
    
    def test_clean_response_meta_commentary(self):
        """Test skipping meta-commentary in parentheses/brackets."""
        translator = Translator()
        
        text = "Hello world\n(This is a greeting)\n[Note: informal]"
        result = translator._clean_response(text)
        assert result == "Hello world"


class TestTranslatorTranslate:
    """Test translation functionality (mocked)."""
    
    @patch("translategemma_cli.translator.load_model")
    def test_translate_basic(self, mock_load, mock_config, mock_model, mock_tokenizer):
        """Test basic translation flow."""
        mock_load.return_value = (mock_model, mock_tokenizer, "mlx")
        
        translator = Translator()
        translator._model = mock_model
        translator._tokenizer = mock_tokenizer
        translator._backend = "mlx"
        translator._current_model_size = "27b"
        
        # Mock MLX generate
        with patch("translategemma_cli.translator.Translator._generate_mlx") as mock_gen:
            mock_gen.return_value = "Hello world"
            
            result, source, target = translator.translate("你好")
            
            assert result == "Hello world"
            assert source == "yue"
            assert target == "en"
    
    @patch("translategemma_cli.translator.load_model")
    def test_translate_with_force_target(
        self, mock_load, mock_config, mock_model, mock_tokenizer
    ):
        """Test translation with forced target language."""
        mock_load.return_value = (mock_model, mock_tokenizer, "mlx")
        
        translator = Translator()
        translator._model = mock_model
        translator._tokenizer = mock_tokenizer
        translator._backend = "mlx"
        translator._current_model_size = "27b"
        translator.set_force_target("ja")
        
        with patch("translategemma_cli.translator.Translator._generate_mlx") as mock_gen:
            mock_gen.return_value = "こんにちは"
            
            result, source, target = translator.translate("Hello")
            
            assert target == "ja"
    
    @patch("translategemma_cli.translator.load_model")
    def test_translate_direct_mode(
        self, mock_load, mock_config, mock_model, mock_tokenizer
    ):
        """Test translation in direct mode cleans response."""
        mock_load.return_value = (mock_model, mock_tokenizer, "mlx")
        
        translator = Translator()
        translator._model = mock_model
        translator._tokenizer = mock_tokenizer
        translator._backend = "mlx"
        translator._current_model_size = "27b"
        translator.set_output_mode("direct")
        
        with patch("translategemma_cli.translator.Translator._generate_mlx") as mock_gen:
            mock_gen.return_value = '"Hello world"\nThis is a greeting.'
            
            result, _, _ = translator.translate("你好")
            
            # Direct mode should clean the response
            assert result == "Hello world"
    
    @patch("translategemma_cli.translator.load_model")
    def test_translate_explain_mode(
        self, mock_load, mock_config, mock_model, mock_tokenizer
    ):
        """Test translation in explain mode preserves explanation."""
        mock_load.return_value = (mock_model, mock_tokenizer, "mlx")
        
        translator = Translator()
        translator._model = mock_model
        translator._tokenizer = mock_tokenizer
        translator._backend = "mlx"
        translator._current_model_size = "27b"
        translator.set_output_mode("explain")
        
        with patch("translategemma_cli.translator.Translator._generate_mlx") as mock_gen:
            mock_gen.return_value = "Hello world\nThis is a greeting."
            
            result, _, _ = translator.translate("你好", mode="explain")
            
            # Explain mode should keep most content
            assert "Hello world" in result


class TestTranslatorModelLoading:
    """Test model loading behavior."""
    
    @patch("translategemma_cli.translator.load_model")
    def test_ensure_model_loaded_first_time(
        self, mock_load, mock_config, mock_model, mock_tokenizer
    ):
        """Test first-time model loading."""
        mock_load.return_value = (mock_model, mock_tokenizer, "mlx")
        
        translator = Translator()
        translator.ensure_model_loaded()
        
        mock_load.assert_called_once()
        assert translator.is_loaded is True
    
    @patch("translategemma_cli.translator.load_model")
    def test_ensure_model_loaded_no_reload(
        self, mock_load, mock_config, mock_model, mock_tokenizer
    ):
        """Test model not reloaded if already loaded."""
        mock_load.return_value = (mock_model, mock_tokenizer, "pytorch")
        
        translator = Translator()
        # Mock _resolve_backend to return consistent value
        translator._resolve_backend = lambda x: "pytorch"
        translator.ensure_model_loaded()
        translator.ensure_model_loaded()
        
        # Should only be called once
        mock_load.assert_called_once()
    
    @patch("translategemma_cli.translator.load_model")
    def test_ensure_model_loaded_switch_model(
        self, mock_load, mock_config, mock_model, mock_tokenizer
    ):
        """Test model switching loads new model."""
        mock_load.return_value = (mock_model, mock_tokenizer, "mlx")
        
        translator = Translator()
        translator.ensure_model_loaded("27b")
        translator.ensure_model_loaded("4b")
        
        # Should be called twice for different sizes
        assert mock_load.call_count == 2


class TestGlobalTranslator:
    """Test global translator functions."""
    
    def test_get_translator_singleton(self):
        """Test get_translator returns same instance."""
        reset_translator()
        
        t1 = get_translator()
        t2 = get_translator()
        
        assert t1 is t2
    
    def test_reset_translator(self):
        """Test reset creates new instance."""
        t1 = get_translator()
        reset_translator()
        t2 = get_translator()
        
        assert t1 is not t2


class TestTranslatorStream:
    """Test streaming translation (mocked)."""
    
    @patch("translategemma_cli.translator.load_model")
    def test_translate_stream_mlx(
        self, mock_load, mock_config, mock_model, mock_tokenizer
    ):
        """Test streaming translation with MLX backend."""
        mock_load.return_value = (mock_model, mock_tokenizer, "mlx")
        
        translator = Translator()
        translator._model = mock_model
        translator._tokenizer = mock_tokenizer
        translator._backend = "mlx"
        translator._current_model_size = "27b"
        
        with patch(
            "translategemma_cli.translator.Translator._stream_mlx"
        ) as mock_stream:
            mock_stream.return_value = iter([
                ("Hello", "yue", "en"),
                (" world", "yue", "en"),
            ])
            
            tokens = list(translator.translate_stream("你好"))
            
            assert len(tokens) == 2
            assert tokens[0][0] == "Hello"
            assert tokens[1][0] == " world"
