# Instruction Bundling Support

This document describes the instruction bundling feature that allows multiple instructions to be packed into a single wider instruction word.

## Overview

Instruction bundling enables you to:
- Pack multiple instructions into a single wider instruction word (e.g., two 32-bit instructions in a 64-bit bundle)
- Define bundle formats that specify how instructions are packed
- Use special bundle opcodes to identify bundled instructions
- Write assembly code using `bundle{instr1, instr2}` syntax
- Execute bundles with two-level decoding (first decode bundle, then decode sub-instructions)

## Grammar Syntax

### Bundle Format Definition

Define a bundle format that specifies how instructions are packed:

```isa
formats {
    bundle format BUNDLE_64 64 {
        slot0: [0:31]
        slot1: [32:63]
    }
}
```

This defines a 64-bit bundle format with two 32-bit slots.

### Bundle Instruction Definition

Define a bundle instruction that uses both a format (for identification) and a bundle format (for slot layout):

```isa
formats {
    format BUNDLE_ID 64 {
        bundle_opcode: [0:7]
    }
}

instructions {
    instruction BUNDLE {
        format: BUNDLE_ID          # Format for bundle identification
        bundle_format: BUNDLE_64   # Bundle format for slot layout
        encoding: { bundle_opcode=255 }  # Special opcode to identify bundle
        bundle_instructions: ADD, SUB  # Instructions that can be bundled
    }
}
```

**Important:** Bundle instructions require:
- A **format** that defines fields for bundle identification (e.g., `bundle_opcode`)
- A **bundle_format** that defines the slot layout
- An **encoding** that references fields in the format (not slots)
- A **bundle_instructions** list of instruction names that can be bundled

## Assembly Syntax

Use the `bundle{...}` syntax to bundle multiple instructions:

```asm
# Bundle two instructions
bundle{ADD R1, R2, R3, SUB R4, R5, 10}

# This creates a 64-bit bundle containing:
# - ADD R1, R2, R3 in slot0
# - SUB R4, R5, 10 in slot1
```

## How It Works

### Simulator Execution

1. **First-level decoding**: The simulator checks if an instruction word matches a bundle encoding
2. **Bundle extraction**: If it's a bundle, extract sub-instructions from each slot
3. **Second-level decoding**: Execute each sub-instruction in sequence
4. **PC update**: Advance PC by the bundle width (not individual instruction width)

### Assembler

1. **Parse bundle syntax**: Recognize `bundle{...}` syntax
2. **Assemble sub-instructions**: Assemble each instruction in the bundle
3. **Pack into bundle**: Pack assembled instructions into bundle slots
4. **Set bundle encoding**: Set the bundle identification opcode

### Disassembler

1. **Detect bundle**: Check if instruction word matches bundle encoding
2. **Extract sub-instructions**: Extract from each slot
3. **Disassemble each**: Disassemble each sub-instruction
4. **Format output**: Display as `BUNDLE{ADD ..., SUB ...}`

## Example ISA with Bundling

```isa
architecture BundledISA {
    word_size: 32
    endianness: little
    
    registers {
        gpr R 32 [8]
        sfr PC 32
    }
    
    formats {
        format R_TYPE 32 {
            opcode: [0:5]
            rd: [6:8]
            rs1: [9:11]
            rs2: [12:14]
        }
        
        bundle format BUNDLE_64 64 {
            slot0: [0:31]
            slot1: [32:63]
        }
    }
    
    instructions {
        instruction ADD {
            format: R_TYPE
            encoding: { opcode=1 }
            operands: rd, rs1, rs2
            behavior: {
                R[rd] = R[rs1] + R[rs2];
            }
        }
        
        instruction SUB {
            format: R_TYPE
            encoding: { opcode=2 }
            operands: rd, rs1, rs2
            behavior: {
                R[rd] = R[rs1] - R[rs2];
            }
        }
        
        instruction BUNDLE {
            bundle_format: BUNDLE_64
            encoding: { slot0=0xFF }  # Special value in slot0 identifies bundle
            bundle_instructions: ADD, SUB
        }
    }
}
```

## Assembly Example

```asm
# Regular instructions
ADD R1, R2, R3
SUB R4, R5, R6

# Bundled instructions
bundle{ADD R1, R2, R3, SUB R4, R5, R6}
```

## Design Considerations

### Bundle Encoding

Bundle instructions use a **format** (not the bundle_format) for encoding identification:

1. **Create a format** that defines identification fields (e.g., `bundle_opcode` at bits [0:7])
2. **Reference the format** in the bundle instruction's `format` field
3. **Set encoding values** using field names from the format (e.g., `bundle_opcode=255`)
4. The **bundle_format** is used only for slot layout, not for encoding

This separation allows:
- Clear identification of bundles via the format
- Flexible slot layouts via the bundle_format
- Forward references (bundle instructions can reference instructions defined later)

### Slot Widths

- Slots can have different widths
- Total bundle width = sum of slot widths (plus any encoding fields)
- Sub-instructions must fit within their assigned slots

### Execution Order

- Sub-instructions are executed in slot order (slot0, slot1, ...)
- All sub-instructions in a bundle execute atomically
- PC advances by bundle width after bundle execution

## Limitations

- Current implementation requires bundle instructions to be explicitly defined
- Bundle syntax parsing is basic (may not handle all operand formats)
- Validation of bundle compatibility is limited

## Future Enhancements

- Automatic bundle format inference
- More flexible bundle syntax
- Bundle optimization hints
- Support for variable-width bundles

