# Release Notes

## Version 0.2.0 - Virtual Registers, Register Aliases, and Instruction Aliases

**Release Date:** 2024-01-05

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

