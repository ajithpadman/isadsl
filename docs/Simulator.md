# Simulator

The ISA DSL generates Python-based instruction simulators that execute machine code according to your ISA specification.

## Overview

The generated simulator:
- Loads binary files containing machine code
- Executes instructions according to RTL behavior specifications
- Supports variable-length instructions with dynamic identification
- Handles instruction bundling with two-level decoding
- Maintains register state (GPRs, SFRs, vector registers)
- Provides memory access capabilities
- Updates program counter (PC) automatically

## Usage

### Basic Usage

```bash
# Generate simulator
uv run isa-dsl generate examples/sample_isa.isa --output output/ --simulator

# Run simulator
python output/simulator.py program.bin [start_address]
```

### Running Simulation

```python
from simulator import Simulator

sim = Simulator()
sim.load_binary_file('program.bin', start_address=0x1000)
sim.run(max_steps=1000)
sim.print_state()
```

## Variable-Length Instruction Support

The simulator supports instructions of varying widths (16-bit, 32-bit, 64-bit, etc.) with dynamic identification.

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

### Two-Step Execution Process

1. **Identification**: Load minimum bits needed and match using identification fields
2. **Execution**: Load full instruction width and execute

### Example: 16-bit and 32-bit Instructions

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

### Implementation Details

- `_identify_instruction()`: Identifies instruction using minimum bits
- `_load_bits()`: Dynamically loads specified number of bits from memory
- `step()`: Two-step process: identify → load full → execute
- PC advancement based on actual instruction width

## Instruction Bundling

The simulator supports instruction bundling with two-level decoding.

### Simulator Execution

1. **First-level decoding**: The simulator checks if an instruction word matches a bundle encoding
2. **Bundle extraction**: If it's a bundle, extract sub-instructions from each slot
3. **Second-level decoding**: Execute each sub-instruction in sequence
4. **PC update**: Advance PC by the bundle width (not individual instruction width)

### Bundle Execution Order

- Sub-instructions are executed in slot order (slot0, slot1, ...)
- All sub-instructions in a bundle execute atomically
- PC advances by bundle width after bundle execution

## API Reference

### Simulator Class

```python
class Simulator:
    def __init__(self):
        """Initialize simulator with registers and memory."""
        
    def load_binary_file(self, filename: str, start_address: int = 0):
        """Load binary file into memory starting at start_address."""
        
    def step(self) -> bool:
        """Execute one instruction. Returns True if executed, False if halted."""
        
    def run(self, max_steps: int = 10000):
        """Run simulation until halt or max_steps reached."""
        
    def print_state(self):
        """Print current simulator state (registers, PC, etc.)."""
```

### Memory Access

The simulator provides a `MEM` dictionary for memory access:

```python
# In RTL behavior
R[rd] = MEM[R[rs1] + imm];        # Load
MEM[R[rs1] + imm] = R[rs2];       # Store
```

### Register Access

- **Register files**: `R[rd]` - access register `rd` in register file `R`
- **Single register**: `PC` - access the PC register directly
- **Register field**: `FLAGS.Z` - access the Z field in FLAGS register
- **Vector registers**: `V[vd][lane]` - access lane `lane` in vector register `vd`

## Error Handling

- **Unknown instruction**: Simulator halts and prints error message
- **Maximum steps**: Simulation stops after `max_steps` if specified
- **Memory access**: Out-of-bounds access may raise exceptions (implementation-dependent)

## Best Practices

1. **Test with Simple Programs**: Start with minimal test programs
2. **Verify Register State**: Use `print_state()` to verify execution
3. **Check PC Updates**: Ensure PC advances correctly for variable-length instructions
4. **Test Bundles**: Verify bundle execution order and PC updates
5. **Memory Initialization**: Initialize memory if needed before loading programs

## Best Practices for Variable-Length Instructions

1. **Specify Identification Fields**: Always specify `identification_fields` for efficient matching
2. **Use Shortest Unique Fields**: Choose fields that uniquely identify the instruction with minimum bits
3. **Order Matters**: Formats are checked shortest-first, so ensure shorter formats don't match longer instructions
4. **Test Thoroughly**: Test with mixed-width instruction sequences

## See Also

- [DSL Specification](DSL_Specification.md#instruction-bundling) - Bundle instruction details
- [DSL Specification](DSL_Specification.md) - Complete DSL reference

