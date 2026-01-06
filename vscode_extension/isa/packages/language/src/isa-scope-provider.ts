import { 
    AstNodeDescription,
    DefaultScopeProvider,
    ReferenceInfo,
    Scope,
    AstUtils
} from 'langium';
import type { IsaServices } from './isa-module.js';
import {
    isInstructionFormat,
    isBundleFormat,
    type InstructionFormat,
    type BundleFormat
} from './generated/ast.js';

/**
 * Custom scope provider for ISA DSL that resolves format references.
 */
export class IsaScopeProvider extends DefaultScopeProvider {
    private readonly langiumServices: IsaServices;

    constructor(services: IsaServices) {
        super(services);
        this.langiumServices = services;
    }


    override getScope(context: ReferenceInfo): Scope {
        // Get the reference type from the context
        const referenceType = this.reflection.getReferenceType(context);
        const container = context.container;

        // Get the default scope first (includes local symbols and global scope)
        const defaultScope = super.getScope(context);

        // Handle InstructionFormat references
        // Include both InstructionFormat and BundleFormat so users can choose either type
        if (referenceType === 'InstructionFormat') {
            const instructionFormats = this.collectInstructionFormatDescriptions(container);
            const bundleFormats = this.collectBundleFormatDescriptions(container);
            // Combine both types of formats
            const allDescriptions = [...instructionFormats, ...bundleFormats];
            // Use default scope as outer scope to include local symbols and global scope
            return this.createScope(allDescriptions, defaultScope);
        }

        // Handle BundleFormat references
        if (referenceType === 'BundleFormat') {
            const descriptions = this.collectBundleFormatDescriptions(container);
            // Use default scope as outer scope to include local symbols and global scope
            return this.createScope(descriptions, defaultScope);
        }

        // Default scope provider for other references
        return defaultScope;
    }

    /**
     * Collect InstructionFormat descriptions from the document and included files.
     */
    private collectInstructionFormatDescriptions(container: any): AstNodeDescription[] {
        const document = AstUtils.getDocument(container);
        
        if (!document) {
            return [];
        }

        const descriptions: AstNodeDescription[] = [];
        const currentDocUri = document.uri.toString();
        
        // Collect from current document
        if (document.parseResult?.value) {
            const root = document.parseResult.value;
            const formats: InstructionFormat[] = [];
            for (const node of AstUtils.streamAllContents(root)) {
                if (isInstructionFormat(node)) {
                    formats.push(node);
                }
            }
            
            for (const format of formats) {
                if (format.name) {
                    descriptions.push(this.descriptions.createDescription(format, format.name, document));
                }
            }
        }
        
        // Collect from all documents in the workspace
        // Since nested elements might not be automatically indexed, we manually traverse all documents
        const langiumDocuments = this.langiumServices.shared.workspace.LangiumDocuments;
        const allDocuments = Array.from(langiumDocuments.all);
        
        for (const doc of allDocuments) {
            const docUri = doc.uri.toString();
            // Skip the current document (already processed above)
            if (docUri === currentDocUri) {
                continue;
            }
            
            // Collect formats from this document
            if (doc.parseResult?.value) {
                const root = doc.parseResult.value;
                for (const node of AstUtils.streamAllContents(root)) {
                    if (isInstructionFormat(node) && node.name) {
                        // Check if we already have this format (avoid duplicates)
                        const existing = descriptions.find(d => d.name === node.name);
                        if (!existing) {
                            const desc = this.descriptions.createDescription(node, node.name, doc);
                            descriptions.push(desc);
                        }
                    }
                }
            }
        }
        
        // Also try the index manager as a fallback (in case elements are indexed)
        const allFormatDescriptions = this.indexManager.allElements('InstructionFormat');
        for (const desc of allFormatDescriptions) {
            if (desc.documentUri.toString() !== currentDocUri) {
                // Check if we already have this format
                const existing = descriptions.find(d => d.name === desc.name);
                if (!existing) {
                    descriptions.push(desc);
                }
            }
        }
        
        return descriptions;
    }

    /**
     * Collect BundleFormat descriptions from the document and included files.
     */
    private collectBundleFormatDescriptions(container: any): AstNodeDescription[] {
        const document = AstUtils.getDocument(container);
        
        if (!document) {
            return [];
        }

        const descriptions: AstNodeDescription[] = [];
        const currentDocUri = document.uri.toString();
        
        // Collect from current document
        if (document.parseResult?.value) {
            const root = document.parseResult.value;
            const bundleFormats: BundleFormat[] = [];
            for (const node of AstUtils.streamAllContents(root)) {
                if (isBundleFormat(node)) {
                    bundleFormats.push(node);
                }
            }
            
            for (const bundleFormat of bundleFormats) {
                if (bundleFormat.name) {
                    descriptions.push(this.descriptions.createDescription(bundleFormat, bundleFormat.name, document));
                }
            }
        }
        
        // Collect from all documents in the workspace
        // Since nested elements might not be automatically indexed, we manually traverse all documents
        const langiumDocuments = this.langiumServices.shared.workspace.LangiumDocuments;
        const allDocuments = Array.from(langiumDocuments.all);
        
        for (const doc of allDocuments) {
            const docUri = doc.uri.toString();
            // Skip the current document (already processed above)
            if (docUri === currentDocUri) {
                continue;
            }
            
            // Collect bundle formats from this document
            if (doc.parseResult?.value) {
                const root = doc.parseResult.value;
                for (const node of AstUtils.streamAllContents(root)) {
                    if (isBundleFormat(node) && node.name) {
                        // Check if we already have this format (avoid duplicates)
                        const existing = descriptions.find(d => d.name === node.name);
                        if (!existing) {
                            descriptions.push(this.descriptions.createDescription(node, node.name, doc));
                        }
                    }
                }
            }
        }
        
        // Also try the index manager as a fallback (in case elements are indexed)
        const allBundleFormatDescriptions = this.indexManager.allElements('BundleFormat');
        for (const desc of allBundleFormatDescriptions) {
            if (desc.documentUri.toString() !== currentDocUri) {
                // Check if we already have this format
                const existing = descriptions.find(d => d.name === desc.name);
                if (!existing) {
                    descriptions.push(desc);
                }
            }
        }
        
        return descriptions;
    }
}


