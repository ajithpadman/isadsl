import { 
    CompletionItem,
    CompletionList,
    CompletionParams
} from 'vscode-languageserver';
import type { IsaServices } from './isa-module.js';
import {
    isISASpecFull,
    isISASpecPartial,
    isFormatBlock,
    isRegisterBlock,
    isInstructionBlock,
    isBundleFormat,
    isInstructionFormat,
    isRegister,
    isInstruction,
    type ISASpecFull,
    type ISASpecPartial,
    type FormatBlock,
    type RegisterBlock,
    type InstructionBlock,
    type BundleFormat,
    type InstructionFormat,
    type Register,
    type Instruction
} from './generated/ast.js';
import { DefaultCompletionProvider } from 'langium/lsp';
import { CstUtils, AstUtils } from 'langium';

/**
 * Context hierarchy for completion - from most specific to least specific
 */
type CompletionContext = 
    | { type: 'bundle-format', node: BundleFormat }
    | { type: 'instruction-format', node: InstructionFormat }
    | { type: 'register', node: Register }
    | { type: 'instruction', node: Instruction }
    | { type: 'format-block', node: FormatBlock }
    | { type: 'register-block', node: RegisterBlock }
    | { type: 'instruction-block', node: InstructionBlock }
    | { type: 'architecture', node: ISASpecFull }
    | { type: 'partial-spec', node: ISASpecPartial }
    | { type: 'root' };

/**
 * Custom completion provider for ISA DSL with hierarchical context-aware suggestions.
 */
export class IsaCompletionProvider extends DefaultCompletionProvider {
    private readonly langiumServices: IsaServices;

    constructor(services: IsaServices) {
        super(services);
        this.langiumServices = services;
    }


    override async getCompletion(document: any, params: CompletionParams): Promise<CompletionList | undefined> {
        // Get default completion first
        const items = await super.getCompletion(document, params);
        
        // Get the document
        const doc = document;
        if (!doc) {
            return items;
        }

        // Find the context hierarchy at the cursor position
        const context = this.findContextHierarchy(doc, params.position);
        
        // Get completions based on the most specific context found
        const contextCompletions = this.getCompletionsForContext(context, doc, params, items);
        
        // Enhance completions with elements from all documents in the workspace
        // This is critical for including elements from #include'd files
        if (contextCompletions) {
            const enhancedCompletions = this.enhanceWithWorkspaceElements(contextCompletions, doc, params, context);
            return enhancedCompletions;
        }
        
        if (items) {
            const enhancedCompletions = this.enhanceWithWorkspaceElements(items, doc, params, context);
            return enhancedCompletions;
        }
        
        return items;
    }

    /**
     * Enhance completion list with elements from all documents in the workspace.
     */
    private enhanceWithWorkspaceElements(
        items: CompletionList,
        doc: any,
        params: CompletionParams,
        context: CompletionContext
    ): CompletionList {
        if (!items || !items.items) {
            return items;
        }

        // Access services to get documents and index manager
        const langiumDocuments = this.langiumServices.shared.workspace.LangiumDocuments;
        const indexManager = (this as any).indexManager;

        const existingNames = new Set(items.items.map((item: CompletionItem) => item.label as string));
        const offset = doc.textDocument.offsetAt(params.position);
        const text = doc.textDocument.getText();
        const beforeCursor = text.substring(Math.max(0, offset - 100), offset);
        
        // Check if we're completing a format reference
        const isFormatReference = beforeCursor.includes('format:') || beforeCursor.match(/format\s*:\s*$/);
        const isBundleFormatReference = beforeCursor.includes('bundle_format:') || beforeCursor.match(/bundle_format\s*:\s*$/);
        
        // Add formats from all documents in the workspace
        if (isFormatReference || isBundleFormatReference || context.type === 'instruction') {
            // Manually traverse all documents to find formats (like scope provider does)
            // This ensures we get formats from included files
            const allDocuments = Array.from(langiumDocuments.all);
            
            for (const document of allDocuments) {
                const docUri = document.uri.toString();
                if (document.parseResult?.value) {
                    const root = document.parseResult.value;
                    
                    for (const node of AstUtils.streamAllContents(root)) {
                        if (isInstructionFormat(node) && node.name && !existingNames.has(node.name)) {
                            items.items.push({
                                label: node.name,
                                kind: 14, // Class/Type
                                detail: 'Instruction Format',
                                documentation: `Instruction format: ${node.name} (from ${docUri})`
                            });
                            existingNames.add(node.name);
                        }
                        if (isBundleFormat(node) && node.name && !existingNames.has(node.name)) {
                            items.items.push({
                                label: node.name,
                                kind: 14, // Class/Type
                                detail: 'Bundle Format',
                                documentation: `Bundle format: ${node.name} (from ${docUri})`
                            });
                            existingNames.add(node.name);
                        }
                    }
                }
            }
            
            // Also try index manager as fallback
            if (indexManager) {
                const allInstructionFormats = indexManager.allElements('InstructionFormat');
                for (const desc of allInstructionFormats) {
                    if (!existingNames.has(desc.name)) {
                        items.items.push({
                            label: desc.name,
                            kind: 14, // Class/Type
                            detail: 'Instruction Format',
                            documentation: `Instruction format: ${desc.name}`
                        });
                        existingNames.add(desc.name);
                    }
                }
                
                const allBundleFormats = indexManager.allElements('BundleFormat');
                for (const desc of allBundleFormats) {
                    if (!existingNames.has(desc.name)) {
                        items.items.push({
                            label: desc.name,
                            kind: 14, // Class/Type
                            detail: 'Bundle Format',
                            documentation: `Bundle format: ${desc.name}`
                        });
                        existingNames.add(desc.name);
                    }
                }
            }
        }
        
        // Add registers from all documents when in register block or instruction context
        if (context.type === 'register-block' || context.type === 'instruction') {
            // Manually traverse all documents
            const allDocuments = Array.from(langiumDocuments.all);
            for (const document of allDocuments) {
                if (document.parseResult?.value) {
                    const root = document.parseResult.value;
                    
                    for (const node of AstUtils.streamAllContents(root)) {
                        if (isRegister(node) && node.name && !existingNames.has(node.name)) {
                            items.items.push({
                                label: node.name,
                                kind: 14, // Class/Type
                                detail: 'Register',
                                documentation: `Register: ${node.name}`
                            });
                            existingNames.add(node.name);
                        }
                    }
                }
            }
            
            // Also try index manager as fallback
            if (indexManager) {
                const allRegisters = indexManager.allElements('Register');
                for (const desc of allRegisters) {
                    if (!existingNames.has(desc.name)) {
                        items.items.push({
                            label: desc.name,
                            kind: 14, // Class/Type
                            detail: 'Register',
                            documentation: `Register: ${desc.name}`
                        });
                        existingNames.add(desc.name);
                    }
                }
            }
        }
        
        // Add instructions from all documents when in instruction block context
        if (context.type === 'instruction-block') {
            // Manually traverse all documents
            const allDocuments = Array.from(langiumDocuments.all);
            for (const document of allDocuments) {
                if (document.parseResult?.value) {
                    const root = document.parseResult.value;
                    
                    for (const node of AstUtils.streamAllContents(root)) {
                        if (isInstruction(node) && node.mnemonic && !existingNames.has(node.mnemonic)) {
                            items.items.push({
                                label: node.mnemonic,
                                kind: 14, // Class/Type
                                detail: 'Instruction',
                                documentation: `Instruction: ${node.mnemonic}`
                            });
                            existingNames.add(node.mnemonic);
                        }
                    }
                }
            }
            
            // Also try index manager as fallback
            if (indexManager) {
                const allInstructions = indexManager.allElements('Instruction');
                for (const desc of allInstructions) {
                    if (!existingNames.has(desc.name)) {
                        items.items.push({
                            label: desc.name,
                            kind: 14, // Class/Type
                            detail: 'Instruction',
                            documentation: `Instruction: ${desc.name}`
                        });
                        existingNames.add(desc.name);
                    }
                }
            }
        }
        
        return items;
    }

    /**
     * Find the context hierarchy at the given position, respecting brace boundaries.
     */
    private findContextHierarchy(doc: any, position: any): CompletionContext {
        if (!doc.parseResult || !doc.parseResult.value) {
            return { type: 'root' };
        }

        const offset = doc.textDocument.offsetAt(position);
        const cursorLine = position.line;
        
        // Find the leaf CST node at the cursor position
        const leafNode = CstUtils.findLeafNodeAtOffset(doc.parseResult.value.$cstNode, offset);
        if (!leafNode || !leafNode.astNode) {
            // Try to infer from text if AST is incomplete
            return this.inferContextFromText(doc, position);
        }

        // Walk up the AST hierarchy to find the most specific context
        // while respecting brace boundaries
        let current: any = leafNode.astNode;
        const text = doc.textDocument.getText();
        
        // Track the most specific context found
        let context: CompletionContext | null = null;

        while (current) {
            // Check if this node is within brace boundaries
            if (this.isWithinBraceBoundaries(current, text, cursorLine)) {
                // Check for most specific contexts first
                if (isBundleFormat(current) && !context) {
                    context = { type: 'bundle-format', node: current };
                } else if (isInstructionFormat(current) && !context) {
                    context = { type: 'instruction-format', node: current };
                } else if (isRegister(current) && !context) {
                    context = { type: 'register', node: current };
                } else if (isInstruction(current) && !context) {
                    context = { type: 'instruction', node: current };
                } else if (isFormatBlock(current) && !context) {
                    context = { type: 'format-block', node: current };
                } else if (isRegisterBlock(current) && !context) {
                    context = { type: 'register-block', node: current };
                } else if (isInstructionBlock(current) && !context) {
                    context = { type: 'instruction-block', node: current };
                } else if (isISASpecFull(current) && !context) {
                    context = { type: 'architecture', node: current };
                } else if (isISASpecPartial(current) && !context) {
                    context = { type: 'partial-spec', node: current };
                }
            }
            
            // Move to parent
            current = current.$container;
            
            // Stop if we've gone beyond brace boundaries
            if (current && !this.isWithinBraceBoundaries(current, text, cursorLine)) {
                break;
            }
        }

        return context || { type: 'root' };
    }

    /**
     * Check if a node is within brace boundaries at the cursor line.
     * This ensures we don't use a context that's outside the current block.
     */
    private isWithinBraceBoundaries(node: any, text: string, cursorLine: number): boolean {
        if (!node.$cstNode) {
            return true; // If no CST node, assume it's valid
        }

        const nodeStart = node.$cstNode.range?.start;
        const nodeEnd = node.$cstNode.range?.end;
        
        if (!nodeStart || !nodeEnd) {
            return true;
        }

        // Check if cursor is within the node's line range
        // Allow some flexibility for incomplete parsing
        const nodeStartLine = nodeStart.line;
        const nodeEndLine = nodeEnd.line;
        
        // Cursor should be within or just after the node
        // We allow being on the same line as the opening brace
        return cursorLine >= nodeStartLine && cursorLine <= nodeEndLine + 1;
    }

    /**
     * Infer context from text when AST parsing fails.
     */
    private inferContextFromText(doc: any, position: any): CompletionContext {
        const offset = doc.textDocument.offsetAt(position);
        const text = doc.textDocument.getText();
        const beforeCursor = text.substring(Math.max(0, offset - 500), offset);
        const lines = beforeCursor.split('\n');
        
        // Track brace depth and find the most recent context
        let braceDepth = 0;
        let inBundleFormat = false;
        let inInstructionFormat = false;
        let inRegister = false;
        let inInstruction = false;
        let inFormatBlock = false;
        let inRegisterBlock = false;
        let inInstructionBlock = false;
        let inArchitecture = false;
        
            // Parse backwards from cursor
            for (let i = lines.length - 1; i >= 0; i--) {
                const line = lines[i].trim();
                
                // Count braces
            for (const char of line) {
                if (char === '{') braceDepth++;
                if (char === '}') braceDepth--;
            }
            
            // Check for contexts (most specific first)
            if (line.includes('bundle format') && !inBundleFormat) {
                inBundleFormat = true;
                break; // Found most specific context
            }
            if (line.match(/^\s*format\s+\w+\s+\d+\s*\{/) && !inInstructionFormat) {
                inInstructionFormat = true;
                break;
            }
            if (line.match(/^\s*(gpr|sfr|vec)\s+\w+/) && !inRegister) {
                inRegister = true;
                break;
            }
            if (line.match(/^\s*instruction\s+\w+\s*\{/) && !inInstruction) {
                inInstruction = true;
                break;
            }
            if (line.includes('formats {') && !inFormatBlock) {
                inFormatBlock = true;
                break;
            }
            if (line.includes('registers {') && !inRegisterBlock) {
                inRegisterBlock = true;
                break;
            }
            if (line.includes('instructions {') && !inInstructionBlock) {
                inInstructionBlock = true;
                break;
            }
            if (line.match(/^\s*architecture\s+\w+\s*\{/) && !inArchitecture) {
                inArchitecture = true;
                break;
            }
            
            // Stop if we've left the current block
            if (braceDepth <= 0 && line.includes('}')) {
                break;
            }
        }
        
        // Return most specific context found
        if (inBundleFormat) return { type: 'bundle-format', node: {} as BundleFormat };
        if (inInstructionFormat) return { type: 'instruction-format', node: {} as InstructionFormat };
        if (inRegister) return { type: 'register', node: {} as Register };
        if (inInstruction) return { type: 'instruction', node: {} as Instruction };
        if (inFormatBlock) return { type: 'format-block', node: {} as FormatBlock };
        if (inRegisterBlock) return { type: 'register-block', node: {} as RegisterBlock };
        if (inInstructionBlock) return { type: 'instruction-block', node: {} as InstructionBlock };
        if (inArchitecture) return { type: 'architecture', node: {} as ISASpecFull };
        
        return { type: 'root' };
    }

    /**
     * Get completions based on the context hierarchy.
     */
    private getCompletionsForContext(
        context: CompletionContext,
        doc: any,
        params: any,
        defaultItems: CompletionList | undefined
    ): CompletionList | undefined {
        const items: CompletionItem[] = [];
        
        switch (context.type) {
            case 'bundle-format':
                return this.getBundleFormatCompletions(context.node, doc, params, defaultItems);
                
            case 'instruction-format':
                return this.getInstructionFormatCompletions(context.node, doc, params, defaultItems);
                
            case 'register':
                // Inside a register definition - suggest register fields
                items.push({
                    label: 'field',
                    kind: 14,
                    detail: 'Register field',
                    insertText: '${1:field_name}: [${2:lsb}:${3:msb}]',
                    insertTextFormat: 2,
                    documentation: 'Define a register field'
                });
                break;
                
            case 'instruction':
                // Inside an instruction definition - suggest instruction properties
                items.push(
                    {
                        label: 'format',
                        kind: 14,
                        detail: 'Instruction format',
                        insertText: 'format: ${1:format_name}',
                        insertTextFormat: 2,
                        documentation: 'Specify the instruction format'
                    },
                    {
                        label: 'encoding',
                        kind: 14,
                        detail: 'Encoding specification',
                        insertText: 'encoding: {\n\t${1:field} = ${2:value}\n}',
                        insertTextFormat: 2,
                        documentation: 'Define instruction encoding'
                    },
                    {
                        label: 'operands',
                        kind: 14,
                        detail: 'Operands list',
                        insertText: 'operands: ${1:operand1}, ${2:operand2}',
                        insertTextFormat: 2,
                        documentation: 'Specify instruction operands'
                    },
                    {
                        label: 'assembly_syntax',
                        kind: 14,
                        detail: 'Assembly syntax',
                        insertText: 'assembly_syntax: "${1:syntax}"',
                        insertTextFormat: 2,
                        documentation: 'Define assembly syntax'
                    },
                    {
                        label: 'behavior',
                        kind: 14,
                        detail: 'RTL behavior',
                        insertText: 'behavior: {\n\t$0\n}',
                        insertTextFormat: 2,
                        documentation: 'Define RTL behavior'
                    }
                );
                break;
                
            case 'format-block':
                // Inside format block - suggest format definitions
                items.push(
                    {
                        label: 'format',
                        kind: 14,
                        detail: 'Instruction format',
                        insertText: 'format ${1:name} ${2:width} {\n\t$0\n}',
                        insertTextFormat: 2,
                        documentation: 'Define an instruction format'
                    },
                    {
                        label: 'bundle format',
                        kind: 14,
                        detail: 'Bundle format',
                        insertText: 'bundle format ${1:name} ${2:width} {\n\t$0\n}',
                        insertTextFormat: 2,
                        documentation: 'Define a bundle format'
                    }
                );
                break;
                
            case 'register-block':
                // Inside register block - suggest register types
                items.push(
                    {
                        label: 'gpr',
                        kind: 14,
                        detail: 'General purpose register',
                        insertText: 'gpr ${1:name} ${2:width}',
                        insertTextFormat: 2,
                        documentation: 'Define a general purpose register'
                    },
                    {
                        label: 'sfr',
                        kind: 14,
                        detail: 'Special function register',
                        insertText: 'sfr ${1:name} ${2:width}',
                        insertTextFormat: 2,
                        documentation: 'Define a special function register'
                    },
                    {
                        label: 'vec',
                        kind: 14,
                        detail: 'Vector register',
                        insertText: 'vec ${1:name} ${2:width}',
                        insertTextFormat: 2,
                        documentation: 'Define a vector register'
                    }
                );
                break;
                
            case 'instruction-block':
                // Inside instruction block - suggest instruction definitions
                items.push({
                    label: 'instruction',
                    kind: 14,
                    detail: 'Instruction definition',
                    insertText: 'instruction ${1:mnemonic} {\n\t$0\n}',
                    insertTextFormat: 2,
                    documentation: 'Define an instruction'
                });
                break;
                
            case 'architecture':
                // Inside architecture block - suggest block keywords
                const archNode = context.node;
                if (!archNode.registers) {
                    items.push({
                        label: 'registers',
                        kind: 14,
                        detail: 'Register block',
                        insertText: 'registers {\n\t$0\n}',
                        insertTextFormat: 2,
                        documentation: 'Define registers'
                    });
                }
                if (!archNode.formats) {
                    items.push({
                        label: 'formats',
                        kind: 14,
                        detail: 'Format block',
                        insertText: 'formats {\n\t$0\n}',
                        insertTextFormat: 2,
                        documentation: 'Define instruction formats'
                    });
                }
                if (!archNode.instructions) {
                    items.push({
                        label: 'instructions',
                        kind: 14,
                        detail: 'Instruction block',
                        insertText: 'instructions {\n\t$0\n}',
                        insertTextFormat: 2,
                        documentation: 'Define instructions'
                    });
                }
                // Also allow properties
                items.push({
                    label: 'property',
                    kind: 14,
                    detail: 'Property definition',
                    insertText: '${1:property_name}: ${2:value}',
                    insertTextFormat: 2,
                    documentation: 'Define a property (key: value)'
                });
                break;
                
            case 'partial-spec':
                // Inside partial spec - suggest block keywords
                items.push(
                    {
                        label: 'registers',
                        kind: 14,
                        detail: 'Register block',
                        insertText: 'registers {\n\t$0\n}',
                        insertTextFormat: 2,
                        documentation: 'Define registers'
                    },
                    {
                        label: 'formats',
                        kind: 14,
                        detail: 'Format block',
                        insertText: 'formats {\n\t$0\n}',
                        insertTextFormat: 2,
                        documentation: 'Define instruction formats'
                    },
                    {
                        label: 'instructions',
                        kind: 14,
                        detail: 'Instruction block',
                        insertText: 'instructions {\n\t$0\n}',
                        insertTextFormat: 2,
                        documentation: 'Define instructions'
                    }
                );
                break;
                
            case 'root':
            default:
                // At root level - suggest architecture or block keywords
                items.push(
                    {
                        label: 'architecture',
                        kind: 14,
                        detail: 'Define a new architecture',
                        insertText: 'architecture ${1:name} {\n\t$0\n}',
                        insertTextFormat: 2,
                        documentation: 'Start an architecture definition block'
                    },
                    {
                        label: 'registers',
                        kind: 14,
                        detail: 'Register block',
                        insertText: 'registers {\n\t$0\n}',
                        insertTextFormat: 2,
                        documentation: 'Define registers'
                    },
                    {
                        label: 'formats',
                        kind: 14,
                        detail: 'Format block',
                        insertText: 'formats {\n\t$0\n}',
                        insertTextFormat: 2,
                        documentation: 'Define instruction formats'
                    },
                    {
                        label: 'instructions',
                        kind: 14,
                        detail: 'Instruction block',
                        insertText: 'instructions {\n\t$0\n}',
                        insertTextFormat: 2,
                        documentation: 'Define instructions'
                    }
                );
                break;
        }
        
        // Filter default items based on context if available
        if (defaultItems && defaultItems.items) {
            const filtered = defaultItems.items.filter((item: CompletionItem) => {
                return this.isValidForContext(item, context);
            });
            items.push(...filtered);
        }
        
        return {
            isIncomplete: false,
            items: items.length > 0 ? items : (defaultItems?.items || [])
        };
    }

    /**
     * Get completions for bundle format context.
     */
    private getBundleFormatCompletions(
        bundleFormat: BundleFormat,
        doc: any,
        params: any,
        defaultItems: CompletionList | undefined
    ): CompletionList {
        const items: CompletionItem[] = [];
        const offset = doc.textDocument.offsetAt(params.position);
        const text = doc.textDocument.getText();
        const beforeCursor = text.substring(Math.max(0, offset - 500), offset);
        
        // Check if instruction_start is already present
        const hasInstructionStart = beforeCursor.includes('instruction_start');
        if (!hasInstructionStart) {
            items.push({
                label: 'instruction_start',
                kind: 14,
                detail: 'Instruction start position',
                insertText: 'instruction_start: ${1:0}',
                insertTextFormat: 2,
                documentation: 'Specify the instruction start position in the bundle'
            });
        }
        
        // Check if identification_fields is already present
        const hasIdentificationFields = beforeCursor.includes('identification_fields');
        if (!hasIdentificationFields) {
            items.push({
                label: 'identification_fields',
                kind: 14,
                detail: 'Identification fields',
                insertText: 'identification_fields: ${1:field1}, ${2:field2}',
                insertTextFormat: 2,
                documentation: 'Specify fields used for instruction identification'
            });
        }
        
        // Always suggest slot definitions (custom fields)
        items.push({
            label: 'slot',
            kind: 14,
            detail: 'Bundle slot or custom field',
            insertText: '${1:field_name}: [${2:lsb}:${3:msb}]',
            insertTextFormat: 2,
            documentation: 'Define a bundle slot or custom field'
        });
        
        // Include valid items from default completions
        if (defaultItems && defaultItems.items) {
            const validItems = defaultItems.items.filter((item: CompletionItem) => {
                const label = item.label as string;
                return label === 'instruction_start' || 
                       label === 'identification_fields' ||
                       label.includes(':') || // Allow field definitions
                       label.startsWith('instruction_start') ||
                       label.startsWith('identification_fields');
            });
            items.push(...validItems);
        }
        
        return {
            isIncomplete: false,
            items
        };
    }

    /**
     * Get completions for instruction format context.
     */
    private getInstructionFormatCompletions(
        format: InstructionFormat,
        doc: any,
        params: any,
        defaultItems: CompletionList | undefined
    ): CompletionList {
        const items: CompletionItem[] = [];
        const offset = doc.textDocument.offsetAt(params.position);
        const text = doc.textDocument.getText();
        const beforeCursor = text.substring(Math.max(0, offset - 500), offset);
        
        // Check if identification_fields is already present
        const hasIdentificationFields = beforeCursor.includes('identification_fields');
        if (!hasIdentificationFields) {
            items.push({
                label: 'identification_fields',
                kind: 14,
                detail: 'Identification fields',
                insertText: 'identification_fields: ${1:field1}, ${2:field2}',
                insertTextFormat: 2,
                documentation: 'Specify fields used for instruction identification'
            });
        }
        
        // Suggest field definitions
        items.push({
            label: 'field',
            kind: 14,
            detail: 'Format field',
            insertText: '${1:field_name}: [${2:lsb}:${3:msb}]',
            insertTextFormat: 2,
            documentation: 'Define a format field'
        });
        
        // Include valid items from default completions
        if (defaultItems && defaultItems.items) {
            const validItems = defaultItems.items.filter((item: CompletionItem) => {
                const label = item.label as string;
                return label === 'identification_fields' ||
                       label.includes(':') || // Allow field definitions
                       label.startsWith('identification_fields');
            });
            items.push(...validItems);
        }
        
        return {
            isIncomplete: false,
            items
        };
    }

    /**
     * Check if a completion item is valid for the given context.
     */
    private isValidForContext(item: CompletionItem, context: CompletionContext): boolean {
        const label = item.label as string;
        
        switch (context.type) {
            case 'bundle-format':
                return label === 'instruction_start' || 
                       label === 'identification_fields' ||
                       label.includes(':');
                       
            case 'instruction-format':
                return label === 'identification_fields' ||
                       label.includes(':');
                       
            case 'register':
                return label.includes(':');
                
            case 'instruction':
                return label === 'format' ||
                       label === 'encoding' ||
                       label === 'operands' ||
                       label === 'assembly_syntax' ||
                       label === 'behavior' ||
                       label.startsWith('format:') ||
                       label.startsWith('encoding:') ||
                       label.startsWith('operands:') ||
                       label.startsWith('assembly_syntax:') ||
                       label.startsWith('behavior:');
                       
            case 'format-block':
                return label.startsWith('format ') ||
                       label.startsWith('bundle format');
                       
            case 'register-block':
                return label === 'gpr' ||
                       label === 'sfr' ||
                       label === 'vec';
                       
            case 'instruction-block':
                return label.startsWith('instruction ');
                
            case 'architecture':
                return label === 'registers' ||
                       label === 'formats' ||
                       label === 'instructions' ||
                       label.includes(':');
                       
            case 'partial-spec':
                return label === 'registers' ||
                       label === 'formats' ||
                       label === 'instructions';
                       
            case 'root':
            default:
                return label === 'architecture' ||
                       label === 'registers' ||
                       label === 'formats' ||
                       label === 'instructions';
        }
    }

}


