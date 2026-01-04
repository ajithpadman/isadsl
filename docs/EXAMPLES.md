# ISA DSL Examples

This document provides an overview of the example ISA specifications. Reference examples are in the `examples/` directory, while test-specific examples are in `tests/*/test_data/` directories.

## Reference Examples

The `examples/` directory contains reference ISA specifications demonstrating best practices:

### ARM Cortex-A9 ISA Specification

A comprehensive ARM Cortex-A9 ISA specification organized across multiple files using the multi-file approach:

- **`arm_cortex_a9.isa`** - Main architecture file with `#include` directives
- **`arm_cortex_a9_registers.isa`** - Register definitions (GPRs, PC, CPSR, SPSR, LR, SP)
- **`arm_cortex_a9_formats.isa`** - Instruction format definitions (ARM_DP_REG, ARM_DP_IMM, ARM_MEM, ARM_BRANCH, etc.)
- **`arm_cortex_a9_instructions.isa`** - Instruction definitions (ADD, SUB, MOV, AND, ORR, EOR, LDR, STR, B, BL, CMP)

**Features demonstrated:**
- Multi-file ISA specification using `#include` directives
- Cross-file format reference resolution via textX scope providers
- Modular organization of ISA components
- Complete ARM Cortex-A9 instruction subset with 15 instructions

**Usage:**
```bash
uv run isa-dsl generate examples/arm_cortex_a9.isa --output output/
uv run isa-dsl validate examples/arm_cortex_a9.isa
uv run isa-dsl info examples/arm_cortex_a9.isa
```

This example demonstrates how to organize a large ISA specification across multiple files, making it easier to maintain and understand.

## Test Examples

Test-specific ISA examples are located in `tests/*/test_data/` directories:

- **`tests/core/test_data/`** - Core test examples (`sample_isa.isa`, `comprehensive.isa`)
- **`tests/multifile/test_data/`** - Multi-file test examples (various `test_*.isa` files)
- **`tests/bundling/test_data/`** - Bundle instruction examples (`bundling.isa`)
- **`tests/variable_length/test_data/`** - Variable-length instruction examples (`variable_length.isa`)
- **`tests/generators/test_data/`** - Generator test examples (`minimal.isa`, `sample_isa.isa`)
- **`tests/integration/test_data/`** - Integration test examples (`comprehensive.isa`, `sample_isa.isa`)
- **`tests/arm/test_data/`** - ARM test examples (`arm_subset.isa`)

**Note**: These test examples are used by the test suite and demonstrate various ISA DSL features. For learning purposes, refer to the reference examples in the `examples/` directory.

## Running Examples

### Generate All Tools

Generate simulator, assembler, disassembler, and documentation from the ARM Cortex-A9 reference:

```bash
uv run isa-dsl generate examples/arm_cortex_a9.isa --output output/
```

### Generate Specific Tools

Generate only the simulator:

```bash
uv run isa-dsl generate examples/arm_cortex_a9.isa \
    --output output/ \
    --simulator \
    --no-assembler \
    --no-disassembler \
    --no-docs
```

### Validate an Example

Check if an example ISA is valid:

```bash
uv run isa-dsl validate examples/arm_cortex_a9.isa
```

### Get ISA Information

Display summary information about an ISA:

```bash
uv run isa-dsl info examples/arm_cortex_a9.isa
```

## Learning Path

1. **Start with the ARM Cortex-A9 example**: Study `examples/arm_cortex_a9.isa` to understand the multi-file approach
2. **Examine the included files**: Look at how registers, formats, and instructions are organized across files
3. **Study test examples**: Explore `tests/*/test_data/` directories to see various ISA DSL features
4. **Create your own**: Use the ARM Cortex-A9 example as a template for your own multi-file ISA specification

## Common Patterns

### Register Definition

```isa
gpr R 32 [8]              // 8 registers, 32 bits each
sfr PC 32                 // Single register
sfr FLAGS 32 {            // Register with fields
    Z: [0:0]
    C: [1:1]
}
vec V 128 <32, 4>         // Vector register: 128 bits, 4 lanes of 32 bits
```

### Instruction Format

```isa
format R_TYPE 32 {
    opcode: [0:5]
    rd: [6:8]
    rs1: [9:11]
    rs2: [12:14]
    funct: [15:17]
}
```

### Instruction Definition

```isa
instruction ADD {
    format: R_TYPE
    encoding: { opcode=1, funct=0 }
    behavior: {
        R[rd] = R[rs1] + R[rs2];
    }
    operands: rd, rs1, rs2
}
```

### Conditional Behavior

```isa
behavior: {
    if (R[rs1] == R[rs2]) {
        PC = PC + (offset << 2);
    }
}
```

### Memory Access

```isa
behavior: {
    R[rd] = MEM[R[rs1] + imm];        // Load
    MEM[R[rs1] + imm] = R[rs2];       // Store
}
```

### Vector Operations

```isa
behavior: {
    V[vd][0] = V[vs1][0] + V[vs2][0];
    V[vd][1] = V[vs1][1] + V[vs2][1];
    V[vd][2] = V[vs1][2] + V[vs2][2];
    V[vd][3] = V[vs1][3] + V[vs2][3];
}
```

## Tips

1. **Always validate** before generating tools:
   ```bash
   uv run isa-dsl validate your_isa.isa
   ```

2. **Check information** to verify your ISA structure:
   ```bash
   uv run isa-dsl info your_isa.isa
   ```

3. **Start simple** and add complexity gradually

4. **Use descriptive names** for formats, registers, and fields

5. **Test generated tools** to ensure behavior is correct

## Next Steps

- Read the [DSL Specification](DSL_Specification.md) for detailed documentation
- Check out [DSL Specification](DSL_Specification.md#simd-vector-support) for vector instruction documentation
- Modify the examples to create your own ISA
- Generate tools and test them with sample programs
- Generate documentation to see how your ISA is documented

