# ISA DSL Documentation Index

Welcome to the ISA DSL documentation. This index helps you navigate all available documentation.

## Getting Started

- **[README.md](../README.md)**: Project overview, installation, and quick start guide
- **[Usage Guide](USAGE.md)**: Complete guide to using the ISA DSL
- **[Examples Guide](EXAMPLES.md)**: Detailed documentation of example ISA specifications

## Feature Documentation

- **[SIMD Support](SIMD_SUPPORT.md)**: Guide to using SIMD vector instructions and vector registers
- **[Instruction Bundling](BUNDLING.md)**: Guide to instruction bundling with bundle formats and two-level decoding
- **[Testing](TESTING.md)**: Complete testing documentation including test suite overview and how to add new tests

## Quick Links

### For New Users
1. Start with the [README.md](../README.md) for installation and quick start
2. Read the [Usage Guide](USAGE.md) to learn the DSL syntax
3. Explore [Examples](EXAMPLES.md) to see real ISA specifications

### For Advanced Users
- [SIMD Support](SIMD_SUPPORT.md) - Vector instruction support
- [Instruction Bundling](BUNDLING.md) - Bundle multiple instructions into wider words
- [Usage Guide](USAGE.md) - Complete syntax reference
- [Examples](EXAMPLES.md) - Advanced examples and patterns
- [Testing](TESTING.md) - Test suite documentation and adding new tests

## Documentation Structure

```
docs/
├── INDEX.md          # This file - documentation index
├── USAGE.md          # Complete usage guide and syntax reference
├── SIMD_SUPPORT.md   # SIMD/vector instruction documentation
├── BUNDLING.md       # Instruction bundling documentation
├── EXAMPLES.md       # Example ISA specifications guide
└── TESTING.md        # Testing documentation and test suite overview
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

For detailed command options, see [Usage Guide](USAGE.md#command-line-interface).

## Examples

Example ISA specifications are located in the `examples/` directory:

- `minimal.isa` - Minimal example for learning
- `sample_isa.isa` - Complete RISC example
- `advanced.isa` - Advanced RISC with 23 instructions
- `simd.isa` - SIMD/vector instruction example

See [Examples Guide](EXAMPLES.md) for detailed descriptions.
