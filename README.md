# ISA DSL - Instruction Set Architecture Domain Specific Language

A powerful Domain Specific Language (DSL) for describing Instruction Set Architectures (ISA) using textX. This DSL enables you to specify instruction formats, registers, instruction encodings, and behavior in RTL (Register Transfer Level) notation, with automatic code generation for simulators, assemblers, disassemblers, and documentation.

## Features

- **Complete ISA Specification**: Define instruction formats, registers (GPRs, SFRs, and vector registers), and instruction encodings
- **RTL Behavior**: Specify instruction behavior using Register Transfer Level notation with support for:
  - Arithmetic and logical operations
  - Conditional statements
  - Memory access operations
  - Vector/SIMD operations
- **Automatic Code Generation**: Generate production-ready tools:
  - Python-based instruction simulators
  - Assemblers for your ISA
  - Disassemblers for binary code
  - Markdown documentation
- **SIMD Support**: Built-in support for vector registers and SIMD instructions
- **Validation**: Comprehensive semantic validation of ISA specifications

## Installation

### Prerequisites

- Python 3.8 or higher
- [UV](https://github.com/astral-sh/uv) (recommended) or pip

### Using UV (Recommended)

[UV](https://github.com/astral-sh/uv) is a fast Python package manager. Install it first:

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or on Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then install the project:

```bash
# Clone the repository
git clone <repository-url>
cd isa-dsl

# Install the project and dependencies
uv sync

# Or install in development mode with test dependencies
uv sync --dev
```

### Using pip (Alternative)

```bash
# Clone the repository
git clone <repository-url>
cd isa-dsl

# Install dependencies
pip install -r requirements.txt

# Or install in editable mode
pip install -e .
```

## Quick Start

1. **Define your ISA** in a `.isa` file (see `examples/arm_cortex_a9.isa` for a multi-file example)

2. **Generate tools**:

```bash
# Using UV
uv run isa-dsl generate examples/arm_cortex_a9.isa --output output/

# Or using Python directly
python -m isa_dsl.cli generate examples/arm_cortex_a9.isa --output output/
```

3. **Use the generated tools**:

```bash
# Validate your ISA
uv run isa-dsl validate examples/arm_cortex_a9.isa

# Get ISA information
uv run isa-dsl info examples/arm_cortex_a9.isa

# Run the generated simulator
python output/simulator.py program.bin
```

## Documentation

All technical documentation is available in the `docs/` folder:

- **[INDEX.md](docs/INDEX.md)**: Documentation index and navigation guide - Start here to find what you need
- **[DSL_Specification.md](docs/DSL_Specification.md)**: Complete DSL specification covering all features including syntax, registers, formats, instructions, RTL behavior, variable-length instructions, bundling, SIMD, and more
- **[EXAMPLES.md](docs/EXAMPLES.md)**: Detailed documentation of example ISA specifications with learning paths and common patterns
- **[TESTING.md](docs/TESTING.md)**: Complete testing documentation including test suite overview, how to run tests, and how to add new tests

## Examples

The `examples/` directory contains reference ISA specifications demonstrating best practices:

- **`arm_cortex_a9.isa`**: Main ARM Cortex-A9 ISA specification (multi-file reference)
  - `arm_cortex_a9_registers.isa` - Register definitions
  - `arm_cortex_a9_formats.isa` - Instruction format definitions
  - `arm_cortex_a9_instructions.isa` - Instruction definitions

This demonstrates the multi-file approach using `#include` directives and cross-file format reference resolution.

**Note**: Test-specific ISA examples are located in `tests/*/test_data/` directories.

To generate tools from the reference example:

```bash
uv run isa-dsl generate examples/arm_cortex_a9.isa --output output/
```

## Command-Line Interface

The `isa-dsl` command provides several subcommands:

### Generate Tools

```bash
uv run isa-dsl generate <isa_file> --output <output_dir>
```

Options:
- `--simulator` / `--no-simulator`: Generate simulator (default: enabled)
- `--assembler` / `--no-assembler`: Generate assembler (default: enabled)
- `--disassembler` / `--no-disassembler`: Generate disassembler (default: enabled)
- `--docs` / `--no-docs`: Generate documentation (default: enabled)

### Validate ISA

```bash
uv run isa-dsl validate <isa_file>
```

### Display ISA Information

```bash
uv run isa-dsl info <isa_file>
```

## Testing

The project includes a comprehensive test suite with **111 automated tests** covering:

- **Core functionality**: ISA parsing, validation, RTL interpretation
- **Code generation**: Assembler, simulator, disassembler, documentation generators
- **Advanced features**: Variable-length instructions, instruction bundling, distributed operands
- **Integration tests**: End-to-end workflows, QEMU verification, ARM toolchain integration
- **Multi-file support**: Include processing, inheritance, merge modes
- **Assembly syntax**: Formatting, literal braces, backward compatibility

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov

# Run specific test suite
uv run pytest tests/arm/
```

**Test Status**: ✅ All 111 tests passing, 0 skipped, 0 failed

## Development

### Setup Development Environment

```bash
# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies (including dev dependencies)
uv sync --dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov
```

### Code Quality

- All test functions are limited to 50 lines or less
- All test files are limited to 500 lines or less
- Helper functions are organized as class methods in separate files
- Comprehensive test coverage across all major features

## Requirements

- Python 3.8+
- textX >= 3.0.0
- Jinja2 >= 3.1.0
- Click >= 8.1.0

For development:
- pytest >= 7.4.0
- pytest-cov >= 4.1.0

## Deployment

### Production Readiness

✅ **Ready for deployment** - The project is production-ready with:

- Comprehensive test suite (111 tests, all passing)
- Well-documented API and CLI interface
- Modular, maintainable codebase
- Complete documentation
- Example ISA specifications
- Validation and error handling

### Installation for Production

```bash
# Using UV (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
pip install -e .
```

### Building Distribution Packages

```bash
# Build wheel and source distribution
python -m build

# Or using UV
uv build
```

## License

MIT License

## Contributing

Contributions are welcome! Please ensure that:
- All tests pass (`uv run pytest`)
- Code follows existing style conventions
- Documentation is updated for new features
- Test functions are kept under 50 lines
- Test files are kept under 500 lines
