"""Generator for disassemblers."""

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from ..model.isa_model import ISASpecification

# Template is now loaded from file: isa_dsl/generators/templates/disassembler.j2
# Template is now loaded from file: isa_dsl/generators/templates/disassembler.j2



class DisassemblerGenerator:
    """Generates disassemblers from ISA specifications."""

    def __init__(self, isa: ISASpecification):
        self.isa = isa

    def generate(self, output_path: str):
        """Generate the disassembler code."""
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
        
        # Add utility functions for building condition strings
        def build_identification_condition(instr):
            """Build condition string for instruction using identification fields."""
            if not instr.format or not instr.encoding:
                return None
            
            id_fields = instr.format.get_identification_fields()
            if not id_fields:
                return None
            
            conditions = []
            for id_field in id_fields:
                # Find matching encoding assignment
                encoding_assignment = None
                for assignment in instr.encoding.assignments:
                    if assignment.field == id_field.name:
                        encoding_assignment = assignment
                        break
                
                if encoding_assignment:
                    field_width = id_field.width()
                    mask_val = (1 << field_width) - 1
                    condition = f'(masked_word >> {id_field.lsb}) & {mask_val} == {encoding_assignment.value}'
                    conditions.append(condition)
                else:
                    # Missing encoding assignment for identification field
                    return None
            
            return conditions if conditions else None
        
        def build_encoding_condition(instr):
            """Build condition string for instruction using all encoding fields."""
            if not instr.format or not instr.encoding:
                return None
            
            conditions = []
            for assignment in instr.encoding.assignments:
                field = instr.format.get_field(assignment.field)
                if field:
                    field_width = field.width()
                    mask_val = (1 << field_width) - 1
                    condition = f'(masked_word >> {field.lsb}) & {mask_val} == {assignment.value}'
                    conditions.append(condition)
            
            return conditions if conditions else None
        
        def get_width_mask_code(width):
            """Get Python code for masking instruction word to specified width."""
            if width == 16:
                return 'instruction_word & 0xFFFF'
            elif width == 32:
                return 'instruction_word & 0xFFFFFFFF'
            elif width == 64:
                return 'instruction_word & 0xFFFFFFFFFFFFFFFF'
            else:
                return f'instruction_word & ((1 << {width}) - 1)'
        
        def build_instruction_match_check(instr, width, var_name='masked_word'):
            """Build instruction matching check code for _identify_instruction_width."""
            if not instr.format or not instr.encoding:
                return None
            
            conditions = build_identification_condition(instr)
            if not conditions:
                conditions = build_encoding_condition(instr)
            
            if not conditions:
                return None
            
            # Replace 'masked_word' with the actual variable name
            conditions_str = ' and '.join([c.replace('masked_word', var_name) for c in conditions])
            return f"if {conditions_str}:\n            return {width}"
        
        def build_disassemble_match_checks(instr):
            """Build matching checks for _disassemble_* methods."""
            if not instr.format or not instr.encoding:
                return []
            
            checks = []
            
            # Check format constant fields first
            for field in instr.format.fields:
                if field.has_constant():
                    field_width = field.width()
                    mask_val = (1 << field_width) - 1
                    check = f"if (instruction_word >> {field.lsb}) & {mask_val} != {field.constant_value}:\n            return None"
                    checks.append(check)
            
            # Check identification fields or all encoding fields
            id_fields = instr.format.get_identification_fields()
            if id_fields:
                for id_field in id_fields:
                    encoding_assignment = None
                    for assignment in instr.encoding.assignments:
                        if assignment.field == id_field.name:
                            encoding_assignment = assignment
                            break
                    
                    if encoding_assignment:
                        field_width = id_field.width()
                        mask_val = (1 << field_width) - 1
                        check = f"if (instruction_word >> {id_field.lsb}) & {mask_val} != {encoding_assignment.value}:\n            return None"
                        checks.append(check)
            else:
                # Use all encoding fields
                for assignment in instr.encoding.assignments:
                    field = instr.format.get_field(assignment.field)
                    if field:
                        field_width = field.width()
                        mask_val = (1 << field_width) - 1
                        check = f"if (instruction_word >> {field.lsb}) & {mask_val} != {assignment.value}:\n            return None"
                        checks.append(check)
            
            return checks
        
        def get_instructions_by_width(isa, width):
            """Get all instructions with the specified width."""
            result = []
            for instr in isa.instructions:
                if (instr.format and instr.format.width == width) or \
                   (instr.bundle_format and instr.bundle_format.width == width):
                    result.append(instr)
            return result
        
        def get_unique_widths(isa, reverse=False):
            """Get unique instruction widths from ISA.
            
            Args:
                reverse: If True, return longer widths first (for identification).
                        If False, return shorter widths first (for disassembly).
            """
            widths = set()
            for instr in isa.instructions:
                if instr.format:
                    widths.add(instr.format.width)
                if instr.bundle_format:
                    widths.add(instr.bundle_format.width)
            return sorted(widths, reverse=reverse)
        
        # Register utility functions in Jinja2 environment
        env.globals['build_identification_condition'] = build_identification_condition
        env.globals['build_encoding_condition'] = build_encoding_condition
        env.globals['get_width_mask_code'] = get_width_mask_code
        env.globals['build_instruction_match_check'] = build_instruction_match_check
        env.globals['build_disassemble_match_checks'] = build_disassemble_match_checks
        env.globals['get_instructions_by_width'] = get_instructions_by_width
        env.globals['get_unique_widths'] = get_unique_widths
        
        # Load template from file
        template = env.get_template('disassembler.j2')
        code = template.render(isa=self.isa)
        
        output_file = Path(output_path) / 'disassembler.py'
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(code)
        
        return output_file

