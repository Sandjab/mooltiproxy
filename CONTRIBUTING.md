# Contributing to Mooltiproxy

Thank you for your interest in contributing to Mooltiproxy! This document provides guidelines and instructions for contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Code Style](#code-style)
5. [Testing](#testing)
6. [Submitting Changes](#submitting-changes)
7. [Adding Features](#adding-features)

---

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards other contributors

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Basic understanding of HTTP proxies and APIs

### Finding Issues

- Check the [issue tracker](https://github.com/Sandjab/mooltiproxy/issues)
- Look for issues labeled `good first issue` or `help wanted`
- Comment on an issue to indicate you're working on it

---

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR-USERNAME/mooltiproxy.git
cd mooltiproxy
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Production dependencies
pip install -r requirements.txt

# Development dependencies (if available)
pip install pytest pytest-cov mypy black flake8 isort
```

### 4. Configure for Testing

```bash
# Copy template config
cp config_template.yaml config.yaml

# Set master key
export MOOLTIPROXY_KEY="test_key_for_development"

# Edit config.yaml as needed for testing
```

### 5. Verify Setup

```bash
# Run the proxy
python -m main

# In another terminal, test:
curl -H "Authorization: Bearer test_key_for_development" http://localhost:8000/
```

---

## Code Style

### Python Style Guide

We follow PEP 8 with some modifications:

**Line Length:**
- Maximum 100 characters (not 79)

**Formatting:**
- Use Black for auto-formatting: `black .`
- Use isort for import sorting: `isort .`

**Naming Conventions:**
```python
# Functions and variables: snake_case
def calculate_total():
    user_name = "Alice"

# Classes: PascalCase
class ProxyHandler:
    pass

# Constants: UPPER_SNAKE_CASE
DEFAULT_TIMEOUT = 30
SERVER_VERSION = "1.0"

# Private/internal: _leading_underscore
def _internal_helper():
    pass
```

**Type Hints:**
```python
from typing import Dict, List, Optional, Any

def process_request(
    payload: Dict[str, Any],
    config: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Always include type hints for function signatures"""
    pass
```

**Docstrings:**
```python
def my_function(param1: str, param2: int) -> bool:
    """
    Short description of function.

    Longer description if needed, explaining the purpose,
    behavior, and any important details.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param2 is negative
    """
    pass
```

### Comments

```python
# Good: Explain WHY, not WHAT
# Use exponential backoff to avoid overwhelming the backend
retry_delay *= 2

# Bad: Obvious comment
# Increment counter
counter += 1

# Good: Complex logic explanation
# The temperature must be > 0 for TGI, but OpenAI allows 0.
# We convert 0 to a small positive value to maintain compatibility.
if temperature <= 0:
    temperature = 0.01
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_mappers.py -v

# Run specific test
pytest tests/test_mappers.py::test_temperature_zero_handled -v
```

### Writing Tests

**Test File Structure:**
```
tests/
├── __init__.py
├── test_mappers.py
├── test_prompters.py
├── test_cerbere.py
└── fixtures/
    └── test_data.yaml
```

**Test Example:**
```python
import pytest
from mappers import textReqOpenAItoTGI

def test_basic_mapping():
    """Test basic OpenAI to TGI request mapping"""
    input_payload = {
        "prompt": "Hello",
        "max_tokens": 50,
        "temperature": 0.7
    }

    result = textReqOpenAItoTGI(input_payload, {})

    assert result["inputs"] == "Hello"
    assert result["parameters"]["max_new_tokens"] == 50
    assert result["parameters"]["temperature"] == 0.7

def test_edge_case_zero_temperature():
    """Test that temperature=0 is converted to 0.01"""
    input_payload = {"prompt": "Test", "temperature": 0}
    result = textReqOpenAItoTGI(input_payload, {})
    assert result["parameters"]["temperature"] == 0.01

@pytest.mark.parametrize("temp,expected", [
    (0, 0.01),
    (-0.5, 0.01),
    (0.5, 0.5),
    (1.0, 1.0),
])
def test_temperature_normalization(temp, expected):
    """Test various temperature values"""
    input_payload = {"prompt": "Test", "temperature": temp}
    result = textReqOpenAItoTGI(input_payload, {})
    assert result["parameters"]["temperature"] == expected
```

### Test Coverage Requirements

- Aim for 80%+ code coverage
- All new features must include tests
- Bug fixes should include regression tests

---

## Submitting Changes

### Branch Naming

```bash
# Feature branches
git checkout -b feature/add-streaming-support

# Bug fixes
git checkout -b fix/handle-empty-messages

# Documentation
git checkout -b docs/update-readme
```

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
type(scope): short description

Longer description if needed, explaining:
- Why this change was needed
- What problem it solves
- Any side effects or implications

Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```bash
feat(mappers): add support for Claude API translation

fix(cerbere): correct class attribute initialization
Fixes instance sharing bug where all Cerbere instances
shared the same blacklist.

Fixes #45

docs(readme): add Docker deployment instructions

test(prompters): add tests for llama2_chat edge cases
```

### Pull Request Process

1. **Before submitting:**
   ```bash
   # Run tests
   pytest tests/ -v

   # Check code style
   black --check .
   isort --check .
   flake8 .

   # Fix any issues
   black .
   isort .
   ```

2. **Create Pull Request:**
   - Use a clear, descriptive title
   - Reference related issues
   - Describe what changed and why
   - Include screenshots for UI changes
   - List any breaking changes

3. **PR Template:**
   ```markdown
   ## Description
   Brief description of changes

   ## Related Issues
   Fixes #123
   Related to #456

   ## Changes
   - Added X feature
   - Fixed Y bug
   - Updated Z documentation

   ## Testing
   - [ ] All tests pass
   - [ ] Added new tests for changes
   - [ ] Manually tested with [describe scenario]

   ## Breaking Changes
   - None / List any breaking changes

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] CHANGELOG.md updated
   ```

4. **Review Process:**
   - Wait for review from maintainers
   - Address feedback promptly
   - Keep discussions professional and focused

---

## Adding Features

### Adding a New Mapper

**1. Create the mapper function in `mappers.py`:**

```python
def customReqSourceToTarget(ip: Any, cfg: dict = {}) -> Any:
    """
    Convert SourceAPI request format to TargetAPI format.

    Args:
        ip: Input payload from SourceAPI
        cfg: Endpoint configuration from config.yaml

    Returns:
        Transformed payload for TargetAPI

    Raises:
        ValueError: If required fields are missing
    """
    # Validate input
    if not isinstance(ip, dict):
        raise ValueError("Input must be a dictionary")

    # Transform payload
    output = {
        "target_field": ip.get("source_field", "default_value"),
        # ... more mappings
    }

    return output

def customAnsTargetToSource(ip: Any, cfg: dict = {}) -> Any:
    """
    Convert TargetAPI response to SourceAPI format.

    Args:
        ip: Response from TargetAPI
        cfg: Endpoint configuration

    Returns:
        Transformed response for SourceAPI
    """
    # Transform response
    return output
```

**2. Add tests in `tests/test_mappers.py`:**

```python
def test_custom_request_mapper():
    input_payload = {"source_field": "value"}
    result = customReqSourceToTarget(input_payload, {})
    assert result["target_field"] == "value"

def test_custom_request_mapper_missing_field():
    result = customReqSourceToTarget({}, {})
    assert result["target_field"] == "default_value"
```

**3. Update configuration:**

```yaml
targets:
  my_target:
    url: https://api.example.com
    mapping:
      /my/endpoint:
        in: customReqSourceToTarget
        out: customAnsTargetToSource
```

**4. Document in CHANGELOG.md:**

```markdown
### Added
- New mapper for SourceAPI to TargetAPI translation
```

### Adding a New Prompter

**1. Create prompter in `prompters.py`:**

```python
def custom_prompter(
    messages: List[Dict[str, str]],
    cfg: Dict[str, Any]
) -> Tuple[str, List[str]]:
    """
    Format messages for CustomModel.

    Args:
        messages: List of message dicts with 'role' and 'content'
        cfg: Endpoint configuration

    Returns:
        Tuple of (formatted_prompt, stop_sequences)
    """
    prompt = ""
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        prompt += f"<{role}>{content}</{role}>\n"

    stop_sequences = ["</assistant>"]
    return prompt, stop_sequences
```

**2. Add tests and documentation as above**

---

## Additional Guidelines

### Security

- Never commit API keys or secrets
- Use environment variables for sensitive data
- Report security issues privately to maintainers
- Review security implications of changes

### Performance

- Profile code for performance-critical paths
- Avoid unnecessary computations
- Consider memory usage for large payloads
- Document performance characteristics

### Documentation

- Update README.md for user-facing changes
- Update ARCHITECTURE.md for design changes
- Add inline comments for complex logic
- Keep CHANGELOG.md up to date

### Dependencies

- Minimize new dependencies
- Justify any new dependency additions
- Pin versions in requirements.txt
- Check license compatibility

---

## Getting Help

- Check existing documentation
- Search existing issues
- Ask questions in issue comments
- Contact maintainers: [provide contact method]

---

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Git commit history

Thank you for contributing to Mooltiproxy! 🎉

---

*This document is based on best practices from open source projects.*
*Last updated: 2025-11-22*
