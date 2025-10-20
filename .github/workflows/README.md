# GitHub Actions Workflows

This directory contains automated workflows for continuous integration and deployment.

## Workflows

### 1. Tests (`test.yml`)

**Trigger**: Push and Pull Requests to `main` and `develop` branches

**Purpose**: Run comprehensive test suite across multiple Python versions

**Matrix**:
- Python 3.10
- Python 3.11
- Python 3.12

**Steps**:
1. Checkout code
2. Set up Python environment with pip caching
3. Install package with test dependencies
4. Run pytest with coverage
5. Upload coverage to Codecov

**Requirements**:
- Codecov token stored in repository secrets as `CODECOV_TOKEN`
- Get token from: https://codecov.io/

**Badge**:
```markdown
[![Tests](https://github.com/ahmedelshazly27/opendss-mcp-server/workflows/Tests/badge.svg)](https://github.com/ahmedelshazly27/opendss-mcp-server/actions/workflows/test.yml)
```

---

### 2. Linting (`lint.yml`)

**Trigger**: Push and Pull Requests to `main` and `develop` branches

**Purpose**: Enforce code quality standards

**Checks**:
- **Black**: Code formatting (fails if not formatted)
- **Pylint**: Code quality (reports but doesn't fail)
- **Mypy**: Type checking (reports but doesn't fail)

**Steps**:
1. Checkout code
2. Set up Python 3.10
3. Install development dependencies
4. Run black in check mode
5. Run pylint (non-blocking)
6. Run mypy (non-blocking)

**Badge**:
```markdown
[![Linting](https://github.com/ahmedelshazly27/opendss-mcp-server/workflows/Linting/badge.svg)](https://github.com/ahmedelshazly27/opendss-mcp-server/actions/workflows/lint.yml)
```

---

### 3. Publish to PyPI (`publish.yml`)

**Trigger**: GitHub Release published

**Purpose**: Automatically publish package to PyPI when a release is created

**Steps**:
1. Checkout code
2. Set up Python 3.10
3. Install build tools
4. Build source and wheel distributions
5. Validate package with twine
6. Upload to PyPI

**Requirements**:
- PyPI API token stored in repository secrets as `PYPI_API_TOKEN`
- Get token from: https://pypi.org/manage/account/token/

**Usage**:
1. Update version in `pyproject.toml`
2. Commit and push changes
3. Create a GitHub release with tag `vX.Y.Z`
4. Workflow automatically publishes to PyPI

**Badge**:
```markdown
[![PyPI](https://img.shields.io/pypi/v/opendss-mcp-server.svg)](https://pypi.org/project/opendss-mcp-server/)
```

---

## Setting Up Secrets

### Codecov Token

1. Go to https://codecov.io/ and sign in with GitHub
2. Add your repository
3. Copy the upload token
4. In GitHub: Settings → Secrets and variables → Actions → New repository secret
5. Name: `CODECOV_TOKEN`
6. Value: Paste the token

### PyPI API Token

1. Go to https://pypi.org/manage/account/token/
2. Create a new API token
3. Scope: Select specific project or entire account
4. Copy the token (starts with `pypi-`)
5. In GitHub: Settings → Secrets and variables → Actions → New repository secret
6. Name: `PYPI_API_TOKEN`
7. Value: Paste the token

## Badge Configuration

Add these badges to your README.md:

```markdown
[![Tests](https://github.com/ahmedelshazly27/opendss-mcp-server/workflows/Tests/badge.svg)](https://github.com/ahmedelshazly27/opendss-mcp-server/actions/workflows/test.yml)
[![Linting](https://github.com/ahmedelshazly27/opendss-mcp-server/workflows/Linting/badge.svg)](https://github.com/ahmedelshazly27/opendss-mcp-server/actions/workflows/lint.yml)
[![codecov](https://codecov.io/gh/ahmedelshazly27/opendss-mcp-server/branch/main/graph/badge.svg)](https://codecov.io/gh/ahmedelshazly27/opendss-mcp-server)
[![PyPI](https://img.shields.io/pypi/v/opendss-mcp-server.svg)](https://pypi.org/project/opendss-mcp-server/)
[![Python Versions](https://img.shields.io/pypi/pyversions/opendss-mcp-server.svg)](https://pypi.org/project/opendss-mcp-server/)
```

## Workflow Status

You can check workflow status at:
https://github.com/ahmedelshazly27/opendss-mcp-server/actions

## Troubleshooting

### Tests Failing

1. Check the test logs in Actions tab
2. Run tests locally: `pytest -v`
3. Ensure all dependencies are installed
4. Check for Python version compatibility

### Linting Errors

1. Format code: `black src/ tests/ examples/`
2. Check pylint: `pylint src/opendss_mcp`
3. Check types: `mypy src/opendss_mcp`

### Publish Failing

1. Verify PyPI token is correct
2. Check version in `pyproject.toml` is unique
3. Ensure package builds: `python -m build`
4. Validate package: `twine check dist/*`

### Codecov Not Uploading

1. Verify token is set correctly
2. Check coverage.xml is generated
3. Review Codecov dashboard for errors
4. Token can be regenerated if needed

## Local Testing

Test workflows locally with [act](https://github.com/nektos/act):

```bash
# Install act
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run test workflow
act -j test

# Run lint workflow
act -j lint
```

## Customization

### Adding New Python Versions

Edit `test.yml`:

```yaml
matrix:
  python-version: ["3.10", "3.11", "3.12", "3.13"]  # Add 3.13
```

### Changing Trigger Branches

Edit workflow `on` section:

```yaml
on:
  push:
    branches: [ main, develop, feature/* ]  # Add feature branches
  pull_request:
    branches: [ main, develop ]
```

### Adding More Checks

Add new workflow or extend existing ones with additional steps:

```yaml
- name: Run security check
  run: |
    pip install safety
    safety check
```

## Best Practices

1. **Always test locally** before pushing
2. **Use semantic versioning** for releases
3. **Write meaningful commit messages**
4. **Keep dependencies up to date**
5. **Monitor workflow failures** and fix promptly
6. **Document workflow changes** in this file

## Support

For workflow issues:
- GitHub Actions Docs: https://docs.github.com/en/actions
- Project Issues: https://github.com/ahmedelshazly27/opendss-mcp-server/issues
