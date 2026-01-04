# ISA DSL Examples

This directory contains reference ISA specifications demonstrating the multi-file approach.

## ARM Cortex-A9 ISA Specification

A comprehensive ARM Cortex-A9 ISA specification organized across multiple files:

- `arm_cortex_a9.isa` - Main architecture file with includes
- `arm_cortex_a9_registers.isa` - Register definitions
- `arm_cortex_a9_formats.isa` - Instruction format definitions
- `arm_cortex_a9_instructions.isa` - Instruction definitions

This demonstrates:
- Multi-file ISA specification using `#include` directives
- Cross-file format reference resolution via textX scope providers
- Modular organization of ISA components

Note: Test-specific ISA files are located in `tests/*/test_data/` directories.
