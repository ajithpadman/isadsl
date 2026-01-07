# Release Notes

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

