# ISA DSL Specification

This document provides a complete specification of the ISA Domain Specific Language (DSL) for describing Instruction Set Architectures.

**Status**: ✅ Production Ready (Beta) - All features are implemented and tested. The test suite includes comprehensive tests covering all features, all passing.

## Table of Contents

1. [Overview](#overview)
2. [File Structure](#file-structure)
3. [Multi-File Support](#multi-file-support)
4. [Architecture Definition](#architecture-definition)
5. [Registers](#registers)
6. [Instruction Formats](#instruction-formats)
7. [Instructions](#instructions)
8. [RTL Behavior](#rtl-behavior)
   - [Expressions](#expressions)
   - [Shift Operators](#shift-operators)
   - [Ternary Conditional Expressions](#ternary-conditional-expressions)
   - [Bitfield Access](#bitfield-access)
   - [Built-in Functions](#built-in-functions)
9. [Variable-Length Instructions](#variable-length-instructions)
10. [Instruction Bundling](#instruction-bundling)
11. [SIMD Vector Support](#simd-vector-support)
12. [Assembly Syntax](#assembly-syntax)
13. [Distributed Operands](#distributed-operands)
14. [Best Practices](#best-practices)

## Overview

The ISA DSL is a domain-specific language for describing Instruction Set Architectures. It allows you to:

- Define register architectures (GPRs, SFRs, vector registers)
- Specify instruction formats and bit layouts
- Define instruction encodings and behavior
- Describe instruction behavior using RTL (Register Transfer Level) notation
- Support variable-length instructions
- Support instruction bundling
- Support SIMD/vector operations
- Generate simulators, assemblers, disassemblers, and documentation

## File Structure

An ISA specification file (`.isa`) follows this structure:

```isa
architecture ArchitectureName {
    word_size: 32
    endianness: little
    
    registers {
        // Register definitions
    }
    
    formats {
        // Instruction format definitions
    }
    
    instructions {
        // Instruction definitions
    }
}
```

## Multi-File Support

The ISA DSL supports organizing ISA specifications across multiple files using `#include` directives. This enables modular organization of large ISA specifications.

### Include Directive

Use `#include` to include other ISA files:

```isa
#include "registers.isa"
#include "formats.isa"
#include "instructions.isa"
```

**Syntax**: `#include "<file_path>"`

- `file_path` can be absolute or relative to the current file
- Included files can contain partial definitions (registers, formats, or instructions without an architecture block)
- Included files can also contain complete architecture blocks (for inheritance mode)

### Cross-File References

The ISA DSL uses textX scope providers to resolve cross-file references automatically:

- **Format references**: Instructions in one file can reference formats defined in another file
- **Automatic resolution**: The scope provider searches included files to resolve format references
- **No explicit imports needed**: References are resolved automatically based on file inclusion order

**Example**: An instruction file can reference a format from a formats file:

```isa
// formats.isa
format R_TYPE 32 {
    opcode: [0:5]
    rd: [6:8]
}

// instructions.isa
#include "formats.isa"

instruction ADD {
    format: R_TYPE  // Automatically resolved from formats.isa
    encoding: { opcode=1 }
}
```

### Merge Mode

When all included files contain partial definitions (no architecture blocks), they are merged into the main file:

```isa
// main.isa
architecture MyISA {
    word_size: 32
    #include "registers.isa"
    #include "formats.isa"
    #include "instructions.isa"
}
```

### Inheritance Mode

When included files contain architecture blocks, the main file extends the base architecture:

```isa
// base.isa
architecture BaseISA {
    word_size: 32
    registers { ... }
}

// extended.isa
#include "base.isa"

architecture ExtendedISA {
    // Extends BaseISA, can override or add definitions
}
```

### Best Practices

1. **Organize by component**: Separate registers, formats, and instructions into different files
2. **Use descriptive names**: Name files based on their content (e.g., `arm_cortex_a9_registers.isa`)
3. **Relative paths**: Use relative paths for portability
4. **Reference example**: See `examples/arm_cortex_a9.isa` for a complete multi-file example

## Architecture Definition

The `architecture` block defines the top-level properties of your ISA:

```isa
architecture MyISA {
    word_size: 32          // Instruction word size in bits
    endianness: little     // Byte order: "little" or "big"
}
```

### Properties

- **`word_size`**: The size of instruction words in bits (typically 16, 32, or 64)
- **`endianness`**: Byte ordering (`little` or `big`)

## Registers

Registers are defined in the `registers` block. There are three types:

### General Purpose Registers (GPR)

Register files with multiple registers:

```isa
registers {
    gpr R 32 [8]    // 8 registers, each 32 bits wide (R[0] to R[7])
}
```

**Syntax**: `gpr <name> <width> [<count>]`

- `name`: Register file name (e.g., `R`)
- `width`: Width of each register in bits (e.g., `32`)
- `count`: Number of registers in the file (e.g., `[8]`)

**Access in RTL**: `R[rd]` - access register `rd` in register file `R`

### Special Function Registers (SFR)

Single registers, optionally with named fields:

```isa
registers {
    sfr PC 32                    // Simple register
    sfr FLAGS 32 {               // Register with fields
        Z: [0:0]                 // Zero flag (bit 0)
        C: [1:1]                 // Carry flag (bit 1)
        N: [2:2]                 // Negative flag (bit 2)
        V: [3:3]                 // Overflow flag (bit 3)
    }
}
```

**Syntax**: `sfr <name> <width> [{ <field_name>: [<lsb>:<msb>] }]`

- `name`: Register name (e.g., `PC`, `FLAGS`)
- `width`: Register width in bits
- `fields`: Optional named fields with bit ranges

**Access in RTL**:
- Single register: `PC` - access the PC register directly
- Register field: `FLAGS.Z` - access the Z field in FLAGS register

**Note**: Bit ranges use `[lsb:msb]` format, where `lsb` is the least significant bit and `msb` is the most significant bit.

### Vector Registers (SIMD)

Vector registers for SIMD operations:

```isa
registers {
    vec V 128 <32, 4>    // 128-bit vector, 4 lanes of 32 bits each
    vec V 256 <32, 8> [8]  // 8 vector registers, each 256 bits, 8 lanes of 32 bits
}
```

**Syntax**: `vec <name> <width> <element_width, lanes> [<count>]?`

- `name`: Register name (e.g., `V`)
- `width`: Total register width in bits (e.g., `128`)
- `element_width`: Width of each element/lane in bits (e.g., `32`)
- `lanes`: Number of lanes/elements (e.g., `4`)
- `count`: Optional number of vector registers (for vector register files)

**Access in RTL**: `V[vd][lane]` - access lane `lane` in vector register `vd`

**Example**:
```isa
behavior: {
    V[vd][0] = V[vs1][0] + V[vs2][0];  // Lane 0
    V[vd][1] = V[vs1][1] + V[vs2][1];  // Lane 1
    V[vd][2] = V[vs1][2] + V[vs2][2];  // Lane 2
    V[vd][3] = V[vs1][3] + V[vs2][3];  // Lane 3
}
```

## Instruction Formats

Instruction formats define the bit layout of instructions:

```isa
formats {
    format R_TYPE 32 {
        opcode: [0:5]      // Bits 0-5: opcode (6 bits)
        rd: [6:8]          // Bits 6-8: destination register (3 bits)
        rs1: [9:11]        // Bits 9-11: source register 1 (3 bits)
        rs2: [12:14]       // Bits 12-14: source register 2 (3 bits)
        funct: [15:17]     // Bits 15-17: function code (3 bits)
        unused: [18:31]    // Bits 18-31: unused (14 bits)
    }
    
    format I_TYPE 32 {
        opcode: [0:5]
        rd: [6:8]
        rs1: [9:11]
        imm: [12:31]       // Immediate value (20 bits)
    }
    
    format J_TYPE 32 {
        opcode: [0:5]
        target: [6:31]     // Jump target address (26 bits)
    }
}
```

**Syntax**: `format <name> <width> { <field_name>: [<lsb>:<msb>] }`

**Important**: 
- Field bit ranges must not overlap
- Total field width should not exceed the format width
- Field names are used to reference fields in instructions
- Bit ranges use `[lsb:msb]` format

### Variable-Length Formats

Formats can have any width (16-bit, 32-bit, 64-bit, etc.):

```isa
formats {
    format SHORT_16 16 {
        opcode: [0:5]
        rd: [6:8]
        rs1: [9:11]
        immediate: [12:15]
    }
    
    format LONG_32 32 {
        opcode: [0:6]
        funct: [7:10]
        rd: [11:15]
        rs1: [16:20]
        rs2: [21:25]
        immediate: [26:31]
    }
}
```

### Identification Fields

For variable-length instructions, formats can specify which fields are used for instruction identification:

```isa
format SHORT_16 16 {
    opcode: [0:5]
    rd: [6:8]
    rs1: [9:11]
    immediate: [12:15]
    identification_fields: opcode
}
```

**Syntax**: `identification_fields: <field1>, <field2>, ...`

- Lists field names used for matching instructions
- If not specified, all encoding fields are used (backward compatible)
- Allows efficient instruction identification with minimum bits

### Distributed Opcode Fields

Opcodes can be split across multiple non-contiguous fields:

```isa
format DIST_32 32 {
    opcode_low: [0:3]
    opcode_high: [20:23]
    rd_low: [4:7]
    rd_high: [16:19]
    rs1: [8:11]
    rs2: [12:15]
    immediate: [24:31]
    identification_fields: opcode_low, opcode_high
}
```

Both fields are checked during identification.

## Instructions

Instructions define the actual operations:

```isa
instructions {
    instruction ADD {
        format: R_TYPE
        encoding: { opcode=1, funct=0 }
        operands: rd, rs1, rs2
        assembly_syntax: "ADD R{rd}, R{rs1}, R{rs2}"
        behavior: {
            R[rd] = R[rs1] + R[rs2];
            FLAGS.Z = (R[rd] == 0) ? 1 : 0;
        }
    }
}
```

### Instruction Fields

1. **`format`**: Reference to an instruction format (required if using encoding/operands)
2. **`encoding`**: Fixed field values that identify this instruction
3. **`operands`**: List of operand names (must match format field names)
4. **`assembly_syntax`**: Optional format string for disassembly output
5. **`behavior`**: RTL statements describing instruction behavior

### Encoding

The `encoding` block specifies fixed values for format fields:

```isa
encoding: { opcode=1, funct=0 }
```

This means:
- The `opcode` field must equal `1`
- The `funct` field must equal `0`

**Important**: Encoding fields must reference fields from the instruction's `format`, not from `bundle_format` (for bundle instructions).

### Operands

Operands are listed in the order they appear in assembly:

```isa
operands: rd, rs1, rs2
```

Operand names must match field names in the instruction format.

### Assembly Syntax

The `assembly_syntax` field defines how instructions are disassembled:

```isa
assembly_syntax: "ADD R{rd}, R{rs1}, R{rs2}"
```

Uses Python's `.format()` syntax where `{operand_name}` is replaced with operand values.

See [Assembly Syntax](#assembly-syntax) section for details.

## RTL Behavior

RTL (Register Transfer Level) behavior describes what each instruction does.

### Assignment

```isa
behavior: {
    R[rd] = R[rs1] + R[rs2];           // Register assignment
    FLAGS.Z = (R[rd] == 0) ? 1 : 0;    // Flag update
}
```

### Conditional Statements

```isa
behavior: {
    if (R[rs1] == R[rs2]) {
        PC = PC + (offset << 2);
    }
}
```

With else clause:

```isa
behavior: {
    if (R[rs1] < R[rs2]) {
        R[rd] = 1;
    } else {
        R[rd] = 0;
    }
}
```

### Memory Access

Load from memory:

```isa
behavior: {
    R[rd] = MEM[R[rs1] + imm];
}
```

Store to memory:

```isa
behavior: {
    MEM[R[rs1] + imm] = R[rs2];
}
```

### Expressions

Supported operators:

- **Arithmetic**: `+`, `-`, `*`, `/`, `%`
- **Bitwise**: `&`, `|`, `^`, `~`
- **Shift**: `<<` (left shift), `>>` (right shift, arithmetic)
- **Comparison**: `==`, `!=`, `<`, `>`, `<=`, `>=`
- **Ternary**: `condition ? then_value : else_value`

#### Shift Operators

The ISA DSL supports bitwise shift operations:

**Left Shift (`<<`)**:
```isa
behavior: {
    R[rd] = R[rs1] << R[rs2];    // Shift left by register value
    R[rd] = R[rs1] << 2;         // Shift left by immediate
    PC = PC + (offset << 2);     // Shift for address calculation
}
```

**Right Shift (`>>`)**:
```isa
behavior: {
    R[rd] = R[rs1] >> R[rs2];    // Arithmetic right shift by register value
    R[rd] = R[rs1] >> 3;         // Arithmetic right shift by immediate
}
```

**Notes**:
- Left shift (`<<`) performs logical left shift, filling with zeros
- Right shift (`>>`) performs arithmetic right shift (sign-extending for signed values)
- Shift amounts can be register values or immediate constants
- Results are masked to 32 bits

**Example**:
```isa
instruction SHL {
    format: R_TYPE
    encoding: { opcode=0x10 }
    operands: rd, rs1, rs2
    behavior: {
        R[rd] = R[rs1] << R[rs2];  // R[rd] = R[rs1] * (2^R[rs2])
    }
}

instruction SHR {
    format: R_TYPE
    encoding: { opcode=0x11 }
    operands: rd, rs1, rs2
    behavior: {
        R[rd] = R[rs1] >> R[rs2];  // Arithmetic right shift
    }
}
```

#### Ternary Conditional Expressions

Ternary expressions allow conditional value selection:

**Syntax**: `condition ? then_value : else_value`

```isa
behavior: {
    R[rd] = (R[rs1] != 0) ? R[rs1] : R[rs2];  // Select R[rs1] if non-zero, else R[rs2]
    FLAGS.Z = (R[rd] == 0) ? 1 : 0;           // Set zero flag
    R[rd] = (R[rs1] > 0) ? 1 : ((R[rs1] < 0) ? -1 : 0);  // Nested ternary (sign function)
}
```

**Notes**:
- The condition must be a simple expression (use parentheses for complex conditions)
- Nested ternaries are supported
- Ternary expressions can be used anywhere an expression is expected

**Example**:
```isa
instruction TERNARY {
    format: R_TYPE
    encoding: { opcode=0x12 }
    operands: rd, rs1, rs2
    behavior: {
        R[rd] = (R[rs1] != 0) ? R[rs1] : R[rs2];
    }
}

instruction TERNARY_SHIFT {
    format: R_TYPE
    encoding: { opcode=0x13 }
    operands: rd, rs1, rs2
    behavior: {
        R[rd] = (R[rs1] != 0) ? (R[rs1] << 2) : (R[rs2] >> 2);
    }
}
```

### Operand References

Operands defined in the instruction can be used directly:

```isa
instruction ADDI {
    format: I_TYPE
    encoding: { opcode=2 }
    operands: rd, rs1, imm
    behavior: {
        R[rd] = R[rs1] + imm;    // 'imm' refers to the immediate operand
    }
}
```

### Register Access

- **Register file**: `R[rd]` - access register `rd` in register file `R`
- **Single register**: `PC` - access the PC register directly
- **Register field**: `FLAGS.Z` - access the Z field in FLAGS register
- **Vector register**: `V[vd][lane]` - access lane `lane` in vector register `vd`

### Constants

Numeric constants can be used directly:

```isa
behavior: {
    R[rd] = R[rs1] + 1;
    PC = PC + 4;
}
```

Constants can also be specified in hexadecimal or binary:

```isa
behavior: {
    R[rd] = 0xFF;        // Hexadecimal
    R[rd] = 0b1010;      // Binary
}
```

### Bitfield Access

You can access specific bit ranges from registers or values using bitfield syntax:

**Syntax**: `value[msb:lsb]`

```isa
behavior: {
    R[rd] = R[rs1][15:8];           // Extract bits 15-8 from R[rs1]
    R[rd] = R[rs1][msb:lsb];        // Extract bits using variables
    temp = R[rs1][7:0];             // Extract lower 8 bits
    R[rd] = sign_extend(R[rs1][15:0], 16);  // Extract and sign extend
}
```

**Notes**:
- Bit ranges use `[msb:lsb]` format, where `msb` is the most significant bit and `lsb` is the least significant bit
- Both `msb` and `lsb` can be constants or expressions
- Bitfield access extracts the specified bit range and zero-extends to the target width
- Bitfield access can be used with built-in functions for sign/zero extension

**Example**:
```isa
instruction EXTRACT {
    format: R_TYPE
    encoding: { opcode=1 }
    operands: rd, rs1
    behavior: {
        // Extract bits [15:8] from R[rs1]
        R[rd] = R[rs1][15:8];
    }
}

instruction BITFIELD {
    format: R_TYPE
    encoding: { opcode=3 }
    operands: rd, rs1, rs2
    behavior: {
        // Extract bits [msb:lsb] where msb and lsb come from rs2
        msb = R[rs2][7:4];
        lsb = R[rs2][3:0];
        R[rd] = R[rs1][msb:lsb];
    }
}
```

### Built-in Functions

The ISA DSL provides built-in functions for common operations:

#### Sign Extension

**Functions**: `sign_extend(value, from_bits)` or `sign_extend(value, from_bits, to_bits)`

**Aliases**: `sext(value, from_bits)` or `sext(value, from_bits, to_bits)`, `sx(value, from_bits)` or `sx(value, from_bits, to_bits)`

Sign-extends a value from `from_bits` to `to_bits` (default 32 bits if `to_bits` is omitted).

```isa
behavior: {
    R[rd] = sign_extend(R[rs1][7:0], 8);        // Sign extend 8-bit value to 32 bits
    R[rd] = sign_extend(R[rs1][15:0], 16, 32); // Sign extend 16-bit value to 32 bits
    R[rd] = sext(R[rs1][7:0], 8);              // Using alias
    R[rd] = sx(R[rs1][7:0], 8);                // Using alias
}
```

**Example**:
```isa
instruction SIGN_EXT {
    format: R_TYPE
    encoding: { opcode=2 }
    operands: rd, rs1
    behavior: {
        // Sign extend lower 16 bits of R[rs1] to 32 bits
        R[rd] = sign_extend(R[rs1][15:0], 16);
    }
}
```

#### Zero Extension

**Functions**: `zero_extend(value, from_bits)` or `zero_extend(value, from_bits, to_bits)`

**Aliases**: `zext(value, from_bits)` or `zext(value, from_bits, to_bits)`, `zx(value, from_bits)` or `zx(value, from_bits, to_bits)`

Zero-extends a value from `from_bits` to `to_bits` (default 32 bits if `to_bits` is omitted).

```isa
behavior: {
    R[rd] = zero_extend(R[rs1][7:0], 8);        // Zero extend 8-bit value to 32 bits
    R[rd] = zero_extend(R[rs1][15:0], 16, 32); // Zero extend 16-bit value to 32 bits
    R[rd] = zext(R[rs1][7:0], 8);              // Using alias
    R[rd] = zx(R[rs1][7:0], 8);                // Using alias
}
```

**Example**:
```isa
instruction ZERO_EXT {
    format: R_TYPE
    encoding: { opcode=4 }
    operands: rd, rs1
    behavior: {
        // Zero extend lower 8 bits of R[rs1] to 32 bits
        R[rd] = zero_extend(R[rs1][7:0], 8);
    }
}
```

#### Bit Extraction

**Function**: `extract_bits(value, msb, lsb)`

Extracts bits `[msb:lsb]` from a value.

```isa
behavior: {
    R[rd] = extract_bits(R[rs1], 15, 8);        // Extract bits [15:8]
    R[rd] = extract_bits(R[rs1], 23, 16);       // Extract bits [23:16]
    temp = extract_bits(R[rs1], 7, 0);          // Extract lower 8 bits
    R[rd] = sign_extend(extract_bits(R[rs1], 15, 8), 8);  // Extract and sign extend
}
```

**Example**:
```isa
instruction EXTRACT_BITS {
    format: R_TYPE
    encoding: { opcode=6 }
    operands: rd, rs1
    behavior: {
        // Extract bits [23:16] using function call
        R[rd] = extract_bits(R[rs1], 23, 16);
    }
}
```

**Note**: `extract_bits(value, msb, lsb)` is equivalent to `value[msb:lsb]`, but the function form can be more readable in complex expressions.

#### Combining Built-in Functions

Built-in functions can be combined with bitfield access and other operations:

```isa
behavior: {
    // Extract bits and sign extend
    temp = extract_bits(R[rs1], 15, 8);
    R[rd] = sign_extend(temp, 8);
    
    // Extract bits and zero extend
    R[rd] = zero_extend(R[rs1][15:8], 8);
    
    // Extract, extend, and shift
    R[rd] = (sign_extend(R[rs1][7:0], 8) << 2);
}
```

**Complete Example**:
```isa
instruction EXTRACT {
    format: R_TYPE
    encoding: { opcode=1 }
    operands: rd, rs1
    behavior: {
        // Extract bits [15:8] from R[rs1] and zero-extend to 32 bits
        R[rd] = zero_extend(R[rs1][15:8], 8);
    }
}

instruction BITFIELD_SIGN_EXT {
    format: R_TYPE
    encoding: { opcode=7 }
    operands: rd, rs1
    behavior: {
        // Extract bits [15:8] and sign extend
        temp = extract_bits(R[rs1], 15, 8);
        R[rd] = sign_extend(temp, 8);
    }
}
```

### For Loops

RTL supports for loops for repetitive operations:

```isa
behavior: {
    for (i = 0; i < 4; i = i + 1) {
        V[vd][i] = V[vs1][i] + V[vs2][i];
    }
}
```

**Syntax**: `for (init; condition; update) { statements }`

## Variable-Length Instructions

The ISA DSL supports instructions of varying widths (16-bit, 32-bit, 64-bit, etc.) with dynamic identification.

### Key Features

1. **Variable Instruction Widths**: Instructions can be 16-bit, 32-bit, 64-bit, or any custom width
2. **Dynamic Identification**: Instructions are identified using minimum required bits before full decoding
3. **Identification Fields**: Formats can specify which fields are used for instruction identification
4. **Distributed Opcodes**: Support for opcodes split across multiple non-contiguous fields
5. **Backward Compatible**: Existing ISAs without identification fields continue to work

### Format Specification

Formats can specify which fields are used to identify instructions:

```isa
format SHORT_16 16 {
    opcode: [0:5]
    rd: [6:8]
    rs1: [9:11]
    immediate: [12:15]
    identification_fields: opcode
}
```

The `identification_fields` keyword lists the field names used for matching. If not specified, all encoding fields are used (backward compatible).

### Instruction Examples

**16-bit Instruction:**
```isa
instruction ADD16 {
    format: SHORT_16
    encoding: { opcode=1 }
    operands: rd, rs1, immediate
    behavior: {
        R[rd] = R[rs1] + immediate;
    }
}
```

**32-bit Instruction:**
```isa
instruction ADD32 {
    format: LONG_32
    encoding: { opcode=2, funct=0 }
    operands: rd, rs1, rs2
    behavior: {
        R[rd] = R[rs1] + R[rs2];
    }
}
```

**Distributed Opcode:**
```isa
instruction ADD_DIST {
    format: DIST_32
    encoding: { opcode_low=3, opcode_high=0 }
    operands: rd(rd_low, rd_high), rs1, rs2
    behavior: {
        R[rd] = R[rs1] + R[rs2];
    }
}
```

### Matching Process

The simulator uses a two-step process:

1. **Identification**: Load minimum bits needed and match using identification fields
2. **Execution**: Load full instruction width and execute

**Example: 16-bit and 32-bit Instructions**

**Memory at PC=0x0000:**
```
0x0000: 0x5201  (16-bit: ADD16, opcode=1)
0x0002: 0x411802  (32-bit: ADD32, opcode=2, funct=0)
```

**Execution:**

1. **Step 1 (PC=0x0000):**
   - Load 16 bits: `0x5201`
   - Check opcode[0:5] = 1 → matches ADD16
   - Execute ADD16
   - PC += 2

2. **Step 2 (PC=0x0002):**
   - Load 16 bits: `0x1802` (first 16 bits of 32-bit instruction)
   - Check opcode[0:5] = 2 → no 16-bit match
   - Load 32 bits: `0x411802`
   - Check opcode[0:6]=2, funct[7:10]=0 → matches ADD32
   - Execute ADD32
   - PC += 4

### Best Practices

1. **Specify Identification Fields**: Always specify `identification_fields` for efficient matching
2. **Use Shortest Unique Fields**: Choose fields that uniquely identify the instruction with minimum bits
3. **Order Matters**: Formats are checked shortest-first, so ensure shorter formats don't match longer instructions
4. **Test Thoroughly**: Test with mixed-width instruction sequences

### Backward Compatibility

Existing ISAs without `identification_fields` continue to work:
- All encoding fields are used for matching
- Default behavior: load format width, match, execute
- No changes required to existing ISA definitions

## Instruction Bundling

Instruction bundling allows multiple instructions to be packed into a single wider instruction word.

### Bundle Format Definition

Define a bundle format that specifies how instructions are packed:

```isa
formats {
    bundle format BUNDLE_64 64 {
        instruction_start: 8
        slot0: [8:39]
        slot1: [40:71]
    }
}
```

**Syntax**: `bundle format <name> <width> { slot_name: [<lsb>:<msb>] }`

- `name`: Bundle format name
- `width`: Total bundle width in bits
- `instruction_start`: Optional offset where instruction slots start
- `slots`: Slot definitions with bit ranges

### Bundle Instruction Definition

Define a bundle instruction that uses both a format (for identification) and a bundle format (for slot layout):

```isa
formats {
    format BUNDLE_ID 80 {
        bundle_opcode: [0:7]
    }
    
    bundle format BUNDLE_64 80 {
        instruction_start: 8
        slot0: [8:39]
        slot1: [40:71]
    }
}

instructions {
    instruction BUNDLE {
        format: BUNDLE_ID          # Format for bundle identification
        bundle_format: BUNDLE_64   # Bundle format for slot layout
        encoding: { bundle_opcode=255 }  # Special opcode to identify bundle
        assembly_syntax: "BUNDLE{{ {slot0}, {slot1} }}"
    }
}
```

**Important:** Bundle instructions require:
- A **format** that defines fields for bundle identification (e.g., `bundle_opcode`)
- A **bundle_format** that defines the slot layout
- An **encoding** that references fields in the format (not slots)

**Dynamic Instruction Identification:** Bundle instructions are abstract - any instruction that fits in a slot's width will be dynamically identified and executed at runtime. You do not need to specify which instructions can be bundled.

### Bundle Identification Fields

Bundle formats can also specify identification fields:

```isa
bundle format BUNDLE_64 80 {
    instruction_start: 8
    identification_fields: bundle_opcode
    slot0: [8:39]
    slot1: [40:71]
}
```

### Assembly Syntax

Use the `bundle{...}` syntax to bundle multiple instructions:

```asm
# Bundle two instructions
bundle{ADD R1, R2, R3, SUB R4, R5, 10}

# This creates a bundle containing:
# - ADD R1, R2, R3 in slot0
# - SUB R4, R5, 10 in slot1
```

### Execution Order

- Sub-instructions are executed in slot order (slot0, slot1, ...)
- All sub-instructions in a bundle execute atomically
- PC advances by bundle width after bundle execution

### Design Considerations

**Bundle Encoding:**
- Bundle instructions use a **format** (not the bundle_format) for encoding identification
- The **bundle_format** is used only for slot layout, not for encoding
- This separation allows clear identification and flexible slot layouts

**Slot Widths:**
- Slots can have different widths
- Total bundle width = sum of slot widths (plus any encoding fields)
- Sub-instructions must fit within their assigned slots

## SIMD Vector Support

The ISA DSL supports SIMD (Single Instruction, Multiple Data) vector instructions.

### Vector Register Definition

```isa
registers {
    vec V 128 <32, 4>    // 128-bit vector, 4 lanes of 32 bits each
    vec V 256 <32, 8> [8]  // 8 vector registers, each 256 bits, 8 lanes
}
```

**Syntax**: `vec <name> <width> <element_width, lanes> [<count>]?`

### Vector Instruction Examples

**Vector-Vector Operations:**
```isa
instruction VADD {
    format: VV_TYPE
    encoding: { opcode=32, funct=0 }
    operands: vd, vs1, vs2
    behavior: {
        V[vd][0] = V[vs1][0] + V[vs2][0];
        V[vd][1] = V[vs1][1] + V[vs2][1];
        V[vd][2] = V[vs1][2] + V[vs2][2];
        V[vd][3] = V[vs1][3] + V[vs2][3];
    }
}
```

**Vector-Scalar Operations:**
```isa
instruction VADD_SCALAR {
    format: VS_TYPE
    encoding: { opcode=33, funct=0 }
    operands: vd, vs1, rs2
    behavior: {
        V[vd][0] = V[vs1][0] + R[rs2];
        V[vd][1] = V[vs1][1] + R[rs2];
        V[vd][2] = V[vs1][2] + R[rs2];
        V[vd][3] = V[vs1][3] + R[rs2];
    }
}
```

**Vector Memory Operations:**
```isa
instruction VLOAD {
    format: VI_TYPE
    encoding: { opcode=35 }
    operands: vd, vs1, imm
    behavior: {
        V[vd][0] = MEM[R[vs1] + imm + 0];
        V[vd][1] = MEM[R[vs1] + imm + 4];
        V[vd][2] = MEM[R[vs1] + imm + 8];
        V[vd][3] = MEM[R[vs1] + imm + 12];
    }
}
```

**Vector Reduction Operations:**
```isa
instruction VDOT {
    format: VV_TYPE
    encoding: { opcode=32, funct=8 }
    operands: vd, vs1, vs2
    behavior: {
        R[vd] = 0;
        R[vd] = R[vd] + (V[vs1][0] * V[vs2][0]);
        R[vd] = R[vd] + (V[vs1][1] * V[vs2][1]);
        R[vd] = R[vd] + (V[vs1][2] * V[vs2][2]);
        R[vd] = R[vd] + (V[vs1][3] * V[vs2][3]);
    }
}
```

### Lane Access

- `V[reg_index][lane_index]`: Access specific lane of a vector register
- `lane_index` can be:
  - A constant (e.g., `0`, `1`, `2`)
  - An operand reference (e.g., `i` if `i` is an operand)
  - Used in for loops for repetitive operations

## Assembly Syntax

The `assembly_syntax` field defines how instructions are disassembled.

### Basic Syntax

```isa
instruction ADD {
    format: R_TYPE
    encoding: { opcode=1, funct=0 }
    operands: rd, rs1, rs2
    assembly_syntax: "ADD R{rd}, R{rs1}, R{rs2}"
}
```

**Output**: `ADD R3, R4, R5`

### Format String Rules

The `assembly_syntax` format string uses **Python's `.format()` method**:

- **Operand substitution**: `{operand_name}` is replaced with the operand value
- **Literal braces**: Use `{{` for literal `{` and `}}` for literal `}`
- **Register formatting**: Include register prefixes in the format string (e.g., `R{rd}`)
- **Custom formatting**: Any valid Python format string syntax

**Important:** To include literal curly braces in the output, you must escape them:
- `{{` in the ISA file produces `{` in the output
- `}}` in the ISA file produces `}` in the output
- `{name}` in the ISA file is a placeholder that gets replaced

### Examples

- `"ADD R{rd}, R{rs1}, R{rs2}"` → `"ADD R3, R4, R5"`
- `"MOV {rd}, {immediate}"` → `"MOV 5, 10"`
- `"VADD V{vd}, V{vs1}, V{vs2}"` → `"VADD V2, V3, V4"`

### Bundle Instructions

Bundle instructions support `assembly_syntax` with special slot placeholders:

```isa
instruction BUNDLE {
    format: BUNDLE_ID
    bundle_format: BUNDLE_64
    encoding: { bundle_opcode=255 }
    assembly_syntax: "BUNDLE{{ {slot0}, {slot1} }}"
}
```

**Slot Placeholders**:
- `{slot0}`, `{slot1}`, etc. - Replaced with the disassembled instruction from each slot
- Each slot is disassembled using the appropriate instruction's `assembly_syntax` if available

**Output**: `BUNDLE{ ADD R3, R4, R5, ADD_DIST R10, R4, R5 }`

### Using Curly Braces

**Parser Support**: The parser fully supports curly braces in `assembly_syntax` strings, including patterns like `"BUNDLE{{ {slot0}, {slot1} }}"`. You can use curly braces freely without workarounds.

**Quick Reference**:

| What You Want in Output | Write in ISA File |
|------------------------|-------------------|
| `{` (literal brace) | `{{` |
| `}` (literal brace) | `}}` |
| `{name}` (placeholder) | `{name}` |
| `{{` (two literal braces) | `{{{{` |
| `}}` (two literal braces) | `}}}}` |

**Common Patterns**:

- Bundle with curly braces: `"BUNDLE{{ {slot0}, {slot1} }}"`
- Bundle with square brackets: `"BUNDLE[ {slot0}, {slot1} ]"`
- Instruction with register formatting: `"ADD R{rd}, R{rs1}, R{rs2}"`
- Instruction with immediate in braces: `"MOV R{rd}, {{imm={immediate}}}"`

### Backward Compatibility

If an instruction does not specify `assembly_syntax`, the disassembler falls back to the default format:
- **Regular instructions**: `MNEMONIC operand1, operand2, operand3, ...` (decimal numeric values)
- **Bundle instructions**: `BUNDLE[slot0=..., slot1=...]` (slot assignments)

## Distributed Operands

Operands can be split across multiple non-contiguous fields in an instruction format.

### Syntax

```isa
instruction ADD_DIST {
    format: DIST_TYPE
    encoding: { opcode=2, funct=0 }
    operands: rd(rd_low, rd_high), rs1, rs2
    assembly_syntax: "ADD_DIST R{rd}, R{rs1}, R{rs2}"
    behavior: {
        R[rd] = R[rs1] + R[rs2];
    }
}
```

**Syntax**: `operand_name(field1, field2, ...)`

- The operand `rd` is distributed across fields `rd_low` and `rd_high`
- The operand value is automatically reconstructed from the fields
- Can be used in RTL behavior and assembly syntax

### Format Definition

```isa
format DIST_TYPE 32 {
    opcode: [0:5]
    rd_low: [6:8]
    rd_high: [20:22]
    rs1: [9:11]
    rs2: [12:14]
    funct: [15:19]
    unused: [23:31]
}
```

The distributed operand `rd` is reconstructed by concatenating `rd_high` and `rd_low` (in that order).

### Usage

Distributed operands work seamlessly:
- In RTL behavior: `R[rd]` - the operand is automatically reconstructed
- In assembly syntax: `R{rd}` - the operand value is used directly
- The fields are automatically extracted and combined during encoding/decoding

## Best Practices

### Naming Conventions

- Use uppercase for instruction mnemonics: `ADD`, `SUB`, `LOAD`
- Use descriptive format names: `R_TYPE`, `I_TYPE`, `J_TYPE`
- Use lowercase for register and field names: `rd`, `rs1`, `imm`

### Bit Ranges

- Always specify bit ranges as `[lsb:msb]`
- Ensure fields don't overlap
- Use descriptive field names

### Encoding

- Use unique encoding values to distinguish instructions
- Keep opcode and function code values small for readability
- For variable-length instructions, specify `identification_fields`

### RTL Behavior

- Keep behavior statements simple and clear
- Use comments in generated code (via documentation generator)
- Test behavior with the generated simulator
- Use for loops for repetitive vector operations

### Variable-Length Instructions

- Always specify `identification_fields` for efficient matching
- Use shortest unique fields for identification
- Ensure shorter formats don't match longer instructions
- Test with mixed-width instruction sequences

### Instruction Bundling

- Use clear bundle format names
- Ensure sub-instructions fit within their slots
- Test bundle execution order
- Use `assembly_syntax` for better disassembly output

### Validation

- Always validate your ISA before generating tools
- Check for overlapping fields
- Verify operand names match format field names
- Test generated tools with sample programs

## Complete Example

```isa
architecture ComprehensiveISA {
    word_size: 32
    endianness: little
    
    registers {
        gpr R 32 [16]
        vec V 128 <32, 4>
        sfr PC 32
        sfr FLAGS 32 {
            Z: [0:0]
            V: [1:1]
        }
    }
    
    formats {
        format R_TYPE 32 {
            opcode: [0:5]
            rd: [6:8]
            rs1: [9:11]
            rs2: [12:14]
            funct: [15:23]
            reserved: [24:31]
        }
        
        format DIST_TYPE 32 {
            opcode: [0:5]
            rd_low: [6:8]
            rd_high: [20:22]
            rs1: [9:11]
            rs2: [12:14]
            funct: [15:19]
            unused: [23:31]
        }
        
        format VV_TYPE 32 {
            opcode: [0:5]
            vd: [6:9]
            vs1: [10:13]
            vs2: [14:17]
            funct: [18:23]
            unused: [24:31]
        }
        
        format BUNDLE_ID 80 {
            bundle_opcode: [0:7]
        }
        
        bundle format BUNDLE_64 80 {
            instruction_start: 8
            slot0: [8:39]
            slot1: [40:71]
        }
    }
    
    instructions {
        instruction ADD {
            format: R_TYPE
            encoding: { opcode=1, funct=0 }
            operands: rd, rs1, rs2
            assembly_syntax: "ADD R{rd}, R{rs1}, R{rs2}"
            behavior: {
                R[rd] = R[rs1] + R[rs2];
                FLAGS.Z = (R[rd] == 0) ? 1 : 0;
            }
        }
        
        instruction ADD_DIST {
            format: DIST_TYPE
            encoding: { opcode=2, funct=0 }
            operands: rd(rd_low, rd_high), rs1, rs2
            assembly_syntax: "ADD_DIST R{rd}, R{rs1}, R{rs2}"
            behavior: {
                R[rd] = R[rs1] + R[rs2];
                FLAGS.Z = (R[rd] == 0) ? 1 : 0;
            }
        }
        
        instruction VADD {
            format: VV_TYPE
            encoding: { opcode=32, funct=0 }
            operands: vd, vs1, vs2
            assembly_syntax: "VADD V{vd}, V{vs1}, V{vs2}"
            behavior: {
                V[vd][0] = V[vs1][0] + V[vs2][0];
                V[vd][1] = V[vs1][1] + V[vs2][1];
                V[vd][2] = V[vs1][2] + V[vs2][2];
                V[vd][3] = V[vs1][3] + V[vs2][3];
            }
        }
        
        instruction BUNDLE {
            format: BUNDLE_ID
            bundle_format: BUNDLE_64
            encoding: { bundle_opcode=255 }
            assembly_syntax: "BUNDLE{{ {slot0}, {slot1} }}"
        }
    }
}
```

## See Also

- [README.md](../README.md) - Installation and quick start
- [Examples Guide](EXAMPLES.md) - Example ISA specifications
- [Simulator](Simulator.md) - Generated simulator documentation
- [Assembler](Assembler.md) - Generated assembler documentation
- [Disassembler](Disassembler.md) - Generated disassembler documentation

