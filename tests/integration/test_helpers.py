"""Helper methods for integration tests."""

import tempfile
import sys
from pathlib import Path

from isa_dsl.generators.simulator import SimulatorGenerator
from isa_dsl.generators.assembler import AssemblerGenerator
from isa_dsl.generators.disassembler import DisassemblerGenerator


class IntegrationTestHelpers:
    """Helper class for integration test functions."""
    
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
    def import_assembler_simulator(tmpdir_path):
        """Import assembler and simulator from generated files."""
        sys.path.insert(0, str(tmpdir_path))
        from assembler import Assembler
        from simulator import Simulator
        return Assembler, Simulator
    
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
    def setup_comprehensive_registers(sim):
        """Setup register values for comprehensive tests."""
        sim.R[2] = 10
        sim.R[3] = 20
        sim.R[5] = 5
        sim.R[6] = 15

