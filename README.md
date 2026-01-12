![Version](https://img.shields.io/badge/version-0.4.0-blue.svg)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
# ISA DSL - Instruction Set Architecture Domain Specific Language

A powerful Domain Specific Language (DSL) for describing Instruction Set Architectures (ISA) using textX. This DSL enables you to specify instruction formats, registers, instruction encodings, and behavior in RTL (Register Transfer Level) notation, with automatic code generation for simulators, assemblers, disassemblers, and documentation.

**Repository**: [https://github.com/ajithpadman/isadsl.git](https://github.com/ajithpadman/isadsl.git)

## Features

- **Complete ISA Specification**: Define instruction formats, registers (GPRs, SFRs, and vector registers), and instruction encodings
- **RTL Behavior**: Specify instruction behavior using Register Transfer Level notation with support for:
  - Arithmetic and logical operations
  - Bitwise shift operations (`<<`, `>>`)
  - Ternary conditional expressions (`condition ? then : else`)
  - Conditional statements
  - Memory access operations
  - Vector/SIMD operations
  - Bitfield access (`value[msb:lsb]`)
  - Built-in functions (`sign_extend`, `zero_extend`, `extract_bits`, `to_signed`, `to_unsigned`)
- **Automatic Code Generation**: Generate production-ready tools:
  - Python-based instruction simulators
  - Assemblers for your ISA
  - Disassemblers for binary code
  - Markdown documentation
- **SIMD Support**: Built-in support for vector registers and SIMD instructions
- **Validation**: Comprehensive semantic validation of ISA specifications
- **Language Server Protocol (LSP) Support**: Full IDE integration with VS Code extension providing:
  - Real-time syntax highlighting
  - Code completion
  - Hover documentation
  - Error diagnostics

## Installation

### From PyPI (Recommended)

Install the package directly from PyPI using pip:

```bash
pip install isa-dsl
```

### From Source

If you want to install from source or contribute to the project:

**Prerequisites:**
- Python 3.8 or higher
- [UV](https://github.com/astral-sh/uv) (recommended) or pip

**Using UV:**

```bash
# Install UV first
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or on Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Clone the repository
git clone https://github.com/ajithpadman/isadsl.git
cd isadsl

# Install the project and dependencies
uv sync

# Or install in development mode with test dependencies
uv sync --dev
```

**Using pip:**

```bash
# Clone the repository
git clone https://github.com/ajithpadman/isadsl.git
cd isadsl

# Install dependencies
pip install -r requirements.txt

# Or install in editable mode
pip install -e .
```

## Quick Start

### 1. Create an ISA Specification

Create a `.isa` file defining your instruction set architecture. Here's a simple example:

```isa
architecture SimpleRISC {
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
    }
    
    instructions {
        instruction ADD {
            format: R_TYPE
            encoding: { opcode=0 }
            operands: rd, rs1, rs2
            assembly_syntax: "ADD R{rd}, R{rs1}, R{rs2}"
            behavior: {
                R[rd] = R[rs1] + R[rs2];
            }
        }
    }
}
```

### 2. Generate Tools

Generate simulator, assembler, disassembler, and documentation:

```bash
isa-dsl generate your_isa.isa --output output/
```

This creates:
- `output/simulator.py` - Instruction simulator
- `output/assembler.py` - Assembler for your ISA
- `output/disassembler.py` - Disassembler for binary code
- `output/documentation.md` - ISA documentation

### 3. Use the Generated Tools

**Validate your ISA:**
```bash
isa-dsl validate your_isa.isa
```

**Get ISA information:**
```bash
isa-dsl info your_isa.isa
```

**Assemble code:**
```bash
python output/assembler.py program.s -o program.bin
```

**Disassemble binary:**
```bash
python output/disassembler.py program.bin
```

**Run simulator:**
```bash
python output/simulator.py program.bin
```

For more complex examples, see the [examples](examples/) directory or check the [DSL Specification](docs/DSL_Specification.md).

## Documentation

All technical documentation is available in the `docs/` folder:

- **[INDEX.md](docs/INDEX.md)**: Documentation index and navigation guide - Start here to find what you need
- **[DSL_Specification.md](docs/DSL_Specification.md)**: Complete DSL specification covering all features including syntax, registers, formats, instructions, RTL behavior, variable-length instructions, bundling, SIMD, and more
- **[EXAMPLES.md](docs/EXAMPLES.md)**: Detailed documentation of example ISA specifications with learning paths and common patterns
- **[TESTING.md](docs/TESTING.md)**: Complete testing documentation including test suite overview, how to run tests, and how to add new tests
- **[LANGUAGE_SERVER.md](docs/LANGUAGE_SERVER.md)**: Language Server Protocol (LSP) setup and usage guide for VS Code extension

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

After installation, the `isa-dsl` command is available. It provides several subcommands:

### Generate Tools

```bash
isa-dsl generate <isa_file> --output <output_dir>
```

**Options:**
- `--simulator` / `--no-simulator`: Generate simulator (default: enabled)
- `--assembler` / `--no-assembler`: Generate assembler (default: enabled)
- `--disassembler` / `--no-disassembler`: Generate disassembler (default: enabled)
- `--docs` / `--no-docs`: Generate documentation (default: enabled)

**Example:**
```bash
isa-dsl generate examples/arm_cortex_a9.isa --output output/
```

### Validate ISA

```bash
isa-dsl validate <isa_file>
```

Validates the ISA specification and reports any errors or warnings.

### Display ISA Information

```bash
isa-dsl info <isa_file>
```

Displays summary information about the ISA specification.

## Features

- **Virtual Registers**: Concatenate multiple registers to form wider virtual registers
- **Register Aliases**: Define alternative names for registers (e.g., `SP = R[13]`)
- **Register Fields**: Access register fields like C union members (e.g., `PSW.V`, `PSW.C`)
- **Instruction Aliases**: Define alternative mnemonics with custom assembly syntax
- **Variable-Length Instructions**: Support for instructions of different widths
- **Instruction Bundling**: Bundle multiple instructions into a single instruction word
- **SIMD/Vector Support**: Built-in support for vector registers and SIMD operations
- **Multi-File Support**: Organize large ISA specifications across multiple files using `#include`
- **Shift Operations**: Left shift (`<<`) and arithmetic right shift (`>>`) operators
- **Ternary Expressions**: Conditional value selection (`condition ? then : else`)
- **Bitfield Access**: Extract bit ranges from values (`value[msb:lsb]`)
- **Built-in Functions**: Sign/zero extension and bit extraction functions
- **VS Code Extension**: Full IDE support with syntax highlighting, code completion, and error diagnostics

## Testing

The project includes a comprehensive test suite with **216 test cases** covering all features. All tests pass successfully.

**Test Status**: 
- ✅ All Python tests passing (216 test cases, 200+ test functions including parametrized tests)
- ✅ All VS Code extension tests passing (55 tests)
- ✅ Continuous Integration (CI) runs all tests automatically

To run tests from source:
```bash
# After cloning and installing from source
pytest
```

## Development

To contribute to the project:

```bash
# Clone the repository
git clone https://github.com/ajithpadman/isadsl.git
cd isadsl

# Install in development mode
pip install -e ".[dev]"

# Or using UV
uv sync --dev

# Run tests
pytest
```

## Requirements

- Python 3.8 or higher
- textX >= 3.0.0
- Jinja2 >= 3.1.0
- Click >= 8.1.0

Dependencies are automatically installed when installing from PyPI.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see the [GitHub repository](https://github.com/ajithpadman/isadsl.git) for contribution guidelines.

**Before contributing:**
- Ensure all tests pass (`pytest`)
- Follow existing code style conventions
- Update documentation for new features
- Add tests for new functionality

## Links

- **GitHub Repository**: [https://github.com/ajithpadman/isadsl.git](https://github.com/ajithpadman/isadsl.git)
- **Documentation**: See the [docs/](docs/) directory for complete documentation
- **Examples**: Check [examples/](examples/) for ISA specification examples
