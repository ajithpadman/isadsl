"""Semantic validator for ISA specifications."""

from typing import List, Dict, Set
from .isa_model import (
    ISASpecification, Register, InstructionFormat, Instruction,
    RTLExpression, RegisterAccess, FieldAccess, RTLAssignment,
    RTLConditional, RTLMemoryAccess, RTLTernary, RTLBinaryOp, RTLUnaryOp
)


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

