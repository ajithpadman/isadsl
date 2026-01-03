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
        
        # Load template from file
        template = env.get_template('disassembler.j2')
        code = template.render(isa=self.isa)
        
        output_file = Path(output_path) / 'disassembler.py'
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(code)
        
        return output_file

