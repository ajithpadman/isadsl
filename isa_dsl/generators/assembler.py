"""Generator for assemblers."""

from jinja2 import Environment
from pathlib import Path
from typing import Dict, List, Tuple
from ..model.isa_model import ISASpecification, Instruction


ASSEMBLER_TEMPLATE = r'''"""
Generated assembler for {{ isa.name }}.

This assembler was automatically generated from the ISA specification.
"""

import re
import sys
from typing import Dict, List, Tuple, Optional


class Assembler:
    """Assembler for {{ isa.name }}."""

    def __init__(self):
        """Initialize the assembler."""
        self.labels: Dict[str, int] = {}
        self.symbols: Dict[str, int] = {}
        self.instructions: List[Tuple[str, List[str], Optional[int]]] = []

    def assemble(self, source: str, start_address: int = 0) -> List[int]:
        """
        Assemble source code to machine code.

        Args:
            source: Assembly source code
            start_address: Starting address for code

        Returns:
            List of instruction words
        """
        lines = self._preprocess(source)
        
        # First pass: collect labels and determine instruction widths
        address = start_address
        for line in lines:
            label_match = re.match(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', line)
            if label_match:
                label = label_match.group(1)
                self.labels[label] = address
                line = re.sub(r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*:', '', line).strip()
            
            if line and not line.startswith('#'):
                # Check if it's an instruction
                if self._is_instruction_line(line):
                    self.instructions.append((line, address))
                    # Determine instruction width based on mnemonic
                    instruction_width = self._get_instruction_width_from_line(line)
                    address += instruction_width

        # Second pass: assemble instructions
        machine_code = []
        for line, addr in self.instructions:
            instruction = self._assemble_instruction(line, addr)
            if instruction is not None:
                machine_code.append(instruction)

        return machine_code

    def _preprocess(self, source: str) -> List[str]:
        """Preprocess source code."""
        lines = []
        for line in source.split('\n'):
            # Remove comments
            if '#' in line:
                line = line[:line.index('#')]
            line = line.strip()
            if line:
                lines.append(line)
        return lines

    def _is_instruction_line(self, line: str) -> bool:
        """Check if a line contains an instruction."""
        # Check for bundle syntax: bundle{...}
        if line.strip().upper().startswith('BUNDLE{'):
            return True
        parts = line.split()
        if not parts:
            return False
        mnemonic = parts[0].upper()
        return mnemonic in self._get_instruction_mnemonics()

    def _get_instruction_mnemonics(self) -> List[str]:
        """Get list of valid instruction mnemonics."""
        return [
{%- for instr in isa.instructions %}
            '{{ instr.mnemonic.upper() }}',
{%- endfor %}
        ]

    def _get_instruction_width_from_line(self, line: str) -> int:
        """Determine instruction width in bytes from assembly line."""
        line_stripped = line.strip()
        
        # Check for bundle syntax
        if line_stripped.upper().startswith('BUNDLE{'):
            # Find the widest bundle format
            {%- set max_bundle_width = 4 %}
            {%- for instr in isa.instructions %}
            {%- if instr.is_bundle() and instr.bundle_format %}
            {%- set bundle_bytes = (instr.bundle_format.width // 8) %}
            {%- if bundle_bytes > max_bundle_width %}
            {%- set max_bundle_width = bundle_bytes %}
            {%- endif %}
            {%- endif %}
            {%- endfor %}
            return {{ max_bundle_width }}
        
        # Extract mnemonic
        parts = line_stripped.split()
        if not parts:
            return 4  # Default
        
        mnemonic = parts[0].upper()
        
        # Look up instruction width by mnemonic
        {%- for instr in isa.instructions %}
        {%- if not instr.is_bundle() %}
        if mnemonic == '{{ instr.mnemonic.upper() }}':
            {%- if instr.format %}
            return ({{ instr.format.width }} + 7) // 8  # Convert bits to bytes
            {%- elif instr.bundle_format %}
            return ({{ instr.bundle_format.width }} + 7) // 8
            {%- else %}
            return 4  # Default
            {%- endif %}
        {%- endif %}
        {%- endfor %}
        
        return 4  # Default width

    def _assemble_instruction(self, line: str, address: int) -> Optional[int]:
        """Assemble a single instruction line."""
        # Check for bundle syntax: bundle{instr1, instr2, ...}
        line_stripped = line.strip()
        if line_stripped.upper().startswith('BUNDLE{'):
            return self._assemble_bundle(line_stripped, address)
        
        parts = line.split()
        if not parts:
            return None

        mnemonic = parts[0].upper()
        operands = parts[1:] if len(parts) > 1 else []

        # Parse operands
        parsed_operands = []
        for op in operands:
            op = op.strip(',').strip()
            # Handle immediate values
            if op.startswith('0x') or op.startswith('0X'):
                parsed_operands.append(int(op, 16))
            elif op.startswith('0b') or op.startswith('0B'):
                parsed_operands.append(int(op, 2))
            elif op.isdigit() or (op.startswith('-') and op[1:].isdigit()):
                parsed_operands.append(int(op))
            elif op in self.labels:
                # Label reference
                label_addr = self.labels[op]
                offset = (label_addr - address - 4) // 4  # PC-relative
                parsed_operands.append(offset)
            elif op in self.symbols:
                parsed_operands.append(self.symbols[op])
            else:
                # Assume it's a register name or operand name
                parsed_operands.append(op)

        return self._encode_instruction(mnemonic, parsed_operands)
    
    def _assemble_bundle(self, line: str, address: int) -> Optional[int]:
        """Assemble a bundle instruction: bundle{instr1, instr2, ...}."""
        import re
        # Extract bundle contents: bundle{...}
        match = re.match(r'bundle\s*\{([^}]+)\}', line, re.IGNORECASE)
        if not match:
            return None
        
        bundle_content = match.group(1).strip()
        
        # Get list of instruction mnemonics to identify instruction boundaries
        instruction_mnemonics = self._get_instruction_mnemonics()
        
        # Split by finding instruction mnemonics
        # Pattern: look for instruction mnemonic followed by operands until next mnemonic or end
        instructions = []
        parts = re.split(r',\s*(?=' + '|'.join([re.escape(m) for m in instruction_mnemonics]) + r'\b)', bundle_content, flags=re.IGNORECASE)
        
        # Group parts that belong to the same instruction
        current_instruction = None
        for part in parts:
            part = part.strip()
            # Check if this part starts with an instruction mnemonic
            is_mnemonic = False
            for mnemonic in instruction_mnemonics:
                if part.upper().startswith(mnemonic.upper()):
                    # This is a new instruction
                    if current_instruction:
                        instructions.append(current_instruction)
                    current_instruction = part
                    is_mnemonic = True
                    break
            
            if not is_mnemonic and current_instruction:
                # This is a continuation of the current instruction (operand)
                current_instruction += ', ' + part
        
        if current_instruction:
            instructions.append(current_instruction)
        
        # Assemble each instruction
        instruction_words = []
        for instr_line in instructions:
            if instr_line:
                instr_word = self._assemble_instruction(instr_line, address)
                if instr_word is not None:
                    instruction_words.append(instr_word)
        
        # Find bundle instruction that can contain these
{%- for instr in isa.instructions %}
        {%- if instr.is_bundle() %}
        if len(instruction_words) == {{ instr.bundle_format.slots|length if instr.bundle_format else 0 }}:
            return self._encode_bundle_{{ instr.mnemonic }}(instruction_words)
        {%- endif %}
{%- endfor %}
        
        return None

    def _encode_instruction(self, mnemonic: str, operands: List) -> Optional[int]:
        """Encode an instruction with operands."""
{%- for instr in isa.instructions %}
        if mnemonic == '{{ instr.mnemonic.upper() }}':
            return self._encode_{{ instr.mnemonic }}(operands)
{%- endfor %}
        return None

{%- for instr in isa.instructions %}
    def _encode_{{ instr.mnemonic }}(self, operands: List) -> Optional[int]:
        """Encode {{ instr.mnemonic }} instruction."""
        {%- if instr.format %}
        instruction = 0
        
        {%- if instr.encoding %}
        # Set encoding fields
        {%- for assignment in instr.encoding.assignments %}
        {%- set field = instr.format.get_field(assignment.field) %}
        {%- if field %}
        instruction |= ({{ assignment.value }} << {{ field.lsb }}) & {{ field.mask() }}
        {%- endif %}
        {%- endfor %}
        {%- endif %}
        
        # Set operand fields
        {%- for i, op_spec in enumerate(instr.operand_specs if instr.operand_specs else []) %}
        {%- if op_spec.is_distributed() %}
        # Distributed operand: {{ op_spec.name }} across fields {{ op_spec.field_names }}
        if len(operands) > {{ i }}:
            value = operands[{{ i }}]
            if isinstance(value, str):
                value = self._resolve_register(value)
            # Split value across distributed fields
            {%- set current_bit = 0 %}
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
            {{ field_name }}_part = (value >> {{ current_bit }}) & ((1 << {{ field.width() }}) - 1)
            instruction |= ({{ field_name }}_part << {{ field.lsb }})
            {%- endif %}
            {%- endfor %}
        {%- else %}
        # Simple operand: {{ op_spec.name }}
        {%- set field = instr.format.get_field(op_spec.name) %}
        {%- if field %}
        if len(operands) > {{ i }}:
            value = operands[{{ i }}]
            if isinstance(value, str):
                value = self._resolve_register(value)
            instruction |= (value & {{ field.width() | mask }}) << {{ field.lsb }}
        {%- endif %}
        {%- endif %}
        {%- endfor %}
        {%- if not instr.operand_specs %}
        # Legacy: use operands list
        {%- for i, operand in enumerate(instr.operands) %}
        {%- set field = instr.format.get_field(operand) %}
        {%- if field %}
        if len(operands) > {{ i }}:
            value = operands[{{ i }}]
            if isinstance(value, str):
                value = self._resolve_register(value)
            instruction |= (value & {{ field.width() | mask }}) << {{ field.lsb }}
        {%- endif %}
        {%- endfor %}
        {%- endif %}
        
        return instruction
        {%- else %}
        return 0
        {%- endif %}

{%- endfor %}
{%- for instr in isa.instructions %}
    {%- if instr.is_bundle() %}
    def _encode_bundle_{{ instr.mnemonic }}(self, instruction_words: List[int]) -> Optional[int]:
        """Encode {{ instr.mnemonic }} bundle instruction."""
        {%- if instr.bundle_format %}
        bundle_word = 0
        
        {%- if instr.encoding %}
        # Set bundle encoding fields FIRST (use instr.format, not bundle_format)
        {%- for assignment in instr.encoding.assignments %}
        {%- if instr.format %}
        {%- set field = instr.format.get_field(assignment.field) %}
        {%- if field %}
        bundle_word |= ({{ assignment.value }} & {{ field.width() | mask }}) << {{ field.lsb }}
        {%- endif %}
        {%- endif %}
        {%- endfor %}
        {%- endif %}
        
        {%- for slot in instr.bundle_format.slots %}
        {%- set slot_idx = loop.index0 %}
        if len(instruction_words) > {{ slot_idx }}:
            # Encode instruction into {{ slot.name }} slot
            # Slot position is already defined in bundle_format, so use slot.lsb directly
            bundle_word |= (instruction_words[{{ slot_idx }}] & {{ slot | slot_mask }}) << {{ slot.lsb }}
        {%- endfor %}
        
        return bundle_word
        {%- else %}
        return 0
        {%- endif %}

    {%- endif %}
{%- endfor %}
    def _resolve_register(self, name: str) -> int:
        """Resolve a register name to a number."""
        # Handle register names like R0, R1, etc.
        if name.upper().startswith('R') and name[1:].isdigit():
            return int(name[1:])
        # Add more register name resolution as needed
        return 0

    def _determine_instruction_width(self, instruction_word: int) -> int:
        """Determine instruction width in bytes by matching encoding."""
        # Strategy: Check instructions from shortest to longest width
        # to avoid false matches (e.g., 16-bit instruction matching 32-bit pattern)
        
        # Get all instruction widths, sorted shortest first
        {%- set all_widths = [] %}
        {%- for instr in isa.instructions %}
        {%- if instr.format %}
        {%- set _ = all_widths.append((instr.format.width, 'format')) %}
        {%- endif %}
        {%- if instr.bundle_format %}
        {%- set _ = all_widths.append((instr.bundle_format.width, 'bundle')) %}
        {%- endif %}
        {%- endfor %}
        {%- set unique_widths = [] %}
        {%- for width_tuple in all_widths %}
        {%- if width_tuple[0] not in unique_widths %}
        {%- set _ = unique_widths.append(width_tuple[0]) %}
        {%- endif %}
        {%- endfor %}
        {%- set unique_widths = unique_widths | sort %}
        
        # Try each width category (shortest first)
        {%- for width in unique_widths %}
        # Check instructions with width {{ width }} bits
        # First, mask instruction_word to this width to avoid false matches
        {%- if width == 16 %}
        masked_word = instruction_word & 0xFFFF
        {%- elif width == 32 %}
        masked_word = instruction_word & 0xFFFFFFFF
        {%- elif width == 64 %}
        masked_word = instruction_word & 0xFFFFFFFFFFFFFFFF
        {%- else %}
        # Calculate mask for {{ width }} bits
        width_mask_{{ width }} = (1 << {{ width }}) - 1
        masked_word = instruction_word & width_mask_{{ width }}
        {%- endif %}
        
        {%- for instr in isa.instructions %}
        {%- if (instr.format and instr.format.width == width) or (instr.bundle_format and instr.bundle_format.width == width) %}
        {%- if instr.format and instr.encoding %}
        {%- set id_fields = instr.format.get_identification_fields() %}
        {%- if id_fields %}
        # Check {{ instr.mnemonic }} using identification fields
        {%- set match_conditions = [] %}
        {%- for id_field in id_fields %}
        {%- set encoding_assignment = None %}
        {%- for assignment in instr.encoding.assignments %}
        {%- if assignment.field == id_field.name %}
        {%- set encoding_assignment = assignment %}
        {%- endif %}
        {%- endfor %}
        {%- if encoding_assignment %}
        {%- set condition_str = '(masked_word >> ' ~ id_field.lsb ~ ') & ' ~ (id_field.width() | mask) ~ ' == ' ~ encoding_assignment.value %}
        {%- set _ = match_conditions.append(condition_str) %}
        {%- endif %}
        {%- endfor %}
        {%- if match_conditions %}
        if {{ match_conditions | join(' and ') }}:
            {%- if instr.bundle_format %}
            return ({{ instr.bundle_format.width }} + 7) // 8
            {%- else %}
            return ({{ instr.format.width }} + 7) // 8
            {%- endif %}
        {%- endif %}
        {%- else %}
        # Check {{ instr.mnemonic }} using all encoding fields
        {%- set match_conditions = [] %}
        {%- for assignment in instr.encoding.assignments %}
        {%- set field = instr.format.get_field(assignment.field) %}
        {%- if field %}
        {%- set condition_str = '(masked_word >> ' ~ field.lsb ~ ') & ' ~ (field.width() | mask) ~ ' == ' ~ assignment.value %}
        {%- set _ = match_conditions.append(condition_str) %}
        {%- endif %}
        {%- endfor %}
        {%- if match_conditions %}
        if {{ match_conditions | join(' and ') }}:
            {%- if instr.bundle_format %}
            return ({{ instr.bundle_format.width }} + 7) // 8
            {%- else %}
            return ({{ instr.format.width }} + 7) // 8
            {%- endif %}
        {%- endif %}
        {%- endif %}
        {%- endif %}
        {%- endif %}
        {%- endfor %}
        {%- endfor %}
        
        # Default: assume 32-bit (4 bytes)
        return 4

    def write_binary(self, machine_code: List[int], filename: str):
        """Write machine code to a binary file, handling variable-length instructions."""
        with open(filename, 'wb') as f:
            for word in machine_code:
                # Determine instruction width
                instruction_width_bytes = self._determine_instruction_width(word)
                
                # Write instruction with correct width
                if instruction_width_bytes <= 4:
                    # 16-bit or 32-bit instruction - write as bytes
                    for i in range(instruction_width_bytes):
                        byte_val = (word >> (i * 8)) & 0xFF
                        f.write(byte_val.to_bytes(1, byteorder='little'))
                else:
                    # Wide instruction (> 32 bits) - write as multiple 32-bit words
                    words_needed = (instruction_width_bytes + 3) // 4
                    for i in range(words_needed):
                        word_part = (word >> (i * 32)) & 0xFFFFFFFF
                        f.write(word_part.to_bytes(4, byteorder='little'))


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: assembler.py <input.asm> <output.bin>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, 'r') as f:
        source = f.read()

    assembler = Assembler()
    machine_code = assembler.assemble(source)
    assembler.write_binary(machine_code, output_file)
    
    print(f"Assembled {len(machine_code)} instructions to {output_file}")


if __name__ == "__main__":
    main()
'''


class AssemblerGenerator:
    """Generates assemblers from ISA specifications."""

    def __init__(self, isa: ISASpecification):
        self.isa = isa

    def generate(self, output_path: str):
        """Generate the assembler code."""
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
        
        template = env.from_string(ASSEMBLER_TEMPLATE)
        code = template.render(isa=self.isa)
        
        output_file = Path(output_path) / 'assembler.py'
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(code)
        
        return output_file

