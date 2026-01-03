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

1. **Define your ISA** in a `.isa` file (see `examples/sample_isa.isa` for a complete example)

2. **Generate tools**:

```bash
# Using UV
uv run isa-dsl generate examples/sample_isa.isa --output output/

# Or using Python directly
python -m isa_dsl.cli generate examples/sample_isa.isa --output output/
```

3. **Use the generated tools**:

```bash
# Validate your ISA
uv run isa-dsl validate examples/sample_isa.isa

# Get ISA information
uv run isa-dsl info examples/sample_isa.isa

# Run the generated simulator
python output/simulator.py program.bin
```

## Documentation

All technical documentation is available in the `docs/` folder:

- **[INDEX.md](docs/INDEX.md)**: Documentation index and navigation guide - Start here to find what you need
- **[USAGE.md](docs/USAGE.md)**: Complete usage guide covering DSL syntax, register definitions, instruction formats, RTL behavior specification, command-line interface, and best practices
- **[SIMD_SUPPORT.md](docs/SIMD_SUPPORT.md)**: Guide to SIMD vector instructions including vector register definitions, vector instruction syntax, lane access patterns, and example vector operations
- **[BUNDLING.md](docs/BUNDLING.md)**: Guide to instruction bundling including bundle formats, bundle instructions, assembly syntax, and two-level decoding
- **[EXAMPLES.md](docs/EXAMPLES.md)**: Detailed documentation of example ISA specifications with learning paths and common patterns
- **[TESTING.md](docs/TESTING.md)**: Complete testing documentation including test suite overview, how to run tests, and how to add new tests

## Examples

The `examples/` directory contains several example ISA specifications:

- **`minimal.isa`**: A minimal ISA with just a few instructions - perfect for learning the basics
- **`sample_isa.isa`**: A complete example with R-type, I-type, and branch instructions
- **`advanced.isa`**: An advanced RISC architecture with 23 instructions and multiple formats
- **`simd.isa`**: SIMD example with vector registers and vector operations

To generate tools from an example:

```bash
uv run isa-dsl generate examples/sample_isa.isa --output output/
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

## Requirements

- Python 3.8+
- textX >= 3.0.0
- Jinja2 >= 3.1.0
- Click >= 8.1.0

For development:
- pytest >= 7.4.0
- pytest-cov >= 4.1.0

## License

MIT License

## Contributing

Contributions are welcome! Please ensure that:
- All tests pass (`uv run pytest`)
- Code follows existing style conventions
- Documentation is updated for new features
