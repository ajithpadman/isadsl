# ISA DSL Examples

This directory contains example ISA specifications demonstrating various features of the ISA DSL.

> **Note**: For detailed documentation about these examples, see [docs/EXAMPLES.md](../docs/EXAMPLES.md)

## Example Files

### minimal.isa

A minimal ISA specification with just two instructions (ADD and SUB). This is a good starting point for understanding the basic syntax.

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
4. **Create your own**: Use these examples as templates for your own ISA

## Common Patterns

### Register Definition

```isa
gpr R 32 [8]              // 8 registers, 32 bits each
sfr PC 32                 // Single register
sfr FLAGS 32 {            // Register with fields
    Z: [0:0]
    C: [1:1]
}
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
    operands: rd, rs1, rs2
    behavior: {
        R[rd] = R[rs1] + R[rs2];
    }
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

- Read the [Usage Guide](../docs/USAGE.md) for detailed documentation
- Modify the examples to create your own ISA
- Generate tools and test them with sample programs
- Generate documentation to see how your ISA is documented

