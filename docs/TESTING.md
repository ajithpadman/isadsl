# Testing Documentation

This document describes the test suite for the ISA DSL project, including how to run tests, what is tested, and how to add new tests.

## Test Suite Overview

The test suite consists of **216 test cases** (200+ test functions including parametrized tests) organized into logical groups within the `tests/` directory. All tests are passing with 0 failed, 0 skipped.

### Test Organization

Tests are organized into the following directories:

- **`tests/core/`** - Core parser, validator, and RTL interpreter tests
  - `test_parser.py` - Tests for ISA file parsing (including identification fields)
  - `test_validator.py` - Tests for semantic validation
  - `test_rtl_interpreter.py` - Tests for RTL expression interpretation

- **`tests/multifile/`** - Multi-file support tests
  - `test_multifile_support.py` - Tests for `#include` directives, merge mode, inheritance mode, and cross-file references

- **`tests/bundling/`** - Bundle instruction tests
  - `test_bundling.py` - Tests for instruction bundling support
  - `test_bundle_assembly_syntax.py` - Tests for bundle assembly syntax

- **`tests/assembly_syntax/`** - Assembly syntax tests
  - `test_assembly_syntax.py` - Tests for assembly syntax generation
  - `test_assembly_syntax_braces.py` - Tests for curly brace handling in assembly syntax

- **`tests/variable_length/`** - Variable-length instruction tests
  - `test_variable_length_assembler.py` - Tests for variable-length instruction assembler
  - `test_variable_length_disassembler.py` - Tests for variable-length instruction disassembler
  - `test_variable_length_execution.py` - Tests for variable-length instruction execution
  - `test_variable_length_comprehensive.py` - Comprehensive tests for variable-length instructions

- **`tests/generators/`** - Code generator tests
  - `test_generators.py` - Tests for code generation
  - `test_generated_tools.py` - Tests for generated assembler and simulator functionality

- **`tests/integration/`** - Integration tests
  - `test_integration.py` - Tests for end-to-end workflows
  - `test_comprehensive_features.py` - Comprehensive feature tests

- **`tests/arm/`** - ARM ISA integration tests
  - `test_arm_basic.py` - Basic ARM Cortex-A9 ISA tests (parsing, tool generation)
  - `test_arm_qemu.py` - QEMU verification tests for ARM Cortex-A9
  - `test_arm_disassembler.py` - Disassembler tests for ARM Cortex-A9
  - `test_arm_end_to_end.py` - End-to-end workflow tests for ARM Cortex-A9
  - `test_arm_integration_basic.py` - Basic ARM ISA subset integration tests
  - `test_arm_integration_qemu.py` - QEMU verification tests for ARM ISA subset
  - `test_arm_integration_disassembler.py` - Disassembler tests for ARM ISA subset
  - `test_arm_integration_end_to_end.py` - End-to-end workflow tests for ARM ISA subset
  - `test_arm_integration_labels_loops.py` - Labels and loops tests with QEMU
  - Helper files: `test_helpers.py`, `test_helpers_basic.py`, `test_helpers_compilation.py`, `test_helpers_qemu.py`, `test_helpers_integration.py`

- **`tests/rtl_builtins/`** - RTL built-in functions and bitfield access tests
  - `test_builtin_functions.py` - Tests for `sign_extend`, `zero_extend`, `extract_bits`, `to_signed`, `to_unsigned` functions and bitfield access syntax
  - `test_new_builtins.py` - Tests for new built-in functions: `ssov`, `suov`, `carry`, `borrow`, `reverse16`, `leading_ones`, `leading_zeros`, `leading_signs`

- **`tests/shift_ternary/`** - Shift operations and ternary expression tests
  - `test_shift_ternary.py` - Tests for shift operators (`<<`, `>>`) and ternary conditional expressions

- **`tests/register_fields/`** - Register field access tests
  - `test_register_fields.py` - Tests for register fields (C union-like access) and field updates

- **`tests/tricore/`** - TriCore architecture tests
  - `test_tricore_end_to_end.py` - End-to-end tests for TriCore ABS instruction (assembler, simulator, disassembler)


## Running Tests

### Run All Tests

```bash
uv run pytest
```

### Run Tests with Verbose Output

```bash
uv run pytest -v
```

### Run Specific Test File

```bash
uv run pytest tests/core/test_parser.py
```

### Run Specific Test Group

```bash
uv run pytest tests/core/
uv run pytest tests/multifile/
uv run pytest tests/bundling/
```

### Run Specific Test

```bash
uv run pytest tests/core/test_parser.py::test_instruction_parsing
```

### Run Tests with Coverage

```bash
uv run pytest --cov
```

## Test Categories

### Core Tests (`tests/core/`)

#### Parser Tests (`test_parser.py`)

Tests the ISA DSL parser functionality:

- **`test_parse_sample_isa`** - Verifies parsing of sample ISA file
- **`test_register_parsing`** - Tests register definition parsing (GPR, SFR, vector)
- **`test_format_parsing`** - Tests instruction format parsing
- **`test_instruction_parsing`** - Tests instruction definition parsing
- **`test_rtl_parsing`** - Tests RTL behavior parsing

**Key Features Tested:**
- Register files and special function registers
- Vector registers with SIMD properties
- Instruction formats with bit fields
- Instruction encodings
- RTL behavior statements (assignments, conditionals, memory access)

#### Validator Tests (`test_validator.py`)

Tests semantic validation of ISA specifications:

- **`test_validate_sample_isa`** - Validates complete sample ISA
- **`test_format_validation`** - Validates instruction format correctness
- **`test_instruction_validation`** - Validates instruction definitions

**Key Features Tested:**
- Format field overlap detection
- Format width validation
- Operand field matching
- Encoding field validation
- Register access validation

#### RTL Interpreter Tests (`test_rtl_interpreter.py`)

Tests the RTL expression interpreter:

- **`test_rtl_constant`** - Tests constant value evaluation
- **`test_rtl_binary_operations`** - Tests binary operations (+, -, *, /, etc.)
- **`test_register_access`** - Tests register access in expressions
- **`test_rtl_assignment`** - Tests RTL assignment execution

**Key Features Tested:**
- Arithmetic operations
- Bitwise operations
- Register file access
- Register field access
- Operand reference resolution

### Multi-file Support Tests (`tests/multifile/`)

Tests for multi-file ISA specifications using `#include` directives:

- **`test_multifile_support.py`** - Comprehensive multi-file support tests
  - Comment support (single-line and multi-line)
  - Include processing (simple, multiple, nested)
  - Relative path resolution
  - Circular dependency detection
  - Merge mode (combining partial definitions)
  - Inheritance mode (extending base architectures)
  - Error handling (duplicate definitions, missing architecture blocks)

**Key Features Tested:**
- `#include` directive parsing
- Cross-file format reference resolution via textX scope providers
- Model merging and inheritance
- Path resolution (absolute and relative)
- Circular dependency detection

### Generator Tests (`tests/generators/`)

Tests code generation functionality:

- **`test_simulator_generation`** - Verifies simulator code generation
- **`test_assembler_generation`** - Verifies assembler code generation
- **`test_disassembler_generation`** - Verifies disassembler code generation
- **`test_documentation_generation`** - Verifies documentation generation

**Key Features Tested:**
- Code generation for all tool types
- Generated code structure and syntax
- Template rendering

### Integration Tests (`tests/integration/`)

Tests end-to-end workflows:

- **`test_end_to_end_generation`** - Tests complete tool generation workflow
- **`test_instruction_encoding_decoding`** - Tests instruction encoding and decoding

**Key Features Tested:**
- Full generation pipeline
- Instruction encoding/decoding round-trip
- Validation integration

### Generated Tools Tests (`tests/generators/test_generated_tools.py`)

Tests the functionality of generated assemblers and simulators:

- **`test_assembler_basic_functionality`** - Tests basic assembler operations
- **`test_simulator_basic_functionality`** - Tests basic simulator operations
- **`test_assembler_simulator_integration`** - Tests full assemble-and-execute workflow
- **`test_assembler_simulator_multiple_instructions`** - Tests multiple instruction execution
- **`test_assembler_binary_output`** - Tests binary file generation
- **`test_simulator_binary_file_loading`** - Tests binary file loading and execution
- **`test_simulator_with_sample_isa`** - Tests with complete sample ISA
- **`test_assembler_handles_comments`** - Tests comment handling in assembly
- **`test_simulator_instruction_counting`** - Tests instruction execution counting

**Key Features Tested:**
- Assembly code parsing
- Machine code generation
- Instruction execution
- Register state updates
- Program counter advancement
- Binary file I/O
- Comment preprocessing
- Instruction counting

### Bundling Tests (`tests/bundling/`)

Tests for instruction bundling functionality:

- **`test_parse_bundle_format`** - Tests parsing bundle format definitions
- **`test_parse_bundle_instruction`** - Tests parsing bundle instruction definitions
- **`test_bundle_encoding_matching`** - Tests bundle encoding matching logic
- **`test_bundle_slot_extraction`** - Tests extracting sub-instructions from bundle slots
- **`test_bundle_instruction_validation`** - Tests validation of bundle instructions
- **`test_generated_simulator_bundle_detection`** - Tests generated simulator can detect bundles
- **`test_generated_assembler_bundle_syntax`** - Tests generated assembler recognizes bundle syntax
- **`test_bundle_assembly`** - Tests assembling bundle instructions
- **`test_bundle_simulation`** - Tests simulating bundle instructions
- **`test_bundle_end_to_end`** - Tests end-to-end bundle workflow (assemble and simulate)
- **`test_bundle_format_slot_encoding`** - Tests encoding instructions into bundle slots

**Key Features Tested:**
- Bundle format parsing (slots, widths)
- Bundle instruction parsing and resolution
- Bundle encoding matching (two-level decoding)
- Slot extraction and encoding
- Generated simulator bundle handling
- Generated assembler bundle syntax (`bundle{instr1, instr2}`)
- End-to-end bundle execution

## Test Coverage

The test suite provides comprehensive coverage of:

1. **Parsing** - All DSL syntax elements (registers, formats, instructions, RTL, bundles)
2. **Validation** - Semantic correctness checks
3. **Code Generation** - All generator types (simulator, assembler, disassembler, docs)
4. **Generated Tools** - Functional testing of generated code
5. **Integration** - End-to-end workflows
6. **Bundling** - Instruction bundling (formats, encoding, assembly, simulation)

## Adding New Tests

### Test File Structure

```python
"""Tests for [component name]."""

import pytest
from pathlib import Path
from isa_dsl.model.parser import parse_isa_file
# ... other imports

def test_feature_name():
    """Test description."""
    # Arrange
    isa_file = Path(__file__).parent.parent / 'examples' / 'sample_isa.isa'
    isa = parse_isa_file(str(isa_file))
    
    # Act
    result = some_function(isa)
    
    # Assert
    assert result == expected_value
```

### Best Practices

1. **Use descriptive test names** - Test names should clearly describe what is being tested
2. **Follow AAA pattern** - Arrange, Act, Assert
3. **Test one thing per test** - Each test should verify a single behavior
4. **Use fixtures for common setup** - Share setup code using pytest fixtures
5. **Test edge cases** - Include tests for boundary conditions and error cases
6. **Keep tests independent** - Tests should not depend on execution order

### Example: Adding a New Parser Test

```python
def test_new_feature_parsing():
    """Test parsing of new feature."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'sample_isa.isa'
    isa = parse_isa_file(str(isa_file))
    
    # Verify new feature is parsed correctly
    assert hasattr(isa, 'new_feature')
    assert isa.new_feature == expected_value
```

### Example: Adding a Generator Test

```python
def test_new_generator():
    """Test new code generator."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'sample_isa.isa'
    isa = parse_isa_file(str(isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        gen = NewGenerator(isa)
        output_file = gen.generate(tmpdir)
        
        assert output_file.exists()
        code = output_file.read_text()
        assert 'expected_pattern' in code
```

## Continuous Integration

All tests should pass before:
- Committing code changes
- Creating pull requests
- Releasing new versions

Run the full test suite:

```bash
uv run pytest tests/ -v
```

## Test Data

Test data is organized in `test_data/` directories within each test group:

- **`tests/core/test_data/`** - Core test ISAs (`sample_isa.isa`, `comprehensive.isa`, `test_identification_fields.isa`)
- **`tests/multifile/test_data/`** - Multi-file test ISAs (all `test_*.isa` files)
- **`tests/bundling/test_data/`** - Bundle test ISA (`bundling.isa`)
- **`tests/assembly_syntax/test_data/`** - Assembly syntax test ISA (`comprehensive.isa`)
- **`tests/variable_length/test_data/`** - Variable-length test ISAs (`variable_length.isa`, `test_identification_fields.isa`)
- **`tests/generators/test_data/`** - Generator test ISAs (`sample_isa.isa`, `minimal.isa`)
- **`tests/integration/test_data/`** - Integration test ISAs (`sample_isa.isa`, `comprehensive.isa`)
- **`tests/arm/test_data/`** - ARM test ISAs and assembly files (`arm_subset.isa`, `*.s`, `*.gdb`)

**Note**: The `examples/` directory now contains only reference ISA specifications (e.g., `arm_cortex_a9.isa` and its includes) demonstrating the multi-file approach. All test-specific files have been moved to appropriate `test_data/` directories.

## Troubleshooting

### Tests Fail After Code Changes

1. Run tests with verbose output: `uv run pytest -v`
2. Check for syntax errors in generated code
3. Verify RTL parsing is working correctly
4. Check that model classes match grammar definitions

### Generated Code Issues

If tests fail due to generated code:

1. Inspect generated files in temporary directories
2. Check template syntax in generators
3. Verify RTL code generation logic
4. Test with minimal ISA first

### Parser Issues

If parser tests fail:

1. Check grammar file (`isa_dsl/grammar/isa.tx`)
2. Verify model class definitions match grammar
3. Check RTL conversion functions in parser
4. Test with simple ISA examples first

## Performance

The full test suite (193 test cases) runs in approximately 20-25 seconds on modern hardware. Individual test files typically complete in under 1 second.

## Code Quality Standards

All test files follow strict code quality standards:

- **Test Function Limit**: No test function exceeds 50 lines of code
- **Test File Limit**: No test file exceeds 500 lines of code
- **Helper Functions**: Helper functions are implemented as class methods in separate files
- **Modularity**: Large test suites are split into multiple focused test files

This ensures maintainability, readability, and ease of debugging.

## Future Test Improvements

Potential areas for additional test coverage:

- Error handling and error messages
- Large ISA specifications
- Complex RTL expressions
- Performance testing
- Memory usage testing
- Cross-platform compatibility

