"""Helper methods for TriCore tests."""

import tempfile
import sys
import importlib.util
from pathlib import Path

from isa_dsl.generators.simulator import SimulatorGenerator
from isa_dsl.generators.assembler import AssemblerGenerator
from isa_dsl.generators.disassembler import DisassemblerGenerator


class TriCoreTestHelpers:
    """Helper class for TriCore test functions."""
    
    @staticmethod
    def generate_all_tools(isa, tmpdir_path):
        """Generate all tools (simulator, assembler, disassembler)."""
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir_path)
        
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir_path)
        
        disasm_gen = DisassemblerGenerator(isa)
        disasm_file = disasm_gen.generate(tmpdir_path)
        
        return sim_file, asm_file, disasm_file
    
    @staticmethod
    def import_all_tools(sim_file, asm_file, disasm_file, tmpdir_path):
        """Import assembler, simulator, and disassembler from generated files."""
        sys.path.insert(0, str(tmpdir_path))
        
        # Import simulator
        sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
        sim_module = importlib.util.module_from_spec(sim_spec)
        sim_spec.loader.exec_module(sim_module)
        Simulator = sim_module.Simulator
        
        # Import assembler
        asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
        asm_module = importlib.util.module_from_spec(asm_spec)
        asm_spec.loader.exec_module(asm_module)
        Assembler = asm_module.Assembler
        
        # Import disassembler (if provided)
        Disassembler = None
        if disasm_file is not None:
            disasm_spec = importlib.util.spec_from_file_location("disassembler", disasm_file)
            disasm_module = importlib.util.module_from_spec(disasm_spec)
            disasm_spec.loader.exec_module(disasm_module)
            Disassembler = disasm_module.Disassembler
        
        return Assembler, Simulator, Disassembler
    
    @staticmethod
    def create_test_assembly_file(tmpdir_path, content):
        """Create a test assembly file with given content."""
        asm_source = tmpdir_path / "test.asm"
        asm_source.write_text(content)
        return asm_source
    
    @staticmethod
    def assemble_and_write_binary(assembler, asm_source, binary_file):
        """Assemble code from file and write to binary."""
        with open(asm_source, 'r') as f:
            source = f.read()
        machine_code = assembler.assemble(source)
        assembler.write_binary(machine_code, str(binary_file))
        return machine_code
    
    @staticmethod
    def write_machine_code_to_file(machine_code, file_path):
        """Write machine code list to binary file."""
        with open(file_path, 'wb') as f:
            for word in machine_code:
                f.write(word.to_bytes(4, byteorder='little'))


