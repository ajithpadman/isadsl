"""RTL expression interpreter for executing instruction behavior."""

from typing import Dict, Any, Optional
from ..model.isa_model import (
    RTLExpression, RTLTernary, RTLBinaryOp, RTLUnaryOp, RTLConstant,
    RTLLValue, RegisterAccess, FieldAccess, Variable, RTLStatement, RTLAssignment,
    RTLConditional, RTLMemoryAccess, Instruction, ISASpecification,
    VirtualRegister, RegisterAlias, OperandReference, RTLBitfieldAccess, RTLFunctionCall
)


class RTLInterpreter:
    """Interprets and executes RTL expressions and statements."""

    def __init__(self, registers: Dict[str, Any], memory: Optional[Dict[int, int]] = None, isa: Optional[ISASpecification] = None):
        """
        Initialize the RTL interpreter.

        Args:
            registers: Dictionary mapping register names to their values
            memory: Dictionary mapping addresses to memory values
            isa: Optional ISA specification for resolving virtual registers and aliases
        """
        self.registers = registers
        self.memory = memory if memory is not None else {}
        self.operand_values: Dict[str, int] = {}
        self.variables: Dict[str, int] = {}  # Temporary variables
        self.isa = isa

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
        elif isinstance(expr, Variable):
            # Temporary variable reference
            return self.variables.get(expr.name, 0)
        elif isinstance(expr, OperandReference):
            # Operand reference (e.g., rd, rs1) - get from operand_values
            # But first check if it's actually a variable (temporary variable)
            if expr.name in self.variables:
                return self.variables[expr.name]
            return self.operand_values.get(expr.name, 0)
        elif isinstance(expr, RTLBitfieldAccess):
            base_value = self._evaluate_expression(expr.base)
            msb_value = self._evaluate_expression(expr.msb)
            lsb_value = self._evaluate_expression(expr.lsb)
            # Extract bits: (value >> lsb) & ((1 << (msb - lsb + 1)) - 1)
            width = msb_value - lsb_value + 1
            return (base_value >> lsb_value) & ((1 << width) - 1)
        elif isinstance(expr, RTLFunctionCall):
            args = [self._evaluate_expression(arg) for arg in expr.args]
            return self._apply_builtin_function(expr.function_name, args)
        else:
            raise ValueError(f"Unknown expression type: {type(expr)}")

    def _apply_builtin_function(self, func_name: str, args: list) -> int:
        """Apply a built-in function."""
        func_name_lower = func_name.lower()
        
        if func_name_lower == "sign_extend" or func_name_lower == "sext" or func_name_lower == "sx":
            if len(args) == 2:
                value, from_bits = args
                to_bits = 32  # Default to 32 bits
            elif len(args) == 3:
                value, from_bits, to_bits = args
            else:
                raise ValueError(f"sign_extend requires 2 or 3 arguments, got {len(args)}")
            
            if from_bits >= to_bits:
                return value & ((1 << to_bits) - 1)
            # Extract the sign bit
            sign_bit = (value >> (from_bits - 1)) & 1
            if sign_bit:
                # Negative: extend with 1s
                mask = ((1 << (to_bits - from_bits)) - 1) << from_bits
                return value | mask
            else:
                # Positive: extend with 0s
                return value & ((1 << to_bits) - 1)
        
        elif func_name_lower == "zero_extend" or func_name_lower == "zext" or func_name_lower == "zx":
            if len(args) == 2:
                value, from_bits = args
                to_bits = 32  # Default to 32 bits
            elif len(args) == 3:
                value, from_bits, to_bits = args
            else:
                raise ValueError(f"zero_extend requires 2 or 3 arguments, got {len(args)}")
            
            if from_bits >= to_bits:
                return value & ((1 << to_bits) - 1)
            # Just mask to the target width (zero extension)
            return value & ((1 << to_bits) - 1)
        
        elif func_name_lower == "extract_bits":
            if len(args) != 3:
                raise ValueError(f"extract_bits requires 3 arguments (value, msb, lsb), got {len(args)}")
            value, msb, lsb = args
            width = msb - lsb + 1
            return (value >> lsb) & ((1 << width) - 1)
        
        else:
            raise ValueError(f"Unknown built-in function: {func_name}")

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

        # Resolve register alias if needed
        reg_name, index = self._resolve_register_alias(reg_name, index)

        # Check if it's a virtual register
        if self.isa:
            vreg = self.isa.get_virtual_register(reg_name)
            if vreg:
                return self._read_virtual_register(vreg)

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

            # Resolve register alias if needed
            reg_name, index = self._resolve_register_alias(reg_name, index)

            # Check if it's a virtual register
            if self.isa:
                vreg = self.isa.get_virtual_register(reg_name)
                if vreg:
                    self._write_virtual_register(vreg, value)
                    return

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

            # Resolve register alias if needed
            reg_name, _ = self._resolve_register_alias(reg_name, None)

            if reg_name not in self.registers:
                raise ValueError(f"Unknown register: {reg_name}")

            # For field access, we need to update specific bits
            # This is simplified - in practice, we'd need field definitions
            self.registers[reg_name] = value
        
        elif isinstance(lvalue, Variable):
            # Temporary variable assignment
            self.variables[lvalue.name] = value
        
        elif isinstance(lvalue, str):
            # Simple register name (backward compatibility)
            if lvalue not in self.registers:
                raise ValueError(f"Unknown register: {lvalue}")
            self.registers[lvalue] = value

    def _to_signed_32(self, value: int) -> int:
        """Convert a 32-bit value to signed integer."""
        value = value & 0xFFFFFFFF
        if value & 0x80000000:
            return value - 0x100000000
        return value
    
    def _resolve_register_alias(self, name: str, index: Optional[int]) -> tuple[str, Optional[int]]:
        """Resolve a register alias to the actual register name and index.
        
        Returns:
            Tuple of (register_name, index) where index may be updated if alias targets indexed register.
        """
        if not self.isa:
            return (name, index)
        
        # Check if name is an alias
        for alias in self.isa.register_aliases:
            if alias.alias_name == name:
                # Alias found - use target register
                target_name = alias.target_reg_name
                # If alias has an index, use it; otherwise use provided index
                target_index = alias.target_index if alias.is_indexed() else index
                return (target_name, target_index)
        
        return (name, index)
    
    def _read_virtual_register(self, vreg: VirtualRegister) -> int:
        """Read virtual register by concatenating component registers."""
        value = 0
        bit_offset = 0
        
        # Read components in order: first component is LSB, last is MSB
        # For little-endian: R[0]|R[1] means R[0] is LSB, R[1] is MSB
        for comp in vreg.components:
            reg = self.isa.get_register(comp.reg_name)
            if not reg:
                raise ValueError(f"Virtual register '{vreg.name}' component '{comp.reg_name}' not found")
            
            if comp.is_indexed():
                # Indexed register from register file
                if not reg.is_register_file():
                    raise ValueError(f"Register {comp.reg_name} is not a register file")
                if comp.index < 0 or (reg.count and comp.index >= reg.count):
                    raise IndexError(f"Register index {comp.index} out of range")
                
                if comp.reg_name not in self.registers:
                    raise ValueError(f"Unknown register: {comp.reg_name}")
                
                reg_file = self.registers[comp.reg_name]
                if not isinstance(reg_file, list):
                    raise ValueError(f"Register {comp.reg_name} is not a register file")
                
                if comp.index >= len(reg_file):
                    raise IndexError(f"Register index {comp.index} out of range")
                
                reg_value = reg_file[comp.index] & ((1 << reg.width) - 1)
            else:
                # Simple register (SFR)
                if comp.reg_name not in self.registers:
                    raise ValueError(f"Unknown register: {comp.reg_name}")
                
                reg_value = self.registers[comp.reg_name] & ((1 << reg.width) - 1)
            
            value |= (reg_value << bit_offset)
            bit_offset += reg.width
        
        return value & ((1 << vreg.width) - 1)
    
    def _write_virtual_register(self, vreg: VirtualRegister, value: int):
        """Write virtual register by splitting to component registers."""
        bit_offset = 0
        
        # Write components in order: first component is LSB, last is MSB
        # For little-endian: R[0]|R[1] means R[0] is LSB, R[1] is MSB
        for comp in vreg.components:
            reg = self.isa.get_register(comp.reg_name)
            if not reg:
                raise ValueError(f"Virtual register '{vreg.name}' component '{comp.reg_name}' not found")
            
            mask = (1 << reg.width) - 1
            reg_value = (value >> bit_offset) & mask
            
            if comp.is_indexed():
                # Indexed register from register file
                if not reg.is_register_file():
                    raise ValueError(f"Register {comp.reg_name} is not a register file")
                if comp.index < 0 or (reg.count and comp.index >= reg.count):
                    raise IndexError(f"Register index {comp.index} out of range")
                
                if comp.reg_name not in self.registers:
                    raise ValueError(f"Unknown register: {comp.reg_name}")
                
                reg_file = self.registers[comp.reg_name]
                if not isinstance(reg_file, list):
                    raise ValueError(f"Register {comp.reg_name} is not a register file")
                
                if comp.index >= len(reg_file):
                    raise IndexError(f"Register index {comp.index} out of range")
                
                reg_file[comp.index] = reg_value
            else:
                # Simple register (SFR)
                if comp.reg_name not in self.registers:
                    raise ValueError(f"Unknown register: {comp.reg_name}")
                
                self.registers[comp.reg_name] = reg_value
            
            bit_offset += reg.width

