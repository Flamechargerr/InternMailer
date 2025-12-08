# TestSprite Test Configuration for InternMailer

## Test Scenarios

### 1. Email Validation Tests
- Test valid university emails (.edu, .ac.uk)
- Test invalid email formats
- Test disposable email detection
- Test role-based email blocking

### 2. Reply Classification Tests  
- Test interested reply detection
- Test not-interested classification
- Test out-of-office detection
- Test question categorization

### 3. Integration Tests
- Test system initialization
- Test config loading
- Test database pooling
- Test rate limiter calculation

### 4. End-to-End Flow
- Initialize integrated system
- Validate sample email
- Log event
- Check rate limits
- Verify all components working

## Expected Results

All tests should pass with:
- Email Validator: 90%+ accuracy
- Reply Classifier: 80%+ accuracy  
- System Integration: 100% success rate
- No import errors
- No runtime exceptions

## Test Commands

```bash
# Run verification
python verify_system.py

# Run pytest suite
pytest tests/test_suite.py -v

# Run specific test
pytest tests/test_suite.py::TestEmailValidator -v
```
