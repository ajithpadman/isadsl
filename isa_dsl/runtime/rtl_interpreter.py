"""RTL expression interpreter for executing instruction behavior."""

from typing import Dict, Any, Optional
from ..model.isa_model import (
    RTLExpression, RTLTernary, RTLBinaryOp, RTLUnaryOp, RTLConstant,
    RTLLValue, RegisterAccess, FieldAccess, RTLStatement, RTLAssignment,
    RTLConditional, RTLMemoryAccess, Instruction
)


class RTLInterpreter:
    """Interprets and executes RTL expressions and statements."""

    def __init__(self, registers: Dict[str, Any], memory: Optional[Dict[int, int]] = None):
        """
        Initialize the RTL interpreter.

        Args:
            registers: Dictionary mapping register names to their values
            memory: Dictionary mapping addresses to memory values
        """
        self.registers = registers
        self.memory = memory if memory is not None else {}
        self.operand_values: Dict[str, int] = {}

    def set_operands(self, operands: Dict[str, int]):
        """Set operand values for the current instruction."""
        self.operand_values = operands

    def execute(self, instruction: Instruction) -> Dict[str, Any]:
        """
        Execute an instruction's RTL behavior.

        Returns:
            Dictionary with execution results and side effects
        """
        if not instruction.behavior:
            return {}

        # Execute all RTL statements
        for stmt in instruction.behavior.statements:
            self._execute_statement(stmt)

        return {
            'registers': self.registers.copy(),
            'memory': self.memory.copy()
        }

    def _execute_statement(self, stmt: RTLStatement):
        """Execute a single RTL statement."""
        if isinstance(stmt, RTLAssignment):
            self._execute_assignment(stmt)
        elif isinstance(stmt, RTLConditional):
            self._execute_conditional(stmt)
        elif isinstance(stmt, RTLMemoryAccess):
            self._execute_memory_access(stmt)

    def _execute_assignment(self, assignment: RTLAssignment):
        """Execute an RTL assignment."""
        value = self._evaluate_expression(assignment.expr)
        self._set_lvalue(assignment.target, value)

    def _execute_conditional(self, conditional: RTLConditional):
        """Execute an RTL conditional statement."""
        condition = self._evaluate_expression(conditional.condition)
        if condition:
            for stmt in conditional.then_statements:
                self._execute_statement(stmt)
        else:
            for stmt in conditional.else_statements:
                self._execute_statement(stmt)

    def _execute_memory_access(self, access: RTLMemoryAccess):
        """Execute a memory access (load or store)."""
        address = self._evaluate_expression(access.address)
        address = address & 0xFFFFFFFF  # Ensure 32-bit address

        if access.is_load and access.target:
            # Load from memory
            value = self.memory.get(address, 0)
            self._set_lvalue(access.target, value)
        elif not access.is_load and access.value:
            # Store to memory
            value = self._evaluate_expression(access.value)
            self.memory[address] = value & 0xFFFFFFFF

    def _evaluate_expression(self, expr: RTLExpression) -> int:
        """Evaluate an RTL expression to an integer value."""
        if isinstance(expr, RTLConstant):
            return expr.value
        elif isinstance(expr, RTLTernary):
            condition = self._evaluate_expression(expr.condition)
            if condition:
                return self._evaluate_expression(expr.then_expr)
            else:
                return self._evaluate_expression(expr.else_expr)
        elif isinstance(expr, RTLBinaryOp):
            left = self._evaluate_expression(expr.left)
            right = self._evaluate_expression(expr.right)
            return self._apply_binary_op(expr.op, left, right)
        elif isinstance(expr, RTLUnaryOp):
            operand = self._evaluate_expression(expr.expr)
            return self._apply_unary_op(expr.op, operand)
        elif isinstance(expr, RegisterAccess):
            return self._get_register_value(expr)
        elif isinstance(expr, FieldAccess):
            return self._get_field_value(expr)
        else:
            raise ValueError(f"Unknown expression type: {type(expr)}")

    def _apply_binary_op(self, op: str, left: int, right: int) -> int:
        """Apply a binary operator."""
        # Ensure values are treated as signed/unsigned appropriately
        left = self._to_signed_32(left)
        right = self._to_signed_32(right)

        if op == '+':
            return (left + right) & 0xFFFFFFFF
        elif op == '-':
            return (left - right) & 0xFFFFFFFF
        elif op == '*':
            return (left * right) & 0xFFFFFFFF
        elif op == '/':
            if right == 0:
                return 0
            return (left // right) & 0xFFFFFFFF
        elif op == '%':
            if right == 0:
                return 0
            return (left % right) & 0xFFFFFFFF
        elif op == '<<':
            return (left << right) & 0xFFFFFFFF
        elif op == '>>':
            # Arithmetic right shift (sign-extending)
            if left & 0x80000000:
                return ((left >> right) | (0xFFFFFFFF << (32 - right))) & 0xFFFFFFFF
            return (left >> right) & 0xFFFFFFFF
        elif op == '&':
            return (left & right) & 0xFFFFFFFF
        elif op == '|':
            return (left | right) & 0xFFFFFFFF
        elif op == '^':
            return (left ^ right) & 0xFFFFFFFF
        elif op == '==':
            return 1 if left == right else 0
        elif op == '!=':
            return 1 if left != right else 0
        elif op == '<':
            return 1 if left < right else 0
        elif op == '>':
            return 1 if left > right else 0
        elif op == '<=':
            return 1 if left <= right else 0
        elif op == '>=':
            return 1 if left >= right else 0
        else:
            raise ValueError(f"Unknown binary operator: {op}")

    def _apply_unary_op(self, op: str, operand: int) -> int:
        """Apply a unary operator."""
        operand = self._to_signed_32(operand)

        if op == '-':
            return (-operand) & 0xFFFFFFFF
        elif op == '!':
            return 0 if operand else 1
        elif op == '~':
            return (~operand) & 0xFFFFFFFF
        else:
            raise ValueError(f"Unknown unary operator: {op}")

    def _get_register_value(self, access: RegisterAccess) -> int:
        """Get the value of a register access."""
        reg_name = access.reg_name
        index = self._evaluate_expression(access.index)

        # Check if it's an operand reference
        if reg_name in self.operand_values:
            # This is likely an operand reference like rd, rs1, etc.
            # We need to get the actual register value
            pass

        # Get register file
        if reg_name not in self.registers:
            raise ValueError(f"Unknown register: {reg_name}")

        reg_value = self.registers[reg_name]
        if isinstance(reg_value, list):
            # Register file
            if index < 0 or index >= len(reg_value):
                raise IndexError(f"Register index {index} out of range for {reg_name}")
            return reg_value[index] & 0xFFFFFFFF
        else:
            # Single register
            return reg_value & 0xFFFFFFFF

    def _get_field_value(self, access: FieldAccess) -> int:
        """Get the value of a register field."""
        reg_name = access.reg_name
        field_name = access.field_name

        if reg_name not in self.registers:
            raise ValueError(f"Unknown register: {reg_name}")

        reg_value = self.registers[reg_name]
        if isinstance(reg_value, list):
            raise ValueError(f"Cannot access field on register file: {reg_name}")

        # For now, we'll need the field definition to extract bits
        # This is a simplified version - in practice, we'd need the ISA model
        # to know the field bit positions
        return reg_value & 0xFFFFFFFF

    def _set_lvalue(self, lvalue: RTLLValue, value: int):
        """Set the value of an lvalue."""
        value = value & 0xFFFFFFFF

        if isinstance(lvalue, RegisterAccess):
            reg_name = lvalue.reg_name
            index = self._evaluate_expression(lvalue.index)

            if reg_name not in self.registers:
                raise ValueError(f"Unknown register: {reg_name}")

            reg_value = self.registers[reg_name]
            if isinstance(reg_value, list):
                # Register file
                if index < 0 or index >= len(reg_value):
                    raise IndexError(f"Register index {index} out of range for {reg_name}")
                self.registers[reg_name][index] = value
            else:
                # Single register
                self.registers[reg_name] = value

        elif isinstance(lvalue, FieldAccess):
            reg_name = lvalue.reg_name
            field_name = lvalue.field_name

            if reg_name not in self.registers:
                raise ValueError(f"Unknown register: {reg_name}")

            # For field access, we need to update specific bits
            # This is simplified - in practice, we'd need field definitions
            self.registers[reg_name] = value

    def _to_signed_32(self, value: int) -> int:
        """Convert a 32-bit value to signed integer."""
        value = value & 0xFFFFFFFF
        if value & 0x80000000:
            return value - 0x100000000
        return value

