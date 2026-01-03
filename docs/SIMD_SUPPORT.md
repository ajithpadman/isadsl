# SIMD Vector Instruction Support

The ISA DSL now supports SIMD (Single Instruction, Multiple Data) vector instructions, allowing you to define vector registers and vector operations.

## Vector Registers

Vector registers are defined using the `vec` register type with vector properties:

```isa
registers {
    vec V 128 <32, 4>    // 128-bit vector register with 4 lanes of 32 bits each
}
```

### Syntax

```
vec <name> <width> <element_width, lanes> [<count>]?
```

- `name`: Register name (e.g., `V`)
- `width`: Total register width in bits (e.g., `128`)
- `element_width`: Width of each element/lane in bits (e.g., `32`)
- `lanes`: Number of lanes/elements (e.g., `4`)
- `count`: Optional number of vector registers (for vector register files)

### Examples

```isa
// Single vector register: 128 bits, 4 lanes of 32 bits
vec V 128 <32, 4>

// Vector register file: 8 vector registers, each 256 bits, 8 lanes of 32 bits
vec V 256 <32, 8> [8]
```

## Vector Register Access in RTL

Vector registers can be accessed in RTL behavior using lane indexing:

```isa
behavior: {
    V[vd][0] = V[vs1][0] + V[vs2][0];  // Lane 0
    V[vd][1] = V[vs1][1] + V[vs2][1];  // Lane 1
    V[vd][2] = V[vs1][2] + V[vs2][2];  // Lane 2
    V[vd][3] = V[vs1][3] + V[vs2][3];  // Lane 3
}
```

### Lane Access Syntax

- `V[reg_index][lane_index]`: Access specific lane of a vector register
- `lane_index` can be:
  - A constant (e.g., `0`, `1`, `2`)
  - An operand reference (e.g., `i` if `i` is an operand)
  - An expression (in future versions)

## Vector Instruction Examples

### Vector-Vector Operations

```isa
instruction VADD {
    format: VV_TYPE
    encoding: { opcode=32, funct=0 }
    behavior: {
        V[vd][0] = V[vs1][0] + V[vs2][0];
        V[vd][1] = V[vs1][1] + V[vs2][1];
        V[vd][2] = V[vs1][2] + V[vs2][2];
        V[vd][3] = V[vs1][3] + V[vs2][3];
    }
    operands: vd, vs1, vs2
}
```

### Vector-Scalar Operations

```isa
instruction VADD_SCALAR {
    format: VS_TYPE
    encoding: { opcode=33, funct=0 }
    behavior: {
        V[vd][0] = V[vs1][0] + R[rs2];
        V[vd][1] = V[vs1][1] + R[rs2];
        V[vd][2] = V[vs1][2] + R[rs2];
        V[vd][3] = V[vs1][3] + R[rs2];
    }
    operands: vd, vs1, rs2
}
```

### Vector Memory Operations

```isa
instruction VLOAD {
    format: VI_TYPE
    encoding: { opcode=35 }
    behavior: {
        V[vd][0] = MEM[R[vs1] + imm + 0];
        V[vd][1] = MEM[R[vs1] + imm + 4];
        V[vd][2] = MEM[R[vs1] + imm + 8];
        V[vd][3] = MEM[R[vs1] + imm + 12];
    }
    operands: vd, vs1, imm
}
```

### Vector Reduction Operations

```isa
instruction VDOT {
    format: VV_TYPE
    encoding: { opcode=32, funct=8 }
    behavior: {
        R[vd] = 0;
        R[vd] = R[vd] + (V[vs1][0] * V[vs2][0]);
        R[vd] = R[vd] + (V[vs1][1] * V[vs2][1]);
        R[vd] = R[vd] + (V[vs1][2] * V[vs2][2]);
        R[vd] = R[vd] + (V[vs1][3] * V[vs2][3]);
    }
    operands: vd, vs1, vs2
}
```

## Generated Code

### Simulator

Vector registers are initialized as 2D arrays:

```python
self.V = [[0] * 4 for _ in range(1)]  # 1 vector register with 4 lanes
```

Lane access is generated as:

```python
self.V[vd][0] = self.V[vs1][0] + self.V[vs2][0]
```

### Documentation

Vector registers are documented with their properties:

```markdown
#### V
- **Type**: Vector Register
- **Width**: 128 bits
- **Lanes**: 4
- **Element Width**: 32 bits
```

## Complete Example

See `examples/simd.isa` for a complete SIMD ISA example with:
- Vector registers
- Vector-vector operations (VADD, VSUB, VMUL)
- Vector-scalar operations (VADD_SCALAR, VMUL_SCALAR)
- Vector-immediate operations (VADD_IMM)
- Vector memory operations (VLOAD, VSTORE)
- Vector reduction operations (VDOT)
- Vector comparison operations (VMAX, VMIN)

## Limitations and Future Enhancements

### Current Limitations

1. **No for loops in RTL**: Loops must be unrolled manually
2. **Fixed lane indices**: Lane indices must be constants or operand references
3. **No vector masking**: All lanes are processed unconditionally

### Future Enhancements

1. **For loop support**: Add `for` loops to RTL for easier vector operation specification
2. **Vector masking**: Support predicate/mask registers for conditional lane execution
3. **Variable lane indices**: Support computed lane indices
4. **Vector shuffles**: Support lane permutation operations
5. **Multiple element widths**: Support mixed-width operations (e.g., 16-bit and 32-bit in same register)

## Usage

1. Define vector registers in the `registers` block
2. Create instruction formats for vector operations
3. Define vector instructions with lane-wise RTL behavior
4. Generate tools as usual:

```bash
uv run isa-dsl generate examples/simd.isa --output output/
```

The generated simulator will support vector register operations with proper lane access.

