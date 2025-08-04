# V2 Test Suite

Organized test management for Mediflux V2 components.

## Test Structure

### `test_runner.py`
Main test suite runner - executes all test categories and provides summary.

### `test_core_components.py`
Tests for fundamental V2 components:
- Module imports validation
- Intent routing functionality  
- Memory store operations

### `test_database.py`
Tests for database architecture:
- Database manager functionality
- JSON storage and retrieval
- Complex data structures

### `test_integration.py`
Tests for component integration:
- Orchestrator workflow
- End-to-end processing

### Legacy Tests (Preserved)
- `test_prompt2.py` - Complete database architecture validation
- `demo_v2.py` - Component demonstration script

## Usage

**Run all tests:**
```bash
python tests/test_runner.py
```

**Run specific test categories:**
```bash
python tests/test_core_components.py
python tests/test_database.py
python tests/test_integration.py
```

**Complete validation:**
```bash
python tests/test_prompt2.py  # Full database test suite
python tests/demo_v2.py       # Component demo
```

## Test Organization Principles

1. **No redundant files** - Each test has a clear purpose
2. **Modular structure** - Tests organized by component area
3. **Functional focus** - Tests validate actual functionality, minimal logging
4. **Easy maintenance** - Clear naming and organization
