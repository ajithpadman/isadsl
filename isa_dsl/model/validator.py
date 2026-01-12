"""Semantic validator for ISA specifications."""

from typing import List, Dict, Set
from .isa_model import (
    ISASpecification, Register, InstructionFormat, Instruction,
    RTLExpression, RegisterAccess, FieldAccess, RTLAssignment,
    RTLConditional, RTLMemoryAccess, RTLTernary, RTLBinaryOp, RTLUnaryOp,
    VirtualRegister, RegisterAlias, InstructionAlias, RTLBitfieldAccess, RTLFunctionCall,
    RTLForLoop
)
from ..runtime.rtl_interpreter import RTLInterpreter


class ValidationError(Exception):
    """Raised when validation fails."""
    def __init__(self, message: str, location: str = ""):
        self.message = message
        self.location = location
        super().__init__(f"{location}: {message}" if location else message)


class ISAValidator:
    """Validates ISA specifications for semantic correctness."""

    def __init__(self, isa: ISASpecification):
        self.isa = isa
        self.errors: List[ValidationError] = []

    def validate(self) -> List[ValidationError]:
        """Run all validation checks."""
        self.errors = []
        self._validate_formats()
        self._validate_instructions()
        self._validate_encodings()
        self._validate_rtl_expressions()
        self._validate_virtual_registers()
        self._validate_register_aliases()
        self._validate_instruction_aliases()
        return self.errors

    def _validate_formats(self):
        """Validate instruction formats."""
        for fmt in self.isa.formats:
            if not fmt.validate_fields():
                self.errors.append(
                    ValidationError(
                        f"Format '{fmt.name}' has overlapping fields or exceeds width",
                        f"format {fmt.name}"
                    )
                )

            total_width = fmt.total_field_width()
            if total_width > fmt.width:
                self.errors.append(
                    ValidationError(
                        f"Format '{fmt.name}' fields exceed format width "
                        f"({total_width} > {fmt.width})",
                        f"format {fmt.name}"
                    )
                )
            
            # Validate constant values fit within field width
            for field in fmt.fields:
                if field.has_constant():
                    field_width = field.width()
                    max_value = (1 << field_width) - 1
                    if field.constant_value < 0:
                        self.errors.append(
                            ValidationError(
                                f"Format '{fmt.name}' field '{field.name}' constant value "
                                f"{field.constant_value} must be non-negative",
                                f"format {fmt.name}"
                            )
                        )
                    elif field.constant_value > max_value:
                        self.errors.append(
                            ValidationError(
                                f"Format '{fmt.name}' field '{field.name}' constant value "
                                f"{field.constant_value} exceeds field width (max: {max_value})",
                                f"format {fmt.name}"
                            )
                        )

    def _validate_instructions(self):
        """Validate instruction definitions."""
        for instr in self.isa.instructions:
            # Check format reference
            if instr.format:
                if instr.format not in self.isa.formats:
                    self.errors.append(
                        ValidationError(
                            f"Instruction '{instr.mnemonic}' references unknown format",
                            f"instruction {instr.mnemonic}"
                        )
                    )
                else:
                    # Check operands match format fields
                    if instr.format:
                        format_field_names = {f.name for f in instr.format.fields}
                        for operand in instr.operands:
                            if operand not in format_field_names:
                                self.errors.append(
                                    ValidationError(
                                        f"Instruction '{instr.mnemonic}' operand '{operand}' "
                                        f"not found in format '{instr.format.name}'",
                                        f"instruction {instr.mnemonic}"
                                    )
                                )

            # Check encoding fields exist in format
            if instr.encoding and instr.format:
                format_field_names = {f.name for f in instr.format.fields}
                for assignment in instr.encoding.assignments:
                    if assignment.field not in format_field_names:
                        self.errors.append(
                            ValidationError(
                                f"Instruction '{instr.mnemonic}' encoding field '{assignment.field}' "
                                f"not found in format '{instr.format.name}'",
                                f"instruction {instr.mnemonic}"
                            )
                        )
                    else:
                        # Check if field has a constant value (cannot be overridden)
                        field = instr.format.get_field(assignment.field)
                        if field and field.has_constant():
                            self.errors.append(
                                ValidationError(
                                    f"Instruction '{instr.mnemonic}' cannot override constant field "
                                    f"'{assignment.field}' from format '{instr.format.name}'",
                                    f"instruction {instr.mnemonic}"
                                )
                            )
            
            # Check that instruction has behavior (unless it's a bundle or has external_behavior)
            if not instr.is_bundle() and not instr.external_behavior:
                if not instr.behavior:
                    self.errors.append(
                        ValidationError(
                            f"Instruction '{instr.mnemonic}' is missing behavior description. "
                            f"Add a 'behavior' block or set 'external_behavior: true' if behavior is implemented externally.",
                            f"instruction {instr.mnemonic}"
                        )
                    )
                elif not instr.behavior.statements:
                    self.errors.append(
                        ValidationError(
                            f"Instruction '{instr.mnemonic}' has an empty behavior block. "
                            f"Add RTL statements to describe the instruction's behavior.",
                            f"instruction {instr.mnemonic}"
                        )
                    )

    def _validate_encodings(self):
        """Check for encoding conflicts between instructions."""
        encoding_map: Dict[int, List[Instruction]] = {}
        
        for instr in self.isa.instructions:
            if not instr.format or not instr.encoding:
                continue

            # Create a signature based on encoding fields
            signature_parts = []
            for assignment in instr.encoding.assignments:
                field = instr.format.get_field(assignment.field)
                if field:
                    signature_parts.append((assignment.field, assignment.value))

            # Check for conflicts
            for other_instr in self.isa.instructions:
                if other_instr == instr or not other_instr.format or not other_instr.encoding:
                    continue

                # Check if encodings could conflict
                if self._encodings_conflict(instr, other_instr):
                    self.errors.append(
                        ValidationError(
                            f"Encoding conflict between '{instr.mnemonic}' and '{other_instr.mnemonic}'",
                            "encoding validation"
                        )
                    )

    def _encodings_conflict(self, instr1: Instruction, instr2: Instruction) -> bool:
        """Check if two instructions have conflicting encodings."""
        if instr1.format != instr2.format:
            return False

        # Check if all encoding fields match
        if not instr1.encoding or not instr2.encoding:
            return False

        enc1_fields = {a.field: a.value for a in instr1.encoding.assignments}
        enc2_fields = {a.field: a.value for a in instr2.encoding.assignments}

        # If all fields in enc1 match enc2, they conflict
        for field, value in enc1_fields.items():
            if field in enc2_fields and enc2_fields[field] != value:
                return False

        # If we get here, all common fields match - potential conflict
        return len(enc1_fields) > 0 and len(enc2_fields) > 0

    def _validate_rtl_expressions(self):
        """Validate RTL expressions reference valid registers and fields."""
        for instr in self.isa.instructions:
            if not instr.behavior:
                continue

            self._validate_rtl_block(instr.behavior, instr.mnemonic)
            # Also validate that behavior can be interpreted by RTL interpreter
            self._validate_rtl_interpretability(instr)

    def _validate_rtl_block(self, block, context: str):
        """Validate an RTL block."""
        for stmt in block.statements:
            self._validate_rtl_statement(stmt, context)

    def _validate_rtl_statement(self, stmt, context: str):
        """Validate an RTL statement."""
        if isinstance(stmt, RTLAssignment):
            self._validate_rtl_lvalue(stmt.target, context)
            self._validate_rtl_expression(stmt.expr, context)
        elif isinstance(stmt, RTLConditional):
            self._validate_rtl_expression(stmt.condition, context)
            for then_stmt in stmt.then_statements:
                self._validate_rtl_statement(then_stmt, context)
            for else_stmt in stmt.else_statements:
                self._validate_rtl_statement(else_stmt, context)
        elif isinstance(stmt, RTLMemoryAccess):
            self._validate_rtl_expression(stmt.address, context)
            if stmt.target:
                self._validate_rtl_lvalue(stmt.target, context)
            if stmt.value:
                self._validate_rtl_expression(stmt.value, context)
        elif isinstance(stmt, RTLForLoop):
            # RTLForLoop is not yet supported by the RTL interpreter
            self.errors.append(
                ValidationError(
                    f"RTL for loops are not yet supported by the RTL interpreter",
                    f"instruction {context}"
                )
            )

    def _validate_rtl_expression(self, expr: RTLExpression, context: str):
        """Validate an RTL expression."""
        if isinstance(expr, RTLTernary):
            self._validate_rtl_expression(expr.condition, context)
            self._validate_rtl_expression(expr.then_expr, context)
            self._validate_rtl_expression(expr.else_expr, context)
        elif isinstance(expr, RTLBinaryOp):
            self._validate_rtl_expression(expr.left, context)
            self._validate_rtl_expression(expr.right, context)
        elif isinstance(expr, RTLUnaryOp):
            self._validate_rtl_expression(expr.expr, context)
        elif isinstance(expr, RegisterAccess):
            self._validate_register_access(expr, context)
        elif isinstance(expr, FieldAccess):
            self._validate_field_access(expr, context)
        elif isinstance(expr, RTLBitfieldAccess):
            self._validate_rtl_expression(expr.base, context)
            self._validate_rtl_expression(expr.msb, context)
            self._validate_rtl_expression(expr.lsb, context)
        elif isinstance(expr, RTLFunctionCall):
            # Validate built-in function arguments
            for arg in expr.args:
                self._validate_rtl_expression(arg, context)
            # Validate function name (check if it's a known built-in)
            valid_builtins = {'sign_extend', 'zero_extend', 'extract_bits', 'sext', 'sx', 'zext', 'zx', 
                            'to_signed', 'to_unsigned', 'ssov', 'suov', 'carry', 'borrow', 
                            'reverse16', 'leading_ones', 'leading_zeros', 'leading_signs'}
            if expr.function_name.lower() not in valid_builtins:
                # Warning: unknown function, but don't fail validation
                pass

    def _validate_rtl_lvalue(self, lvalue, context: str):
        """Validate an RTL left-hand value."""
        if isinstance(lvalue, RegisterAccess):
            self._validate_register_access(lvalue, context)
        elif isinstance(lvalue, FieldAccess):
            self._validate_field_access(lvalue, context)

    def _validate_register_access(self, access: RegisterAccess, context: str):
        """Validate a register access."""
        reg = self.isa.get_register(access.reg_name)
        if not reg:
            self.errors.append(
                ValidationError(
                    f"Unknown register '{access.reg_name}' in RTL expression",
                    f"instruction {context}"
                )
            )
        elif not reg.is_register_file() and not reg.is_vector_register():
            self.errors.append(
                ValidationError(
                    f"Register '{access.reg_name}' is not a register file or vector register (cannot use indexing)",
                    f"instruction {context}"
                )
            )
        elif reg.is_vector_register() and access.lane_index is None:
            # Vector register access without lane index - this is valid for whole vector operations
            pass

    def _validate_field_access(self, access: FieldAccess, context: str):
        """Validate a register field access."""
        reg = self.isa.get_register(access.reg_name)
        if not reg:
            self.errors.append(
                ValidationError(
                    f"Unknown register '{access.reg_name}' in RTL expression",
                    f"instruction {context}"
                )
            )
        else:
            field = reg.get_field(access.field_name)
            if not field:
                    self.errors.append(
                        ValidationError(
                            f"Unknown field '{access.field_name}' in register '{access.reg_name}'",
                            f"instruction {context}"
                        )
                    )
    
    def _validate_virtual_registers(self):
        """Validate virtual register definitions."""
        register_names = {reg.name for reg in self.isa.registers}
        
        for vreg in self.isa.virtual_registers:
            # Check for name conflicts
            if vreg.name in register_names:
                self.errors.append(
                    ValidationError(
                        f"Virtual register '{vreg.name}' conflicts with existing register name",
                        f"virtual register {vreg.name}"
                    )
                )
            
            # Validate components
            total_width = 0
            for comp in vreg.components:
                reg = self.isa.get_register(comp.reg_name)
                if not reg:
                    self.errors.append(
                        ValidationError(
                            f"Virtual register '{vreg.name}' component '{comp.reg_name}' does not exist",
                            f"virtual register {vreg.name}"
                        )
                    )
                    continue
                
                if comp.is_indexed():
                    # Indexed register - must be a register file
                    if not reg.is_register_file():
                        self.errors.append(
                            ValidationError(
                                f"Virtual register '{vreg.name}' component '{comp.reg_name}' is not a register file (cannot use indexing)",
                                f"virtual register {vreg.name}"
                            )
                        )
                    elif comp.index < 0 or (reg.count and comp.index >= reg.count):
                        self.errors.append(
                            ValidationError(
                                f"Virtual register '{vreg.name}' component '{comp.reg_name}[{comp.index}]' index out of range (0-{reg.count-1})",
                                f"virtual register {vreg.name}"
                            )
                        )
                
                total_width += reg.width
            
            # Check total width matches virtual register width
            if total_width != vreg.width:
                self.errors.append(
                    ValidationError(
                        f"Virtual register '{vreg.name}' width mismatch: declared {vreg.width} bits, components total {total_width} bits",
                        f"virtual register {vreg.name}"
                    )
                )
    
    def _validate_register_aliases(self):
        """Validate register alias definitions."""
        register_names = {reg.name for reg in self.isa.registers}
        virtual_register_names = {vreg.name for vreg in self.isa.virtual_registers}
        alias_names = {alias.alias_name for alias in self.isa.register_aliases}
        
        for alias in self.isa.register_aliases:
            # Check for name conflicts
            if alias.alias_name in register_names:
                self.errors.append(
                    ValidationError(
                        f"Register alias '{alias.alias_name}' conflicts with existing register name",
                        f"alias {alias.alias_name}"
                    )
                )
            if alias.alias_name in virtual_register_names:
                self.errors.append(
                    ValidationError(
                        f"Register alias '{alias.alias_name}' conflicts with existing virtual register name",
                        f"alias {alias.alias_name}"
                    )
                )
            
            # Check target register exists
            reg = self.isa.get_register(alias.target_reg_name)
            if not reg:
                self.errors.append(
                    ValidationError(
                        f"Register alias '{alias.alias_name}' target '{alias.target_reg_name}' does not exist",
                        f"alias {alias.alias_name}"
                    )
                )
            elif alias.is_indexed():
                # Indexed target - must be a register file
                if not reg.is_register_file():
                    self.errors.append(
                        ValidationError(
                            f"Register alias '{alias.alias_name}' target '{alias.target_reg_name}' is not a register file (cannot use indexing)",
                            f"alias {alias.alias_name}"
                        )
                    )
                elif alias.target_index < 0 or (reg.count and alias.target_index >= reg.count):
                    self.errors.append(
                        ValidationError(
                            f"Register alias '{alias.alias_name}' target '{alias.target_reg_name}[{alias.target_index}]' index out of range (0-{reg.count-1})",
                            f"alias {alias.alias_name}"
                        )
                    )
            
            # Check for circular aliases (simple check - alias pointing to another alias)
            # This is a basic check; full circular detection would require graph traversal
            if alias.target_reg_name in alias_names:
                # Could be circular, but allow it for now (e.g., SP = R[13], R13 = SP)
                # Full circular detection would need to be more sophisticated
                pass
    
    def _validate_instruction_aliases(self):
        """Validate instruction alias definitions."""
        instruction_mnemonics = {instr.mnemonic for instr in self.isa.instructions}
        alias_mnemonics = {alias.alias_mnemonic for alias in self.isa.instruction_aliases}
        
        for alias in self.isa.instruction_aliases:
            # Check for name conflicts
            if alias.alias_mnemonic in instruction_mnemonics:
                self.errors.append(
                    ValidationError(
                        f"Instruction alias '{alias.alias_mnemonic}' conflicts with existing instruction mnemonic",
                        f"alias instruction {alias.alias_mnemonic}"
                    )
                )
            
            # Check target instruction exists
            target_instr = self.isa.get_instruction(alias.target_mnemonic)
            if not target_instr:
                self.errors.append(
                    ValidationError(
                        f"Instruction alias '{alias.alias_mnemonic}' target '{alias.target_mnemonic}' does not exist",
                        f"alias instruction {alias.alias_mnemonic}"
                    )
                )
            
            # Check for circular aliases (simple check)
            if alias.target_mnemonic in alias_mnemonics:
                # Could be circular, but allow it for now
                pass

    def _validate_rtl_interpretability(self, instruction: Instruction):
        """Validate that RTL behavior can be interpreted by the RTL interpreter.
        
        This catches unsupported features and syntax errors that would cause
        instructions to fail during execution or disappear from ISA info.
        """
        if not instruction.behavior or instruction.external_behavior:
            return
        
        # Create dummy registers for validation
        dummy_registers = {}
        for reg in self.isa.registers:
            if reg.is_register_file():
                # Create a dummy register file with default values
                dummy_registers[reg.name] = [0] * (reg.count or 16)
            else:
                # Create a dummy single register
                dummy_registers[reg.name] = 0
        
        # Create a dummy interpreter with minimal state
        interpreter = RTLInterpreter(
            registers=dummy_registers.copy(),
            memory={},
            isa=self.isa
        )
        
        # Set dummy operand values (use 0 for all operands)
        dummy_operands = {}
        if instruction.operands:
            for op in instruction.operands:
                dummy_operands[op] = 0
        elif instruction.operand_specs:
            for op_spec in instruction.operand_specs:
                dummy_operands[op_spec.name] = 0
        
        interpreter.set_operands(dummy_operands)
        
        # Try to execute the behavior block and catch any errors
        try:
            interpreter.execute(instruction)
        except ValueError as e:
            # ValueError indicates unsupported features or invalid syntax
            self.errors.append(
                ValidationError(
                    f"RTL behavior contains unsupported feature or syntax error: {str(e)}",
                    f"instruction {instruction.mnemonic}"
                )
            )
        except IndexError as e:
            # IndexError indicates register index out of range
            self.errors.append(
                ValidationError(
                    f"RTL behavior contains invalid register index: {str(e)}",
                    f"instruction {instruction.mnemonic}"
                )
            )
        except Exception as e:
            # Catch any other unexpected errors
            self.errors.append(
                ValidationError(
                    f"RTL behavior cannot be interpreted: {str(e)}",
                    f"instruction {instruction.mnemonic}"
                )
            )

