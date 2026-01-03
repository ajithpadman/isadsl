# ISA DSL Examples

This document provides an overview of the example ISA specifications included in the `examples/` directory.

## Example Files

### minimal.isa

A minimal ISA specification with just two instructions (ADD and SUB). This is an excellent starting point for understanding the basic syntax.

**Features demonstrated:**
- Basic register definitions (GPR and SFR)
- Simple instruction format
- Basic RTL behavior
- Minimal instruction set

**Usage:**
```bash
uv run isa-dsl generate examples/minimal.isa --output output/
uv run isa-dsl info examples/minimal.isa
```

### sample_isa.isa

A complete example ISA called "SimpleRISC" with a full instruction set including:
- Arithmetic operations (ADD, SUB, AND, OR, XOR)
- Immediate operations (ADDI)
- Memory operations (LOAD, STORE)
- Branch instructions (BEQ, BNE)
- Jump instructions (JMP)

**Features demonstrated:**
- Multiple instruction formats (R_TYPE, I_TYPE, BRANCH_TYPE)
- Register files and special function registers
- Register fields (FLAGS register with Z, C, N flags)
- Conditional RTL behavior
- Memory access operations
- Complex expressions

**Usage:**
```bash
uv run isa-dsl generate examples/sample_isa.isa --output output/
uv run isa-dsl validate examples/sample_isa.isa
uv run isa-dsl info examples/sample_isa.isa
```

### advanced.isa

An advanced RISC architecture with comprehensive instruction set including:
- All R-type operations (ADD, SUB, SLL, SRL, AND, OR, XOR)
- I-type operations (ADDI, SLTI, LOAD)
- S-type operations (STORE)
- B-type operations (BEQ, BNE, BLT, BGE)
- U-type operations (LUI, AUIPC)
- J-type operations (JAL, JALR)
- Stack operations (PUSH, POP)
- Function call/return (CALL, RET)

**Features demonstrated:**
- Multiple register files (R, F)
- Multiple special function registers (PC, SP, FLAGS, STATUS)
- Complex register fields
- All instruction format types
- Advanced RTL behavior with conditionals
- Stack manipulation
- Function call conventions

**Usage:**
```bash
uv run isa-dsl generate examples/advanced.isa --output output/
uv run isa-dsl validate examples/advanced.isa
uv run isa-dsl info examples/advanced.isa
```

### simd.isa

A SIMD-enabled ISA demonstrating vector instruction support:
- Vector registers (128-bit, 4 lanes of 32 bits)
- Vector-vector operations (VADD, VSUB, VMUL)
- Vector-scalar operations (VADD_SCALAR, VMUL_SCALAR)
- Vector-immediate operations (VADD_IMM)
- Vector memory operations (VLOAD, VSTORE)
- Vector reduction operations (VDOT)
- Vector comparison operations (VMAX, VMIN)

**Features demonstrated:**
- Vector register definitions
- Lane access in RTL
- Element-wise operations
- Vector memory access patterns

**Usage:**
```bash
uv run isa-dsl generate examples/simd.isa --output output/
uv run isa-dsl validate examples/simd.isa
uv run isa-dsl info examples/simd.isa
```

## Running Examples

### Generate All Tools

Generate simulator, assembler, disassembler, and documentation:

```bash
uv run isa-dsl generate examples/sample_isa.isa --output output/
```

### Generate Specific Tools

Generate only the simulator:

```bash
uv run isa-dsl generate examples/sample_isa.isa \
    --output output/ \
    --simulator \
    --no-assembler \
    --no-disassembler \
    --no-docs
```

### Validate an Example

Check if an example ISA is valid:

```bash
uv run isa-dsl validate examples/sample_isa.isa
```

### Get ISA Information

Display summary information about an ISA:

```bash
uv run isa-dsl info examples/sample_isa.isa
```

## Learning Path

1. **Start with `minimal.isa`**: Understand basic syntax and structure
2. **Study `sample_isa.isa`**: Learn about different instruction formats and RTL behavior
3. **Explore `advanced.isa`**: See advanced features and complex instruction sets
4. **Try `simd.isa`**: Learn about vector registers and SIMD operations
5. **Create your own**: Use these examples as templates for your own ISA

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

- Read the [Usage Guide](USAGE.md) for detailed documentation
- Check out [SIMD Support](SIMD_SUPPORT.md) for vector instruction documentation
- Modify the examples to create your own ISA
- Generate tools and test them with sample programs
- Generate documentation to see how your ISA is documented

