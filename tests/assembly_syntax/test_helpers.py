"""Helper methods for assembly syntax tests."""

import tempfile
import importlib.util
from pathlib import Path

from isa_dsl.generators.disassembler import DisassemblerGenerator
from isa_dsl.generators.assembler import AssemblerGenerator


class AssemblySyntaxTestHelpers:
    """Helper class for assembly syntax test functions."""
    
    @staticmethod
    def generate_and_import_tools(isa, tmpdir_path):
        """Generate assembler and disassembler and import them."""
        disasm_gen = DisassemblerGenerator(isa)
        asm_gen = AssemblerGenerator(isa)
        
        disasm_gen.generate(tmpdir_path)
        asm_gen.generate(tmpdir_path)
        
        disasm_file = Path(tmpdir_path) / "disassembler.py"
        asm_file = Path(tmpdir_path) / "assembler.py"
        
        disasm_spec = importlib.util.spec_from_file_location("disassembler", disasm_file)
        disassembler_module = importlib.util.module_from_spec(disasm_spec)
        disasm_spec.loader.exec_module(disassembler_module)
        Disassembler = disassembler_module.Disassembler
        
        asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
        assembler_module = importlib.util.module_from_spec(asm_spec)
        asm_spec.loader.exec_module(assembler_module)
        Assembler = assembler_module.Assembler
        
        return Assembler, Disassembler
    
    @staticmethod
    def test_round_trip(assembler, disassembler, source_code):
        """Test round-trip: assemble -> disassemble."""
        machine_code = assembler.assemble(source_code)
        assert len(machine_code) > 0, "Failed to assemble instruction"
        result = disassembler.disassemble(machine_code[0])
        return result, machine_code
    
    @staticmethod
    def create_temp_isa_file(isa_content):
        """Create a temporary ISA file with given content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.isa', delete=False) as f:
            f.write(isa_content)
            return f.name
    
    @staticmethod
    def find_instruction_by_mnemonic(isa, mnemonic):
        """Find instruction by mnemonic."""
        return next((instr for instr in isa.instructions if instr.mnemonic == mnemonic), None)
    
    @staticmethod
    def generate_disassembler_only(isa, tmpdir_path):
        """Generate only disassembler and import it."""
        disasm_gen = DisassemblerGenerator(isa)
        disasm_gen.generate(tmpdir_path)
        
        disasm_file = Path(tmpdir_path) / "disassembler.py"
        disasm_spec = importlib.util.spec_from_file_location("disassembler", disasm_file)
        disassembler_module = importlib.util.module_from_spec(disasm_spec)
        disasm_spec.loader.exec_module(disassembler_module)
        return disassembler_module.Disassembler

