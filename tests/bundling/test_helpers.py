"""Helper methods for bundling tests."""

import tempfile
import importlib.util
from pathlib import Path

from isa_dsl.generators.disassembler import DisassemblerGenerator
from isa_dsl.generators.assembler import AssemblerGenerator


class BundlingTestHelpers:
    """Helper class for bundling test functions."""
    
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
    def test_bundle_round_trip(assembler, disassembler, source_code):
        """Test round-trip: assemble -> disassemble for bundles."""
        machine_code = assembler.assemble(source_code)
        assert len(machine_code) > 0, "Failed to assemble bundle"
        result = disassembler.disassemble(machine_code[0])
        assert result is not None, "Failed to disassemble bundle"
        return result, machine_code
    
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
    
    @staticmethod
    def generate_and_import_simulator(isa, tmpdir_path):
        """Generate simulator and import it."""
        from isa_dsl.generators.simulator import SimulatorGenerator
        
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir_path)
        
        spec = importlib.util.spec_from_file_location("simulator", sim_file)
        sim_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sim_module)
        return sim_module.Simulator
    
    @staticmethod
    def generate_and_import_assembler_simulator(isa, tmpdir_path):
        """Generate assembler and simulator and import them."""
        from isa_dsl.generators.simulator import SimulatorGenerator
        
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir_path)
        
        asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
        asm_module = importlib.util.module_from_spec(asm_spec)
        asm_spec.loader.exec_module(asm_module)
        
        sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
        sim_module = importlib.util.module_from_spec(sim_spec)
        sim_spec.loader.exec_module(sim_module)
        
        return asm_module.Assembler, sim_module.Simulator
    
    @staticmethod
    def create_bundle_word(add_instr, sub_instr, bundle_opcode=255):
        """Create a 64-bit bundle word from instruction words."""
        return (bundle_opcode << 0) | (add_instr << 0) | (sub_instr << 32)
    
    @staticmethod
    def setup_simulator_registers(sim, r2=10, r3=5, r5=20, r6=8):
        """Setup simulator registers for bundle tests."""
        sim.R[2] = r2
        sim.R[3] = r3
        sim.R[5] = r5
        sim.R[6] = r6
    
    @staticmethod
    def load_bundle_to_memory(sim, bundle_word, address=0):
        """Load bundle word to simulator memory."""
        sim.memory[address] = bundle_word & 0xFFFFFFFF
        sim.memory[address + 4] = (bundle_word >> 32) & 0xFFFFFFFF
        sim.pc = address

