# ISA DSL Usage Guide

This guide explains how to use the ISA DSL to describe Instruction Set Architectures and generate tools.

## Table of Contents

1. [Basic Syntax](#basic-syntax)
2. [Architecture Definition](#architecture-definition)
3. [Registers](#registers)
4. [Instruction Formats](#instruction-formats)
5. [Instructions](#instructions)
6. [RTL Behavior](#rtl-behavior)
7. [Command Line Interface](#command-line-interface)
8. [Examples](#examples)

## Basic Syntax

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

## Architecture Definition

The `architecture` block defines the top-level properties of your ISA:

```isa
architecture MyISA {
    word_size: 32          // Instruction word size in bits
    endianness: little     // Byte order: "little" or "big"
}
```

### Properties

- `word_size`: The size of instruction words in bits (typically 16, 32, or 64)
- `endianness`: Byte ordering (`little` or `big`)

## Registers

Registers are defined in the `registers` block. There are three types:

### General Purpose Registers (GPR)

Register files with multiple registers:

```isa
registers {
    gpr R 32 [8]    // 8 registers, each 32 bits wide (R[0] to R[7])
}
```

Syntax: `gpr <name> <width> [<count>]`

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

Syntax: `sfr <name> <width> [{ <field_name>: [<lsb>:<msb>] }]`

**Note**: Bit ranges use `[lsb:msb]` format, where `lsb` is the least significant bit and `msb` is the most significant bit.

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

Syntax: `format <name> <width> { <field_name>: [<lsb>:<msb>] }`

**Important**: 
- Field bit ranges must not overlap
- Total field width should not exceed the format width
- Field names are used to reference fields in instructions

## Instructions

Instructions define the actual operations:

```isa
instructions {
    instruction ADD {
        format: R_TYPE
        encoding: { opcode=1, funct=0 }
        behavior: {
            R[rd] = R[rs1] + R[rs2];
            FLAGS.Z = (R[rd] == 0) ? 1 : 0;
        }
        operands: rd, rs1, rs2
    }
}
```

### Instruction Fields

1. **format**: Reference to an instruction format (required if using encoding/operands)
2. **encoding**: Fixed field values that identify this instruction
3. **behavior**: RTL statements describing instruction behavior
4. **operands**: List of operand names (must match format field names)

### Encoding

The `encoding` block specifies fixed values for format fields:

```isa
encoding: { opcode=1, funct=0 }
```

This means:
- The `opcode` field must equal `1`
- The `funct` field must equal `0`

### Operands

Operands are listed in the order they appear in assembly:

```isa
operands: rd, rs1, rs2
```

Operand names must match field names in the instruction format.

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
- **Bitwise**: `&`, `|`, `^`, `~`, `<<`, `>>`
- **Comparison**: `==`, `!=`, `<`, `>`, `<=`, `>=`
- **Ternary**: `condition ? then_value : else_value`

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

### Constants

Numeric constants can be used directly:

```isa
behavior: {
    R[rd] = R[rs1] + 1;
    PC = PC + 4;
}
```

## Command Line Interface

### Generate Tools

Generate all tools (simulator, assembler, disassembler, documentation):

```bash
uv run isa-dsl generate examples/sample_isa.isa --output output/
```

Generate specific tools only:

```bash
uv run isa-dsl generate examples/sample_isa.isa \
    --output output/ \
    --simulator \
    --no-assembler \
    --no-disassembler \
    --docs
```

### Validate ISA

Check if an ISA specification is valid:

```bash
uv run isa-dsl validate examples/sample_isa.isa
```

### Display ISA Information

Show summary information about an ISA:

```bash
uv run isa-dsl info examples/sample_isa.isa
```

## Vector Registers

The ISA DSL supports SIMD vector registers for vector instruction processing. See [SIMD Support](SIMD_SUPPORT.md) for detailed documentation.

### Vector Register Definition

```isa
registers {
    vec V 128 <32, 4>    // 128-bit vector, 4 lanes of 32 bits each
}
```

### Vector Lane Access

```isa
behavior: {
    V[vd][0] = V[vs1][0] + V[vs2][0];  // Access lane 0
    V[vd][1] = V[vs1][1] + V[vs2][1];  // Access lane 1
}
```

## Examples

For comprehensive examples, see [Examples Guide](EXAMPLES.md).

### Minimal Example

A simple ISA with one instruction:

```isa
architecture Minimal {
    word_size: 32
    endianness: little
    
    registers {
        gpr R 32 [4]
        sfr PC 32
    }
    
    formats {
        format SIMPLE 32 {
            opcode: [0:7]
            rd: [8:10]
            rs1: [11:13]
            imm: [14:31]
        }
    }
    
    instructions {
        instruction ADD {
            format: SIMPLE
            encoding: { opcode=1 }
            operands: rd, rs1, imm
            behavior: {
                R[rd] = R[rs1] + imm;
            }
        }
    }
}
```

### Complete Example

See `examples/sample_isa.isa` for a complete example with multiple instruction types, register files, and complex RTL behavior.

For more examples including SIMD support, see [Examples Guide](EXAMPLES.md).

## Best Practices

1. **Naming Conventions**:
   - Use uppercase for instruction mnemonics: `ADD`, `SUB`, `LOAD`
   - Use descriptive format names: `R_TYPE`, `I_TYPE`, `J_TYPE`
   - Use lowercase for register and field names: `rd`, `rs1`, `imm`

2. **Bit Ranges**:
   - Always specify bit ranges as `[lsb:msb]`
   - Ensure fields don't overlap
   - Use descriptive field names

3. **Encoding**:
   - Use unique encoding values to distinguish instructions
   - Keep opcode and function code values small for readability

4. **RTL Behavior**:
   - Keep behavior statements simple and clear
   - Use comments in generated code (via documentation generator)
   - Test behavior with the generated simulator

5. **Validation**:
   - Always validate your ISA before generating tools
   - Check for overlapping fields
   - Verify operand names match format field names

## Troubleshooting

### Common Errors

1. **"Field width is negative"**:
   - Check that bit ranges use `[lsb:msb]` format (not `[msb:lsb]`)
   - Ensure `msb >= lsb` for all fields

2. **"Operand not found in format"**:
   - Verify operand names match format field names exactly
   - Check for typos in operand or field names

3. **"Overlapping fields"**:
   - Ensure no two fields share the same bits
   - Check bit range calculations

4. **"Validation failed"**:
   - Run `isa-dsl validate` to see detailed error messages
   - Check all format fields fit within the format width

## Next Steps

1. Start with a simple ISA (see `examples/minimal.isa`)
2. Validate your specification
3. Generate tools and test them
4. Iterate and refine your ISA design
5. Generate documentation for your ISA

For more information, see:
- [Examples Guide](EXAMPLES.md) - Detailed examples documentation
- [Testing Guide](TESTING.md) - How to test your ISA and generated tools
- `examples/` directory - Example ISA specification files
- [SIMD Support](SIMD_SUPPORT.md) - Vector instruction examples

