# Documentation Generation

The ISA DSL includes a documentation generator that automatically creates Markdown documentation from your ISA specification.

## Overview

The documentation generator:
- Extracts information from your ISA specification
- Formats it as readable Markdown documentation
- Includes register definitions, instruction formats, and instruction set
- Documents instruction encodings and RTL behavior
- Generates bit layout diagrams

## Usage

### Basic Usage

```bash
# Generate documentation
uv run isa-dsl generate examples/arm_cortex_a9.isa --output output/ --docs

# Documentation will be generated as:
# output/isa_documentation.md
```

### Generate All Tools Including Documentation

```bash
uv run isa-dsl generate examples/arm_cortex_a9.isa --output output/
```

This generates simulator, assembler, disassembler, and documentation.

## Generated Documentation Structure

The generated documentation includes:

### Architecture Overview

- Architecture name
- Properties (word_size, endianness, etc.)

### Registers

#### General Purpose Registers
- Register name
- Type (GPR)
- Width in bits
- Count (for register files)
- Index range (e.g., R[0] to R[7])

#### Vector Registers
- Register name
- Type (Vector)
- Width in bits
- Number of lanes
- Element width
- Count (for vector register files)

#### Special Function Registers
- Register name
- Type (SFR)
- Width in bits
- Fields (if any)

### Instruction Formats

For each format:
- Format name
- Width in bits
- Field layout table (Field, Bits, Width, Description)
- Bit layout diagram

### Instruction Set

For each instruction:
- Instruction mnemonic
- Format reference
- Operands list
- Encoding (field values)
- RTL behavior (formatted)

## Example Output

```markdown
# MyISA Instruction Set Architecture

## Architecture Overview

- **word_size**: 32
- **endianness**: little

## Registers

### General Purpose Registers

#### R
- **Type**: General Purpose Register
- **Width**: 32 bits
- **Count**: 8 registers (R[0] to R[7])

### Special Function Registers

#### PC
- **Type**: Special Function Register
- **Width**: 32 bits

## Instruction Formats

### R_TYPE

- **Width**: 32 bits

**Field Layout**:

| Field | Bits | Width | Description |
|-------|------|-------|-------------|
| `opcode` | [5:0] | 6 | |
| `rd` | [8:6] | 3 | |
| `rs1` | [11:9] | 3 | |
| `rs2` | [14:12] | 3 | |
| `funct` | [17:15] | 3 | |

**Bit Layout**:
```
OOOOOORRRSSSFFF------------------
```

## Instruction Set

### ADD

**Format**: R_TYPE

**Operands**: rd, rs1, rs2

**Encoding**:
- `opcode` = `0x1`
- `funct` = `0x0`

**Behavior**:
```
R[rd] = R[rs1] + R[rs2];
FLAGS.Z = (R[rd] == 0) ? 1 : 0;
```

---
```

## Customization

The documentation generator uses a Jinja2 template that can be customized if needed. The template is located in `isa_dsl/generators/documentation.py`.

### Template Features

- **RTL Formatting**: Automatically formats RTL statements for readability
- **Bit Layout Diagrams**: Generates ASCII art bit layout diagrams
- **Field Tables**: Creates markdown tables for field layouts
- **Encoding Display**: Shows encoding values in hexadecimal

## Best Practices

1. **Use Descriptive Names**: Clear names make documentation more readable
2. **Document Fields**: Add field descriptions in your ISA (if supported)
3. **Organize Instructions**: Group related instructions together
4. **Review Generated Docs**: Check the generated documentation for accuracy
5. **Update Regularly**: Regenerate documentation when ISA changes

## Integration

The documentation generator is integrated with the CLI:

```bash
# Generate only documentation
uv run isa-dsl generate examples/arm_cortex_a9.isa --output output/ --no-simulator --no-assembler --no-disassembler --docs

# Generate all tools including documentation
uv run isa-dsl generate examples/arm_cortex_a9.isa --output output/
```

## Limitations

- Documentation format is fixed (Markdown)
- Field descriptions are not extracted from ISA (if not supported)
- Custom formatting options are limited
- Bit layout diagrams are ASCII art only

## Future Enhancements

Potential improvements:
- HTML output format
- PDF generation
- Customizable templates
- Field descriptions in ISA
- Instruction grouping and categorization
- Cross-references between sections

## See Also

- [DSL Specification](DSL_Specification.md) - Complete DSL reference
- [Examples Guide](EXAMPLES.md) - Example ISA specifications

