# CI/CD Setup Guide

This document describes the continuous integration and continuous deployment (CI/CD) setup for the InternMailing project.

## Overview

The project uses GitHub Actions for automated testing, coverage monitoring, and code quality checks. The CI pipeline is designed to:

1. **Run comprehensive tests** across multiple Python versions
2. **Monitor code coverage** and prevent regressions
3. **Enforce code quality** through linting and formatting checks
4. **Fail fast** on test failures or coverage drops

## Files Created

### 1. GitHub Actions Workflow (`.github/workflows/ci.yml`)

The main CI pipeline that runs on every push and pull request to `main` and `develop` branches.

**Key Features:**
- **Multi-version testing**: Tests across Python 3.8, 3.9, 3.10, and 3.11
- **Dependency caching**: Speeds up builds by caching pip dependencies
- **Coverage reporting**: Generates XML and terminal coverage reports
- **Coverage threshold**: Fails if coverage drops below 80%
- **Codecov integration**: Uploads coverage reports for tracking
- **Coverage regression detection**: Compares coverage between base and current branch
- **Code quality checks**: Runs black, isort, and flake8

### 2. Dependencies Added

**Added to `requirements.txt`:**
- `pytest-cov`: For coverage testing with pytest

### 3. Configuration Files

**`pytest.ini`:**
- Configures pytest with coverage defaults
- Sets up test discovery and markers
- Enables verbose output and short tracebacks

**`.coveragerc`:**
- Defines what code to include/exclude from coverage
- Sets up output formats (XML, HTML, terminal)
- Excludes test files, virtual environments, and demo scripts
- Shows missing lines and provides precise coverage metrics

## How It Works

### Test Execution

The pipeline runs the following command:
```bash
pytest --cov=src --cov=InternMailer --cov-report=xml --cov-report=term-missing --cov-fail-under=80
```

This:
- Runs all tests in the `tests/` directory
- Collects coverage for `src/` and `InternMailer/` directories
- Generates XML coverage report for Codecov
- Shows missing lines in terminal output
- **Fails the build if coverage is below 80%**

### Coverage Regression Detection

For pull requests, the pipeline:
1. Runs tests on the current branch and captures coverage
2. Checks out the base branch and runs tests again
3. Compares coverage percentages
4. **Fails if coverage drops by more than 2%**

### Code Quality Checks

The `lint` job runs:
- **Black**: Code formatting checker
- **isort**: Import sorting checker  
- **Flake8**: Python linting for syntax errors and code issues

## Usage

### Local Testing

Run tests with coverage locally:
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests with coverage
pytest --cov=src --cov=InternMailer --cov-report=term-missing

# Run with coverage threshold
pytest --cov=src --cov=InternMailer --cov-report=term-missing --cov-fail-under=80

# Generate HTML coverage report
pytest --cov=src --cov=InternMailer --cov-report=html
# View htmlcov/index.html in browser
```

### Coverage Testing Script

Use the included `test_coverage.py` script to test coverage thresholds:
```bash
python test_coverage.py
```

This script tests both passing and failing coverage scenarios.

## Failure Scenarios

The CI pipeline will **FAIL** in these situations:

1. **Test failures**: Any test fails
2. **Low coverage**: Total coverage below 80%
3. **Coverage regression**: Coverage drops by more than 2% in PRs
4. **Code quality issues**: 
   - Code not formatted with black
   - Imports not sorted with isort
   - Syntax errors or critical issues detected by flake8

## Configuration Customization

### Adjust Coverage Threshold

Edit `.github/workflows/ci.yml` and change:
```yaml
--cov-fail-under=80  # Change 80 to your desired percentage
```

### Modify Regression Threshold

In the coverage regression check step, change:
```python
regression_threshold = 2.0  # Allow up to 2% regression
```

### Update Excluded Files

Edit `.coveragerc` to modify what's excluded from coverage:
```ini
[run]
omit = 
    */tests/*
    */demo_*
    # Add more patterns here
```

### Change Python Versions

Update the matrix in `.github/workflows/ci.yml`:
```yaml
strategy:
  matrix:
    python-version: [3.8, 3.9, '3.10', '3.11']  # Modify as needed
```

## Monitoring

- **GitHub Actions**: View build status and logs in the Actions tab
- **Codecov**: Coverage trends and reports (if configured)
- **Pull Request Checks**: Automatic status checks on PRs

## Benefits

1. **Quality Assurance**: Automated testing prevents regressions
2. **Coverage Monitoring**: Ensures code is well-tested
3. **Code Consistency**: Enforces formatting and style standards
4. **Fast Feedback**: Developers get immediate feedback on changes
5. **Deployment Confidence**: Only well-tested code reaches production

## Next Steps

Consider adding:
- **Security scanning** (e.g., Bandit, Safety)
- **Dependency vulnerability checks**
- **Performance testing**
- **Deployment automation**
- **Notification integrations** (Slack, email)

## Troubleshooting

### Common Issues

1. **Coverage parsing errors**: Check that source code is syntactically valid
2. **Test timeouts**: Some tests may run slowly; consider splitting or optimizing
3. **Dependency conflicts**: Ensure requirements.txt is up to date
4. **Path issues**: Verify coverage source paths match your project structure

### Getting Help

- Check GitHub Actions logs for detailed error messages
- Review pytest output for test failures
- Examine coverage reports to identify untested code
- Ensure all dependencies are properly installed

---

The CI setup provides a robust foundation for maintaining code quality and preventing regressions. Adjust thresholds and configurations as your project evolves.
