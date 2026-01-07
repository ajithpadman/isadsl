"""Generator for Python-based instruction simulators."""

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Dict, Any
from ..model.isa_model import ISASpecification

# Template is now loaded from file: isa_dsl/generators/templates/simulator.j2


class SimulatorGenerator:
    """Generates Python simulators from ISA specifications."""

    def __init__(self, isa: ISASpecification):
        self.isa = isa

    def _generate_rtl_code(self, stmt) -> str:
        """Generate Python code from an RTL statement."""
        from ..model.isa_model import (
            RTLAssignment, RTLConditional, RTLMemoryAccess,
            RegisterAccess, FieldAccess, RTLConstant, RTLBinaryOp,
            RTLUnaryOp, RTLTernary
        )
        
        if isinstance(stmt, RTLAssignment):
            # Check if target is a virtual register
            from ..model.isa_model import RegisterAccess
            is_virtual = False
            vreg_name = None
            if isinstance(stmt.target, str):
                vreg = self.isa.get_virtual_register(stmt.target)
                if vreg:
                    is_virtual = True
                    vreg_name = stmt.target
            elif isinstance(stmt.target, RegisterAccess):
                vreg = self.isa.get_virtual_register(stmt.target.reg_name)
                if vreg:
                    is_virtual = True
                    vreg_name = stmt.target.reg_name
            
            if is_virtual:
                # Virtual register write - use helper method
                expr = self._generate_expr_code(stmt.expr)
                return f"        self._write_virtual_register('{vreg_name}', {expr} & 0xFFFFFFFF)"
            else:
                # Regular register write
                target = self._generate_lvalue_code(stmt.target)
                expr = self._generate_expr_code(stmt.expr)
                return f"        {target} = {expr} & 0xFFFFFFFF"
        elif isinstance(stmt, RTLConditional):
            condition = self._generate_expr_code(stmt.condition)
            code = f"        if {condition}:\n"
            for then_stmt in stmt.then_statements:
                # Add extra indentation for then block
                stmt_code = self._generate_rtl_code(then_stmt)
                # Increase indentation by 4 spaces
                for line in stmt_code.split('\n'):
                    if line.strip():
                        code += "    " + line + "\n"
            if stmt.else_statements:
                code += "        else:\n"
                for else_stmt in stmt.else_statements:
                    # Add extra indentation for else block
                    stmt_code = self._generate_rtl_code(else_stmt)
                    for line in stmt_code.split('\n'):
                        if line.strip():
                            code += "    " + line + "\n"
            return code.rstrip()
        elif isinstance(stmt, RTLMemoryAccess):
            address = self._generate_expr_code(stmt.address)
            if stmt.is_load and stmt.target:
                target = self._generate_lvalue_code(stmt.target)
                return f"        {target} = self.memory.get({address} & 0xFFFFFFFF, 0)"
            elif not stmt.is_load and stmt.value:
                value = self._generate_expr_code(stmt.value)
                return f"        self.memory[{address} & 0xFFFFFFFF] = {value} & 0xFFFFFFFF"
        return "        # RTL statement"

    def _generate_lvalue_code(self, lvalue) -> str:
        """Generate code for an lvalue."""
        from ..model.isa_model import RegisterAccess, FieldAccess
        
        # Handle string (simple register name like PC)
        if isinstance(lvalue, str):
            # Check for register alias (virtual registers are handled in assignment)
            resolved_name, _ = self._resolve_register_alias(lvalue, None)
            return f"self.{resolved_name}"
        
        if isinstance(lvalue, RegisterAccess):
            index = self._generate_expr_code(lvalue.index)
            # Check for register alias (virtual registers are handled in assignment)
            resolved_name, resolved_index = self._resolve_register_alias(lvalue.reg_name, index)
            if resolved_index is not None:
                return f"self.{resolved_name}[{resolved_index}]"
            return f"self.{resolved_name}[{index}]"
        elif isinstance(lvalue, FieldAccess):
            # Resolve alias if needed
            resolved_name, _ = self._resolve_register_alias(lvalue.reg_name, None)
            return f"self.{resolved_name}_{lvalue.field_name}"
        return "unknown"
    
    def _resolve_register_alias(self, name: str, index) -> tuple:
        """Resolve a register alias to the actual register name and index."""
        for alias in self.isa.register_aliases:
            if alias.alias_name == name:
                target_name = alias.target_reg_name
                target_index = alias.target_index if alias.is_indexed() else index
                return (target_name, target_index)
        return (name, index)

    def _generate_expr_code(self, expr) -> str:
        """Generate code for an expression."""
        from ..model.isa_model import (
            RTLConstant, RegisterAccess, RTLBinaryOp, RTLUnaryOp,
            RTLTernary, FieldAccess, OperandReference
        )
        
        if isinstance(expr, RTLConstant):
            return str(expr.value)
        elif isinstance(expr, OperandReference):
            # Check if this is actually a register name (not an operand)
            # Register names are SFRs (single registers) defined in the ISA
            # Check if it's a virtual register
            vreg = self.isa.get_virtual_register(expr.name)
            if vreg:
                return f"self._read_virtual_register('{expr.name}')"
            # Check for register alias
            resolved_name, _ = self._resolve_register_alias(expr.name, None)
            reg = self.isa.get_register(resolved_name)
            if reg and not reg.is_register_file() and not reg.is_vector_register():
                # This is a simple register (SFR) like PC
                return f"self.{resolved_name}"
            # Otherwise, it's an operand reference (variable name in generated code)
            return expr.name
        elif isinstance(expr, RegisterAccess):
            index = self._generate_expr_code(expr.index)
            # Check if this is a virtual register
            vreg = self.isa.get_virtual_register(expr.reg_name)
            if vreg:
                # Virtual register - use helper method
                return f"self._read_virtual_register('{expr.reg_name}')"
            # Check for register alias
            resolved_name, resolved_index = self._resolve_register_alias(expr.reg_name, index)
            if resolved_index is not None:
                return f"self.{resolved_name}[{resolved_index}]"
            return f"self.{resolved_name}[{index}]"
        elif isinstance(expr, FieldAccess):
            return f"self.{expr.reg_name}_{expr.field_name}"
        elif isinstance(expr, RTLBinaryOp):
            left = self._generate_expr_code(expr.left)
            right = self._generate_expr_code(expr.right)
            return f"({left} {expr.op} {right})"
        elif isinstance(expr, RTLUnaryOp):
            operand = self._generate_expr_code(expr.expr)
            return f"({expr.op}{operand})"
        elif isinstance(expr, RTLTernary):
            condition = self._generate_expr_code(expr.condition)
            then_expr = self._generate_expr_code(expr.then_expr)
            else_expr = self._generate_expr_code(expr.else_expr)
            return f"({then_expr} if {condition} else {else_expr})"
        elif isinstance(expr, str):
            # Simple register name - check if it's a register
            # Check if it's a virtual register
            vreg = self.isa.get_virtual_register(expr)
            if vreg:
                return f"self._read_virtual_register('{expr}')"
            # Check for register alias
            resolved_name, _ = self._resolve_register_alias(expr, None)
            reg = self.isa.get_register(resolved_name)
            if reg and not reg.is_register_file() and not reg.is_vector_register():
                return f"self.{resolved_name}"
            # Otherwise treat as operand reference
            return expr
        return "0"

    def generate(self, output_path: str):
        """Generate the simulator code."""
        from jinja2 import Environment, FileSystemLoader
        
        # Get templates directory
        templates_dir = Path(__file__).parent / 'templates'
        
        # Create environment with FileSystemLoader
        env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            trim_blocks=False,
            lstrip_blocks=False
        )
        
        # Add custom filter for computing bit masks
        def mask_filter(width):
            if width is None or width < 0:
                return 0
            return (1 << width) - 1
        
        # Add filter for computing slot masks (for bundles)
        def slot_mask_filter(slot):
            if slot is None:
                return 0
            width = slot.width()
            if width <= 0:
                return 0
            return (1 << width) - 1
        
        env.filters['mask'] = mask_filter
        env.filters['slot_mask'] = slot_mask_filter
        
        # Add enumerate to globals
        env.globals['enumerate'] = enumerate
        
        # Load template from file
        template = env.get_template('simulator.j2')
        
        # Create a function that can be called from template
        def generate_rtl_code(stmt, instruction):
            return self._generate_rtl_code(stmt)
        
        code = template.render(isa=self.isa, generate_rtl_code=generate_rtl_code)
        
        output_file = Path(output_path) / 'simulator.py'
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(code)
        
        return output_file

