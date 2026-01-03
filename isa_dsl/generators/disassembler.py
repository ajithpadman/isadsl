"""Generator for disassemblers."""

from jinja2 import Environment
from pathlib import Path
from ..model.isa_model import ISASpecification


DISASSEMBLER_TEMPLATE = '''"""
Generated disassembler for {{ isa.name }}.

This disassembler was automatically generated from the ISA specification.
"""

import sys
from typing import List, Optional, Tuple


class Disassembler:
    """Disassembler for {{ isa.name }}."""

    def __init__(self):
        """Initialize the disassembler."""
        pass

    def disassemble(self, instruction_word: int) -> Optional[str]:
        """
        Disassemble a single instruction word.

        Args:
            instruction_word: 32-bit instruction word

        Returns:
            Assembly mnemonic string or None if unknown
        """
{%- for instr in isa.instructions %}
        result = self._disassemble_{{ instr.mnemonic }}(instruction_word)
        if result is not None:
            return result
{%- endfor %}
        return f"UNKNOWN 0x{instruction_word:08x}"

    def disassemble_file(self, filename: str, start_address: int = 0) -> List[Tuple[int, str]]:
        """
        Disassemble a binary file.

        Args:
            filename: Binary file path
            start_address: Starting address

        Returns:
            List of (address, instruction) tuples
        """
        instructions = []
        with open(filename, 'rb') as f:
            address = start_address
            while True:
                data = f.read(4)
                if len(data) < 4:
                    break
                instruction_word = int.from_bytes(data, byteorder='little')
                asm = self.disassemble(instruction_word)
                instructions.append((address, asm))
                address += 4
        return instructions

{%- for instr in isa.instructions %}
    def _disassemble_{{ instr.mnemonic }}(self, instruction_word: int) -> Optional[str]:
        """Disassemble {{ instr.mnemonic }} instruction."""
        {%- if instr.format and instr.encoding %}
        # Check if instruction matches encoding
        {%- for assignment in instr.encoding.assignments %}
        {%- set field = instr.format.get_field(assignment.field) %}
        {%- if field %}
        if (instruction_word >> {{ field.lsb }}) & {{ field.width() | mask }} != {{ assignment.value }}:
            return None
        {%- endif %}
        {%- endfor %}
        
        # Extract operands
        operands = []
        {%- for op_spec in (instr.operand_specs if instr.operand_specs else []) %}
        {%- if op_spec.is_distributed() %}
        # Distributed operand: {{ op_spec.name }} from fields {{ op_spec.field_names }}
        {{ op_spec.name }}_val = 0
        {%- set current_bit = 0 %}
        {%- for field_name in op_spec.field_names %}
        {%- set field = instr.format.get_field(field_name) %}
        {%- if field %}
        {{ op_spec.name }}_val |= ((instruction_word >> {{ field.lsb }}) & {{ field.width() | mask }}) << {{ current_bit }}
        {%- set current_bit = current_bit + field.width() %}
        {%- endif %}
        {%- endfor %}
        operands.append(str({{ op_spec.name }}_val))
        {%- else %}
        # Simple operand: {{ op_spec.name }}
        {%- set field = instr.format.get_field(op_spec.name) %}
        {%- if field %}
        {{ op_spec.name }}_val = (instruction_word >> {{ field.lsb }}) & {{ field.width() | mask }}
        operands.append(str({{ op_spec.name }}_val))
        {%- endif %}
        {%- endif %}
        {%- endfor %}
        {%- if not instr.operand_specs %}
        # Legacy: use operands list
        {%- for operand in instr.operands %}
        {%- set field = instr.format.get_field(operand) %}
        {%- if field %}
        {{ operand }}_val = (instruction_word >> {{ field.lsb }}) & {{ field.width() | mask }}
        operands.append(str({{ operand }}_val))
        {%- endif %}
        {%- endfor %}
        {%- endif %}
        
        if operands:
            return "{{ instr.mnemonic.upper() }} " + ", ".join(operands)
        else:
            return "{{ instr.mnemonic.upper() }}"
        {%- else %}
        return None
        {%- endif %}

{%- endfor %}


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: disassembler.py <binary_file> [start_address]")
        sys.exit(1)

    filename = sys.argv[1]
    start_address = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0

    disasm = Disassembler()
    instructions = disasm.disassemble_file(filename, start_address)
    
    for address, asm in instructions:
        print(f"0x{address:08x}: {asm}")


if __name__ == "__main__":
    main()
'''


class DisassemblerGenerator:
    """Generates disassemblers from ISA specifications."""

    def __init__(self, isa: ISASpecification):
        self.isa = isa

    def generate(self, output_path: str):
        """Generate the disassembler code."""
        env = Environment()
        
        # Add custom filter for computing bit masks
        def mask_filter(width):
            if width is None or width < 0:
                return 0
            return (1 << width) - 1
        env.filters['mask'] = mask_filter
        
        template = env.from_string(DISASSEMBLER_TEMPLATE)
        code = template.render(isa=self.isa)
        
        output_file = Path(output_path) / 'disassembler.py'
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(code)
        
        return output_file

