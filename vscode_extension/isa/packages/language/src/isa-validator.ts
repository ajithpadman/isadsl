import type { ValidationAcceptor, ValidationChecks } from 'langium';
import { AstUtils } from 'langium';
import type { IsaAstType } from './generated/ast.js';
import type { IsaServices } from './isa-module.js';
import { 
    type InstructionFormat, 
    type FormatField, 
    type Instruction, 
    type Register,
    type RegisterField,
    type EncodingAssignment,
    type EncodingValue,
    type BundleFormat,
    type BundleSlot,
    type ISASpecFull,
    type ISASpecPartial,
    type VirtualRegister,
    type VirtualRegisterComponent,
    type RTLFunctionCall,
    type RTLConstant
} from './generated/ast.js';

/**
 * Register custom validation checks.
 */
export function registerValidationChecks(services: IsaServices) {
    const registry = services.validation.ValidationRegistry;
    const validator = services.validation.IsaValidator;
    const checks: ValidationChecks<IsaAstType> = {
        InstructionFormat: validator.checkInstructionFormat,
        FormatField: validator.checkFormatField,
        Instruction: validator.checkInstruction,
        Register: validator.checkRegister,
        RegisterField: validator.checkRegisterField,
        EncodingAssignment: validator.checkEncodingAssignment,
        BundleFormat: validator.checkBundleFormat,
        BundleSlot: validator.checkBundleSlot,
        ISASpecFull: validator.checkISASpecFull,
        ISASpecPartial: validator.checkISASpecPartial,
        VirtualRegister: validator.checkVirtualRegister,
        RTLFunctionCall: validator.checkRTLFunctionCall
    };
    registry.register(checks, validator);
}

/**
 * Implementation of custom validations.
 */
export class IsaValidator {

    /**
     * Validate instruction format.
     */
    checkInstructionFormat(format: InstructionFormat, accept: ValidationAcceptor): void {
        // Check format width is positive
        if (format.width <= 0) {
            accept('error', `Format '${format.name}' must have a positive width`, { node: format, property: 'width' });
        }

        // Check for duplicate field names
        const fieldNames = new Set<string>();
        for (const field of format.fields) {
            if (fieldNames.has(field.name)) {
                accept('error', `Duplicate field name '${field.name}' in format '${format.name}'`, { node: field, property: 'name' });
            }
            fieldNames.add(field.name);
        }

        // Check field ranges and overlaps
        const fieldRanges: Array<{ field: FormatField; lsb: number; msb: number }> = [];
        for (const field of format.fields) {
            const lsb = field.lsb;
            const msb = field.msb;

            // Check lsb <= msb
            if (lsb > msb) {
                accept('error', `Field '${field.name}' in format '${format.name}': LSB (${lsb}) must be <= MSB (${msb})`, { node: field });
            }

            // Check field is within format width
            if (msb >= format.width) {
                accept('error', `Field '${field.name}' in format '${format.name}' exceeds format width (MSB ${msb} >= width ${format.width})`, { node: field });
            }

            // Check for overlapping fields
            for (const existing of fieldRanges) {
                if (!(msb < existing.lsb || lsb > existing.msb)) {
                    accept('error', `Field '${field.name}' overlaps with field '${existing.field.name}' in format '${format.name}'`, { node: field });
                }
            }

            fieldRanges.push({ field, lsb, msb });
            
            // Validate constant value if present
            if (field.constant_value !== undefined && field.constant_value !== null) {
                const fieldWidth = msb - lsb + 1;
                const maxValue = (1 << fieldWidth) - 1;
                
                // Extract constant value (can be hex or int from EncodingValue)
                let constantValue: number;
                const constVal = field.constant_value as EncodingValue | number | undefined;
                
                if (typeof constVal === 'object' && constVal !== null) {
                    if ('hex_value' in constVal && constVal.hex_value !== undefined && constVal.hex_value !== null) {
                        constantValue = parseInt(constVal.hex_value, 16);
                    } else if ('int_value' in constVal && constVal.int_value !== undefined && constVal.int_value !== null) {
                        constantValue = constVal.int_value;
                    } else {
                        continue; // Unknown format, skip validation
                    }
                } else if (typeof constVal === 'number') {
                    constantValue = constVal;
                } else {
                    continue; // Unknown format, skip validation
                }
                
                if (isNaN(constantValue)) {
                    accept('error', `Format '${format.name}' field '${field.name}' constant value is not a valid number`, { node: field, property: 'constant_value' });
                } else if (constantValue < 0) {
                    accept('error', `Format '${format.name}' field '${field.name}' constant value ${constantValue} must be non-negative`, { node: field, property: 'constant_value' });
                } else if (constantValue > maxValue) {
                    accept('error', `Format '${format.name}' field '${field.name}' constant value ${constantValue} exceeds field width (max: ${maxValue})`, { node: field, property: 'constant_value' });
                }
            }
        }

        // Check identification fields exist
        if (format.identification_fields) {
            const idFields = [format.identification_fields.first, ...format.identification_fields.rest];
            for (const idField of idFields) {
                if (!fieldNames.has(idField)) {
                    accept('error', `Identification field '${idField}' not found in format '${format.name}'`, { node: format.identification_fields });
                }
            }
        }
    }

    /**
     * Validate format field.
     */
    checkFormatField(field: FormatField, accept: ValidationAcceptor): void {
        if (field.lsb > field.msb) {
            accept('error', `Field '${field.name}': LSB (${field.lsb}) must be <= MSB (${field.msb})`, { node: field });
        }
        
        // Validate constant value if present
        if (field.constant_value !== undefined && field.constant_value !== null) {
            const fieldWidth = field.msb - field.lsb + 1;
            const maxValue = (1 << fieldWidth) - 1;
            
            // Extract constant value (can be hex or int from EncodingValue)
            let constantValue: number;
            const constVal = field.constant_value as EncodingValue | number | undefined;
            
            if (typeof constVal === 'object' && constVal !== null) {
                if ('hex_value' in constVal && constVal.hex_value !== undefined && constVal.hex_value !== null) {
                    constantValue = parseInt(constVal.hex_value, 16);
                } else if ('int_value' in constVal && constVal.int_value !== undefined && constVal.int_value !== null) {
                    constantValue = constVal.int_value;
                } else {
                    return; // Unknown format, skip validation
                }
            } else if (typeof constVal === 'number') {
                constantValue = constVal;
            } else {
                return; // Unknown format, skip validation
            }
            
            if (isNaN(constantValue)) {
                accept('error', `Constant value for field '${field.name}' is not a valid number`, { node: field, property: 'constant_value' });
                return;
            }
            
            if (constantValue < 0) {
                accept('error', `Constant value ${constantValue} for field '${field.name}' must be non-negative`, { node: field, property: 'constant_value' });
            } else if (constantValue > maxValue) {
                accept('error', `Constant value ${constantValue} exceeds field '${field.name}' width (max: ${maxValue})`, { node: field, property: 'constant_value' });
            }
        }
    }

    /**
     * Validate instruction.
     */
    checkInstruction(instruction: Instruction, accept: ValidationAcceptor): void {
        // Check format reference is resolved
        if (instruction.format) {
            if (instruction.format.ref === undefined) {
                accept('error', `Instruction '${instruction.mnemonic}' references unknown format`, { node: instruction, property: 'format' });
                return;
            }

            const format = instruction.format.ref;

            // Check encoding fields exist in format
            if (instruction.encoding) {
                const formatFieldNames = new Set(format.fields.map(f => f.name));
                for (const assignment of instruction.encoding.assignments) {
                    if (!formatFieldNames.has(assignment.field)) {
                        accept('error', `Encoding field '${assignment.field}' not found in format '${format.name}'`, { node: assignment, property: 'field' });
                    } else {
                        // Check if field has a constant value (cannot be overridden)
                        const field = format.fields.find(f => f.name === assignment.field);
                        if (field && field.constant_value !== undefined && field.constant_value !== null) {
                            accept('error', `Instruction '${instruction.mnemonic}' cannot override constant field '${assignment.field}' from format '${format.name}'`, { node: assignment, property: 'field' });
                            continue;
                        }
                        
                        // Check encoding value fits in field width
                        if (field) {
                            // Extract numeric value from EncodingValue (can be hex or int)
                            const encValue = assignment.value as EncodingValue | undefined;
                            if (!encValue) {
                                accept('error', `Encoding value is missing for field '${assignment.field}'`, { node: assignment, property: 'value' });
                                continue;
                            }
                            
                            let value: number;
                            if (encValue.hex_value !== undefined && encValue.hex_value !== null) {
                                value = parseInt(encValue.hex_value, 16);
                            } else if (encValue.int_value !== undefined && encValue.int_value !== null) {
                                value = encValue.int_value;
                            } else {
                                // Fallback for backward compatibility - try to parse as number
                                const rawValue = assignment.value as any;
                                if (typeof rawValue === 'number') {
                                    value = rawValue;
                                } else if (typeof rawValue === 'string') {
                                    // Try to parse as hex or decimal
                                    if (rawValue.startsWith('0x') || rawValue.startsWith('0X')) {
                                        value = parseInt(rawValue, 16);
                                    } else {
                                        value = parseInt(rawValue, 10);
                                    }
                                } else {
                                    accept('error', `Invalid encoding value for field '${assignment.field}'`, { node: assignment, property: 'value' });
                                    continue;
                                }
                            }
                            
                            // Check if value is valid number
                            if (isNaN(value)) {
                                accept('error', `Encoding value for field '${assignment.field}' is not a valid number`, { node: assignment, property: 'value' });
                                continue;
                            }
                            
                            const fieldWidth = field.msb - field.lsb + 1;
                            const maxValue = (1 << fieldWidth) - 1;
                            if (value > maxValue) {
                                accept('error', `Encoding value ${value} exceeds field '${assignment.field}' width (max: ${maxValue})`, { node: assignment, property: 'value' });
                            }
                            if (value < 0) {
                                accept('error', `Encoding value ${value} must be non-negative`, { node: assignment, property: 'value' });
                            }
                        }
                    }
                }
            }

            // Check operands match format fields
            if (instruction.operands_list) {
                const formatFieldNames = new Set(format.fields.map(f => f.name));
                const operandNames = this.getOperandNames(instruction.operands_list);
                
                for (const operandName of operandNames) {
                    if (!formatFieldNames.has(operandName)) {
                        accept('error', `Operand '${operandName}' not found in format '${format.name}'`, { node: instruction, property: 'operands_list' });
                    }
                }
            }
        }

        // Check bundle format reference
        if (instruction.bundle_format) {
            if (instruction.bundle_format.ref === undefined) {
                accept('error', `Instruction '${instruction.mnemonic}' references unknown bundle format`, { node: instruction, property: 'bundle_format' });
            }
        }

        // Check that instruction has behavior (unless it's a bundle or has external_behavior)
        const isBundle = instruction.bundle_format !== undefined && instruction.bundle_format !== null;
        const hasExternalBehavior = instruction.external_behavior === true;
        const hasBehavior = instruction.behavior !== undefined && instruction.behavior !== null;
        
        if (!isBundle && !hasExternalBehavior) {
            if (!hasBehavior) {
                accept('error', `Instruction '${instruction.mnemonic}' is missing behavior description. Add a 'behavior' block or set 'external_behavior: true' if behavior is implemented externally.`, { node: instruction, property: 'behavior' });
            } else if (instruction.behavior && (instruction.behavior.statements === undefined || instruction.behavior.statements.length === 0)) {
                accept('error', `Instruction '${instruction.mnemonic}' has an empty behavior block. Add RTL statements to describe the instruction's behavior.`, { node: instruction.behavior, property: 'statements' });
            }
        }
    }

    /**
     * Get all operand names from an operand list.
     */
    private getOperandNames(operandsList: any): string[] {
        const names: string[] = [];
        if (operandsList.first) {
            if (operandsList.first.distributed_operand) {
                names.push(operandsList.first.distributed_operand.name);
            } else if (operandsList.first.simple_operand) {
                names.push(operandsList.first.simple_operand);
            }
        }
        if (operandsList.rest) {
            names.push(...this.getOperandNames(operandsList.rest));
        }
        return names;
    }

    /**
     * Validate register.
     */
    checkRegister(register: Register, accept: ValidationAcceptor): void {
        // Check register width is positive
        if (register.width <= 0) {
            accept('error', `Register '${register.name}' must have a positive width`, { node: register, property: 'width' });
        }

        // Check count is positive if specified
        if (register.count !== undefined && register.count <= 0) {
            accept('error', `Register '${register.name}' count must be positive`, { node: register, property: 'count' });
        }

        // Check for duplicate field names
        const fieldNames = new Set<string>();
        for (const field of register.fields) {
            if (fieldNames.has(field.name)) {
                accept('error', `Duplicate field name '${field.name}' in register '${register.name}'`, { node: field, property: 'name' });
            }
            fieldNames.add(field.name);
        }

        // Check field ranges
        for (const field of register.fields) {
            if (field.lsb > field.msb) {
                accept('error', `Field '${field.name}' in register '${register.name}': LSB (${field.lsb}) must be <= MSB (${field.msb})`, { node: field });
            }
            if (field.msb >= register.width) {
                accept('error', `Field '${field.name}' in register '${register.name}' exceeds register width (MSB ${field.msb} >= width ${register.width})`, { node: field });
            }
        }

        // Check vector properties
        if (register.vector_props) {
            if (register.vector_props.element_width <= 0) {
                accept('error', `Vector register '${register.name}' element width must be positive`, { node: register.vector_props, property: 'element_width' });
            }
            if (register.vector_props.lanes <= 0) {
                accept('error', `Vector register '${register.name}' lanes must be positive`, { node: register.vector_props, property: 'lanes' });
            }
        }
    }

    /**
     * Validate register field.
     */
    checkRegisterField(field: RegisterField, accept: ValidationAcceptor): void {
        if (field.lsb > field.msb) {
            accept('error', `Register field '${field.name}': LSB (${field.lsb}) must be <= MSB (${field.msb})`, { node: field });
        }
    }

    /**
     * Validate virtual register.
     */
    checkVirtualRegister(vreg: VirtualRegister, accept: ValidationAcceptor): void {
        // Check width is positive
        if (vreg.width <= 0) {
            accept('error', `Virtual register '${vreg.name}' must have a positive width`, { node: vreg, property: 'width' });
        }

        // Check components exist
        if (!vreg.components || vreg.components.first === undefined) {
            accept('error', `Virtual register '${vreg.name}' must have at least one component`, { node: vreg, property: 'components' });
            return;
        }

        // Collect all components (first + rest)
        const allComponents: VirtualRegisterComponent[] = [];
        if (vreg.components.first) {
            allComponents.push(vreg.components.first);
        }
        if (vreg.components.rest) {
            allComponents.push(...vreg.components.rest);
        }

        if (allComponents.length === 0) {
            accept('error', `Virtual register '${vreg.name}' must have at least one component`, { node: vreg, property: 'components' });
            return;
        }

        // Get root node to traverse AST
        const root = AstUtils.getContainerOfType(vreg, (node): node is any => 
            node.$type === 'ISASpecFull' || node.$type === 'ISASpecPartial'
        );
        
        if (!root) {
            return;
        }

        // Get all registers from the AST
        const allRegisters: Register[] = [];
        for (const node of AstUtils.streamAllContents(root)) {
            if (node.$type === 'Register' && (node as Register).name) {
                allRegisters.push(node as Register);
            }
        }

        // Validate each component and calculate total width
        let totalWidth = 0;

        for (const comp of allComponents) {
            let regName: string;
            let regIndex: number | undefined;

            if (comp.indexed_register) {
                regName = comp.indexed_register.reg_name;
                regIndex = comp.indexed_register.index;
            } else if (comp.simple_register) {
                regName = comp.simple_register;
                regIndex = undefined;
            } else {
                accept('error', `Virtual register '${vreg.name}' component is invalid`, { node: comp });
                continue;
            }

            // Find the register
            const reg = allRegisters.find(r => r.name === regName);
            if (!reg) {
                accept('error', `Virtual register '${vreg.name}' component '${regName}' does not exist`, { node: comp });
                continue;
            }

            // Check if indexed register is valid
            if (regIndex !== undefined) {
                if (!reg.count) {
                    accept('error', `Virtual register '${vreg.name}' component '${regName}' is not a register file (cannot use indexing)`, { node: comp });
                    continue;
                }
                if (regIndex < 0 || regIndex >= reg.count) {
                    accept('error', `Virtual register '${vreg.name}' component '${regName}[${regIndex}]' index out of range (0-${reg.count - 1})`, { node: comp });
                    continue;
                }
            }

            // Add component width
            totalWidth += reg.width;
        }

        // Check total width matches virtual register width
        if (totalWidth !== vreg.width) {
            accept('error', `Virtual register '${vreg.name}' width (${vreg.width}) does not match sum of component widths (${totalWidth})`, { node: vreg, property: 'width' });
        }
    }

    /**
     * Validate encoding assignment.
     */
    checkEncodingAssignment(assignment: EncodingAssignment, accept: ValidationAcceptor): void {
        // Extract numeric value from EncodingValue (can be hex or int)
        const encValue = assignment.value as EncodingValue | undefined;
        if (!encValue) {
            accept('error', `Encoding value is missing`, { node: assignment, property: 'value' });
            return;
        }
        
        let value: number;
        if (encValue.hex_value !== undefined && encValue.hex_value !== null) {
            value = parseInt(encValue.hex_value, 16);
        } else if (encValue.int_value !== undefined && encValue.int_value !== null) {
            value = encValue.int_value;
        } else {
            // Fallback for backward compatibility - try to parse as number
            const rawValue = assignment.value as any;
            if (typeof rawValue === 'number') {
                value = rawValue;
            } else if (typeof rawValue === 'string') {
                // Try to parse as hex or decimal
                if (rawValue.startsWith('0x') || rawValue.startsWith('0X')) {
                    value = parseInt(rawValue, 16);
                } else {
                    value = parseInt(rawValue, 10);
                }
            } else {
                accept('error', `Invalid encoding value`, { node: assignment, property: 'value' });
                return;
            }
        }
        
        // Check if value is valid number
        if (isNaN(value)) {
            accept('error', `Encoding value is not a valid number`, { node: assignment, property: 'value' });
            return;
        }
        
        if (value < 0) {
            accept('error', `Encoding value ${value} must be non-negative`, { node: assignment, property: 'value' });
        }
    }

    /**
     * Validate bundle format.
     */
    checkBundleFormat(bundle: BundleFormat, accept: ValidationAcceptor): void {
        // Check bundle width is positive
        if (bundle.width <= 0) {
            accept('error', `Bundle format '${bundle.name}' must have a positive width`, { node: bundle, property: 'width' });
        }

        // Check for duplicate slot names
        const slotNames = new Set<string>();
        for (const slot of bundle.slots) {
            if (slotNames.has(slot.slot_name)) {
                accept('error', `Duplicate slot name '${slot.slot_name}' in bundle format '${bundle.name}'`, { node: slot, property: 'slot_name' });
            }
            slotNames.add(slot.slot_name);
        }

        // Check slot ranges
        const slotRanges: Array<{ slot: BundleSlot; lsb: number; msb: number }> = [];
        for (const slot of bundle.slots) {
            const lsb = slot.lsb;
            const msb = slot.msb;

            if (lsb > msb) {
                accept('error', `Slot '${slot.slot_name}' in bundle format '${bundle.name}': LSB (${lsb}) must be <= MSB (${msb})`, { node: slot });
            }

            if (msb >= bundle.width) {
                accept('error', `Slot '${slot.slot_name}' in bundle format '${bundle.name}' exceeds bundle width (MSB ${msb} >= width ${bundle.width})`, { node: slot });
            }

            // Check for overlapping slots
            for (const existing of slotRanges) {
                if (!(msb < existing.lsb || lsb > existing.msb)) {
                    accept('error', `Slot '${slot.slot_name}' overlaps with slot '${existing.slot.slot_name}' in bundle format '${bundle.name}'`, { node: slot });
                }
            }

            slotRanges.push({ slot, lsb, msb });
        }

        // Check instruction_start if specified
        if (bundle.instruction_start !== undefined) {
            if (bundle.instruction_start < 0 || bundle.instruction_start >= bundle.width) {
                accept('error', `Bundle format '${bundle.name}' instruction_start (${bundle.instruction_start}) must be within bundle width [0, ${bundle.width})`, { node: bundle, property: 'instruction_start' });
            }
        }
    }

    /**
     * Validate bundle slot.
     */
    checkBundleSlot(slot: BundleSlot, accept: ValidationAcceptor): void {
        if (slot.lsb > slot.msb) {
            accept('error', `Bundle slot '${slot.slot_name}': LSB (${slot.lsb}) must be <= MSB (${slot.msb})`, { node: slot });
        }
    }

    /**
     * Validate full ISA specification.
     */
    checkISASpecFull(spec: ISASpecFull, accept: ValidationAcceptor): void {
        // Check for duplicate format names
        if (spec.formats) {
            const formatNames = new Set<string>();
            for (const format of spec.formats.formats) {
                if (formatNames.has(format.name)) {
                    accept('error', `Duplicate format name '${format.name}'`, { node: format, property: 'name' });
                }
                formatNames.add(format.name);
            }
            for (const bundle of spec.formats.bundle_formats) {
                if (formatNames.has(bundle.name)) {
                    accept('error', `Duplicate bundle format name '${bundle.name}'`, { node: bundle, property: 'name' });
                }
                formatNames.add(bundle.name);
            }
        }

        // Check for duplicate register names
        if (spec.registers) {
            const registerNames = new Set<string>();
            for (const register of spec.registers.registers) {
                if (registerNames.has(register.name)) {
                    accept('error', `Duplicate register name '${register.name}'`, { node: register, property: 'name' });
                }
                registerNames.add(register.name);
            }
        }

        // Check for duplicate instruction mnemonics
        if (spec.instructions) {
            const mnemonicNames = new Set<string>();
            for (const instruction of spec.instructions.instructions) {
                if (mnemonicNames.has(instruction.mnemonic)) {
                    accept('warning', `Duplicate instruction mnemonic '${instruction.mnemonic}'`, { node: instruction, property: 'mnemonic' });
                }
                mnemonicNames.add(instruction.mnemonic);
            }
        }
    }

    /**
     * Validate partial ISA specification.
     */
    checkISASpecPartial(spec: ISASpecPartial, accept: ValidationAcceptor): void {
        // Collect all formats, registers, and instructions across all blocks
        const formatNames = new Set<string>();
        const registerNames = new Set<string>();
        const mnemonicNames = new Set<string>();

        for (const formatBlock of spec.formats) {
            for (const format of formatBlock.formats) {
                if (formatNames.has(format.name)) {
                    accept('error', `Duplicate format name '${format.name}'`, { node: format, property: 'name' });
                }
                formatNames.add(format.name);
            }
            for (const bundle of formatBlock.bundle_formats) {
                if (formatNames.has(bundle.name)) {
                    accept('error', `Duplicate bundle format name '${bundle.name}'`, { node: bundle, property: 'name' });
                }
                formatNames.add(bundle.name);
            }
        }

        for (const registerBlock of spec.registers) {
            for (const register of registerBlock.registers) {
                if (registerNames.has(register.name)) {
                    accept('error', `Duplicate register name '${register.name}'`, { node: register, property: 'name' });
                }
                registerNames.add(register.name);
            }
        }

        for (const instructionBlock of spec.instructions) {
            for (const instruction of instructionBlock.instructions) {
                if (mnemonicNames.has(instruction.mnemonic)) {
                    accept('warning', `Duplicate instruction mnemonic '${instruction.mnemonic}'`, { node: instruction, property: 'mnemonic' });
                }
                mnemonicNames.add(instruction.mnemonic);
            }
        }
    }

    /**
     * Validate RTL function call (built-in functions).
     */
    checkRTLFunctionCall(funcCall: RTLFunctionCall, accept: ValidationAcceptor): void {
        if (!funcCall.function_name) {
            accept('error', 'Function name is missing', { node: funcCall, property: 'function_name' });
            return;
        }

        const funcName = funcCall.function_name.toLowerCase();
        const validBuiltins = ['sign_extend', 'zero_extend', 'extract_bits', 'sext', 'sx', 'zext', 'zx', 'to_signed', 'to_unsigned', 
            'ssov', 'suov', 'carry', 'borrow', 'reverse16', 'leading_ones', 'leading_zeros', 'leading_signs'];
        
        if (!validBuiltins.includes(funcName)) {
            accept('warning', `Unknown built-in function '${funcCall.function_name}'. Valid functions: ${validBuiltins.join(', ')}`, 
                { node: funcCall, property: 'function_name' });
            return;
        }

        // Validate argument count
        const argCount = funcCall.args?.length || 0;
        
        if (funcName === 'sign_extend' || funcName === 'sext' || funcName === 'sx') {
            if (argCount < 2 || argCount > 3) {
                accept('error', `sign_extend requires 2 or 3 arguments (value, from_bits[, to_bits]), got ${argCount}`, 
                    { node: funcCall, property: 'args' });
                return;
            }
            // Validate from_bits and to_bits if they are constants
            if (argCount >= 2) {
                const fromBits = this.extractConstantValue(funcCall.args[1]);
                if (fromBits !== null) {
                    if (fromBits <= 0) {
                        accept('error', `sign_extend: from_bits must be positive, got ${fromBits}`, 
                            { node: funcCall.args[1], property: 'value' });
                    } else if (fromBits > 64) {
                        accept('error', `sign_extend: from_bits must be <= 64, got ${fromBits}`, 
                            { node: funcCall.args[1], property: 'value' });
                    }
                }
            }
            if (argCount >= 3) {
                const toBits = this.extractConstantValue(funcCall.args[2]);
                if (toBits !== null) {
                    if (toBits <= 0) {
                        accept('error', `sign_extend: to_bits must be positive, got ${toBits}`, 
                            { node: funcCall.args[2], property: 'value' });
                    } else if (toBits > 64) {
                        accept('error', `sign_extend: to_bits must be <= 64, got ${toBits}`, 
                            { node: funcCall.args[2], property: 'value' });
                    }
                }
            }
        } else if (funcName === 'zero_extend' || funcName === 'zext' || funcName === 'zx') {
            if (argCount < 2 || argCount > 3) {
                accept('error', `zero_extend requires 2 or 3 arguments (value, from_bits[, to_bits]), got ${argCount}`, 
                    { node: funcCall, property: 'args' });
                return;
            }
            // Validate from_bits and to_bits if they are constants
            if (argCount >= 2) {
                const fromBits = this.extractConstantValue(funcCall.args[1]);
                if (fromBits !== null) {
                    if (fromBits <= 0) {
                        accept('error', `zero_extend: from_bits must be positive, got ${fromBits}`, 
                            { node: funcCall.args[1], property: 'value' });
                    } else if (fromBits > 64) {
                        accept('error', `zero_extend: from_bits must be <= 64, got ${fromBits}`, 
                            { node: funcCall.args[1], property: 'value' });
                    }
                }
            }
            if (argCount >= 3) {
                const toBits = this.extractConstantValue(funcCall.args[2]);
                if (toBits !== null) {
                    if (toBits <= 0) {
                        accept('error', `zero_extend: to_bits must be positive, got ${toBits}`, 
                            { node: funcCall.args[2], property: 'value' });
                    } else if (toBits > 64) {
                        accept('error', `zero_extend: to_bits must be <= 64, got ${toBits}`, 
                            { node: funcCall.args[2], property: 'value' });
                    }
                }
            }
        } else if (funcName === 'extract_bits') {
            if (argCount !== 3) {
                accept('error', `extract_bits requires 3 arguments (value, msb, lsb), got ${argCount}`, 
                    { node: funcCall, property: 'args' });
            }
        } else if (funcName === 'to_signed' || funcName === 'to_unsigned') {
            if (argCount !== 2) {
                accept('error', `${funcName} requires 2 arguments (value, width), got ${argCount}`, 
                    { node: funcCall, property: 'args' });
                return;
            }
            // Validate width if it is a constant
            const width = this.extractConstantValue(funcCall.args[1]);
            if (width !== null) {
                if (width <= 0) {
                    accept('error', `${funcName}: width must be positive, got ${width}`, 
                        { node: funcCall.args[1], property: 'value' });
                } else if (width > 64) {
                    accept('error', `${funcName}: width must be <= 64, got ${width}`, 
                        { node: funcCall.args[1], property: 'value' });
                }
            }
        } else if (funcName === 'ssov' || funcName === 'suov') {
            if (argCount !== 2) {
                accept('error', `${funcName} requires 2 arguments (value, width), got ${argCount}`, 
                    { node: funcCall, property: 'args' });
                return;
            }
            // Validate width if it is a constant
            const width = this.extractConstantValue(funcCall.args[1]);
            if (width !== null) {
                if (width <= 0) {
                    accept('error', `${funcName}: width must be positive, got ${width}`, 
                        { node: funcCall.args[1], property: 'value' });
                } else if (width > 64) {
                    accept('error', `${funcName}: width must be <= 64, got ${width}`, 
                        { node: funcCall.args[1], property: 'value' });
                }
            }
        } else if (funcName === 'carry' || funcName === 'borrow') {
            if (argCount !== 3) {
                accept('error', `${funcName} requires 3 arguments (operand1, operand2, carry_in/borrow_in), got ${argCount}`, 
                    { node: funcCall, property: 'args' });
            }
        } else if (funcName === 'reverse16' || funcName === 'leading_ones' || funcName === 'leading_zeros' || funcName === 'leading_signs') {
            if (argCount !== 1) {
                accept('error', `${funcName} requires 1 argument (value), got ${argCount}`, 
                    { node: funcCall, property: 'args' });
            }
        }
    }

    /**
     * Extract constant value from an RTL expression if it's a constant.
     * Returns the numeric value if it's a constant, null otherwise.
     * 
     * RTLExpression -> RTLTernaryExpression -> RTLAtom -> RTLConstant
     * We need to traverse the AST to find the constant.
     */
    private extractConstantValue(expr: any): number | null {
        if (!expr || typeof expr !== 'object') {
            return null;
        }
        
        // Use AstUtils to find RTLConstant in the expression tree
        for (const node of AstUtils.streamAllContents(expr)) {
            if (node.$type === 'RTLConstant') {
                const constant = node as RTLConstant;
                if (constant.hex_value !== undefined && constant.hex_value !== null) {
                    const value = parseInt(constant.hex_value, 16);
                    return isNaN(value) ? null : value;
                } else if (constant.binary_value !== undefined && constant.binary_value !== null) {
                    const value = parseInt(constant.binary_value, 2);
                    return isNaN(value) ? null : value;
                } else if (constant.value !== undefined && constant.value !== null) {
                    return constant.value;
                }
            }
        }
        
        // Fallback: Check if it's directly an RTLConstant (for simple cases)
        if (expr.$type === 'RTLConstant') {
            const constant = expr as RTLConstant;
            if (constant.hex_value !== undefined && constant.hex_value !== null) {
                const value = parseInt(constant.hex_value, 16);
                return isNaN(value) ? null : value;
            } else if (constant.binary_value !== undefined && constant.binary_value !== null) {
                const value = parseInt(constant.binary_value, 2);
                return isNaN(value) ? null : value;
            } else if (constant.value !== undefined && constant.value !== null) {
                return constant.value;
            }
        }
        
        // Check if it's a direct number (for backward compatibility)
        if (typeof expr === 'number') {
            return expr;
        }
        
        return null;
    }
}
