# Langium Setup for ISA DSL VS Code Extension

This document describes how to set up a Langium-based VS Code extension for ISA DSL, which provides code completion, syntax highlighting, and diagnostics without reimplementing the parser.

## Why Langium?

Langium is a language engineering framework that:
- Provides grammar-based language server features (completion, diagnostics, hover)
- Generates parsers and language servers automatically
- Integrates seamlessly with VS Code
- Eliminates the need to manually implement parsers in TypeScript

## Prerequisites

- Node.js 16.0+ and npm
- VS Code (for testing)

## Step 1: Install Yeoman and Langium Generator

```bash
npm install -g yo generator-langium
```

## Step 2: Scaffold Langium Extension

```bash
cd isa_dsl
mkdir vscode_extension_langium
cd vscode_extension_langium
yo langium
```

**When prompted, use these values:**
- **Extension Name:** `isa-dsl`
- **Language Name:** `ISADSL`
- **File Extensions:** `.isa`
- **VS Code Extension:** `Yes`
- **CLI:** `No` (optional)
- **Web Worker:** `No` (optional)
- **Language Tests:** `Yes`

## Step 3: Convert Grammar from textX to Langium

The existing textX grammar (`isa_dsl/grammar/isa.tx`) needs to be converted to Langium format (`src/language/isa-dsl.langium`).

### Key Differences:

1. **Grammar File Format:**
   - textX: `.tx` files
   - Langium: `.langium` files

2. **Syntax:**
   - textX uses `name=ID` for assignments
   - Langium uses `name: ID` for assignments

3. **Rules:**
   - textX: `RuleName: ... ;`
   - Langium: `RuleName: ... ;` (similar, but with different syntax for references)

### Example Conversion:

**textX (isa.tx):**
```
ISASpecFull:
    'architecture' name=ID '{'
        (properties*=Property)*
        (registers=RegisterBlock)?
    '}'
;
```

**Langium (isa-dsl.langium):**
```
ISASpecFull:
    'architecture' name=ID '{'
        (properties+=Property)*
        (registers=RegisterBlock)?
    '}'
;
```

## Step 4: Update Extension Configuration

1. **Keep existing syntax highlighting:**
   - Copy `syntaxes/isa-dsl.tmLanguage.json` to the new extension
   - Update `package.json` to reference it

2. **Update language configuration:**
   - Copy `language-configuration.json` to the new extension
   - Update `package.json` to reference it

3. **Update package.json:**
   - Ensure the extension name and language ID match
   - Verify file associations are correct

## Step 5: Implement Language Features

Langium automatically provides:
- **Code Completion:** Based on grammar rules
- **Diagnostics:** Syntax and semantic validation
- **Hover Information:** Documentation from grammar
- **Go to Definition:** For cross-references

You can customize these in:
- `src/language/isa-dsl-module.ts` - Language services
- `src/language/isa-dsl-validator.ts` - Custom validation rules
- `src/language/isa-dsl-completion.ts` - Custom completion providers

## Step 6: Build and Test

```bash
# Install dependencies
npm install

# Build the extension
npm run build

# Run tests
npm test
```

## Step 7: Test in VS Code

1. Open the extension folder in VS Code
2. Press `F5` to launch Extension Development Host
3. Create a `.isa` file
4. Test features:
   - Syntax highlighting
   - Code completion (Ctrl+Space)
   - Error diagnostics
   - Hover information

## Step 8: Package Extension

```bash
# Install vsce if not already installed
npm install -g @vscode/vsce

# Package extension
vsce package
```

## Migration from Current Extension

The current TypeScript parser implementation can be removed:
- `src/parser.ts` - Not needed (Langium generates parser)
- `src/test/parser.test.ts` - Replace with Langium grammar tests
- Keep `src/server.ts` but update to use Langium services
- Keep `src/extension.ts` but update to use Langium client

## Benefits of Langium Approach

1. **Grammar-Driven:** Single source of truth (grammar file)
2. **Automatic Features:** Completion, diagnostics, hover generated automatically
3. **Type Safety:** TypeScript types generated from grammar
4. **Maintainable:** Changes to grammar automatically update language features
5. **No Parser Reimplementation:** Grammar defines both syntax and semantics

## Resources

- [Langium Documentation](https://langium.org/docs/)
- [Langium Grammar Language](https://langium.org/docs/grammar-language/)
- [Langium VS Code Integration](https://langium.org/docs/tools/vscode-extension/)

## Next Steps

1. Scaffold the Langium extension
2. Convert the grammar from textX to Langium format
3. Test basic parsing and diagnostics
4. Add custom validation rules
5. Customize completion providers
6. Package and distribute the extension

