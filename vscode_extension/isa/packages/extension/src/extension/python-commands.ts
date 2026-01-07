import * as vscode from 'vscode';
import * as path from 'node:path';
import * as fs from 'node:fs';
import * as os from 'node:os';
import { exec, spawn } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

interface PythonCommandResult {
    success: boolean;
    output: string;
    error?: string;
}

/**
 * Get platform-specific command for finding executables
 */
function getWhichCommand(): string {
    return os.platform() === 'win32' ? 'where' : 'which';
}

/**
 * Get platform-specific executable extension
 */
function getExecutableExtension(): string {
    return os.platform() === 'win32' ? '.exe' : '';
}

/**
 * Find UV executable in the system (cross-platform)
 */
async function findUV(): Promise<string | null> {
    const whichCmd = getWhichCommand();
    const ext = getExecutableExtension();
    
    try {
        // Try to find UV in PATH
        const { stdout } = await execAsync(`${whichCmd} uv${ext}`);
        const uvPath = stdout.trim().split('\n')[0].trim();
        if (uvPath && fs.existsSync(uvPath)) {
            return uvPath;
        }
    } catch {
        // Continue to try common paths
    }
    
    // Try common installation locations (platform-specific)
    const commonPaths: string[] = [];
    
    if (os.platform() === 'win32') {
        // Windows paths
        const homeDir = process.env.USERPROFILE || process.env.HOME || '';
        const localAppData = process.env.LOCALAPPDATA || '';
        const appData = process.env.APPDATA || '';
        
        if (homeDir) {
            commonPaths.push(
                path.join(homeDir, '.local', 'bin', `uv${ext}`),
                path.join(homeDir, '.cargo', 'bin', `uv${ext}`),
                path.join(homeDir, 'AppData', 'Local', 'Programs', 'uv', `uv${ext}`)
            );
        }
        if (localAppData) {
            commonPaths.push(path.join(localAppData, 'Programs', 'uv', `uv${ext}`));
        }
        if (appData) {
            commonPaths.push(path.join(appData, 'uv', `uv${ext}`));
        }
        // Common Windows installation locations
        commonPaths.push(
            path.join('C:', 'Program Files', 'uv', `uv${ext}`),
            path.join('C:', 'Program Files (x86)', 'uv', `uv${ext}`)
        );
    } else {
        // Linux/macOS paths
        const homeDir = process.env.HOME || os.homedir();
        if (homeDir) {
            commonPaths.push(
                path.join(homeDir, '.local', 'bin', `uv${ext}`),
                path.join(homeDir, '.cargo', 'bin', `uv${ext}`)
            );
        }
        commonPaths.push(
            `/usr/local/bin/uv${ext}`,
            `/usr/bin/uv${ext}`,
            `/opt/uv/bin/uv${ext}`
        );
    }
    
    for (const uvPath of commonPaths) {
        if (fs.existsSync(uvPath)) {
            return uvPath;
        }
    }
    
    return null;
}

/**
 * Install ISA-DSL Python package using UV
 */
export async function installISADSL(context: vscode.ExtensionContext): Promise<void> {
    const outputChannel = vscode.window.createOutputChannel('ISA DSL - Installation');
    outputChannel.show();
    outputChannel.appendLine('=== Installing ISA-DSL Python Package ===');
    outputChannel.appendLine('');
    
    try {
        // Find UV
        outputChannel.appendLine('Looking for UV...');
        const uvPath = await findUV();
        
        if (!uvPath) {
            const errorMsg = 'UV not found. Please install UV first: https://github.com/astral-sh/uv';
            outputChannel.appendLine(`ERROR: ${errorMsg}`);
            vscode.window.showErrorMessage(
                errorMsg,
                'Open UV Installation Guide'
            ).then(selection => {
                if (selection === 'Open UV Installation Guide') {
                    vscode.env.openExternal(vscode.Uri.parse('https://github.com/astral-sh/uv'));
                }
            });
            return;
        }
        
        outputChannel.appendLine(`Found UV at: ${uvPath}`);
        outputChannel.appendLine('');
        
        // Get workspace folder
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            const errorMsg = 'No workspace folder found. Please open a workspace first.';
            outputChannel.appendLine(`ERROR: ${errorMsg}`);
            vscode.window.showErrorMessage(errorMsg);
            return;
        }
        
        const workspacePath = workspaceFolder.uri.fsPath;
        outputChannel.appendLine(`Workspace: ${workspacePath}`);
        outputChannel.appendLine('');
        
        // Install isa-dsl using UV
        outputChannel.appendLine('Installing isa-dsl from PyPI...');
        outputChannel.appendLine(`Running: uv tool install isa-dsl`);
        outputChannel.appendLine('');
        
        // Use shell: true on Windows, false on Unix-like systems
        const useShell = os.platform() === 'win32';
        const installProcess = spawn(uvPath, ['tool', 'install', 'isa-dsl'], {
            cwd: workspacePath,
            env: { ...process.env },
            shell: useShell
        });
        
        let stdout = '';
        let stderr = '';
        
        installProcess.stdout.on('data', (data) => {
            const text = data.toString();
            stdout += text;
            outputChannel.append(text);
        });
        
        installProcess.stderr.on('data', (data) => {
            const text = data.toString();
            stderr += text;
            outputChannel.append(text);
        });
        
        installProcess.on('close', (code) => {
            outputChannel.appendLine('');
            if (code === 0) {
                outputChannel.appendLine('=== Installation Successful ===');
                outputChannel.appendLine('');
                outputChannel.appendLine('ISA-DSL has been installed and is available in your workspace.');
                outputChannel.appendLine('You can now use the ISA-DSL commands from the command palette or context menu.');
                
                vscode.window.showInformationMessage(
                    'ISA-DSL installed successfully!',
                    'OK'
                );
            } else {
                outputChannel.appendLine(`=== Installation Failed (exit code: ${code}) ===`);
                vscode.window.showErrorMessage(
                    `Failed to install ISA-DSL. Check the output for details.`,
                    'View Output'
                ).then(selection => {
                    if (selection === 'View Output') {
                        outputChannel.show();
                    }
                });
            }
        });
        
        installProcess.on('error', (error) => {
            outputChannel.appendLine(`ERROR: ${error.message}`);
            vscode.window.showErrorMessage(`Failed to run UV: ${error.message}`);
        });
        
    } catch (error: any) {
        outputChannel.appendLine(`ERROR: ${error.message}`);
        vscode.window.showErrorMessage(`Installation error: ${error.message}`);
    }
}

/**
 * Find ISA-DSL CLI command (using UV) - cross-platform
 * Returns an object with the command and arguments separately for proper execution
 */
async function findISADSLCommand(): Promise<{ command: string; args: string[] } | null> {
    const ext = getExecutableExtension();
    
    try {
        // Try to find isa-dsl using UV
        const uvPath = await findUV();
        if (uvPath) {
            // Test if UV can run isa-dsl
            try {
                await execAsync(`"${uvPath}" tool run isa-dsl${ext} --help`);
                // Return command and args separately
                return {
                    command: uvPath,
                    args: ['tool', 'run', `isa-dsl${ext}`]
                };
            } catch {
                // UV found but isa-dsl not installed, return UV command anyway
                // User will get a helpful error message when trying to run
                return {
                    command: uvPath,
                    args: ['tool', 'run', `isa-dsl${ext}`]
                };
            }
        }
    } catch {
        // Continue to try direct command
    }
    
    // Try direct command (if in PATH)
    try {
        const whichCmd = getWhichCommand();
        const { stdout } = await execAsync(`${whichCmd} isa-dsl${ext}`);
        const isaDslPath = stdout.trim().split('\n')[0].trim();
        if (isaDslPath && fs.existsSync(isaDslPath)) {
            return {
                command: isaDslPath,
                args: []
            };
        }
        // If not found via which, try just the command name (might be in PATH)
        return {
            command: `isa-dsl${ext}`,
            args: []
        };
    } catch {
        return null;
    }
}

/**
 * Run ISA-DSL CLI command
 */
async function runISADSLCommand(
    commandInfo: { command: string; args: string[] },
    additionalArgs: string[],
    cwd: string,
    outputChannel: vscode.OutputChannel
): Promise<PythonCommandResult> {
    return new Promise((resolve) => {
        const allArgs = [...commandInfo.args, ...additionalArgs];
        outputChannel.appendLine(`Running: ${commandInfo.command} ${allArgs.join(' ')}`);
        outputChannel.appendLine(`Working directory: ${cwd}`);
        outputChannel.appendLine('');
        
        // When using UV with 'tool run', we need shell mode to properly resolve
        // the tool from UV's tool directory. Also use shell mode on Windows.
        // For direct commands (isa-dsl in PATH), we can use shell: false on Linux/macOS
        const isUVTool = commandInfo.args.length > 0 && commandInfo.args[0] === 'tool';
        const useShell = isUVTool || os.platform() === 'win32';
        
        // If using shell mode, construct the full command as a string
        // Otherwise, pass command and args separately for direct execution
        let childProcess;
        if (useShell) {
            // For shell mode, construct the full command string
            // Escape the command path if it contains spaces
            const escapedCommand = commandInfo.command.includes(' ') 
                ? `"${commandInfo.command}"` 
                : commandInfo.command;
            
            const escapedArgs = allArgs.map(arg => {
                // Quote arguments that contain spaces or special characters
                if (arg.includes(' ') || arg.includes('"') || arg.includes("'")) {
                    return `"${arg.replace(/"/g, '\\"')}"`;
                }
                return arg;
            });
            
            const fullCommand = `${escapedCommand} ${escapedArgs.join(' ')}`;
            childProcess = spawn(fullCommand, [], {
                cwd,
                env: { ...process.env },
                shell: true
            });
        } else {
            // Direct execution without shell
            childProcess = spawn(commandInfo.command, allArgs, {
                cwd,
                env: { ...process.env },
                shell: false
            });
        }
        
        let stdout = '';
        let stderr = '';
        
        childProcess.stdout.on('data', (data: Buffer) => {
            const text = data.toString();
            stdout += text;
            outputChannel.append(text);
        });
        
        childProcess.stderr.on('data', (data: Buffer) => {
            const text = data.toString();
            stderr += text;
            outputChannel.append(text);
        });
        
        childProcess.on('close', (code: number | null) => {
            outputChannel.appendLine('');
            if (code === 0) {
                outputChannel.appendLine('=== Command completed successfully ===');
                resolve({ success: true, output: stdout });
            } else {
                outputChannel.appendLine(`=== Command failed (exit code: ${code}) ===`);
                resolve({ success: false, output: stdout, error: stderr });
            }
        });
        
        childProcess.on('error', (error: Error) => {
            outputChannel.appendLine(`ERROR: ${error.message}`);
            resolve({ success: false, output: stdout, error: error.message });
        });
    });
}

/**
 * Run ISA-DSL generate command
 */
export async function runGenerateCommand(uri?: vscode.Uri): Promise<void> {
    const outputChannel = vscode.window.createOutputChannel('ISA DSL - Generate');
    outputChannel.show();
    outputChannel.appendLine('=== ISA-DSL Generate Command ===');
    outputChannel.appendLine('');
    
    try {
        // Get the ISA file
        let isaFile: string;
        
        if (uri) {
            isaFile = uri.fsPath;
        } else {
            const activeEditor = vscode.window.activeTextEditor;
            if (!activeEditor || activeEditor.document.languageId !== 'isa-dsl') {
                vscode.window.showErrorMessage('Please open an ISA DSL file first or right-click on an .isa file.');
                return;
            }
            isaFile = activeEditor.document.uri.fsPath;
        }
        
        if (!fs.existsSync(isaFile)) {
            vscode.window.showErrorMessage(`File not found: ${isaFile}`);
            return;
        }
        
        outputChannel.appendLine(`ISA File: ${isaFile}`);
        outputChannel.appendLine('');
        
        // Find ISA-DSL command
        const isaDslCommand = await findISADSLCommand();
        if (!isaDslCommand) {
            const errorMsg = 'ISA-DSL not found. Please install it first using "ISA-DSL: Install Python Package" command.';
            outputChannel.appendLine(`ERROR: ${errorMsg}`);
            vscode.window.showErrorMessage(errorMsg, 'Install Now').then(selection => {
                if (selection === 'Install Now') {
                    vscode.commands.executeCommand('isa-dsl.install');
                }
            });
            return;
        }
        
        // Ask for output directory (use platform-appropriate path separator)
        const defaultOutputDir = path.join(path.dirname(isaFile), 'output');
        const outputDir = await vscode.window.showInputBox({
            prompt: 'Output directory',
            value: defaultOutputDir,
            placeHolder: 'Enter output directory path'
        });
        
        if (!outputDir) {
            return; // User cancelled
        }
        
        // Ask which tools to generate
        const generateOptions = await vscode.window.showQuickPick(
            [
                { label: 'All', value: 'all' },
                { label: 'Simulator only', value: 'simulator' },
                { label: 'Assembler only', value: 'assembler' },
                { label: 'Disassembler only', value: 'disassembler' },
                { label: 'Documentation only', value: 'docs' },
                { label: 'Custom selection', value: 'custom' }
            ],
            { placeHolder: 'Select what to generate' }
        );
        
        if (!generateOptions) {
            return;
        }
        
        const args: string[] = ['generate', isaFile, '--output', outputDir];
        
        if (generateOptions.value === 'simulator') {
            args.push('--simulator', '--no-assembler', '--no-disassembler', '--no-docs');
        } else if (generateOptions.value === 'assembler') {
            args.push('--no-simulator', '--assembler', '--no-disassembler', '--no-docs');
        } else if (generateOptions.value === 'disassembler') {
            args.push('--no-simulator', '--no-assembler', '--disassembler', '--no-docs');
        } else if (generateOptions.value === 'docs') {
            args.push('--no-simulator', '--no-assembler', '--no-disassembler', '--docs');
        } else if (generateOptions.value === 'custom') {
            // For custom, we'll use defaults (all) - user can modify if needed
        }
        
        const cwd = path.dirname(isaFile);
        const result = await runISADSLCommand(isaDslCommand, args, cwd, outputChannel);
        
        if (result.success) {
            // Normalize the output directory path for display
            const normalizedOutputDir = path.normalize(outputDir);
            vscode.window.showInformationMessage(
                `Generation complete! Output: ${normalizedOutputDir}`,
                'Open Folder'
            ).then(selection => {
                if (selection === 'Open Folder') {
                    vscode.commands.executeCommand('revealFileInOS', vscode.Uri.file(normalizedOutputDir));
                }
            });
        } else {
            vscode.window.showErrorMessage(
                'Generation failed. Check the output for details.',
                'View Output'
            ).then(selection => {
                if (selection === 'View Output') {
                    outputChannel.show();
                }
            });
        }
    } catch (error: any) {
        outputChannel.appendLine(`ERROR: ${error.message}`);
        vscode.window.showErrorMessage(`Error: ${error.message}`);
    }
}

/**
 * Run ISA-DSL validate command
 */
export async function runValidateCommand(uri?: vscode.Uri): Promise<void> {
    const outputChannel = vscode.window.createOutputChannel('ISA DSL - Validate');
    outputChannel.show();
    outputChannel.appendLine('=== ISA-DSL Validate Command ===');
    outputChannel.appendLine('');
    
    try {
        // Get the ISA file
        let isaFile: string;
        
        if (uri) {
            isaFile = uri.fsPath;
        } else {
            const activeEditor = vscode.window.activeTextEditor;
            if (!activeEditor || activeEditor.document.languageId !== 'isa-dsl') {
                vscode.window.showErrorMessage('Please open an ISA DSL file first or right-click on an .isa file.');
                return;
            }
            isaFile = activeEditor.document.uri.fsPath;
        }
        
        if (!fs.existsSync(isaFile)) {
            vscode.window.showErrorMessage(`File not found: ${isaFile}`);
            return;
        }
        
        outputChannel.appendLine(`ISA File: ${isaFile}`);
        outputChannel.appendLine('');
        
        // Find ISA-DSL command
        const isaDslCommand = await findISADSLCommand();
        if (!isaDslCommand) {
            const errorMsg = 'ISA-DSL not found. Please install it first using "ISA-DSL: Install Python Package" command.';
            outputChannel.appendLine(`ERROR: ${errorMsg}`);
            vscode.window.showErrorMessage(errorMsg, 'Install Now').then(selection => {
                if (selection === 'Install Now') {
                    vscode.commands.executeCommand('isa-dsl.install');
                }
            });
            return;
        }
        
        const cwd = path.dirname(isaFile);
        const result = await runISADSLCommand(isaDslCommand, ['validate', isaFile], cwd, outputChannel);
        
        if (result.success) {
            vscode.window.showInformationMessage('Validation passed! No errors found.');
        } else {
            vscode.window.showErrorMessage(
                'Validation failed. Check the output for details.',
                'View Output'
            ).then(selection => {
                if (selection === 'View Output') {
                    outputChannel.show();
                }
            });
        }
    } catch (error: any) {
        outputChannel.appendLine(`ERROR: ${error.message}`);
        vscode.window.showErrorMessage(`Error: ${error.message}`);
    }
}

/**
 * Run ISA-DSL info command
 */
export async function runInfoCommand(uri?: vscode.Uri): Promise<void> {
    const outputChannel = vscode.window.createOutputChannel('ISA DSL - Info');
    outputChannel.show();
    outputChannel.appendLine('=== ISA-DSL Info Command ===');
    outputChannel.appendLine('');
    
    try {
        // Get the ISA file
        let isaFile: string;
        
        if (uri) {
            isaFile = uri.fsPath;
        } else {
            const activeEditor = vscode.window.activeTextEditor;
            if (!activeEditor || activeEditor.document.languageId !== 'isa-dsl') {
                vscode.window.showErrorMessage('Please open an ISA DSL file first or right-click on an .isa file.');
                return;
            }
            isaFile = activeEditor.document.uri.fsPath;
        }
        
        if (!fs.existsSync(isaFile)) {
            vscode.window.showErrorMessage(`File not found: ${isaFile}`);
            return;
        }
        
        outputChannel.appendLine(`ISA File: ${isaFile}`);
        outputChannel.appendLine('');
        
        // Find ISA-DSL command
        const isaDslCommand = await findISADSLCommand();
        if (!isaDslCommand) {
            const errorMsg = 'ISA-DSL not found. Please install it first using "ISA-DSL: Install Python Package" command.';
            outputChannel.appendLine(`ERROR: ${errorMsg}`);
            vscode.window.showErrorMessage(errorMsg, 'Install Now').then(selection => {
                if (selection === 'Install Now') {
                    vscode.commands.executeCommand('isa-dsl.install');
                }
            });
            return;
        }
        
        const cwd = path.dirname(isaFile);
        await runISADSLCommand(isaDslCommand, ['info', isaFile], cwd, outputChannel);
    } catch (error: any) {
        outputChannel.appendLine(`ERROR: ${error.message}`);
        vscode.window.showErrorMessage(`Error: ${error.message}`);
    }
}

