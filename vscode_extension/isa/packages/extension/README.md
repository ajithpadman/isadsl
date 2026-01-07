# ISA DSL Language Server

[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](https://marketplace.visualstudio.com/items?itemName=ajithpadman.isa-dsl-language-server)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A comprehensive VS Code extension providing language support for the **ISA DSL (Instruction Set Architecture Domain Specific Language)**. This extension offers syntax highlighting, code completion, validation, and seamless integration with the ISA-DSL Python toolchain.

## Features

### 🎨 Language Support
- **Syntax Highlighting**: Full syntax highlighting for `.isa` files
- **Code Completion**: Intelligent autocomplete for ISA DSL keywords, instruction formats, registers, and more
- **Hover Documentation**: Get instant information about ISA elements by hovering over them
- **Error Diagnostics**: Real-time validation with detailed error messages

### 🔧 Integrated Toolchain
- **Install Python Package**: Install the `isa-dsl` Python package directly from VS Code using `uv`
- **Generate Tools**: Generate simulators, assemblers, disassemblers, and documentation
- **Validate ISA Files**: Validate your ISA specification files
- **View ISA Info**: Get detailed information about your ISA specification

### 📝 ISA DSL Capabilities
- Define instruction formats with field specifications
- Specify registers (GPRs, SFRs, vector registers)
- Define virtual registers (concatenated registers)
- Create register aliases
- Define instruction encodings (hex and decimal values)
- Specify instruction behavior using RTL (Register Transfer Level) notation
- Support for temporary variables in RTL behavior
- Support for hexadecimal values in behavior expressions
- External behavior functions for complex instructions
- Bundle instruction formats for VLIW architectures
- Instruction aliases for alternative mnemonics

## Installation

### From VS Code Marketplace

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X / Cmd+Shift+X)
3. Search for "ISA DSL Language Server"
4. Click Install

### From VSIX File

1. Download the `.vsix` file
2. Open VS Code
3. Go to Extensions → ... (More Actions) → Install from VSIX...
4. Select the downloaded `.vsix` file

## Requirements

- **VS Code**: Version 1.67.0 or higher
- **Python**: Python 3.8 or higher (for ISA-DSL Python package)
- **UV** (Optional but recommended): For managing the Python package installation

## Quick Start

### 1. Install the Python Package

After installing the extension, you need to install the ISA-DSL Python package:

1. Open the Command Palette (Ctrl+Shift+P / Cmd+Shift+P)
2. Run: `ISA-DSL: Install Python Package`
3. The extension will use `uv` to install `isa-dsl` in your workspace

Alternatively, install manually:
```bash
pip install isa-dsl
# Or using uv:
uv tool install isa-dsl
```

### 2. Create an ISA File

Create a new file with the `.isa` extension:

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
            encoding: {
                opcode=0x01
            }
            operands: rd,rs1,rs2
            behavior: {
                R[rd] = R[rs1] + R[rs2];
            }
        }
    }
}
```

### 3. Use Extension Commands

Right-click on an `.isa` file or use the Command Palette to access:

- **ISA-DSL: Generate** - Generate simulators, assemblers, disassemblers, and documentation
- **ISA-DSL: Validate** - Validate your ISA specification
- **ISA-DSL: Info** - View detailed information about your ISA

## Commands

| Command | Description | Shortcut |
|---------|-------------|----------|
| `ISA-DSL: Install Python Package` | Install the isa-dsl Python package using uv | - |
| `ISA-DSL: Generate` | Generate tools from ISA specification | Right-click on `.isa` file |
| `ISA-DSL: Validate` | Validate ISA specification | Right-click on `.isa` file |
| `ISA-DSL: Info` | Show ISA specification information | Right-click on `.isa` file |
| `ISA-DSL: Show Extension Version` | Display the extension version | - |

## Features in Detail

### Syntax Highlighting

The extension provides comprehensive syntax highlighting for:
- Keywords (`instruction`, `format`, `register`, etc.)
- Register names and field accesses
- Hex values (`0x0B`) and binary values (`0b1010`)
- RTL expressions and operators
- Comments (single-line `//` and multi-line `/* */`)

### Code Completion

Intelligent autocomplete suggestions for:
- ISA DSL keywords
- Register names and field names
- Instruction format names
- Operand specifications
- RTL operators and functions

### Validation

Real-time validation checks for:
- Format field definitions and overlaps
- Register specifications
- Instruction encoding validity
- Operand references
- Virtual register component validation
- Register alias references
- RTL expression syntax

### Integrated Python Toolchain

The extension seamlessly integrates with the ISA-DSL Python package:

- **Cross-platform**: Works on Linux, Windows, and macOS
- **Automatic Detection**: Automatically finds `uv` or `isa-dsl` in your PATH
- **Output Channels**: All command outputs are displayed in dedicated VS Code output channels
- **Error Handling**: Clear error messages with actionable suggestions

## Example ISA Specifications

### Virtual Registers

```isa
registers {
    gpr D 32 [16]
    virtual register E 64 = {D[0]|D[1]}
}
```

### Register Aliases

```isa
registers {
    gpr R 32 [16]
    alias SP = R[13]
    alias LR = R[14]
}
```

### Instruction with Hex Encoding

```isa
instruction ABS {
    format: R_TYPE
    encoding: {
        op1=0x0B,
        op2=28
    }
    operands: s2,d
    behavior: {
        D[d] = D[s2]>=0?D[s2]:(0-D[s2]);
    }
}
```

### External Behavior Functions

```isa
instruction COMPLEX_OP {
    format: R_TYPE
    encoding: {
        opcode=0x10
    }
    operands: rd,rs1,rs2
    external_behavior: True
}
```

## Configuration

The extension uses the default VS Code settings. No additional configuration is required. The extension will automatically:

- Associate `.isa` files with the ISA DSL language
- Provide language features for all `.isa` files in your workspace
- Detect and use the ISA-DSL Python package from your environment

## Troubleshooting

### Python Package Not Found

If you see errors about the Python package not being found:

1. Install the package using the extension command: `ISA-DSL: Install Python Package`
2. Or install manually: `pip install isa-dsl` or `uv tool install isa-dsl`
3. Ensure Python is in your PATH

### Validation Errors

If you see validation errors:

1. Check that your ISA file syntax is correct
2. Verify that all referenced formats and registers are defined
3. Ensure encoding values fit within field widths
4. Check that virtual register component widths sum correctly

### Command Not Working

If commands fail:

1. Check the Output panel for detailed error messages
2. Verify that `uv` or `isa-dsl` is installed and in your PATH
3. Try running the command from the terminal to see the actual error

## Contributing

Contributions are welcome! Please see the main repository for contribution guidelines:

**Repository**: [https://github.com/ajithpadman/isadsl](https://github.com/ajithpadman/isadsl)

## License

This extension is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Links

- **Repository**: [https://github.com/ajithpadman/isadsl](https://github.com/ajithpadman/isadsl)
- **Python Package**: [PyPI - isa-dsl](https://pypi.org/project/isa-dsl/)
- **Issues**: [GitHub Issues](https://github.com/ajithpadman/isadsl/issues)

## Release Notes

See [RELEASE_NOTES.md](https://github.com/ajithpadman/isadsl/blob/main/RELEASE_NOTES.md) for detailed release notes and changelog.

## Support

For issues, questions, or feature requests, please open an issue on GitHub:

[https://github.com/ajithpadman/isadsl/issues](https://github.com/ajithpadman/isadsl/issues)

---

**Enjoy using ISA DSL!** 🚀

