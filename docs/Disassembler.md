# Disassembler

The ISA DSL generates Python-based disassemblers that convert machine code binary files back into assembly source code.

## Overview

The generated disassembler:
- Reads binary files containing machine code
- Identifies instructions using encoding fields
- Extracts operand values from instruction fields
- Formats output as assembly syntax
- Supports variable-length instructions
- Handles instruction bundling
- Supports ISA-specific assembly syntax via `assembly_syntax` field

## Usage

### Basic Usage

```bash
# Generate disassembler
uv run isa-dsl generate examples/sample_isa.isa --output output/ --disassembler

# Disassemble binary file
python output/disassembler.py program.bin [start_address]
```

### Python API

```python
from disassembler import Disassembler

disasm = Disassembler()

# Disassemble single instruction
asm = disasm.disassemble(0x58c1)
print(asm)  # "ADD R3, R4, R5"

# Disassemble entire file
instructions = disasm.disassemble_file('program.bin', start_address=0x1000)
for address, asm in instructions:
    print(f"0x{address:08x}: {asm}")
```

## Assembly Syntax Generation

The disassembler generates assembly syntax by extracting operand values from instruction fields and formatting them as a string.

### ISA-Specific Assembly Syntax

Each instruction can specify an `assembly_syntax` format string that defines how the instruction should be disassembled:

```isa
instruction ADD {
    format: R_TYPE
    encoding: { opcode=1, funct=0 }
    operands: rd, rs1, rs2
    assembly_syntax: "ADD R{rd}, R{rs1}, R{rs2}"
    behavior: {
        R[rd] = R[rs1] + R[rs2];
    }
}
```

The format string uses Python's `.format()` syntax, where `{operand_name}` is replaced with the operand value extracted from the instruction.

### Example

**Input (binary)**: `0x58c1` (ADD instruction with rd=3, rs1=4, rs2=5)

**With assembly_syntax**: `"ADD R3, R4, R5"` ✓

**Without assembly_syntax** (fallback): `"ADD 3, 4, 5"`

### Format String Syntax

The `assembly_syntax` format string uses **Python's `.format()` method**, which means you must follow Python format string rules:

- **Operand substitution**: `{operand_name}` is replaced with the operand value
- **Literal braces**: Use `{{` for literal `{` and `}}` for literal `}`
- **Register formatting**: Include register prefixes in the format string (e.g., `R{rd}`)
- **Custom formatting**: Any valid Python format string syntax

**Important:** To include literal curly braces in the output, you must escape them:
- `{{` in the ISA file produces `{` in the output
- `}}` in the ISA file produces `}` in the output
- `{name}` in the ISA file is a placeholder that gets replaced

Examples:
- `"ADD R{rd}, R{rs1}, R{rs2}"` → `"ADD R3, R4, R5"`
- `"MOV {rd}, {immediate}"` → `"MOV 5, 10"`
- `"VADD V{vd}, V{vs1}, V{vs2}"` → `"VADD V2, V3, V4"`
- `"BUNDLE{{ {slot0}, {slot1} }}"` → `"BUNDLE{ ADD R3, R4, R5, ADD R6, R7, R8 }"`

### Using Curly Braces in Assembly Syntax

**Parser Support**: The parser fully supports curly braces in `assembly_syntax` strings, including patterns like `"BUNDLE{{ {slot0}, {slot1} }}"`. The parser automatically handles these cases by extracting and re-injecting assembly syntax strings that contain braces.

You can use curly braces freely in your assembly syntax strings without any workarounds!

**Examples with Literal Braces:**

**Regular Instructions:**
```isa
instruction ADD {
    format: R_TYPE
    encoding: { opcode=1 }
    operands: rd, rs1, rs2
    assembly_syntax: "ADD R{rd}, R{rs1}, R{rs2}"
}
```
**Output:** `ADD R3, R4, R5`

**Bundle Instructions with Literal Braces:**
```isa
instruction BUNDLE {
    format: BUNDLE_ID
    bundle_format: BUNDLE_64
    encoding: { bundle_opcode=255 }
    bundle_instructions: ADD, ADD_DIST
    assembly_syntax: "BUNDLE{{ {slot0}, {slot1} }}"
}
```

**Explanation:**
- `BUNDLE{{` - The `{{` becomes a literal `{` in output: `BUNDLE{`
- `{slot0}` - Placeholder replaced with disassembled slot0 instruction
- `, ` - Literal comma and space
- `{slot1}` - Placeholder replaced with disassembled slot1 instruction  
- `}}` - The `}}` becomes a literal `}` in output: `}`

**Output:** `BUNDLE{ ADD R3, R4, R5, ADD_DIST R10, R4, R5 }`

**More Complex Examples:**

**Nested braces:**
```isa
assembly_syntax: "{{ {slot0} }}"
```
**Output:** `{ ADD R3, R4, R5 }`

**Multiple literal braces:**
```isa
assembly_syntax: "BUNDLE{{{{ {slot0} }}}}"
```
**Output:** `BUNDLE{{ ADD R3, R4, R5 }}`

**Mix of placeholders and literals:**
```isa
assembly_syntax: "{{operand={rd}}}"
```
**Output:** `{operand=3}`

**Quick Reference:**

| What You Want in Output | Write in ISA File |
|------------------------|-------------------|
| `{` (literal brace) | `{{` |
| `}` (literal brace) | `}}` |
| `{name}` (placeholder) | `{name}` |
| `{{` (two literal braces) | `{{{{` |
| `}}` (two literal braces) | `}}}}` |

**Common Patterns:**

**Bundle with curly braces:**
```isa
assembly_syntax: "BUNDLE{{ {slot0}, {slot1} }}"
```
**Output:** `BUNDLE{ ADD R3, R4, R5, ADD R6, R7, R8 }`

**Bundle with square brackets:**
```isa
assembly_syntax: "BUNDLE[ {slot0}, {slot1} ]"
```
**Output:** `BUNDLE[ ADD R3, R4, R5, ADD R6, R7, R8 ]`

**Instruction with register formatting:**
```isa
assembly_syntax: "ADD R{rd}, R{rs1}, R{rs2}"
```
**Output:** `ADD R3, R4, R5`

**Instruction with immediate in braces:**
```isa
assembly_syntax: "MOV R{rd}, {{imm={immediate}}}"
```
**Output:** `MOV R3, {imm=10}`

**Troubleshooting:**

- **Format string error**: `KeyError` or `ValueError` - Make sure all placeholders (e.g., `{slot0}`, `{rd}`) match actual operand/slot names
- **Literal braces not appearing**: Use `{{` for `{` and `}}` for `}`
- **Parser error**: Ensure braces are inside quoted strings: `"BUNDLE{{ {slot0} }}"`

### Distributed Operands

Assembly syntax works with distributed operands:

```isa
instruction ADD_DIST {
    format: DIST_TYPE
    encoding: { opcode=2, funct=0 }
    operands: rd(rd_low, rd_high), rs1, rs2
    assembly_syntax: "ADD_DIST R{rd}, R{rs1}, R{rs2}"
}
```

The distributed operand `rd` is automatically reconstructed from `rd_low` and `rd_high` before substitution.

### Bundle Instructions

Bundle instructions support `assembly_syntax` with special slot placeholders:

```isa
instruction BUNDLE {
    format: BUNDLE_ID
    bundle_format: BUNDLE_64
    encoding: { bundle_opcode=255 }
    bundle_instructions: ADD, ADD_DIST
    assembly_syntax: "BUNDLE[ {slot0}, {slot1} ]"
}
```

**Slot Placeholders**:
- `{slot0}`, `{slot1}`, etc. - Replaced with the disassembled instruction from each slot
- Each slot is disassembled using the appropriate instruction's `assembly_syntax` if available
- Slots are matched against `bundle_instructions` in order

**Example Output**:
- Format string: `"BUNDLE[ {slot0}, {slot1} ]"`
- Disassembled: `"BUNDLE[ ADD R3, R4, R5, ADD_DIST R10, R4, R5 ]"`

**Default Format** (if `assembly_syntax` not provided):
```
BUNDLE[slot0=ADD R3, R4, R5, slot1=ADD_DIST R10, R4, R5]
```

### Backward Compatibility

If an instruction does not specify `assembly_syntax`, the disassembler falls back to the default format:
- **Regular instructions**: `MNEMONIC operand1, operand2, operand3, ...` (decimal numeric values)
- **Bundle instructions**: `BUNDLE[slot0=..., slot1=...]` (slot assignments)

## Variable-Length Instruction Support

The disassembler handles variable-length instructions by:

1. **Identifying Width**: Uses `_identify_instruction_width()` to identify width from encoded word
2. **Dynamic Loading**: `disassemble_file()` handles variable-length instructions in binary files
3. **Address Calculation**: Address calculation accounts for variable widths

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

### Distributed Opcodes

Opcodes can be split across multiple fields:

```isa
format DIST_32 32 {
    opcode_low: [0:3]
    opcode_high: [20:23]
    // ... other fields
    identification_fields: opcode_low, opcode_high
}
```

Both fields are checked during identification.

### Implementation Details

- `_identify_instruction_width()`: Identifies width from encoded word
- `disassemble_file()`: Handles variable-length instructions in binary files
- Address calculation accounts for variable widths
- Formats are checked shortest-first to avoid false matches

## Instruction Bundling

The disassembler supports instruction bundling with two-level decoding.

### How It Works

1. **Detect bundle**: Check if instruction word matches bundle encoding
2. **Extract sub-instructions**: Extract from each slot
3. **Disassemble each**: Disassemble each sub-instruction
4. **Format output**: Display as `BUNDLE{ADD ..., SUB ...}`

### Bundle Disassembly Process

1. Check if instruction matches bundle encoding
2. Extract slot words from bundle format
3. For each slot, try to match against `bundle_instructions`
4. Disassemble each matched instruction
5. Format output using `assembly_syntax` if provided

## API Reference

### Disassembler Class

```python
class Disassembler:
    def __init__(self):
        """Initialize the disassembler."""
        
    def disassemble(self, instruction_word: int, num_bits: int = None) -> Optional[str]:
        """Disassemble a single instruction word.
        
        Args:
            instruction_word: Instruction word (may be 16, 32, 64 bits, etc.)
            num_bits: Number of bits in instruction (None = auto-detect)
            
        Returns:
            Assembly mnemonic string or None if unknown
        """
        
    def disassemble_file(self, filename: str, start_address: int = 0) -> List[Tuple[int, str]]:
        """Disassemble a binary file, handling variable-length instructions.
        
        Args:
            filename: Binary file path
            start_address: Starting address
            
        Returns:
            List of (address, instruction) tuples
        """
        
    def _identify_instruction_width(self, instruction_word: int) -> int:
        """Identify instruction width by checking identification fields."""
```

## Default Output Format

### Without assembly_syntax

**Regular Instructions**:
```
ADD 3, 4, 5
SUB 1, 2, 3
```

**Bundle Instructions**:
```
BUNDLE[slot0=ADD 3, 4, 5, slot1=SUB 1, 2, 3]
```

### With assembly_syntax

**Regular Instructions**:
```
ADD R3, R4, R5
SUB R1, R2, R3
```

**Bundle Instructions**:
```
BUNDLE[ ADD R3, R4, R5, SUB R1, R2, R3 ]
```

## Best Practices

1. **Specify assembly_syntax**: Use `assembly_syntax` for better output formatting
2. **Test Round-Trip**: Assemble → Disassemble to verify correctness
3. **Handle Variable Lengths**: Ensure disassembler correctly identifies instruction widths
4. **Bundle Formatting**: Use slot placeholders for bundle instructions
5. **Escape Braces**: Use `{{` and `}}` for literal braces in format strings

## Limitations

- Default output uses decimal numeric values (not register names)
- Register naming convention is ISA-specific (handled via `assembly_syntax`)
- Bundle syntax parsing may not handle all operand formats

## See Also

- [DSL Specification](DSL_Specification.md#instruction-bundling) - Bundle instruction details
- [DSL Specification](DSL_Specification.md) - Complete DSL reference

