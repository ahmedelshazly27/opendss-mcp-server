# Contributing to OpenDSS MCP Server

Thank you for your interest in contributing to OpenDSS MCP Server! We welcome contributions from the community.

## Code of Conduct

This project follows the standard open source code of conduct. Please be respectful and constructive in all interactions.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/ahmedelshazly27/opendss-mcp-server/issues)
2. If not, create a new issue using the **Bug Report** template
3. Provide as much detail as possible:
   - Version of opendss-mcp-server
   - Python version
   - Operating system
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages/logs

### Suggesting Features

1. Check [Issues](https://github.com/ahmedelshazly27/opendss-mcp-server/issues) and [Discussions](https://github.com/ahmedelshazly27/opendss-mcp-server/discussions) for similar suggestions
2. Create a new issue using the **Feature Request** template
3. Describe:
   - The problem you're trying to solve
   - Your proposed solution
   - Use cases
   - Any alternatives you've considered

### Submitting Pull Requests

1. **Fork the repository** and create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards (see below)

3. **Add tests** for any new functionality

4. **Run the test suite**:
   ```bash
   pytest
   ```

5. **Format your code**:
   ```bash
   black src/ tests/
   ```

6. **Run linting**:
   ```bash
   pylint src/opendss_mcp
   ```

7. **Update documentation** as needed

8. **Commit your changes** with clear, descriptive messages:
   ```bash
   git commit -m "feat: add new MCP tool for XYZ"
   ```

9. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

10. **Create a Pull Request** using our PR template

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip
- git

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/opendss-mcp-server.git
cd opendss-mcp-server

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Or just test dependencies
pip install -e ".[test]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/opendss_mcp --cov-report=term-missing

# Run specific test file
pytest tests/test_power_flow.py

# Run specific test
pytest tests/test_power_flow.py::test_power_flow_basic
```

## Coding Standards

### Style Guide

- **Line length**: 100 characters (see `.cursorrules`)
- **Formatter**: black
- **Linter**: pylint (target score >8.0)
- **Type checker**: mypy
- **Docstrings**: Google style

### Code Structure

```python
def function_name(param: type) -> return_type:
    """Short description.

    Longer description if needed.

    Args:
        param: Description of parameter

    Returns:
        Description of return value

    Raises:
        ExceptionType: When and why this is raised
    """
    # Implementation
    pass
```

### Naming Conventions

- **Variables**: `descriptive_snake_case` (e.g., `bus_voltages_pu`, `min_voltage_pu`)
- **Constants**: `UPPER_CASE` (e.g., `MAX_ITERATIONS`, `DEFAULT_VOLTAGE`)
- **Classes**: `PascalCase` (e.g., `DSSCircuit`, `VoltageChecker`)
- **Functions**: `snake_case` (e.g., `run_power_flow`, `check_violations`)

### Tool Implementation Pattern

All MCP tools should follow this structure:

```python
def tool_name(param: type) -> dict[str, Any]:
    """Tool description.

    Args:
        param: Parameter description

    Returns:
        Response dict with keys: success, data, metadata, errors
    """
    # 1. Validate inputs
    validation_error = validate_input(param)
    if validation_error:
        return format_error_response(validation_error)

    # 2. Check circuit state if needed

    # 3. Perform OpenDSS operations with error handling
    try:
        # OpenDSS operations
        result = perform_operation()
    except Exception as e:
        return format_error_response(f"Error: {str(e)}")

    # 4. Format and return results
    return format_success_response(
        data=result,
        metadata={"computation_time": elapsed}
    )
```

### Testing Guidelines

- **Coverage target**: >80%
- **Test naming**: `test_<function>_<scenario>`
- **Use fixtures** for common setup
- **Test edge cases** and error conditions
- **Mock external dependencies** when appropriate

Example test structure:

```python
def test_power_flow_basic():
    """Test basic power flow analysis."""
    # Setup
    circuit = load_test_feeder("IEEE13")

    # Execute
    result = run_power_flow(circuit)

    # Assert
    assert result["success"] is True
    assert "voltages" in result["data"]
    assert len(result["data"]["voltages"]) > 0
```

## Documentation

### Updating README.md

- Keep it concise and user-focused
- Update examples if you add new features
- Maintain the current structure and tone

### Updating CHANGELOG.md

Follow the format:
```markdown
## [Version] - YYYY-MM-DD

### Added
- New feature description

### Changed
- Changed feature description

### Fixed
- Bug fix description
```

### Docstrings

All public functions, classes, and modules must have docstrings following Google style.

## Commit Messages

Follow conventional commits format:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Examples:
```
feat: add voltage regulation MCP tool
fix: correct power flow convergence check
docs: update installation guide for Windows
test: add tests for DER optimization
```

## Questions?

- **General questions**: Start a [Discussion](https://github.com/ahmedelshazly27/opendss-mcp-server/discussions)
- **Bug reports**: Create an [Issue](https://github.com/ahmedelshazly27/opendss-mcp-server/issues)
- **Feature requests**: Create an [Issue](https://github.com/ahmedelshazly27/opendss-mcp-server/issues)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to OpenDSS MCP Server! ⚡
