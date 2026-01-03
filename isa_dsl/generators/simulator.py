"""Generator for Python-based instruction simulators."""

from jinja2 import Environment
from pathlib import Path
from typing import Dict, Any
from ..model.isa_model import ISASpecification


SIMULATOR_TEMPLATE = '''"""
Generated instruction simulator for {{ isa.name }}.

This simulator was automatically generated from the ISA specification.
"""

from typing import Dict, List, Optional
import sys


class Simulator:
    """Instruction simulator for {{ isa.name }}."""

    def __init__(self):
        """Initialize the simulator state."""
        # Initialize registers
{%- for reg in isa.registers %}
        {%- if reg.is_vector_register() %}
        self.{{ reg.name }} = [[0] * {{ reg.lanes }} for _ in range({{ reg.count if reg.count else 1 }})]
        {%- elif reg.is_register_file() %}
        self.{{ reg.name }} = [0] * {{ reg.count }}
        {%- else %}
        self.{{ reg.name }} = 0
        {%- endif %}
{%- endfor %}
        
        # Memory
        self.memory: Dict[int, int] = {}
        
        # Execution state
        self.pc = 0
        self.halted = False
        self.instruction_count = 0

    def load_program(self, program: List[int], start_address: int = 0):
        """Load a program into memory."""
        for i, instruction in enumerate(program):
            self.memory[start_address + i * 4] = instruction
        self.pc = start_address

    def load_binary_file(self, filename: str, start_address: int = 0):
        """Load a binary file into memory."""
        with open(filename, 'rb') as f:
            data = f.read()
            address = start_address
            i = 0
            while i < len(data):
                if i + 4 <= len(data):
                    word = int.from_bytes(data[i:i+4], byteorder='little')
                    self.memory[address] = word
                    address += 4
                    i += 4
                else:
                    # Handle partial word at end of file
                    remaining_bytes = len(data) - i
                    if remaining_bytes > 0:
                        # Pad with zeros to make a complete word
                        word_bytes = bytearray(data[i:])
                        word_bytes.extend([0] * (4 - remaining_bytes))
                        word = int.from_bytes(bytes(word_bytes), byteorder='little')
                        self.memory[address] = word
                    break
        self.pc = start_address

    def step(self) -> bool:
        """Execute one instruction. Returns True if execution continues."""
        if self.halted:
            return False

        # Fetch instruction - check if it's a bundle (64-bit) or regular (32-bit)
        # First, try to fetch as 64-bit bundle
        {%- set max_bundle_width = 4 %}
        {%- for instr in isa.instructions %}
        {%- if instr.is_bundle() and instr.bundle_format %}
        {%- set bundle_bytes = (instr.bundle_format.width // 8) %}
        {%- if bundle_bytes > max_bundle_width %}
        {%- set max_bundle_width = bundle_bytes %}
        {%- endif %}
        {%- endif %}
        {%- endfor %}
        {%- if max_bundle_width > 4 %}
        # Check for wide bundle (64-bit, 80-bit, etc.)
        {%- set bundle_words_needed = (max_bundle_width + 3) // 4 %}
        bundle_available = True
        bundle_word = 0
        for i in range({{ bundle_words_needed }}):
            if self.pc + i * 4 not in self.memory:
                bundle_available = False
                break
            bundle_word |= (self.memory[self.pc + i * 4] << (i * 32))
        
        if bundle_available:
            # Check if this matches a bundle encoding
            {%- for instr in isa.instructions %}
            {%- if instr.is_bundle() %}
            if self._matches_{{ instr.mnemonic }}(bundle_word):
                self._execute_{{ instr.mnemonic }}(bundle_word)
                self.instruction_count += 1
                return True
            {%- endif %}
            {%- endfor %}
        {%- endif %}
        
        # Fetch as 32-bit instruction
        if self.pc not in self.memory:
            self.halted = True
            return False

        instruction_word = self.memory[self.pc]
        self.instruction_count += 1

        # Decode and execute
        executed = self._execute_instruction(instruction_word)
        
        if not executed:
            print(f"Unknown instruction at PC=0x{self.pc:08x}: 0x{instruction_word:08x}")
            self.halted = True
            return False

        return True

    def run(self, max_steps: int = 10000):
        """Run the simulator until halt or max_steps."""
        steps = 0
        while steps < max_steps and self.step():
            steps += 1

        if steps >= max_steps:
            print(f"Reached maximum step count ({max_steps})")

    def _execute_instruction(self, instruction_word: int) -> bool:
        """Execute a single instruction word."""
        # First, check if this is a bundle instruction
{%- for instr in isa.instructions %}
        {%- if instr.is_bundle() %}
        if self._matches_{{ instr.mnemonic }}(instruction_word):
            self._execute_{{ instr.mnemonic }}(instruction_word)
            return True
        {%- endif %}
{%- endfor %}
        
        # If not a bundle, try regular instructions
{%- for instr in isa.instructions %}
        {%- if not instr.is_bundle() %}
        {%- if instr.matches_encoding %}
        # Check {{ instr.mnemonic }}
        if self._matches_{{ instr.mnemonic }}(instruction_word):
            self._execute_{{ instr.mnemonic }}(instruction_word)
            return True
        {%- else %}
        # {{ instr.mnemonic }}
        if self._matches_{{ instr.mnemonic }}(instruction_word):
            self._execute_{{ instr.mnemonic }}(instruction_word)
            return True
        {%- endif %}
        {%- endif %}
{%- endfor %}
        return False

{%- for instr in isa.instructions %}
    def _matches_{{ instr.mnemonic }}(self, instruction_word: int) -> bool:
        """Check if instruction word matches {{ instr.mnemonic }} encoding."""
        {%- if instr.is_bundle() %}
        # Bundle instruction - check encoding using format (not bundle_format)
        {%- if instr.format and instr.encoding %}
        {%- for assignment in instr.encoding.assignments %}
        {%- set field = instr.format.get_field(assignment.field) %}
        {%- if field %}
        # Check {{ assignment.field }} == {{ assignment.value }}
        if (instruction_word >> {{ field.lsb }}) & {{ field.width() | mask }} != {{ assignment.value }}:
            return False
        {%- endif %}
        {%- endfor %}
        return True
        {%- else %}
        return False
        {%- endif %}
        {%- elif instr.format and instr.encoding %}
        {%- for assignment in instr.encoding.assignments %}
        {%- set field = instr.format.get_field(assignment.field) %}
        {%- if field %}
        # Check {{ assignment.field }} == {{ assignment.value }}
        if (instruction_word >> {{ field.lsb }}) & {{ field.width() | mask }} != {{ assignment.value }}:
            return False
        {%- endif %}
        {%- endfor %}
        return True
        {%- else %}
        return False
        {%- endif %}

    def _execute_{{ instr.mnemonic }}(self, instruction_word: int):
        """Execute {{ instr.mnemonic }} instruction."""
        {%- if instr.is_bundle() %}
        # Bundle instruction - extract and execute sub-instructions
        {%- if instr.bundle_format %}
        # Extract sub-instructions from bundle
        # Instructions start at instruction_start bit position
        {%- for slot in instr.bundle_format.slots %}
        {{ slot.name }}_word = (instruction_word >> {{ slot.lsb }}) & {{ slot | slot_mask }}
        {%- endfor %}
        
        # Execute each sub-instruction in sequence
        # Note: We execute sub-instructions directly without checking for bundles again
        # to avoid recursion. Sub-instructions are regular instructions, not bundles.
        # Save PC before executing bundle slots (instructions in bundles shouldn't update PC)
        saved_pc = self.pc
        {%- for slot in instr.bundle_format.slots %}
        {%- set slot_idx = loop.index0 %}
        # Execute instruction in {{ slot.name }} slot (direct execution, skip bundle check)
        {%- if instr.bundle_instructions %}
        # Try to match against bundle instructions in order
        # Match slot {{ slot_idx }} with instruction at index {{ slot_idx }}
        slot_{{ slot.name }}_matched = False
        {%- if slot_idx < (instr.bundle_instructions|length) %}
        {%- set sub_instr = instr.bundle_instructions[slot_idx] %}
        if self._matches_{{ sub_instr.mnemonic }}({{ slot.name }}_word):
            # Save PC before executing (instruction will update it, but we'll restore)
            self.pc = saved_pc
            self._execute_{{ sub_instr.mnemonic }}({{ slot.name }}_word)
            saved_pc = self.pc  # Update saved PC after execution
            slot_{{ slot.name }}_matched = True
        {%- endif %}
        # If no match, try other bundle instructions as fallback
        if not slot_{{ slot.name }}_matched:
            {%- for sub_instr in instr.bundle_instructions %}
            {%- if loop.index0 != slot_idx %}
            if not slot_{{ slot.name }}_matched and self._matches_{{ sub_instr.mnemonic }}({{ slot.name }}_word):
                # Save PC before executing (instruction will update it, but we'll restore)
                self.pc = saved_pc
                self._execute_{{ sub_instr.mnemonic }}({{ slot.name }}_word)
                saved_pc = self.pc  # Update saved PC after execution
                slot_{{ slot.name }}_matched = True
            {%- endif %}
            {%- endfor %}
        {%- else %}
        # No bundle instructions specified, try regular execution
        self.pc = saved_pc
        self._execute_instruction({{ slot.name }}_word)
        saved_pc = self.pc
        {%- endif %}
        {%- endfor %}
        # Restore PC to value before bundle execution (will be updated by bundle width below)
        self.pc = saved_pc
        
        # Update PC by bundle width (not individual instruction width)
        # Bundle is stored as multiple 32-bit words in memory
        {%- set bundle_words = (instr.bundle_format.width + 31) // 32 %}
        self.pc += {{ bundle_words * 4 }}
        {%- else %}
        self.pc += 4
        {%- endif %}
        {%- elif instr.format %}
        # Decode operands
        {%- for op_spec in (instr.operand_specs if instr.operand_specs else []) %}
        {%- if op_spec.is_distributed() %}
        # Distributed operand: {{ op_spec.name }} from fields {{ op_spec.field_names }}
        {{ op_spec.name }} = 0
        {%- for field_idx, field_name in enumerate(op_spec.field_names) %}
        {%- set field = instr.format.get_field(field_name) %}
        {%- if field %}
        {%- if field_idx > 0 %}
        {%- set prev_widths = [] %}
        {%- for prev_idx in range(field_idx) %}
        {%- set prev_field = instr.format.get_field(op_spec.field_names[prev_idx]) %}
        {%- if prev_field %}
        {%- set _ = prev_widths.append(prev_field.width()) %}
        {%- endif %}
        {%- endfor %}
        {%- set current_bit = prev_widths | sum %}
        {%- else %}
        {%- set current_bit = 0 %}
        {%- endif %}
        {{ op_spec.name }} |= ((instruction_word >> {{ field.lsb }}) & {{ field.width() | mask }}) << {{ current_bit }}
        {%- endif %}
        {%- endfor %}
        {%- else %}
        # Simple operand: {{ op_spec.name }}
        {%- set field = instr.format.get_field(op_spec.name) %}
        {%- if field %}
        {{ op_spec.name }} = (instruction_word >> {{ field.lsb }}) & {{ field.width() | mask }}
        {%- endif %}
        {%- endif %}
        {%- endfor %}
        {%- if not instr.operand_specs %}
        # Legacy: use operands list
        {%- for operand in instr.operands %}
        {%- set field = instr.format.get_field(operand) %}
        {%- if field %}
        {{ operand }} = (instruction_word >> {{ field.lsb }}) & {{ field.width() | mask }}
        {%- endif %}
        {%- endfor %}
        {%- endif %}
        
        # Execute behavior
        {%- if instr.behavior %}
        {%- for stmt in instr.behavior.statements %}
{{ generate_rtl_code(stmt, instr) }}
        {%- endfor %}
        {%- endif %}
        
        # Update PC
        self.pc += 4
        {%- else %}
        # No format defined
        self.pc += 4
        {%- endif %}

{%- endfor %}
    def print_state(self):
        """Print the current simulator state."""
        print("=== Simulator State ===")
        print(f"PC: 0x{self.pc:08x}")
        print(f"Instructions executed: {self.instruction_count}")
        print("\\nRegisters:")
{%- for reg in isa.registers %}
        {%- if reg.is_vector_register() %}
        for i in range({{ reg.count if reg.count else 1 }}):
            print(f"  {{ reg.name }}[{i}]: ", end="")
            for lane in range({{ reg.lanes }}):
                print(f"[{lane}]=0x{self.{{ reg.name }}[i][lane]:08x} ", end="")
            print()
        {%- elif reg.is_register_file() %}
        for i in range({{ reg.count }}):
            print(f"  {{ reg.name }}[{i}]: 0x{self.{{ reg.name }}[i]:08x}")
        {%- else %}
        print(f"  {{ reg.name }}: 0x{self.{{ reg.name }}:08x}")
        {%- endif %}
{%- endfor %}
        print()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: simulator.py <binary_file> [start_address]")
        sys.exit(1)

    filename = sys.argv[1]
    start_address = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0

    sim = Simulator()
    sim.load_binary_file(filename, start_address)
    
    print("Starting simulation...")
    sim.run()
    sim.print_state()


if __name__ == "__main__":
    main()
'''


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
            return f"self.{lvalue}"
        
        if isinstance(lvalue, RegisterAccess):
            index = self._generate_expr_code(lvalue.index)
            return f"self.{lvalue.reg_name}[{index}]"
        elif isinstance(lvalue, FieldAccess):
            return f"self.{lvalue.reg_name}_{lvalue.field_name}"
        return "unknown"

    def _generate_expr_code(self, expr) -> str:
        """Generate code for an expression."""
        from ..model.isa_model import (
            RTLConstant, RegisterAccess, RTLBinaryOp, RTLUnaryOp,
            RTLTernary, FieldAccess, OperandReference
        )
        
        if isinstance(expr, RTLConstant):
            return str(expr.value)
        elif isinstance(expr, OperandReference):
            # Operand references are variable names in the generated code
            return expr.name
        elif isinstance(expr, RegisterAccess):
            index = self._generate_expr_code(expr.index)
            return f"self.{expr.reg_name}[{index}]"
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
            # Simple register name or operand reference as string
            return expr
        return "0"

    def generate(self, output_path: str):
        """Generate the simulator code."""
        from jinja2 import Environment
        
        env = Environment()
        
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
        
        template = env.from_string(SIMULATOR_TEMPLATE)
        
        # Create a function that can be called from template
        def generate_rtl_code(stmt, instruction):
            return self._generate_rtl_code(stmt)
        
        code = template.render(isa=self.isa, generate_rtl_code=generate_rtl_code)
        
        output_file = Path(output_path) / 'simulator.py'
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(code)
        
        return output_file

