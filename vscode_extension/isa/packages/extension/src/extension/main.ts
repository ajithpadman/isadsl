import type { LanguageClientOptions, ServerOptions } from 'vscode-languageclient/node.js';
import * as vscode from 'vscode';
import * as path from 'node:path';
import * as fs from 'node:fs';
import { LanguageClient, TransportKind } from 'vscode-languageclient/node.js';
import { installISADSL, runGenerateCommand, runValidateCommand, runInfoCommand } from './python-commands.js';

let client: LanguageClient;
let outputChannel: vscode.OutputChannel;

// This function is called when the extension is activated.
export async function activate(context: vscode.ExtensionContext): Promise<void> {
    // Create output channel for ISA DSL language server
    // Use a clear, identifiable name that will show in the Output dropdown
    outputChannel = vscode.window.createOutputChannel('ISA DSL');
    outputChannel.appendLine('=== ISA DSL Language Server activated ===');
    outputChannel.appendLine(`Extension activated at: ${new Date().toISOString()}`);
    outputChannel.appendLine('');
    
    // Show the output channel so users can see it
    outputChannel.show();
    
    // Store output channel in context so it persists
    context.subscriptions.push(outputChannel);
    
    // Register command to show version
    const showVersionCommand = vscode.commands.registerCommand('isa-dsl.showVersion', () => {
        try {
            // Read package.json to get version info
            const packageJsonPath = path.join(context.extensionPath, 'package.json');
            const packageJsonContent = fs.readFileSync(packageJsonPath, 'utf-8');
            const packageJson = JSON.parse(packageJsonContent);
            
            const version = packageJson.version || 'unknown';
            const displayName = packageJson.displayName || 'ISA DSL Language Server';
            
            outputChannel.appendLine(`=== ${displayName} Version ===`);
            outputChannel.appendLine(`Version: ${version}`);
            outputChannel.appendLine(`Extension ID: ${packageJson.name}`);
            outputChannel.appendLine(`VS Code Engine: ${packageJson.engines?.vscode || 'unknown'}`);
            outputChannel.appendLine(`Language Server: Active`);
            outputChannel.appendLine(`Output Channel: ISA DSL`);
            outputChannel.appendLine('');
            outputChannel.show();
            
            vscode.window.showInformationMessage(
                `${displayName} v${version} is active!`,
                'View Output'
            ).then(selection => {
                if (selection === 'View Output') {
                    outputChannel.show();
                }
            });
        } catch (error) {
            outputChannel.appendLine(`Error reading version: ${error}`);
            outputChannel.show();
            vscode.window.showErrorMessage('Failed to read extension version');
        }
    });
    
    context.subscriptions.push(showVersionCommand);
    
    // Register Python package installation command
    const installCommand = vscode.commands.registerCommand('isa-dsl.install', () => {
        installISADSL(context);
    });
    context.subscriptions.push(installCommand);
    
    // Register CLI commands
    const generateCommand = vscode.commands.registerCommand('isa-dsl.generate', (uri?: vscode.Uri) => {
        runGenerateCommand(uri);
    });
    context.subscriptions.push(generateCommand);
    
    const validateCommand = vscode.commands.registerCommand('isa-dsl.validate', (uri?: vscode.Uri) => {
        runValidateCommand(uri);
    });
    context.subscriptions.push(validateCommand);
    
    const infoCommand = vscode.commands.registerCommand('isa-dsl.info', (uri?: vscode.Uri) => {
        runInfoCommand(uri);
    });
    context.subscriptions.push(infoCommand);
    
    client = await startLanguageClient(context);
    
    // Also add client to subscriptions for cleanup
    context.subscriptions.push({
        dispose: () => {
            if (client) {
                client.stop();
            }
        }
    });
}

// This function is called when the extension is deactivated.
export function deactivate(): Thenable<void> | undefined {
    if (client) {
        return client.stop();
    }
    return undefined;
}

async function startLanguageClient(context: vscode.ExtensionContext): Promise<LanguageClient> {
    const serverModule = context.asAbsolutePath(path.join('out', 'language', 'main.cjs'));
    // The debug options for the server
    // --inspect=6009: runs the server in Node's Inspector mode so VS Code can attach to the server for debugging.
    // By setting `process.env.DEBUG_BREAK` to a truthy value, the language server will wait until a debugger is attached.
    const debugOptions = { execArgv: ['--nolazy', `--inspect${process.env.DEBUG_BREAK ? '-brk' : ''}=${process.env.DEBUG_SOCKET || '6009'}`] };

    // If the extension is launched in debug mode then the debug server options are used
    // Otherwise the run options are used
    const serverOptions: ServerOptions = {
        run: { module: serverModule, transport: TransportKind.ipc },
        debug: { module: serverModule, transport: TransportKind.ipc, options: debugOptions }
    };

    // Options to control the language client
    const clientOptions: LanguageClientOptions = {
        documentSelector: [{ scheme: '*', language: 'isa-dsl' }],
        outputChannel: outputChannel  // Use our custom output channel - this routes connection.console to it
    };
    
    // Log to output channel to verify it's working
    outputChannel.appendLine('Starting language client...');
    outputChannel.appendLine(`Server module: ${serverModule}`);
    outputChannel.appendLine('');

    // Create the language client and start the client.
    const client = new LanguageClient(
        'isa',
        'ISA DSL Language Server',
        serverOptions,
        clientOptions
    );

    // Log when client starts
    outputChannel.appendLine('Language client created, starting...');
    
    // Start the client. This will also launch the server
    await client.start();
    
    outputChannel.appendLine('Language client started successfully');
    outputChannel.appendLine('All logs from the language server will appear here');
    outputChannel.appendLine('');
    
    return client;
}
