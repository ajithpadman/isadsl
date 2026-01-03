"""Generator for ISA documentation."""

from jinja2 import Environment, FileSystemLoader, Template
from pathlib import Path
from ..model.isa_model import ISASpecification

# Template is now loaded from file: isa_dsl/generators/templates/documentation.j2
# Template is now loaded from file: isa_dsl/generators/templates/documentation.j2



class DocumentationGenerator:
    """Generates documentation from ISA specifications."""

    def __init__(self, isa: ISASpecification):
        self.isa = isa

    def _format_rtl_statement(self, stmt) -> str:
        """Format an RTL statement as text."""
        from ..model.isa_model import (
            RTLAssignment, RTLConditional, RTLMemoryAccess,
            RegisterAccess, FieldAccess, RTLConstant, RTLBinaryOp,
            RTLUnaryOp, RTLTernary
        )
        
        if isinstance(stmt, RTLAssignment):
            target = self._format_lvalue(stmt.target)
            expr = self._format_expr(stmt.expr)
            return f"{target} = {expr};"
        elif isinstance(stmt, RTLConditional):
            condition = self._format_expr(stmt.condition)
            code = f"if ({condition}) {{\n"
            for then_stmt in stmt.then_statements:
                code += f"    {self._format_rtl_statement(then_stmt)}\n"
            code += "}"
            if stmt.else_statements:
                code += " else {\n"
                for else_stmt in stmt.else_statements:
                    code += f"    {self._format_rtl_statement(else_stmt)}\n"
                code += "}"
            return code
        elif isinstance(stmt, RTLMemoryAccess):
            address = self._format_expr(stmt.address)
            if stmt.is_load and stmt.target:
                target = self._format_lvalue(stmt.target)
                return f"{target} = MEM[{address}];"
            elif not stmt.is_load and stmt.value:
                value = self._format_expr(stmt.value)
                return f"MEM[{address}] = {value};"
        return "// RTL statement"

    def _format_lvalue(self, lvalue) -> str:
        """Format an lvalue as text."""
        from ..model.isa_model import RegisterAccess, FieldAccess
        
        if isinstance(lvalue, RegisterAccess):
            index = self._format_expr(lvalue.index)
            return f"{lvalue.reg_name}[{index}]"
        elif isinstance(lvalue, FieldAccess):
            return f"{lvalue.reg_name}.{lvalue.field_name}"
        return "unknown"

    def _format_expr(self, expr) -> str:
        """Format an expression as text."""
        from ..model.isa_model import (
            RTLConstant, RegisterAccess, RTLBinaryOp, RTLUnaryOp,
            RTLTernary, FieldAccess
        )
        
        if isinstance(expr, RTLConstant):
            return str(expr.value)
        elif isinstance(expr, RegisterAccess):
            index = self._format_expr(expr.index)
            return f"{expr.reg_name}[{index}]"
        elif isinstance(expr, FieldAccess):
            return f"{expr.reg_name}.{expr.field_name}"
        elif isinstance(expr, RTLBinaryOp):
            left = self._format_expr(expr.left)
            right = self._format_expr(expr.right)
            return f"({left} {expr.op} {right})"
        elif isinstance(expr, RTLUnaryOp):
            operand = self._format_expr(expr.expr)
            return f"{expr.op}{operand}"
        elif isinstance(expr, RTLTernary):
            condition = self._format_expr(expr.condition)
            then_expr = self._format_expr(expr.then_expr)
            else_expr = self._format_expr(expr.else_expr)
            return f"({condition} ? {then_expr} : {else_expr})"
        return "0"

    def generate(self, output_path: str, format: str = 'markdown'):
        """Generate documentation."""
        # Get templates directory
        templates_dir = Path(__file__).parent / 'templates'
        
        # Create environment with FileSystemLoader
        env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            trim_blocks=False,
            lstrip_blocks=False
        )
        
        def format_rtl_statement(stmt):
            return self._format_rtl_statement(stmt)
        
        # Load template from file
        template = env.get_template('documentation.j2')
        code = template.render(isa=self.isa, format_rtl_statement=format_rtl_statement)
        
        ext = 'md' if format == 'markdown' else 'html'
        output_file = Path(output_path) / f'isa_documentation.{ext}'
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(code)
        
        return output_file

