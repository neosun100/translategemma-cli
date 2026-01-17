"""Tests for CLI commands."""

from unittest.mock import MagicMock, patch
import pytest

from typer.testing import CliRunner

from translategemma_cli.cli import app
from translategemma_cli.config import MODEL_SIZES


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


class TestCliHelp:
    """Test CLI help commands."""
    
    def test_main_help(self, runner):
        """Test main help command."""
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "TranslateGemma" in result.stdout
        assert "--to" in result.stdout
        assert "--model" in result.stdout
    
    def test_model_help(self, runner):
        """Test model subcommand help."""
        result = runner.invoke(app, ["model", "--help"])
        
        assert result.exit_code == 0
        assert "Manage" in result.stdout
    
    def test_text_help(self, runner):
        """Test text subcommand help."""
        result = runner.invoke(app, ["text", "--help"])
        
        assert result.exit_code == 0
        assert "Translate text" in result.stdout


class TestModelCommand:
    """Test model management commands."""
    
    def test_model_list(self, runner, mock_config):
        """Test model list command."""
        result = runner.invoke(app, ["model", "list"])
        
        assert result.exit_code == 0
        assert "TranslateGemma Models" in result.stdout
        assert "4b" in result.stdout
        assert "12b" in result.stdout
        assert "27b" in result.stdout
    
    def test_model_status_default(self, runner, mock_config):
        """Test model status for default model."""
        result = runner.invoke(app, ["model", "status"])
        
        assert result.exit_code == 0
        assert "27b" in result.stdout
        assert "google/translategemma-27b-it" in result.stdout
    
    def test_model_status_specific(self, runner, mock_config):
        """Test model status for specific model."""
        result = runner.invoke(app, ["model", "status", "4b"])
        
        assert result.exit_code == 0
        assert "4b" in result.stdout
        assert "google/translategemma-4b-it" in result.stdout
    
    def test_model_langs(self, runner, mock_config):
        """Test model langs command."""
        result = runner.invoke(app, ["model", "langs"])
        
        assert result.exit_code == 0
        assert "Supported Languages" in result.stdout
        assert "English" in result.stdout
        assert "Cantonese" in result.stdout
    
    def test_model_download_no_size(self, runner, mock_config):
        """Test model download without size."""
        result = runner.invoke(app, ["model", "download"])
        
        assert result.exit_code == 1
        assert "specify model size" in result.stdout.lower()
    
    def test_model_download_invalid_size(self, runner, mock_config):
        """Test model download with invalid size."""
        result = runner.invoke(app, ["model", "download", "invalid"])
        
        assert result.exit_code == 1
        assert "Invalid model size" in result.stdout
    
    def test_model_remove_no_size(self, runner, mock_config):
        """Test model remove without size."""
        result = runner.invoke(app, ["model", "remove"])
        
        assert result.exit_code == 1
        assert "specify model size" in result.stdout.lower()
    
    def test_model_remove_not_found(self, runner, mock_config):
        """Test model remove when not downloaded."""
        result = runner.invoke(app, ["model", "remove", "4b"])
        
        assert result.exit_code == 0
        assert "not found" in result.stdout.lower()
    
    def test_model_invalid_action(self, runner, mock_config):
        """Test model command with invalid action."""
        result = runner.invoke(app, ["model", "invalid"])
        
        assert result.exit_code == 1
        assert "Unknown action" in result.stdout


class TestMainOptions:
    """Test main command options."""
    
    def test_invalid_to_language(self, runner, mock_config):
        """Test --to with invalid language."""
        result = runner.invoke(app, ["--to", "invalid", "--text", "Hello"])
        
        assert result.exit_code == 1
        assert "Invalid target language" in result.stdout
    
    def test_invalid_model_size(self, runner, mock_config):
        """Test --model with invalid size."""
        result = runner.invoke(app, ["--model", "invalid", "--text", "Hello"])
        
        assert result.exit_code == 1
        assert "Invalid model size" in result.stdout
    
    def test_file_not_found(self, runner, mock_config):
        """Test --file with non-existent file."""
        result = runner.invoke(app, ["--file", "/nonexistent/file.txt"])
        
        assert result.exit_code == 1
        assert "File not found" in result.stdout


class TestTextCommand:
    """Test text translation command."""
    
    def test_text_invalid_to(self, runner, mock_config):
        """Test text command with invalid --to."""
        result = runner.invoke(app, ["text", "--to", "invalid", "Hello"])
        
        assert result.exit_code == 1
        assert "Invalid target language" in result.stdout
    
    def test_text_invalid_model(self, runner, mock_config):
        """Test text command with invalid --model."""
        result = runner.invoke(app, ["text", "--model", "invalid", "Hello"])
        
        assert result.exit_code == 1
        assert "Invalid model size" in result.stdout


class TestTranslationFlow:
    """Test actual translation flow (mocked)."""
    
    @patch("translategemma_cli.cli.is_model_ready", return_value=True)
    @patch("translategemma_cli.cli.get_translator")
    def test_single_shot_translation(
        self, mock_get_translator, mock_ready, runner, mock_config
    ):
        """Test single-shot translation."""
        mock_translator = MagicMock()
        mock_translator.translate.return_value = ("你好", "en", "yue")
        mock_get_translator.return_value = mock_translator
        
        result = runner.invoke(app, ["--text", "Hello"])
        
        assert result.exit_code == 0
        mock_translator.translate.assert_called()
    
    @patch("translategemma_cli.cli.is_model_ready", return_value=True)
    @patch("translategemma_cli.cli.get_translator")
    def test_translation_with_target(
        self, mock_get_translator, mock_ready, runner, mock_config
    ):
        """Test translation with target language."""
        mock_translator = MagicMock()
        mock_translator.translate.return_value = ("こんにちは", "en", "ja")
        mock_get_translator.return_value = mock_translator
        
        result = runner.invoke(app, ["--to", "ja", "--text", "Hello"])
        
        assert result.exit_code == 0
    
    @patch("translategemma_cli.cli.is_model_ready", return_value=True)
    @patch("translategemma_cli.cli.get_translator")
    def test_translation_explain_mode(
        self, mock_get_translator, mock_ready, runner, mock_config
    ):
        """Test translation with explain mode."""
        mock_translator = MagicMock()
        mock_translator.translate.return_value = ("你好\nExplanation...", "en", "yue")
        mock_get_translator.return_value = mock_translator
        
        result = runner.invoke(app, ["--explain", "--text", "Hello"])
        
        assert result.exit_code == 0
    
    @patch("translategemma_cli.cli.is_model_ready", return_value=True)
    @patch("translategemma_cli.cli.get_translator")
    def test_text_subcommand_translation(
        self, mock_get_translator, mock_ready, runner, mock_config
    ):
        """Test text subcommand translation."""
        mock_translator = MagicMock()
        mock_translator.translate.return_value = ("你好", "en", "yue")
        mock_get_translator.return_value = mock_translator
        
        result = runner.invoke(app, ["text", "Hello"])
        
        assert result.exit_code == 0


class TestFileTranslation:
    """Test file-based translation."""
    
    @patch("translategemma_cli.cli.is_model_ready", return_value=True)
    @patch("translategemma_cli.cli.get_translator")
    def test_file_input(
        self, mock_get_translator, mock_ready, runner, mock_config, tmp_path
    ):
        """Test translation from file input."""
        mock_translator = MagicMock()
        mock_translator.translate.return_value = ("你好", "en", "yue")
        mock_get_translator.return_value = mock_translator
        
        # Create input file
        input_file = tmp_path / "input.txt"
        input_file.write_text("Hello world")
        
        result = runner.invoke(app, ["--file", str(input_file)])
        
        assert result.exit_code == 0
    
    @patch("translategemma_cli.cli.is_model_ready", return_value=True)
    @patch("translategemma_cli.cli.get_translator")
    def test_file_output(
        self, mock_get_translator, mock_ready, runner, mock_config, tmp_path
    ):
        """Test translation to file output."""
        mock_translator = MagicMock()
        mock_translator.translate.return_value = ("你好", "en", "yue")
        mock_get_translator.return_value = mock_translator
        
        # Create input file
        input_file = tmp_path / "input.txt"
        input_file.write_text("Hello")
        
        output_file = tmp_path / "output.txt"
        
        result = runner.invoke(app, [
            "--file", str(input_file),
            "--output", str(output_file)
        ])
        
        assert result.exit_code == 0
        assert "written to" in result.stdout


class TestInteractiveCommands:
    """Test interactive command handling."""
    
    def test_handle_quit_command(self, mock_config):
        """Test /quit command handling."""
        from translategemma_cli.cli import handle_command
        
        translator = MagicMock()
        
        result = handle_command("/quit", translator)
        assert result is False  # Should exit
    
    def test_handle_exit_command(self, mock_config):
        """Test /exit command handling."""
        from translategemma_cli.cli import handle_command
        
        translator = MagicMock()
        
        result = handle_command("/exit", translator)
        assert result is False
    
    def test_handle_help_command(self, mock_config):
        """Test /help command handling."""
        from translategemma_cli.cli import handle_command
        
        translator = MagicMock()
        
        result = handle_command("/help", translator)
        assert result is True  # Should continue
    
    def test_handle_to_command_valid(self, mock_config):
        """Test /to command with valid language."""
        from translategemma_cli.cli import handle_command
        
        translator = MagicMock()
        
        result = handle_command("/to en", translator)
        
        assert result is True
        translator.set_force_target.assert_called_with("en")
    
    def test_handle_to_command_invalid(self, mock_config):
        """Test /to command with invalid language."""
        from translategemma_cli.cli import handle_command
        
        translator = MagicMock()
        
        result = handle_command("/to invalid", translator)
        
        assert result is True
        translator.set_force_target.assert_not_called()
    
    def test_handle_auto_command(self, mock_config):
        """Test /auto command handling."""
        from translategemma_cli.cli import handle_command
        
        translator = MagicMock()
        
        result = handle_command("/auto", translator)
        
        assert result is True
        translator.set_force_target.assert_called_with(None)
    
    def test_handle_mode_direct(self, mock_config):
        """Test /mode direct command."""
        from translategemma_cli.cli import handle_command
        
        translator = MagicMock()
        
        result = handle_command("/mode direct", translator)
        
        assert result is True
        translator.set_output_mode.assert_called_with("direct")
    
    def test_handle_mode_explain(self, mock_config):
        """Test /mode explain command."""
        from translategemma_cli.cli import handle_command
        
        translator = MagicMock()
        
        result = handle_command("/mode explain", translator)
        
        assert result is True
        translator.set_output_mode.assert_called_with("explain")
    
    def test_handle_mode_invalid(self, mock_config):
        """Test /mode with invalid mode."""
        from translategemma_cli.cli import handle_command
        
        translator = MagicMock()
        
        result = handle_command("/mode invalid", translator)
        
        assert result is True
        translator.set_output_mode.assert_not_called()
    
    def test_handle_langs_command(self, mock_config):
        """Test /langs command."""
        from translategemma_cli.cli import handle_command
        
        translator = MagicMock()
        
        result = handle_command("/langs", translator)
        assert result is True
    
    def test_handle_model_command_info(self, mock_config):
        """Test /model command (info)."""
        from translategemma_cli.cli import handle_command
        
        translator = MagicMock()
        
        result = handle_command("/model", translator)
        assert result is True
    
    def test_handle_config_command(self, mock_config):
        """Test /config command."""
        from translategemma_cli.cli import handle_command
        
        translator = MagicMock()
        translator.get_output_mode.return_value = "direct"
        translator.get_force_target.return_value = None
        
        result = handle_command("/config", translator)
        assert result is True
    
    def test_handle_unknown_command(self, mock_config):
        """Test unknown command handling."""
        from translategemma_cli.cli import handle_command
        
        translator = MagicMock()
        
        result = handle_command("/unknown", translator)
        assert result is True  # Should continue, just show error


class TestPrintFunctions:
    """Test output printing functions."""
    
    def test_print_languages(self, mock_config, capsys):
        """Test print_languages function."""
        from translategemma_cli.cli import print_languages
        
        # This should not raise
        print_languages()
    
    def test_print_help(self, mock_config, capsys):
        """Test print_help function."""
        from translategemma_cli.cli import print_help
        
        # This should not raise
        print_help()
    
    def test_print_config(self, mock_config, capsys):
        """Test print_config function."""
        from translategemma_cli.cli import print_config
        
        # Reset translator for clean state
        from translategemma_cli.translator import reset_translator
        reset_translator()
        
        # This should not raise
        print_config()
