/**
 * Document processor for handling #include directives.
 * 
 * This processor extracts #include directives from ISA DSL files and
 * actively loads the referenced files into the Langium workspace.
 * This ensures that formats and other elements from included files
 * are available for cross-reference resolution and completion.
 */

import { 
    LangiumDocument,
    LangiumDocuments,
    DocumentBuilder,
    URI
} from 'langium';
import type { IsaServices } from './isa-module.js';
import type { Include, ISASpec } from './generated/ast.js';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Document processor that handles #include directives by loading
 * referenced files into the workspace.
 */
export class IsaDocumentProcessor {
    private readonly documents: LangiumDocuments;
    private readonly documentBuilder: DocumentBuilder;
    private readonly processedIncludes: Set<string> = new Set();

    constructor(services: IsaServices) {
        this.documents = services.shared.workspace.LangiumDocuments;
        this.documentBuilder = services.shared.workspace.DocumentBuilder;
    }


    /**
     * Process a document and load all included files.
     * This is called after a document is parsed.
     */
    async processDocument(document: LangiumDocument): Promise<void> {
        if (!document.parseResult?.value) {
            return;
        }

        const root = document.parseResult.value as ISASpec;
        if (!root.includes) {
            return;
        }

        // Convert document URI to file system path
        // document.uri is a string URI, parse it to get the URI object
        const documentUriString = typeof document.uri === 'string' ? document.uri : document.uri.toString();
        const documentUri = URI.parse(documentUriString);
        // fsPath is a property of URI that gives the file system path as a string
        const documentPath = documentUri.fsPath as string;
        const documentDir = path.dirname(documentPath);

        // Process all includes
        for (const include of root.includes) {
            await this.processInclude(include, documentDir, documentUri.toString());
        }
    }

    /**
     * Process a single include directive.
     */
    private async processInclude(
        include: Include,
        baseDir: string,
        includingDocumentUri: string
    ): Promise<void> {
        if (!include.path) {
            return;
        }

        // Remove quotes from the path
        let includePath = include.path.replace(/^["']|["']$/g, '');
        
        // Resolve the path relative to the including file's directory
        let resolvedPath: string;
        if (path.isAbsolute(includePath)) {
            resolvedPath = includePath;
        } else {
            resolvedPath = path.resolve(baseDir, includePath);
        }

        // Normalize the path
        resolvedPath = path.normalize(resolvedPath);

        // Create URI for the included file
        const includedUri = URI.file(resolvedPath);

        // Check if we've already processed this include (avoid circular dependencies)
        const includeKey = `${includingDocumentUri} -> ${includedUri.toString()}`;
        if (this.processedIncludes.has(includeKey)) {
            return;
        }

        // Check if file exists
        if (!fs.existsSync(resolvedPath)) {
            // Validation will catch this
            return;
        }

        // Mark as processed
        this.processedIncludes.add(includeKey);

        try {
            // Read the file content
            const content = fs.readFileSync(resolvedPath, 'utf-8');

            // Get or create the document
            let includedDocument = this.documents.getDocument(includedUri);
            
            if (!includedDocument) {
                // Document doesn't exist - create it
                includedDocument = this.documents.createDocument(includedUri, content);
            } else {
                // Document already exists - check if content has changed
                const existingContent = includedDocument.textDocument.getText();
                if (existingContent !== content) {
                    // Content has changed - invalidate and recreate
                    this.documents.invalidateDocument(includedUri);
                    // Delete the old document and create a new one
                    this.documents.deleteDocument(includedUri);
                    // Create a new document with updated content
                    includedDocument = this.documents.createDocument(includedUri, content);
                }
                // If content hasn't changed, just use the existing document
            }

            // Ensure we have a valid document before proceeding
            if (!includedDocument) {
                return;
            }

            // Build the document to parse and index it
            // This will parse the document and add it to the index manager
            await this.documentBuilder.build([includedDocument], {
                eagerLinking: true,
                validation: false  // Skip validation for included files to avoid circular dependency issues
            });

            // Recursively process includes in the included file
            await this.processDocument(includedDocument);

        } catch (error) {
            // Don't throw - let validation handle errors
        }
    }

    /**
     * Clear the processed includes cache.
     * Call this when the workspace is cleared or reset.
     */
    clearCache(): void {
        this.processedIncludes.clear();
    }
}

