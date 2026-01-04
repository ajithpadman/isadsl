# Assembler

The ISA DSL generates Python-based assemblers that convert assembly source code into machine code binary files.

## Overview

The generated assembler:
- Parses assembly source code
- Resolves labels and symbols
- Encodes instructions according to ISA specifications
- Handles variable-length instructions
- Supports instruction bundling
- Generates binary output files

## Usage

### Basic Usage

```bash
# Generate assembler
uv run isa-dsl generate examples/arm_cortex_a9.isa --output output/ --assembler

# Assemble source file
python output/assembler.py program.asm program.bin
```

### Assembly Syntax

```asm
# Labels
loop:
    ADD R1, R2, R3
    SUB R4, R5, R6
    BEQ R1, R0, loop

# Immediate values
ADDI R1, R2, 10        # Decimal
ADDI R1, R2, 0xA       # Hexadecimal
ADDI R1, R2, 0b1010    # Binary

# Labels as operands
JMP loop
BEQ R1, R2, target
```

### Instruction Bundling

```asm
# Bundle two instructions
bundle{ADD R1, R2, R3, SUB R4, R5, 10}

# This creates a bundle containing:
# - ADD R1, R2, R3 in slot0
# - SUB R4, R5, 10 in slot1
```

## Variable-Length Instruction Support

The assembler handles variable-length instructions by:

1. **Determining Width**: Uses `_get_instruction_width_from_line()` to determine width from mnemonic
2. **Address Calculation**: First pass calculates addresses using variable widths
3. **Binary Output**: `write_binary()` writes instructions with correct byte widths

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

### Assembly Examples

**16-bit Instruction:**
```asm
ADD16 R0, R1, 5
```

**32-bit Instruction:**
```asm
ADD32 R3, R1, R2
```

**Distributed Opcode:**
```isa
instruction ADD_DIST {
    format: DIST_32
    encoding: { opcode_low=3, opcode_high=0 }
    operands: rd(rd_low, rd_high), rs1, rs2
}
```

### Implementation Details

- `_get_instruction_width_from_line()`: Determines width from mnemonic
- First pass calculates addresses using variable widths
- `write_binary()`: Writes instructions with correct byte widths
- `_determine_instruction_width()`: Identifies instruction width from encoded word using identification fields

## Instruction Bundling

The assembler supports bundling multiple instructions into a single wider word.

### How It Works

1. **Parse bundle syntax**: Recognize `bundle{...}` syntax
2. **Assemble sub-instructions**: Assemble each instruction in the bundle
3. **Pack into bundle**: Pack assembled instructions into bundle slots
4. **Set bundle encoding**: Set the bundle identification opcode

### Bundle Syntax

```asm
bundle{ADD R1, R2, R3, SUB R4, R5, R6}
```

The assembler:
- Parses the bundle content
- Identifies instruction boundaries
- Assembles each instruction
- Packs them into the bundle format
- Sets the bundle opcode

## API Reference

### Assembler Class

```python
class Assembler:
    def __init__(self):
        """Initialize assembler."""
        
    def assemble(self, source: str, start_address: int = 0) -> List[int]:
        """Assemble source code to machine code.
        
        Args:
            source: Assembly source code
            start_address: Starting address for code
            
        Returns:
            List of instruction words
        """
        
    def write_binary(self, machine_code: List[int], filename: str):
        """Write machine code to a binary file, handling variable-length instructions."""
```

### Two-Pass Assembly

The assembler uses a two-pass approach:

1. **First Pass**: Collect labels and determine instruction widths
2. **Second Pass**: Assemble instructions with resolved labels

## Operand Parsing

The assembler supports various operand formats:

- **Registers**: `R0`, `R1`, `R2`, etc.
- **Immediate values**: 
  - Decimal: `10`
  - Hexadecimal: `0xA`, `0x10`
  - Binary: `0b1010`
- **Labels**: Referenced by name (e.g., `loop`, `target`)
- **Symbols**: User-defined symbols

### Register Resolution

The assembler has built-in register name resolution:

```python
def _resolve_register(self, name: str) -> int:
    """Resolve a register name to a number."""
    # Handles register names like R0, R1, etc.
    if name.upper().startswith('R') and name[1:].isdigit():
        return int(name[1:])
    return 0
```

## Error Handling

- **Unknown instruction**: Returns `None` for unparseable instructions
- **Invalid operands**: May raise exceptions or return `None`
- **Label resolution**: Unresolved labels may cause errors

## Best Practices

1. **Use Consistent Syntax**: Follow the expected assembly syntax
2. **Label Naming**: Use descriptive label names
3. **Comments**: Use `#` for comments
4. **Test Assembly**: Verify assembled output with disassembler
5. **Variable-Length Instructions**: Ensure correct mnemonics for different widths

## Limitations

- Register name parsing is basic (supports `R0`, `R1`, etc. format)
- Bundle syntax parsing may not handle all operand formats
- Limited validation of instruction compatibility

## See Also

- [DSL Specification](DSL_Specification.md#instruction-bundling) - Bundle instruction details
- [DSL Specification](DSL_Specification.md) - Complete DSL reference

