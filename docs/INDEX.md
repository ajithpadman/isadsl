# ISA DSL Documentation Index

Welcome to the ISA DSL documentation. This index helps you navigate all available documentation.

## Getting Started

- **[README.md](../README.md)**: Project overview, installation, and quick start guide
- **[DSL Specification](DSL_Specification.md)**: Complete specification of all DSL features
- **[Examples Guide](EXAMPLES.md)**: Detailed documentation of example ISA specifications

## Feature Documentation

- **[DSL Specification](DSL_Specification.md)**: Complete specification of all DSL features including SIMD, bundling, variable-length instructions, and more
- **[Testing](TESTING.md)**: Complete testing documentation including test suite overview and how to add new tests

**Note**: For detailed feature documentation, see [DSL Specification](DSL_Specification.md) which consolidates all DSL features.

## Generated Tools Documentation

- **[Simulator](Simulator.md)**: Documentation for the generated instruction simulator
- **[Assembler](Assembler.md)**: Documentation for the generated assembler
- **[Disassembler](Disassembler.md)**: Documentation for the generated disassembler
- **[Documentation Generation](documentation_generation.md)**: Documentation generator features and usage

## Quick Links

### For New Users
1. Start with the [README.md](../README.md) for installation and quick start
2. Read the [DSL Specification](DSL_Specification.md) for complete feature reference
3. Explore [Examples](EXAMPLES.md) to see real ISA specifications

### For Advanced Users
- [DSL Specification](DSL_Specification.md) - Complete feature reference
- [Examples](EXAMPLES.md) - Advanced examples and patterns
- [Testing](TESTING.md) - Test suite documentation and adding new tests

## Documentation Structure

```
docs/
├── INDEX.md                  # This file - documentation index
├── DSL_Specification.md     # Complete DSL specification (all features)
├── EXAMPLES.md               # Example ISA specifications guide
├── TESTING.md                # Testing documentation and test suite overview
├── Simulator.md              # Generated simulator documentation
├── Assembler.md              # Generated assembler documentation
├── Disassembler.md           # Generated disassembler documentation
├── documentation_generation.md  # Documentation generator features
```

## Command Reference

All commands use the `isa-dsl` CLI:

```bash
# Generate tools from ISA specification
uv run isa-dsl generate <isa_file> --output <output_dir>

# Validate ISA specification
uv run isa-dsl validate <isa_file>

# Display ISA information
uv run isa-dsl info <isa_file>
```

For detailed command options, see [README.md](../README.md#command-line-interface).

## Examples

Example ISA specifications are located in the `examples/` directory:

- `minimal.isa` - Minimal example for learning
- `sample_isa.isa` - Complete RISC example
- `advanced.isa` - Advanced RISC with 23 instructions
- `simd.isa` - SIMD/vector instruction example

See [Examples Guide](EXAMPLES.md) for detailed descriptions.
