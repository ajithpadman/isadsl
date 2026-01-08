# Release Notes

## Version 0.3.7 - Format Constant Fields Feature

**Release Date:** 2026-01-07

### 🎯 Major Changes

#### Format Constant Fields

Added support for defining constant values directly in instruction format field definitions. This feature eliminates repetition when multiple instructions share the same constant field value (e.g., opcode).

**New Syntax:**
```isa
formats {
    format R_TYPE 32 {
        opcode: [0:5] = 0x01    // All R_TYPE instructions have opcode=1
        rd: [6:10]
        rs1: [11:15]
        rs2: [16:20]
    }
}
```

**Key Features:**
- Constants can be specified in hex (`0x01`) or decimal (`1`)
- Constant values must fit within the field width
- Constant values must be non-negative
- **Constants cannot be overridden** in instruction encodings (validation error if attempted)
- Constants are automatically encoded in all instructions using the format
- Constants do not appear as operands in disassembly output

**Benefits:**
- Reduces repetition when multiple instructions share the same constant field value
- Makes format definitions more self-documenting
- Ensures consistency across all instructions using the format
- Simplifies instruction definitions by removing redundant encoding assignments

**Example:**
```isa
formats {
    format R_TYPE 32 {
        opcode: [0:5] = 0x01    // Format constant
        rd: [6:10]
        rs1: [11:15]
        rs2: [16:20]
        funct: [21:25]         // Instruction encoding can set this
    }
}

instructions {
    instruction ADD {
        format: R_TYPE
        encoding: { funct=0x0A }  // Only need to specify funct, opcode is constant
        operands: rd, rs1, rs2
    }
}
```

### ✨ Improvements

- **Grammar Support**: Extended both textX and Langium grammars to support constant field syntax
- **Model Integration**: Added `constant_value` field to `FormatField` class with helper methods
- **Validation**: Comprehensive validation in both Python and TypeScript:
  - Validates constant values fit within field width
  - Validates constants are non-negative
  - Prevents instruction-level overrides of format constants
- **Code Generation**: Updated assembler, simulator, and disassembler templates:
  - Assembler: Applies format constants before instruction-specific encodings
  - Simulator: Checks format constants during instruction matching
  - Disassembler: Excludes constant fields from operand display
- **VS Code Extension**: Full language server support with validation and syntax highlighting
- **Backward Compatibility**: Existing formats without constants continue to work unchanged

### 📝 Technical Details

**Files Modified:**
- `isa_dsl/grammar/isa.tx` - Added optional constant value to `FormatField` rule
- `vscode_extension/isa/packages/language/src/isa.langium` - Added constant value support to Langium grammar
- `isa_dsl/model/isa_model.py` - Added `constant_value` field and helper methods to `FormatField`
- `isa_dsl/model/textx_model_converter.py` - Extract constant values from parsed model
- `isa_dsl/model/validator.py` - Added validation for format constants
- `vscode_extension/isa/packages/language/src/isa-validator.ts` - Added TypeScript validation
- `isa_dsl/generators/templates/assembler.j2` - Apply format constants during encoding
- `isa_dsl/generators/templates/simulator.j2` - Check format constants during matching
- `isa_dsl/generators/templates/disassembler.j2` - Exclude constants from operand display

**Tests:**
- `tests/core/test_format_constants.py` - Comprehensive test suite (12 tests) covering:
  - Parsing hex and decimal constants
  - Validation (field width, non-negative, override prevention)
  - Assembler encoding with format constants
  - Simulator matching with format constants
  - Disassembler exclusion of constants
  - Combined format constants and instruction encodings

**Examples:**
- `examples/format_constants_example.isa` - Example demonstrating format constant usage

### 📦 Files Changed

**Core Implementation:**
- `isa_dsl/grammar/isa.tx` - Grammar extension for constant fields
- `isa_dsl/model/isa_model.py` - Model support for constants
- `isa_dsl/model/textx_model_converter.py` - Constant extraction
- `isa_dsl/model/validator.py` - Validation logic
- `isa_dsl/generators/templates/assembler.j2` - Constant encoding
- `isa_dsl/generators/templates/simulator.j2` - Constant matching
- `isa_dsl/generators/templates/disassembler.j2` - Constant exclusion

**VS Code Extension:**
- `vscode_extension/isa/packages/language/src/isa.langium` - Grammar extension
- `vscode_extension/isa/packages/language/src/isa-validator.ts` - Validation

**Tests:**
- `tests/core/test_format_constants.py` - New comprehensive test suite

**Examples:**
- `examples/format_constants_example.isa` - New example file

**Documentation:**
- `docs/DSL_Specification.md` - Added "Constant Fields in Formats" section

**Version Updates:**
- `pyproject.toml` - Version 0.3.6 → 0.3.7
- `vscode_extension/isa/packages/extension/package.json` - Version 0.3.6 → 0.3.7
- `vscode_extension/isa/packages/language/package.json` - Version 0.3.6 → 0.3.7
- `vscode_extension/isa/package.json` - Version 0.3.6 → 0.3.7

### 🔄 Migration Guide

No breaking changes. Existing ISA specifications continue to work without modification.

**To Use Format Constants:**
1. Add constant values to format field definitions: `field_name: [lsb:msb] = constant_value`
2. Remove redundant encoding assignments from instructions that use the format
3. Ensure constant values fit within field width (validation will catch errors)

**Example Migration:**
```isa
// Before:
format R_TYPE 32 {
    opcode: [0:5]
    ...
}
instruction ADD {
    format: R_TYPE
    encoding: { opcode=0x01, funct=0x0A }
    ...
}

// After:
format R_TYPE 32 {
    opcode: [0:5] = 0x01  // Constant in format
    ...
}
instruction ADD {
    format: R_TYPE
    encoding: { funct=0x0A }  // Only non-constant fields
    ...
}
```

### 📊 Test Coverage

- **Python Tests**: 193 test cases, all passing (12 new tests for format constants)
- **VS Code Extension Tests**: 55 tests, all passing
- **Total**: 248 tests, all passing

---

## Version 0.3.6 - Negative Shift Count Fix and VS Code Validation Enhancements

**Release Date:** 2026-01-07

### 🎯 Major Changes

#### Fixed Negative Shift Count Issue in Simulator Template

Fixed a critical bug where `sign_extend` and related functions could cause "ValueError: negative shift count" when called with invalid parameters (zero or negative bit counts).

**Problem Fixed:**
- `sign_extend(value, from_bits, to_bits)` would crash with negative shift count when `from_bits` was 0 or negative
- This was particularly problematic for instructions like TriCore `ABS.B` that use byte-wise operations
- The issue only appeared when using `sim.run()` instead of `sim.step()`, making it easy to miss in tests

**Solution:**
- Added parameter validation to `_sign_extend` in simulator template to check:
  - `from_bits` and `to_bits` must be positive (> 0)
  - `from_bits` and `to_bits` must be <= 64
- Added the same validation to RTL interpreter for consistency
- Fixed TriCore `ABS.B` instruction to use correct `extract_bits` + `sign_extend` pattern instead of incorrect bit position parameters

**Example Fix:**
```isa
// Before (incorrect - causes negative shift count):
D_7_0 = sign_extend(D[s2], 0, 7);  // Wrong: uses bit positions

// After (correct):
D_7_0 = sign_extend(extract_bits(D[s2], 7, 0), 8);  // Correct: extract then extend
```

#### Enhanced VS Code Extension Validation

Added validation checks in the VS Code language server to catch invalid built-in function parameters at edit time.

**New Validations:**
- Validates `from_bits` and `to_bits` are positive for `sign_extend`/`zero_extend`
- Validates `from_bits` and `to_bits` are <= 64
- Validates `width` parameter for `to_signed`/`to_unsigned`
- Added `to_signed` and `to_unsigned` to valid built-in functions list

**Benefits:**
- Developers get immediate feedback when using invalid parameters
- Prevents runtime errors from being discovered only during simulation
- Improves developer experience with real-time validation

### ✨ Improvements

- **Robust Error Handling**: Simulator and interpreter now validate parameters before use
- **Better Developer Experience**: VS Code extension provides immediate validation feedback
- **Fixed TriCore ABS.B**: Corrected instruction definition to use proper bit extraction pattern
- **Test Coverage**: Added test case using `sim.run()` to catch issues that `sim.step()` might miss

### 📝 Technical Details

**Files Modified:**
- `isa_dsl/generators/templates/simulator.j2` - Added parameter validation to `_sign_extend`
- `isa_dsl/runtime/rtl_interpreter.py` - Added parameter validation to `sign_extend`
- `vscode_extension/isa/packages/language/src/isa-validator.ts` - Added constant value extraction and validation
- `tests/tricore/test_data/tc18_instructions.isa` - Fixed `ABS.B` instruction to use correct pattern
- `tests/tricore/test_tricore_end_to_end.py` - Added `test_tricore_abs_b_with_run` test case

**How Validation Works:**
1. VS Code extension extracts constant values from RTL expressions using AST traversal
2. Validates constant parameters (positive, <= 64) and reports errors immediately
3. Runtime validation in simulator/interpreter provides fallback for non-constant expressions
4. Both validations use the same rules for consistency

### 📦 Files Changed

**Core Implementation:**
- `isa_dsl/generators/templates/simulator.j2` - Parameter validation in `_sign_extend`
- `isa_dsl/runtime/rtl_interpreter.py` - Parameter validation in `_apply_builtin_function`
- `vscode_extension/isa/packages/language/src/isa-validator.ts` - Enhanced `checkRTLFunctionCall` with constant validation

**Tests:**
- `tests/tricore/test_tricore_end_to_end.py` - Added `test_tricore_abs_b_with_run` test
- `vscode_extension/isa/packages/language/test/builtin-functions.test.ts` - Added validation test cases

**Instruction Definitions:**
- `tests/tricore/test_data/tc18_instructions.isa` - Fixed `ABS.B` instruction

**Version Updates:**
- `pyproject.toml` - Version 0.3.5 → 0.3.6
- `vscode_extension/isa/packages/extension/package.json` - Version 0.3.5 → 0.3.6
- `vscode_extension/isa/packages/language/package.json` - Version 0.3.5 → 0.3.6
- `vscode_extension/isa/package.json` - Version 0.3.5 → 0.3.6

### 🔄 Migration Guide

No breaking changes. Existing code continues to work, but invalid parameter usage will now be caught earlier.

**If You Have Invalid `sign_extend` Usage:**
- Change `sign_extend(value, bit_pos1, bit_pos2)` to `sign_extend(extract_bits(value, bit_pos1, bit_pos2), width)`
- Ensure all bit count parameters are positive and <= 64

**Benefits:**
- More robust error handling prevents runtime crashes
- Better developer experience with immediate validation feedback
- Consistent validation between VS Code extension and runtime

### 📊 Statistics

- **4 core files modified**
- **2 test files updated**
- **1 instruction definition fixed**
- **All 181 Python tests passing**
- **All 55 VS Code extension tests passing**

---

## Version 0.3.5 - Signed Integer Support for `to_signed` Built-in Function

**Release Date:** 2026-01-07

### 🎯 Major Changes

#### Fixed `to_signed` Built-in Function to Return Proper Signed Integers

The `to_signed(value, width)` built-in function now correctly returns signed integer values that Python can properly compare, enabling correct absolute value calculations and signed comparisons in RTL behavior blocks.

**Problem Fixed:**
- Previously, `to_signed(0xF1, 8)` would return `0xFFFFFFF1` (4294967281 as unsigned), causing comparisons like `>= 0` to always be `True` even for negative values
- This broke absolute value calculations that relied on signed comparisons

**Solution:**
- Updated `_sign_extend` helper in generated simulators to convert unsigned bit patterns to Python signed integers
- Updated `to_signed` in the RTL interpreter to return signed values
- Modified code generator to preserve signed values in temporary variables (skip `& 0xFFFFFFFF` mask for variables)

**Example:**
```isa
behavior: {
    signed3 = to_signed(temp3, 8);  // Now returns -15 for 0xF1, not 4294967281
    abs3 = (signed3 >= 0) ? signed3 : (0 - signed3);  // Now works correctly!
}
```

### ✨ Improvements

- **Correct Signed Comparisons**: `to_signed` now returns values that Python correctly interprets as signed
- **Fixed Absolute Value Calculations**: Byte-wise absolute value operations now work correctly
- **Preserved Signed Values**: Temporary variables maintain signed values for intermediate calculations
- **Backward Compatible**: Register writes still use unsigned 32-bit values (as expected)

### 📝 Technical Details

**Files Modified:**
- `isa_dsl/generators/templates/simulator.j2` - Added signed conversion to `_sign_extend`
- `isa_dsl/runtime/rtl_interpreter.py` - Added signed conversion to `to_signed`
- `isa_dsl/generators/simulator.py` - Skip mask for temporary variables to preserve signed values

**How It Works:**
1. Sign extension produces unsigned bit pattern (e.g., `0xFFFFFFF1`)
2. Signed conversion: `result >= 0x80000000 ? result - 0x100000000 : result` (e.g., `-15`)
3. Temporary variables store signed values without masking
4. Comparisons now work correctly: `-15 >= 0` → `False` ✓

### 📦 Files Changed

**Core Implementation:**
- `isa_dsl/generators/templates/simulator.j2` - Signed conversion in `_sign_extend`
- `isa_dsl/runtime/rtl_interpreter.py` - Signed conversion in `to_signed`
- `isa_dsl/generators/simulator.py` - Conditional masking for variables vs registers

**Tests:**
- `tests/rtl_builtins/test_builtin_functions.py` - `test_abs_bytes_packing` now passes

**Version Updates:**
- `pyproject.toml` - Version 0.3.4 → 0.3.5
- `vscode_extension/isa/packages/extension/package.json` - Version 0.3.4 → 0.3.5
- `vscode_extension/isa/packages/language/package.json` - Version 0.3.4 → 0.3.5
- `vscode_extension/isa/package.json` - Version 0.3.4 → 0.3.5

### 🔄 Migration Guide

No breaking changes. Existing code continues to work, but signed comparisons with `to_signed` now work correctly.

**Benefits:**
- Absolute value calculations work correctly with signed byte values
- Signed comparisons (`>=`, `<`, etc.) work as expected
- More intuitive behavior matching hardware semantics

### 📊 Statistics

- **3 core files modified**
- **1 test case fixed**
- **All 16 built-in function tests passing**

---

## Version 0.3.4 - Documentation Consistency and Accuracy Improvements

**Release Date:** 2026-01-07

### 🎯 Major Changes

#### Documentation Consistency Review and Fixes

Comprehensive review and update of all documentation files to ensure consistency, accuracy, and completeness across the project.

**Issues Fixed:**
- **Test Count Inconsistencies**: Updated test counts across all documentation files to reflect accurate numbers (170+ test cases, 200+ test functions)
- **Version Number Mismatches**: Fixed VS Code extension README version badge (0.2.0 → 0.3.4)
- **Missing Features**: Added documentation for recently implemented features that were missing from README files
- **Syntax Inconsistencies**: Fixed ternary expression and operands syntax examples to match actual DSL syntax
- **Outdated Test Directories**: Added missing test directories to testing documentation

**Files Updated:**
- `README.md` - Updated test counts, added shift operators, ternary expressions, built-in functions, bitfield access, and register fields
- `vscode_extension/isa/packages/extension/README.md` - Updated version badge, added missing features, fixed syntax examples
- `docs/INDEX.md` - Updated test count
- `docs/TESTING.md` - Updated test count and added new test directories (rtl_builtins, shift_ternary, register_fields, tricore)

### ✨ Improvements

- **Accurate Test Counts**: All documentation now reflects the current test suite size (170+ test cases)
- **Complete Feature Documentation**: All implemented features are now documented in README files
- **Consistent Examples**: All code examples use correct syntax and formatting
- **Version Consistency**: All version numbers match across packages

### 📝 Documentation Updates

**Main README (`README.md`):**
- Updated test count from "126 tests" to "170+ test cases (200+ test functions)"
- Added shift operators (`<<`, `>>`) to RTL behavior features
- Added ternary conditional expressions to features list
- Added bitfield access syntax (`value[msb:lsb]`)
- Added built-in functions (`sign_extend`, `zero_extend`, `extract_bits`)
- Added register fields feature with C union-like behavior

**VS Code Extension README:**
- Updated version badge from 0.2.0 to 0.3.4
- Added all missing features (shift, ternary, built-ins, bitfields, register fields)
- Fixed ternary syntax example: `D[s2]>=0?D[s2]` → `(D[s2] >= 0) ? D[s2]`
- Fixed operands syntax consistency: `operands: rd,rs1,rs2` → `operands: rd, rs1, rs2`

**Testing Documentation:**
- Updated test count in `docs/INDEX.md` and `docs/TESTING.md`
- Added new test directories: `rtl_builtins/`, `shift_ternary/`, `register_fields/`, `tricore/`
### 📦 Files Changed

**Documentation:**
- `README.md` - Feature list and test count updates
- `vscode_extension/isa/packages/extension/README.md` - Version, features, syntax fixes
- `docs/INDEX.md` - Test count update
- `docs/TESTING.md` - Test count and directory updates

**Version Updates:**
- `pyproject.toml` - Version 0.3.3 → 0.3.4
- `vscode_extension/isa/packages/extension/package.json` - Version 0.3.3 → 0.3.4
- `vscode_extension/isa/packages/language/package.json` - Version 0.3.3 → 0.3.4
- `vscode_extension/isa/package.json` - Version 0.3.3 → 0.3.4

### 🔄 Migration Guide

No breaking changes. This is a documentation-only release.

**Benefits:**
- Documentation is now accurate and up-to-date
- All features are properly documented
- Examples use correct syntax
- Version numbers are consistent across all packages

### 📊 Statistics

- **4 documentation files updated**
- **4 version files updated**
- **All inconsistencies resolved**
- **100% documentation accuracy achieved**

---
### 🧪 Testing

- **All 170+ Python tests passing** ✅
- **All VS Code extension tests passing** ✅
- Documentation examples verified for correctness
- All syntax examples match actual DSL grammar



## Version 0.3.3 - Assembler State Management and Test Isolation Fixes

**Release Date:** 2026-01-07

### 🎯 Major Changes

#### Assembler State Management Fix

Fixed a critical bug where the assembler was accumulating state across multiple `assemble()` calls, causing incorrect machine code generation when the same assembler instance was reused.

**Problem:**
- When calling `assemble()` multiple times on the same instance, instructions from previous calls were included in subsequent results
- This caused tests to fail when assembling multiple instructions separately
- Example: `assemble("SET_V R0")` followed by `assemble("CHECK_V R1")` would return `[0x1, 0x45]` instead of `[0x45]`

**Solution:**
- Assembler now clears state (`self.instructions`, `self.labels`, `self.symbols`) at the start of each `assemble()` call
- Each call processes only the provided source code independently
- Works correctly for both single calls with multiple instructions and multiple calls on the same instance

**Before:**
```python
assembler = Assembler()
code1 = assembler.assemble("SET_V R0")  # Returns [0x1]
code2 = assembler.assemble("CHECK_V R1")  # Returns [0x1, 0x45] ❌ WRONG!
```

**After:**
```python
assembler = Assembler()
code1 = assembler.assemble("SET_V R0")  # Returns [0x1] ✓
code2 = assembler.assemble("CHECK_V R1")  # Returns [0x45] ✓ CORRECT!
```

#### Test Isolation Improvements

Fixed test isolation issues in `register_fields` tests by ensuring each test creates separate module instances, preventing module caching from causing shared state between tests.

**Problem:**
- Tests were using `import_module()` which caches modules in `sys.modules`
- When running the full test suite, modules from previous tests were reused
- This caused `AttributeError` and incorrect behavior in some tests

**Solution:**
- Updated all `register_fields` tests to use `importlib.util.spec_from_file_location()` instead of `import_module()`
- Each test now gets a fresh module instance, ensuring proper isolation
- Tests can now run in any order without affecting each other

**Before:**
```python
from importlib import import_module
sim_module = import_module(sim_file.stem)  # Uses cached module ❌
```

**After:**
```python
import importlib.util
sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
sim_module = importlib.util.module_from_spec(sim_spec)
sim_spec.loader.exec_module(sim_module)  # Fresh module instance ✓
```

### ✨ New Features

- **Proper State Isolation**: Assembler instances can now be safely reused across multiple assembly operations
- **Improved Test Reliability**: All tests now have proper isolation, preventing flaky test failures

### 🔧 Technical Improvements

#### Python Package

**Assembler Template (`assembler.j2`):**
- Added state clearing at the start of `assemble()` method
- Clears `self.instructions`, `self.labels`, and `self.symbols` before processing each source
- Ensures each `assemble()` call is independent and idempotent

**Test Suite (`test_register_fields.py`):**
- Replaced `import_module()` with `importlib.util.spec_from_file_location()` pattern
- Ensures each test gets fresh module instances
- Fixed module caching issues that caused test failures in full suite runs

### 📝 Documentation Updates

- Updated test patterns to use proper module isolation
- Documented assembler state management behavior

### 🧪 Testing

- **All 167 Python tests passing** ✅ (up from 160)
- **All 7 register_fields tests now pass in full suite** ✅
- **All assembler tests passing** ✅
- Fixed test isolation issues that caused failures when running full test suite
- Verified assembler works correctly for both:
  - Multiple instructions in one `assemble()` call
  - Multiple `assemble()` calls on the same instance

### 📦 Files Changed

**Python Package:**
- `isa_dsl/generators/templates/assembler.j2` - Added state clearing in `assemble()` method
- `tests/register_fields/test_register_fields.py` - Fixed module isolation using `importlib.util.spec_from_file_location()`

### 🔄 Migration Guide

No breaking changes. Existing code continues to work without modification.

**Benefits:**
- Assembler instances can now be safely reused
- Multiple `assemble()` calls on the same instance work correctly
- Tests are more reliable and can run in any order

### 🐛 Bug Fixes

- **Fixed assembler state accumulation bug**: Assembler now correctly clears state between calls
- **Fixed test isolation issues**: Register fields tests now properly isolate module instances
- **Fixed module caching**: Tests no longer share state through cached modules

### 📊 Statistics

- **2 files modified**
- **+15 insertions, -5 deletions**
- **Net code addition**: 10 lines (state clearing + module isolation)
- **Test improvements**: 7 previously failing tests now passing in full suite

---

## Version 0.3.2 - Register Fields with C Union-like Behavior

**Release Date:** 2026-01-07

### 🎯 Major Changes

#### Register Fields Support with C Union-like Behavior

Registers with fields now support direct field access similar to C union types, allowing both full register access and individual field manipulation.

**Features:**
- **Full Register Access**: Registers work as integers for backward compatibility (`PSW = 0x12345678`)
- **Field Access**: Direct field access using dot notation (`PSW.V = 1`, `PSW.SV = 0`)
- **Field Reads**: Field values can be read in conditions (`if (PSW.V) { ... }`)
- **Integer Operations**: Full register operations still work (`PSW = PSW + 1`)
- **Automatic Synchronization**: Field changes automatically update the full register value and vice versa

**Syntax:**
```isa
sfr PSW 32 {
    V: [30:30]    // Overflow flag
    SV: [29:29]   // Sticky overflow flag
    AV: [28:28]   // Advance overflow flag
    C: [31:31]    // Carry flag
}

instruction ABS {
    behavior: {
        // Direct field assignment - much cleaner!
        PSW.V = 1;
        PSW.SV = 0;
        
        // Field reads in conditions
        if (PSW.V) {
            R[0] = 1;
        }
        
        // Full register access still works
        PSW = 0x12345678;
    }
}
```

**Before (bit manipulation):**
```isa
behavior: {
    PSW = PSW | (1 << 30);  // Set V flag
    PSW = PSW & ~(1 << 29); // Clear SV flag
}
```

**After (field access):**
```isa
behavior: {
    PSW.V = 1;   // Set V flag - much cleaner!
    PSW.SV = 0;  // Clear SV flag
}
```

**Implementation Details:**
- Registers with fields use a `Register` wrapper class that behaves like both an integer and has field attributes
- Registers without fields remain plain integers (backward compatible)
- Register files with fields create lists of `Register` objects
- Field access uses dynamic attribute access (`__getattr__` and `__setattr__`)
- Proper bit manipulation ensures field changes don't affect other fields

### ✨ New Features

- **Register Wrapper Class**: C union-like behavior supporting both integer and field access
- **Dynamic Field Access**: Fields accessible as attributes (`PSW.V`, `PSW.SV`)
- **Field Assignment**: Direct field updates (`PSW.V = 1`)
- **Enhanced Print State**: Register state display shows both full value and individual fields
- **Backward Compatibility**: Registers without fields continue to work as plain integers

### 🔧 Technical Improvements

#### Python Package

**Simulator Generator (`base_simulator.j2`):**
- Added `Register` wrapper class with:
  - Integer-like behavior (`__int__`, `__add__`, `__sub__`, etc.)
  - Dynamic field access via `__getattr__` and `__setattr__`
  - Proper bit manipulation for field get/set
  - Automatic synchronization between fields and full register value
- Updated register initialization to use `Register` wrapper for registers with fields
- Enhanced `print_state` to display field values alongside full register value

**RTL Code Generation (`simulator.py`):**
- Updated field access to generate `self.PSW.V` instead of `self.PSW_V`
- Field assignments now generate proper attribute assignments
- Maintains backward compatibility for registers without fields

**RTL Interpreter (`rtl_interpreter.py`):**
- Updated `_get_field_value()` to work with `Register` wrapper objects
- Updated `_set_lvalue()` to handle field assignments on `Register` objects
- Falls back to bit manipulation for plain integer registers

**Print State (`simulator.j2`):**
- Enhanced to show field values: `PSW: 0x12345678 (V=0x1, SV=0x1, AV=0x0)`
- Works for both single registers and register files

### 📝 Documentation Updates

- Added register fields examples in test files
- Updated implementation plan document (`REGISTER_FIELDS_IMPLEMENTATION_PLAN.md`)

### 🧪 Testing

- **All 160 Python tests passing** ✅
- **All 50 VS Code extension tests passing** ✅
- TriCore tests with field access (`PSW.V`, `PSW.SV`, `PSW.AV`) working correctly
- All existing tests continue to pass (backward compatibility verified)

### 📦 Files Changed

**Python Package:**
- `isa_dsl/generators/templates/base_simulator.j2` - Added `Register` wrapper class
- `isa_dsl/generators/templates/simulator.j2` - Updated register initialization and print_state
- `isa_dsl/generators/simulator.py` - Updated RTL code generation for field access
- `isa_dsl/runtime/rtl_interpreter.py` - Updated field get/set methods

### 🔄 Migration Guide

No breaking changes. Existing ISA specifications continue to work without modification.

**To use register fields:**
1. Define registers with fields in your ISA specification
2. Use field access syntax: `PSW.V = 1` instead of bit manipulation
3. Read fields in conditions: `if (PSW.V) { ... }`
4. Full register access still works: `PSW = 0x12345678`

**Example:**
```isa
// Define register with fields
sfr PSW 32 {
    V: [30:30]
    SV: [29:29]
    AV: [28:28]
}

// Use in behavior
behavior: {
    PSW.V = 1;      // Set overflow flag
    PSW.SV = PSW.V; // Copy V to SV
}
```

### 🐛 Bug Fixes

- Fixed recursion issues in `Register` class using `object.__setattr__` and `object.__getattribute__`
- Fixed field access code generation to use proper attribute syntax

### 📊 Statistics

- **4 files modified**
- **+250 insertions, -10 deletions**
- **Net code addition**: 240 lines (Register class + updates)

---

## Version 0.3.1 - Built-in Functions and Bitfield Access

**Release Date:** 2026-01-07

### 🎯 Major Changes

#### 1. Built-in Functions Support in RTL Expressions

Added support for built-in functions in RTL behavior descriptions, enabling common operations like sign extension, zero extension, and bit extraction.

**Available Functions:**
- `sign_extend(value, from_bits[, to_bits])` - Sign extend a value from `from_bits` to `to_bits` (default 32)
- `zero_extend(value, from_bits[, to_bits])` - Zero extend a value from `from_bits` to `to_bits` (default 32)
- `extract_bits(value, msb, lsb)` - Extract bits from `msb` to `lsb` (inclusive) from a value

**Function Aliases:**
- `sext` / `sx` - Alias for `sign_extend`
- `zext` / `zx` - Alias for `zero_extend`

**Syntax:**
```isa
instruction ABS {
    format: RR
    encoding: { opcode=1 }
    behavior: {
        R[rd] = sign_extend(R[rs1][7:0], 8, 32);
        R[rd] = zero_extend(R[rs1][15:8], 8);
        R[rd] = extract_bits(R[rs1], 23, 16);
        R[rd] = sext(R[rs1][7:0], 8);  // Using alias
    }
}
```

**Features:**
- Full support in Python simulator (RTL interpreter)
- Argument count validation (2-3 args for extend functions, 3 args for extract_bits)
- Works with bitfield access and nested expressions
- All functions properly handle bit widths and sign extension

#### 2. Bitfield Access Support

Added support for accessing specific bit ranges within registers and values using array-like syntax.

**Syntax:**
```isa
R[rs1][15:8]    // Extract bits 15 to 8 from register R[rs1]
value[msb:lsb]  // Extract bits from any RTL expression
```

**Features:**
- Can be used with registers, constants, and other RTL expressions
- Works seamlessly with built-in functions
- Full support in simulator and RTL interpreter
- Proper bit extraction and masking

**Example:**
```isa
behavior: {
    // Extract lower 8 bits and sign extend
    R[rd] = sign_extend(R[rs1][7:0], 8);
    
    // Extract middle byte
    temp = R[rs1][15:8];
    
    // Combine with extract_bits function
    R[rd] = extract_bits(R[rs1], 23, 16);
}
```

### ✨ New Features

- **Built-in Functions**: `sign_extend`, `zero_extend`, `extract_bits` with full argument validation
- **Function Aliases**: Short aliases (`sext`, `sx`, `zext`, `zx`) for convenience
- **Bitfield Access**: `value[msb:lsb]` syntax for extracting bit ranges
- **VS Code Autocomplete**: Built-in functions appear in completion suggestions within behavior blocks
- **VS Code Validation**: Real-time validation of function names and argument counts
- **Cross-Platform Support**: All features work on both Linux and Windows

### 🔧 Technical Improvements

#### Python Package

**RTL Interpreter (`rtl_interpreter.py`):**
- Added `_apply_builtin_function()` method to handle all built-in functions
- Implemented sign extension with proper bit manipulation
- Implemented zero extension with masking
- Implemented bit extraction from values
- Support for function aliases (sext, sx, zext, zx)
- Proper handling of optional `to_bits` parameter (defaults to 32)

**Simulator Generator (`simulator.j2`):**
- Added `_sign_extend()` helper method to generated simulators
- Added `_zero_extend()` helper method to generated simulators
- Bitfield access properly extracts bits using masking and shifting
- Functions work correctly in all RTL expression contexts

**Grammar (`isa.tx`):**
- Added `RTLBitfieldAccess` rule: `base '[' msb ':' lsb ']'`
- Added `RTLFunctionCall` rule: `function_name '(' args* ')'`
- Updated `RTLExpression` to include function calls
- Updated `RTLExpressionAtom` to include bitfield access

**Model (`isa_model.py`):**
- Added `RTLBitfieldAccess` dataclass with `base`, `msb`, `lsb` fields
- Added `RTLFunctionCall` dataclass with `function_name` and `args` fields
- Updated model converter to parse new constructs
- Updated validator to validate function calls and bitfield access

#### VS Code Extension

**Grammar (`isa.langium`):**
- Fixed left recursion issue with `RTLBitfieldAccess` by introducing `RTLBitfieldBase`
- Added `RTLFunctionCall` to `RTLAtom` and `RTLExpression`
- Proper tokenization precedence for function calls

**Validator (`isa-validator.ts`):**
- Added `checkRTLFunctionCall()` validation method
- Validates function names against known built-ins
- Validates argument counts for each function type
- Shows warnings for unknown functions
- Shows errors for incorrect argument counts

**Completion Provider (`isa-completion-provider.ts`):**
- Added `getRTLBuiltinCompletions()` method
- Detects RTL expression contexts (behavior blocks)
- Provides autocomplete for all 7 built-in functions
- Includes function signatures and documentation
- Suggests functions after operators and at expression start

**Scope Provider:**
- Built-in functions are globally available (no special scope needed)

### 📝 Documentation Updates

- Added examples of built-in functions in test files
- Added bitfield access examples
- Updated RTL expression documentation

### 🧪 Testing

- **All Python tests passing** ✅
- **All VS Code extension tests passing** ✅
- Added comprehensive test suite for built-in functions (`tests/rtl_builtins/`)
  - 9 test cases covering all functions and aliases
  - Tests for correct usage, argument validation, and edge cases
- Added VS Code extension test suite (`builtin-functions.test.ts`)
  - 17 test cases covering parsing, validation, completion, and AST structure
- All end-to-end tests passing with new features

### 📦 Files Changed

**Python Package:**
- `isa_dsl/grammar/isa.tx` - Added bitfield access and function call rules
- `isa_dsl/model/isa_model.py` - Added model classes
- `isa_dsl/model/textx_model_converter.py` - Added conversion logic
- `isa_dsl/model/validator.py` - Added validation
- `isa_dsl/runtime/rtl_interpreter.py` - Added function execution
- `isa_dsl/generators/templates/simulator.j2` - Added helper methods
- `tests/rtl_builtins/` - New comprehensive test suite

**VS Code Extension:**
- `vscode_extension/isa/packages/language/src/isa.langium` - Grammar updates
- `vscode_extension/isa/packages/language/src/isa-validator.ts` - Validation
- `vscode_extension/isa/packages/language/src/isa-completion-provider.ts` - Autocomplete
- `vscode_extension/isa/packages/language/test/builtin-functions.test.ts` - Test suite

### 🔄 Migration Guide

No breaking changes. Existing ISA specifications continue to work without modification.

**To use new features:**
1. Use `sign_extend(value, from_bits[, to_bits])` for sign extension
2. Use `zero_extend(value, from_bits[, to_bits])` for zero extension
3. Use `extract_bits(value, msb, lsb)` for bit extraction
4. Use `value[msb:lsb]` for bitfield access
5. Use aliases (`sext`, `sx`, `zext`, `zx`) for shorter syntax

### 🐛 Bug Fixes

- Fixed left recursion issue in Langium grammar for bitfield access
- Fixed `print_state` method placement in generated simulator
- Improved error handling for Chevrotain recursion issues in VS Code extension

### 📊 Statistics

- **15+ files modified, 2 new test directories**
- **+1200 insertions, -50 deletions**
- **Net code addition**: 1150 lines (features + comprehensive tests)

---

## Version 0.2.0 - Virtual Registers, Register Aliases, and Instruction Aliases

**Release Date:** 2026-01-06

### 🎯 Major Changes

#### 1. Abstract Bundle Instructions with Dynamic Identification

Bundle instructions are now truly abstract - they can contain any instruction that fits in each slot's width, without requiring pre-specification of which instructions can be bundled.

**Breaking Changes:**
- Removed `bundle_instructions` field from instruction definitions
- Bundle instructions now dynamically identify sub-instructions at runtime

#### 2. Virtual Registers Support

Added support for virtual registers - concatenated registers that form wider registers (e.g., 64-bit registers from 32-bit pairs).

**Syntax:**
```isa
virtual register E 64 = {D[0]|D[1]}
virtual register E2 64 = {D[2]|D[3]}
```

**Features:**
- Virtual registers can concatenate multiple physical registers
- Components can be indexed register files (e.g., `D[0]`) or simple registers
- Width validation ensures component widths sum to virtual register width
- Full support in simulator, assembler, and disassembler

#### 3. Register Aliases Support

Added support for register aliases - alternative names for existing registers.

**Syntax:**
```isa
alias SP = R[13]    // Stack Pointer alias
alias LR = R[14]    // Link Register alias
alias PC_ALIAS = PC // Program Counter alias
```

**Features:**
- Aliases can reference indexed register files or simple registers
- Full support in simulator, assembler, and disassembler
- Validation ensures referenced registers exist

#### 4. Instruction Aliases Support

Added support for instruction aliases - different mnemonics for the same instruction with custom assembly syntax.

**Syntax:**
```isa
alias instruction PUSH = STM {
    assembly_syntax: "PUSH R{rd}"
}
```

**Features:**
- Aliases can have custom assembly syntax different from target instruction
- Operand inference for aliases with fewer operands (e.g., PUSH only provides `rd`, but STM needs `rd` and `rs1`)
- Full support in assembler and disassembler
- Validation ensures target instructions exist

**Before:**
```isa
instruction BUNDLE {
    format: BUNDLE_ID
    bundle_format: BUNDLE_64
    encoding: { bundle_opcode=255 }
    bundle_instructions: ADD, SUB  # ❌ No longer needed
}
```

**After:**
```isa
instruction BUNDLE {
    format: BUNDLE_ID
    bundle_format: BUNDLE_64
    encoding: { bundle_opcode=255 }
    # ✅ Any instruction that fits will be automatically identified
}
```

### ✨ New Features

- **Dynamic Instruction Identification**: Bundle slots now automatically identify and execute any instruction that fits in the slot width
- **Improved Flexibility**: Bundle instructions can now contain any combination of instructions without explicit declaration
- **Recursion Prevention**: Fixed infinite recursion issue when executing bundle instructions
- **Virtual Registers**: Concatenate multiple registers to form wider virtual registers
- **Register Aliases**: Define alternative names for registers (e.g., `SP = R[13]`)
- **Instruction Aliases**: Define alternative mnemonics for instructions with custom assembly syntax

### 🔧 Technical Improvements

#### Simulator
- Added `_execute_non_bundle_instruction()` method to prevent recursion when executing bundle slots
- Bundle execution now uses dynamic instruction identification instead of pre-specified instruction lists
- Improved PC handling for bundle execution
- Added virtual register read/write support with correct concatenation order (LSB first, MSB last)
- Added register alias resolution
- Added instruction alias recognition and operand inference

#### Assembler
- Added virtual register support in operand parsing
- Added register alias resolution
- Added instruction alias encoding with operand inference (e.g., PUSH → STM with rs1=rd)

#### Disassembler
- Updated to dynamically disassemble instructions in bundle slots
- Removed dependency on `bundle_instructions` field
- Added virtual register support in disassembly output
- Added register alias support in disassembly output
- Added instruction alias disassembly (recognizes aliases and outputs custom syntax)

#### Grammar Updates
- Removed `bundle_instructions` and `BundleInstructionList` from textX grammar (`isa.tx`)
- Removed `bundle_instructions` and `BundleInstructionList` from Langium grammar (`isa.langium`)
- Added `VirtualRegister`, `RegisterAlias`, and `InstructionAlias` rules to both grammars
- Updated `RegisterBlock` to include virtual registers and aliases
- Updated model to remove `bundle_instructions` field from `Instruction` class
- Added `VirtualRegister`, `RegisterAlias`, and `InstructionAlias` to model classes

#### VS Code Extension
- Fixed virtual register validation in Langium validator
- Added `checkVirtualRegister` validation method
- Updated grammar to correctly parse virtual registers as separate elements
- Validation now checks component existence, index ranges, and width matching

### 📝 Documentation Updates

- Updated `DSL_Specification.md` to reflect abstract bundle instruction behavior
- Updated `Simulator.md` with dynamic instruction identification details
- Updated `Disassembler.md` to explain dynamic disassembly in bundles
- Removed all `bundle_instructions` examples from documentation

### 🧪 Testing

- **All 126 Python tests passing** ✅
- **All 18 VS Code extension tests passing** ✅
- Updated all test data files to remove `bundle_instructions`
- Fixed bundle simulation test that was failing due to recursion
- Added comprehensive test suite for virtual registers (15+ tests)
- Added comprehensive test suite for register aliases (10+ tests)
- Added comprehensive test suite for instruction aliases (15+ tests)
- All end-to-end tests passing with new features

### 📦 Files Changed

- **Grammar Files**: `isa.tx`, `isa.langium` (added virtual registers, aliases)
- **Model**: `isa_model.py`, `textx_model_converter.py`, `model_merger.py`, `validator.py`, `assembly_syntax_processor.py`
- **Runtime**: `rtl_interpreter.py` (virtual register support)
- **Templates**: `simulator.j2`, `assembler.j2`, `disassembler.j2` (all new features)
- **Generators**: `simulator.py`, `assembler.py` (new feature support)
- **Tests**: Added `tests/aliases/` with comprehensive test suite
- **VS Code Extension**: `isa-validator.ts`, `isa.langium` (validation fixes)
- **Documentation**: Release notes updated

### 🔄 Migration Guide

If you have existing ISA specifications with `bundle_instructions`:

1. **Remove the `bundle_instructions` field** from all bundle instruction definitions
2. **No other changes needed** - the simulator will automatically identify instructions in slots
3. **Test your specifications** - all existing functionality is preserved, but now more flexible

### 🐛 Bug Fixes

- Fixed infinite recursion when executing bundle instructions
- Fixed bundle instruction identification in simulator

### 📊 Statistics

- **22 files modified, 6 new test files**
- **+1869 insertions, -44 deletions**
- **Net code addition**: 1825 lines (new features + comprehensive tests)

---

## Version 0.1.1 - Previous Release

### Features
- VS Code extension with Language Server Protocol support
- GitHub Actions CI/CD integration
- Comprehensive test suite (111 tests)
- Multi-file support with `#include` directives
- Variable-length instruction support
- Instruction bundling support
- SIMD/vector register support

### Improvements
- Modular test suite organization
- Enhanced documentation
- Codebase cleanup and optimization

---

## Version 0.1.0 - Initial Release

### Features
- Complete ISA DSL specification
- Code generation for simulators, assemblers, disassemblers, and documentation
- RTL behavior specification
- Register definitions (GPR, SFR, vector)
- Instruction format definitions
- Encoding specifications
- Assembly syntax support

