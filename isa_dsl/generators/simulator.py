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
        """Execute one instruction with dynamic width loading. Returns True if execution continues."""
        if self.halted:
            return False

        # Step 1: Identify instruction by loading minimum bits and matching
        # Strategy: Try formats from shortest to longest
        # Collect all format widths and their minimum identification bits
        matched_mnemonic = None
        matched_width = None
        
        # Try each unique format width (sorted shortest first)
        {%- set all_widths = [] %}
        {%- for instr in isa.instructions %}
        {%- if instr.format %}
        {%- set _ = all_widths.append(instr.format.width) %}
        {%- endif %}
        {%- if instr.bundle_format %}
        {%- set _ = all_widths.append(instr.bundle_format.width) %}
        {%- endif %}
        {%- endfor %}
        {%- set unique_widths = [] %}
        {%- for width in all_widths %}
        {%- if width not in unique_widths %}
        {%- set _ = unique_widths.append(width) %}
        {%- endif %}
        {%- endfor %}
        {%- set unique_widths = unique_widths | sort %}
        
        {%- for width in unique_widths %}
        if matched_mnemonic is None:
            # Find minimum bits needed for this width category
            {%- set min_bits_list = [] %}
            {%- for instr in isa.instructions %}
            {%- if instr.format and instr.format.width == width %}
            {%- set min_bits = instr.format.get_minimum_bits_for_identification() %}
            {%- set _ = min_bits_list.append(min_bits) %}
            {%- endif %}
            {%- if instr.bundle_format and instr.bundle_format.width == width %}
            {%- if instr.format %}
            {%- set min_bits = instr.format.get_minimum_bits_for_identification() %}
            {%- else %}
            {%- set min_bits = 32 %}
            {%- endif %}
            {%- set _ = min_bits_list.append(min_bits) %}
            {%- endif %}
            {%- endfor %}
            {%- if min_bits_list %}
            min_bits = min([{{ min_bits_list | join(', ') }}])
            peeked_bits = self._load_bits(self.pc, min_bits)
            
            # Try to match instructions with this format width
            # Check instructions with more encoding fields first (more specific matches)
            {%- for instr in isa.instructions %}
            {%- if instr.format and instr.format.width == width %}
            if matched_mnemonic is None and self._matches_{{ instr.mnemonic }}(peeked_bits):
                matched_mnemonic = '{{ instr.mnemonic }}'
                matched_width = {{ width }}
            {%- endif %}
            {%- if instr.bundle_format and instr.bundle_format.width == width %}
            if matched_mnemonic is None and self._matches_{{ instr.mnemonic }}(peeked_bits):
                matched_mnemonic = '{{ instr.mnemonic }}'
                matched_width = {{ width }}
            {%- endif %}
            {%- endfor %}
            {%- endif %}
        {%- endfor %}
        
        if matched_mnemonic is None:
            self.halted = True
            return False
        
        # Step 2: Load full instruction based on matched width
        full_instruction = self._load_bits(self.pc, matched_width)
        
        # Step 3: Execute instruction
        executed = self._execute_instruction_by_mnemonic(full_instruction, matched_mnemonic)
        
        if not executed:
            print(f"Unknown instruction at PC=0x{self.pc:08x}: 0x{full_instruction:x}")
            self.halted = True
            return False
        
        # Step 4: Update PC by instruction width (in bytes)
        self.pc += (matched_width + 7) // 8
        self.instruction_count += 1
        return True

    def _execute_instruction_by_mnemonic(self, instruction_word: int, mnemonic: str) -> bool:
        """Execute instruction by mnemonic name."""
        {%- for instr in isa.instructions %}
        if mnemonic == '{{ instr.mnemonic }}':
            self._execute_{{ instr.mnemonic }}(instruction_word)
            return True
        {%- endfor %}
        return False

    def run(self, max_steps: int = 10000):
        """Run the simulator until halt or max_steps."""
        steps = 0
        while steps < max_steps and self.step():
            steps += 1

        if steps >= max_steps:
            print(f"Reached maximum step count ({max_steps})")

    def _load_bits(self, address: int, num_bits: int) -> int:
        """
        Load specified number of bits from memory starting at address.
        Handles instructions that span multiple word boundaries.
        
        Args:
            address: Starting address (byte-aligned)
            num_bits: Number of bits to load
            
        Returns:
            Integer value of loaded bits (little-endian)
        """
        num_bytes = (num_bits + 7) // 8
        value = 0
        for i in range(num_bytes):
            byte_addr = address + i
            # Memory stores 32-bit words, need to extract bytes
            word_addr = (byte_addr // 4) * 4
            byte_offset = byte_addr % 4
            if word_addr in self.memory:
                word = self.memory[word_addr]
                byte_val = (word >> (byte_offset * 8)) & 0xFF
                value |= (byte_val << (i * 8))
        # Mask to requested number of bits
        if num_bits < 64:
            return value & ((1 << num_bits) - 1)
        else:
            return value

    def _get_instruction_width(self, instruction) -> int:
        """Get the full width of an instruction in bits."""
        if hasattr(instruction, 'bundle_format') and instruction.bundle_format:
            return instruction.bundle_format.width
        elif hasattr(instruction, 'format') and instruction.format:
            return instruction.format.width
        else:
            return 32  # Default

    def _execute_instruction(self, instruction_word: int) -> bool:
        """Execute a single instruction word."""
        # First, check if this might be a wide bundle by checking the first byte
        # If it matches a bundle_opcode, construct the full bundle_word from memory
        # Calculate max bundle width
        {%- set bundle_widths = [] %}
        {%- for instr in isa.instructions %}
        {%- if instr.is_bundle() and instr.bundle_format %}
        {%- set bundle_bytes = (instr.bundle_format.width // 8) %}
        {%- set _ = bundle_widths.append(bundle_bytes) %}
        {%- endif %}
        {%- endfor %}
        {%- if bundle_widths %}
        {%- set max_bundle_width = bundle_widths | max %}
        {%- else %}
        {%- set max_bundle_width = 4 %}
        {%- endif %}
        {%- if max_bundle_width > 4 %}
        # Check if first byte matches any bundle_opcode - if so, load full bundle
        first_byte = instruction_word & 0xFF
        if first_byte == 255:
            # This might be a bundle - construct full bundle_word from memory
            {%- set bundle_words_needed = (max_bundle_width + 3) // 4 %}
            bundle_word_wide = 0
            wide_bundle_available = True
            for i in range({{ bundle_words_needed }}):
                addr = self.pc + i * 4
                if addr not in self.memory:
                    wide_bundle_available = False
                    break
                word_val = self.memory[addr]
                bundle_word_wide |= (word_val << (i * 32))
            
            if wide_bundle_available:
                {%- for instr in isa.instructions %}
                {%- if instr.is_bundle() %}
                if self._matches_{{ instr.mnemonic }}(bundle_word_wide):
                    self._execute_{{ instr.mnemonic }}(bundle_word_wide)
                    return True
                {%- endif %}
                {%- endfor %}
{%- endif %}
        # Check if this is a bundle instruction (using the 32-bit word) - only for small bundles
{%- for instr in isa.instructions %}
        {%- if instr.is_bundle() %}
        {%- if not instr.bundle_format or (instr.bundle_format.width // 8) <= 4 %}
        if self._matches_{{ instr.mnemonic }}(instruction_word):
            self._execute_{{ instr.mnemonic }}(instruction_word)
            return True
        {%- endif %}
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
        {%- set id_fields = instr.format.get_identification_fields() %}
        {%- if id_fields %}
        # Use identification fields: {{ id_fields | map(attribute='name') | join(', ') }}
        {%- for id_field in id_fields %}
        {%- set encoding_assignment = None %}
        {%- for assignment in instr.encoding.assignments %}
        {%- if assignment.field == id_field.name %}
        {%- set encoding_assignment = assignment %}
        {%- endif %}
        {%- endfor %}
        {%- if encoding_assignment %}
        # Check identification field {{ id_field.name }} == {{ encoding_assignment.value }}
        if (instruction_word >> {{ id_field.lsb }}) & {{ id_field.width() | mask }} != {{ encoding_assignment.value }}:
            return False
        {%- endif %}
        {%- endfor %}
        return True
        {%- else %}
        # No identification fields specified - use all encoding fields (backward compatible)
        {%- for assignment in instr.encoding.assignments %}
        {%- set field = instr.format.get_field(assignment.field) %}
        {%- if field %}
        # Check {{ assignment.field }} == {{ assignment.value }}
        if (instruction_word >> {{ field.lsb }}) & {{ field.width() | mask }} != {{ assignment.value }}:
            return False
        {%- endif %}
        {%- endfor %}
        return True
        {%- endif %}
        {%- else %}
        return False
        {%- endif %}
        {%- elif instr.format and instr.encoding %}
        # Always check ALL encoding fields to ensure exact match
        # (Identification fields are for quick filtering, but we need exact match)
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
        matches_{{ slot.name }}_{{ sub_instr.mnemonic }} = self._matches_{{ sub_instr.mnemonic }}({{ slot.name }}_word)
        if matches_{{ slot.name }}_{{ sub_instr.mnemonic }}:
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
            if not slot_{{ slot.name }}_matched:
                matches_fallback = self._matches_{{ sub_instr.mnemonic }}({{ slot.name }}_word)
                if matches_fallback:
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
        # Restore PC to value before bundle execution (step() will update PC by bundle width)
        self.pc = saved_pc
        {%- else %}
        # No bundle format - step() will update PC
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
        
        # Decode format fields that are not operands but may be used in behavior
        {%- set operand_names = [] %}
        {%- if instr.operand_specs %}
        {%- for op_spec in instr.operand_specs %}
        {%- if op_spec.is_distributed() %}
        {%- for field_name in op_spec.field_names %}
        {%- set _ = operand_names.append(field_name) %}
        {%- endfor %}
        {%- else %}
        {%- set _ = operand_names.append(op_spec.name) %}
        {%- endif %}
        {%- endfor %}
        {%- else %}
        {%- for operand in instr.operands %}
        {%- set _ = operand_names.append(operand) %}
        {%- endfor %}
        {%- endif %}
        {%- for field in instr.format.fields %}
        {%- if field.name not in operand_names %}
        # Decode format field {{ field.name }} (not an operand, but may be used in behavior)
        {{ field.name }} = (instruction_word >> {{ field.lsb }}) & {{ field.width() | mask }}
        {%- endif %}
        {%- endfor %}
        
        # Execute behavior
        {%- if instr.behavior %}
        {%- for stmt in instr.behavior.statements %}
{{ generate_rtl_code(stmt, instr) }}
        {%- endfor %}
        {%- endif %}
        
        # PC update is handled by step() method
        {%- else %}
        # No format defined - PC update is handled by step() method
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
            # Check if this is actually a register name (not an operand)
            # Register names are SFRs (single registers) defined in the ISA
            reg = self.isa.get_register(expr.name)
            if reg and not reg.is_register_file() and not reg.is_vector_register():
                # This is a simple register (SFR) like PC
                return f"self.{expr.name}"
            # Otherwise, it's an operand reference (variable name in generated code)
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
            # Simple register name - check if it's a register
            reg = self.isa.get_register(expr)
            if reg and not reg.is_register_file() and not reg.is_vector_register():
                return f"self.{expr}"
            # Otherwise treat as operand reference
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

