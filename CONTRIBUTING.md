# Contributing to TranslateGemma CLI

Thank you for your interest in contributing to TranslateGemma CLI!

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/jhkchan/translategemma-cli.git
   cd translategemma-cli
   ```

3. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Option A: Using pip extras
   pip install -e ".[dev,mlx]"  # or [dev,cuda] or [dev,cpu]
   
   # Option B: Using requirements files
   pip install -r requirements-dev.txt
   pip install -r requirements-mlx.txt  # or requirements-cuda.txt or requirements-cpu.txt
   pip install -e .
   ```

4. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=translategemma_cli

# Run specific test file
pytest tests/test_detector.py -v
```

### Code Style

We use `black` for formatting and `ruff` for linting:

```bash
# Format code
black translategemma_cli tests

# Lint code
ruff check translategemma_cli tests
```

### Project Structure

```
translategemma-cli/
├── translategemma_cli/     # Main package
│   ├── __init__.py
│   ├── cli.py              # CLI commands
│   ├── config.py           # Configuration management
│   ├── detector.py         # Language detection
│   ├── model.py            # Model management
│   └── translator.py       # Translation engine
├── tests/                  # Test suite
├── docs/                   # Documentation
├── pyproject.toml          # Project configuration
├── requirements.txt        # Dependencies
└── README.md
```

## Making Changes

1. Make your changes in your feature branch
2. Add tests for any new functionality
3. Ensure all tests pass: `pytest`
4. Format your code: `black translategemma_cli tests`
5. Commit your changes with a clear message

## Submitting a Pull Request

1. Push your changes to your fork
2. Create a Pull Request against the `main` branch
3. Describe your changes clearly in the PR description
4. Link any related issues

## Reporting Issues

When reporting issues, please include:

- Operating system and version
- Python version
- Steps to reproduce the issue
- Expected vs actual behavior
- Any relevant error messages or logs

## Code of Conduct

Please be respectful and constructive in all interactions. We're all here to build something useful together.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
