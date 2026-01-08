# Language Server Support for ISA DSL

The ISA DSL includes Language Server Protocol (LSP) support through a VS Code extension, enabling rich IDE features like syntax highlighting, code completion, hover information, and real-time diagnostics.

## Overview

The language server provides:

- **Syntax Highlighting**: Color-coded keywords, comments, strings, numbers, and operators
- **Code Completion**: Context-aware suggestions for keywords, register types, and operators
- **Hover Information**: Documentation tooltips when hovering over keywords
- **Error Diagnostics**: Real-time validation with precise error reporting
- **Definition Lookup**: Go-to-definition for format and instruction references

## Installation

### Prerequisites

- Python 3.8+ with ISA DSL installed
- Node.js 16.0+ and npm (required for building the extension)
- VS Code (for using the extension)

### Building the Extension

The VS Code extension source is included in the ISA DSL package. Build it using the CLI command:

```bash
isa-dsl build-extension
```

This command will:
1. Check for Node.js and npm (provide instructions if missing)
2. Install `@vscode/vsce` if needed
3. Install extension dependencies
4. Compile TypeScript source
5. Package the extension into a VSIX file
6. Output the VSIX to `dist/` directory

**Options:**
- `--output-dir DIR`: Specify output directory (default: `dist`)
- `--skip-deps`: Skip dependency installation (faster for development)

**Example:**
```bash
# Build with default settings
isa-dsl build-extension

# Build to custom directory
isa-dsl build-extension --output-dir my-extensions

# Skip dependency installation (if already installed)
isa-dsl build-extension --skip-deps
```

### Installing the Extension

After building, install the VSIX file in VS Code:

1. **Open VS Code**
2. **Open Extensions**: Press `Ctrl+Shift+X` (or `Cmd+Shift+X` on Mac)
3. **Install from VSIX**:
   - Click the "..." menu (three dots) in the top right of the Extensions panel
   - Select "Install from VSIX..."
   - Navigate to the `dist/` directory (or your custom output directory)
   - Select the `.vsix` file (e.g., `isa-dsl-language-server-0.1.0.vsix`)
   - Click "Install"
4. **Reload VS Code**: Click "Reload" when prompted, or press `Ctrl+Shift+P` → "Developer: Reload Window"

## End-User Setup Guide

### Step-by-Step: Building and Installing

#### Step 1: Install ISA DSL Package

```bash
# Using pip
pip install isa-dsl

# Or for development
pip install -e .

# Or using UV
uv sync
```

#### Step 2: Verify Prerequisites

The build script will check for Node.js and npm. If they're not installed:

**Windows:**
1. Visit https://nodejs.org/
2. Download the LTS version
3. Run the installer
4. Restart your terminal

**Linux:**
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**macOS (with Homebrew):**
```bash
brew install node
```

#### Step 3: Build the Extension

```bash
isa-dsl build-extension
```

The script will:
- ✓ Check Node.js installation
- ✓ Check npm installation
- ✓ Install vsce (VS Code Extension manager)
- ✓ Install extension dependencies
- ✓ Compile TypeScript
- ✓ Package VSIX file

**Expected output:**
```
============================================================
ISA DSL VS Code Extension Builder
============================================================
Extension directory: /path/to/isa_dsl/vscode_extension
Output directory: /path/to/dist

Checking Node.js installation...
✓ Node.js v20.x.x found
Checking npm installation...
✓ npm 10.x.x found
Checking vsce installation...
✓ vsce found
Installing extension dependencies...
✓ Dependencies installed successfully
Compiling TypeScript...
✓ TypeScript compiled successfully
Packaging extension...
✓ Extension packaged: /path/to/dist/isa-dsl-language-server-0.1.0.vsix

============================================================
Build completed successfully!
============================================================

VSIX file: /path/to/dist/isa-dsl-language-server-0.1.0.vsix

To install in VS Code:
  1. Open VS Code
  2. Press Ctrl+Shift+X (or Cmd+Shift+X on Mac)
  3. Click '...' menu (top right)
  4. Select 'Install from VSIX...'
  5. Select: /path/to/dist/isa-dsl-language-server-0.1.0.vsix
  6. Click 'Install' and reload when prompted
============================================================
```

#### Step 4: Install in VS Code

1. **Open VS Code**
2. **Open Extensions Panel**: `Ctrl+Shift+X` (or `Cmd+Shift+X` on Mac)
3. **Install from VSIX**:
   - Click the "..." (three dots) menu in the top right
   - Select "Install from VSIX..."
   - Navigate to the `dist/` directory
   - Select the `.vsix` file
   - Click "Install"
4. **Reload Window**: Click "Reload" when prompted

#### Step 5: Verify Installation

1. **Open a `.isa` file** (e.g., `examples/arm_cortex_a9.isa`)
2. **Check syntax highlighting**: Keywords should be colored
3. **Test completion**: 
   - Type `arch` and press `Ctrl+Space`
   - Should see `architecture` in suggestions
4. **Test hover**: 
   - Hover over `architecture` keyword
   - Should see documentation tooltip
5. **Test diagnostics**: 
   - Make a syntax error (remove a `}`)
   - Should see red squiggles
   - Check Problems panel: `View → Problems` (`Ctrl+Shift+M`)

## Features

### Syntax Highlighting

The extension provides syntax highlighting for:
- **Keywords**: `architecture`, `registers`, `formats`, `instructions`, etc. (blue/purple)
- **Register Types**: `gpr`, `sfr`, `vec` (different color)
- **Comments**: `//` style (gray/italic)
- **Strings**: Double-quoted strings (green/yellow)
- **Numbers**: Integers, hex (`0x...`), binary (`0b...`) (orange/blue)
- **Operators**: `+`, `-`, `*`, `/`, `=`, etc. (default color)

### Code Completion

Automatic code completion for:
- **Keywords**: `architecture`, `registers`, `formats`, `instructions`, `format`, `bundle`, `instruction`, `encoding`, `operands`, `assembly_syntax`, `behavior`
- **Register Types**: `gpr`, `sfr`, `vec`
- **RTL Keywords**: `if`, `else`, `for`, `MEM`
- **Operators**: `<<`, `>>`, `<=`, `>=`, `==`, `!=`, `+`, `-`, `*`, `/`, `%`, `&`, `|`, `^`
- **Context-aware**: Operators suggested in RTL context (behavior blocks)

**Usage**: Type a keyword and press `Ctrl+Space` (or `Cmd+Space` on Mac)

### Hover Information

Hover over keywords to see documentation:
- **Architecture definitions**: What `architecture` block does
- **Register types**: Documentation for `gpr`, `sfr`, `vec`
- **Instruction formats**: Information about format definitions
- **RTL keywords**: Documentation for RTL constructs

**Usage**: Hover your mouse over any keyword

### Error Diagnostics

Real-time syntax validation:
- **Syntax errors**: Missing braces, invalid syntax
- **Semantic errors**: Duplicate definitions, undefined references
- **Validation errors**: Format reference errors, register conflicts
- **Built-in function validation**: Parameter validation for `sign_extend`, `zero_extend`, `to_signed`, `to_unsigned` (checks for positive values, reasonable bit widths)

**Usage**: Errors appear as red squiggles and in the Problems panel

**Built-in Function Validation**:
The language server validates built-in function calls and reports errors for:
- Invalid parameter counts (e.g., `sign_extend` requires 2-3 arguments)
- Invalid bit counts (must be positive and <= 64)
- Unknown built-in functions (warnings for unrecognized function names)

Example validation errors:
- `sign_extend(R[rs1], 0)` → Error: "from_bits must be positive, got 0"
- `sign_extend(R[rs1], 65)` → Error: "from_bits must be <= 64, got 65"

### Definition Lookup

Go-to-definition for format references:
- Click on a format name in an instruction
- Press `F12` or right-click → "Go to Definition"
- Jumps to the format definition

## Configuration

The extension can be configured in VS Code settings:

```json
{
    "isa-dsl.enableLanguageServer": true
}
```

## Troubleshooting

### Build Script Issues

**Problem**: "Node.js is not installed"
- **Solution**: Install Node.js 16.0+ from https://nodejs.org/
- The script will provide installation instructions if Node.js is missing

**Problem**: "npm not found"
- **Solution**: npm is included with Node.js. Reinstall Node.js if npm is missing

**Problem**: "Failed to install vsce"
- **Solution**: Try installing manually: `npm install -g @vscode/vsce`
- Check that you have permissions for global npm installs

**Problem**: "TypeScript compilation failed"
- **Solution**: Check that all dependencies are installed: `cd isa_dsl/vscode_extension && npm install`
- Check TypeScript version: `npx tsc --version`

**Problem**: "VSIX packaging failed"
- **Solution**: Ensure `vsce` is installed: `npm install -g @vscode/vsce`
- Check that TypeScript compiled successfully (check for `out/` directory)

### Extension Issues

**Problem**: Extension doesn't activate
- **Solution**: 
  - Check Output panel: `View → Output` → Select "ISA DSL Language Server"
  - Reload window: `Ctrl+Shift+P` → "Developer: Reload Window"
  - Verify file has `.isa` extension

**Problem**: No syntax highlighting
- **Solution**:
  - Check language mode (bottom right should show "ISA DSL")
  - Verify file has `.isa` extension
  - Reload window

**Problem**: No completions
- **Solution**:
  - Verify extension is enabled
  - Try manual trigger: `Ctrl+Space`
  - Check Output panel for errors

**Problem**: Language server not starting
- **Solution**:
  - Check Output panel for error messages
  - Verify extension is installed and enabled
  - Check VS Code version (requires 1.74.0+)

### Manual Build (Alternative)

If the build script doesn't work, you can build manually:

```bash
cd isa_dsl/vscode_extension

# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Install vsce (if not installed)
npm install -g @vscode/vsce

# Package extension
vsce package
```

The VSIX file will be created in the `isa_dsl/vscode_extension/` directory.

## Development

### Extension Source Location

The extension source is located in `isa_dsl/vscode_extension/`:
- `src/` - TypeScript source files
- `syntaxes/` - TextMate grammar for syntax highlighting
- `package.json` - Extension manifest
- `tsconfig.json` - TypeScript configuration

### Modifying the Extension

1. **Edit source files** in `isa_dsl/vscode_extension/src/`
2. **Compile**: `cd isa_dsl/vscode_extension && npm run compile`
3. **Test**: Press `F5` in VS Code to run in development mode
4. **Rebuild**: Run `isa-dsl build-extension` to create new VSIX

### Extension Structure

- `extension.ts` - Extension entry point, starts language server
- `server.ts` - LSP server implementation (diagnostics, completion, hover, definition)
- `parser.ts` - ISA DSL parser in TypeScript
- `types.ts` - TypeScript type definitions

## Future Enhancements

Potential future features:
- Symbol navigation
- Code formatting
- Refactoring support
- Better error messages with precise locations
- Multi-file include support in language server
- Format reference resolution across files

## Testing the Extension

The extension includes a comprehensive test suite using Vitest. Run tests using:

```bash
# Run extension tests
cd vscode_extension/isa/packages/language
npm test

# Run with watch mode (for development)
npm run test:watch
```

**Note:** Extension tests require Node.js 20+ and npm. The tests are automatically run in CI on every push and pull request.

The test suite includes:
- **Parsing tests**: Verify ISA DSL parsing functionality
- **Linking tests**: Verify cross-reference resolution
- **Validation tests**: Verify error detection and reporting
- **Completion tests**: Verify code completion functionality (15 tests)

**Test Status**: ✅ All 55 tests passing (1 parsing, 1 linking, 1 validation, 15 completion, 22 built-in functions, 15 behavior features)

## Support

For issues or questions:
- Check the Output panel in VS Code for error messages
- Verify all prerequisites are installed
- Try rebuilding the extension
- Check VS Code version compatibility
- Run tests: `isa-dsl test-extension` to verify extension functionality

