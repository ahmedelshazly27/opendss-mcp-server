# Publishing to PyPI

This guide explains how to publish the OpenDSS MCP Server package to PyPI.

## Prerequisites

1. **PyPI Account**: Create accounts on both:
   - Test PyPI: https://test.pypi.org/account/register/
   - Production PyPI: https://pypi.org/account/register/

2. **API Tokens**: Generate API tokens for both:
   - Test PyPI: https://test.pypi.org/manage/account/token/
   - Production PyPI: https://pypi.org/manage/account/token/

3. **Build Tools**: Install required packages:
   ```bash
   pip install --upgrade build twine
   ```

## Version Management

Update the version in `pyproject.toml`:

```toml
[project]
name = "opendss-mcp-server"
version = "1.0.0"  # Update this for each release
```

Version scheme (Semantic Versioning):
- **Major** (1.x.x): Breaking API changes
- **Minor** (x.1.x): New features, backward compatible
- **Patch** (x.x.1): Bug fixes, backward compatible

## Pre-Publication Checklist

Before publishing, ensure:

- [ ] All tests pass: `pytest`
- [ ] Code coverage ≥75%: `pytest --cov=src/opendss_mcp`
- [ ] Code quality ≥8.0: `pylint src/opendss_mcp`
- [ ] Code formatted: `black src/ tests/ examples/`
- [ ] Verification passes: `bash verify_complete.sh`
- [ ] Version updated in `pyproject.toml`
- [ ] CHANGELOG updated (if exists)
- [ ] README accurate and up-to-date
- [ ] All dependencies correct

## Build the Package

```bash
# Clean previous builds
rm -rf dist/ build/ src/*.egg-info

# Build source distribution and wheel
python -m build
```

This creates:
- `dist/opendss_mcp_server-X.Y.Z.tar.gz` (source distribution)
- `dist/opendss_mcp_server-X.Y.Z-py3-none-any.whl` (wheel)

## Verify the Build

```bash
# Check package integrity
python -m twine check dist/*
```

Expected output:
```
Checking dist/opendss_mcp_server-1.0.0-py3-none-any.whl: PASSED
Checking dist/opendss_mcp_server-1.0.0.tar.gz: PASSED
```

## Test on Test PyPI

Always test on Test PyPI first:

```bash
# Upload to Test PyPI
python -m twine upload --repository testpypi dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your Test PyPI API token (starts with `pypi-`)

Verify installation from Test PyPI:

```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    opendss-mcp-server

# Test basic import
python -c "from opendss_mcp.server import main; print('Import successful!')"

# Deactivate and clean up
deactivate
rm -rf test_env
```

## Publish to Production PyPI

Once tested, publish to production:

```bash
# Upload to PyPI
python -m twine upload dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your PyPI API token (starts with `pypi-`)

## Post-Publication

After publishing:

1. **Verify on PyPI**:
   - Check package page: https://pypi.org/project/opendss-mcp-server/
   - Verify metadata, description, and links

2. **Tag the Release**:
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

3. **Create GitHub Release**:
   - Go to: https://github.com/ahmedelshazly27/opendss-mcp-server/releases
   - Create new release from tag
   - Add release notes highlighting changes

4. **Test Installation**:
   ```bash
   # In a clean environment
   pip install opendss-mcp-server
   ```

5. **Update Documentation**:
   - Update README if needed
   - Update installation instructions
   - Document new features/changes

## Using .pypirc (Optional)

To avoid entering credentials each time, create `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PRODUCTION_TOKEN

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TEST_TOKEN
```

**Security Warning**: This file contains sensitive tokens. Ensure it has restricted permissions:

```bash
chmod 600 ~/.pypirc
```

## Automated Publishing with GitHub Actions

For automated publishing on tag creation, add `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine

    - name: Build package
      run: python -m build

    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

Add your PyPI token to GitHub Secrets:
- Go to: Settings → Secrets and variables → Actions
- Add secret: `PYPI_API_TOKEN`

## Troubleshooting

### Error: "File already exists"

PyPI doesn't allow overwriting existing versions. Solutions:
- Increment version number
- Delete from Test PyPI (production versions can't be deleted)

### Error: "Invalid distribution"

Run checks:
```bash
python -m twine check dist/*
```

Fix issues in `pyproject.toml` and rebuild.

### Error: "Authentication failed"

- Verify token is correct
- Ensure username is `__token__` (not your PyPI username)
- Check token hasn't expired

### Large Package Size

To reduce package size:
- Exclude unnecessary files in `MANIFEST.in`
- Don't include test data in source distribution
- Compress large data files

## Package Maintenance

### Yanking a Release

If a release has critical issues:

1. **On PyPI web interface**:
   - Go to release management
   - Select "Yank" (doesn't delete, just marks as bad)

2. **Publish fixed version**:
   ```bash
   # Update version to X.Y.Z+1
   # Fix issues
   # Build and publish
   ```

### Deprecation Notice

To deprecate the package:

1. Update README with deprecation notice
2. Add to package description
3. Publish final version with notice
4. Don't delete - breaks existing installations

## Resources

- **PyPI Packaging Guide**: https://packaging.python.org/
- **Twine Documentation**: https://twine.readthedocs.io/
- **PEP 517/518**: https://peps.python.org/pep-0517/
- **Semantic Versioning**: https://semver.org/

## Support

For publishing issues:
- PyPI Support: https://github.com/pypi/support
- Project Issues: https://github.com/ahmedelshazly27/opendss-mcp-server/issues
