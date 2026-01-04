"""Helper methods for variable-length instruction tests."""

import tempfile
import importlib.util
import os
from pathlib import Path

from isa_dsl.generators.simulator import SimulatorGenerator
from isa_dsl.generators.assembler import AssemblerGenerator
from isa_dsl.generators.disassembler import DisassemblerGenerator


class VariableLengthTestHelpers:
    """Helper class for variable-length test functions."""
    
    @staticmethod
    def generate_and_import_assembler(isa, tmpdir_path):
        """Generate assembler and import it."""
        asm_gen = AssemblerGenerator(isa)
        asm_gen.generate(tmpdir_path)
        asm_file = Path(tmpdir_path) / "assembler.py"
        
        spec = importlib.util.spec_from_file_location("assembler", asm_file)
        assembler_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(assembler_module)
        return assembler_module.Assembler
    
    @staticmethod
    def generate_and_import_simulator(isa, tmpdir_path):
        """Generate simulator and import it."""
        sim_gen = SimulatorGenerator(isa)
        sim_gen.generate(tmpdir_path)
        sim_file = Path(tmpdir_path) / "simulator.py"
        
        spec = importlib.util.spec_from_file_location("simulator", sim_file)
        simulator_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(simulator_module)
        return simulator_module.Simulator
    
    @staticmethod
    def generate_and_import_disassembler(isa, tmpdir_path):
        """Generate disassembler and import it."""
        disasm_gen = DisassemblerGenerator(isa)
        disasm_gen.generate(tmpdir_path)
        disasm_file = Path(tmpdir_path) / "disassembler.py"
        
        spec = importlib.util.spec_from_file_location("disassembler", disasm_file)
        disassembler_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(disassembler_module)
        return disassembler_module.Disassembler
    
    @staticmethod
    def generate_and_import_all_tools(isa, tmpdir_path):
        """Generate all tools and import them."""
        sim_gen = SimulatorGenerator(isa)
        asm_gen = AssemblerGenerator(isa)
        disasm_gen = DisassemblerGenerator(isa)
        
        sim_gen.generate(tmpdir_path)
        asm_gen.generate(tmpdir_path)
        disasm_gen.generate(tmpdir_path)
        
        sim_file = Path(tmpdir_path) / "simulator.py"
        asm_file = Path(tmpdir_path) / "assembler.py"
        disasm_file = Path(tmpdir_path) / "disassembler.py"
        
        sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
        simulator_module = importlib.util.module_from_spec(sim_spec)
        sim_spec.loader.exec_module(simulator_module)
        
        asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
        assembler_module = importlib.util.module_from_spec(asm_spec)
        asm_spec.loader.exec_module(assembler_module)
        
        disasm_spec = importlib.util.spec_from_file_location("disassembler", disasm_file)
        disassembler_module = importlib.util.module_from_spec(disasm_spec)
        disasm_spec.loader.exec_module(disassembler_module)
        
        return (simulator_module.Simulator, assembler_module.Assembler, disassembler_module.Disassembler)
    
    @staticmethod
    def test_instruction_end_to_end(isa, tmpdir_path, source_code, expected_r0, expected_pc, instruction_name):
        """Test end-to-end flow for a single instruction."""
        Simulator, Assembler, Disassembler = VariableLengthTestHelpers.generate_and_import_all_tools(isa, tmpdir_path)
        
        sim = Simulator()
        asm = Assembler()
        disasm = Disassembler()
        
        machine_code = asm.assemble(source_code)
        binary_file = os.path.join(tmpdir_path, "test.bin")
        asm.write_binary(machine_code, binary_file)
        
        sim.load_binary_file(binary_file)
        sim.R[1] = 5
        sim.step()
        
        assert sim.R[0] == expected_r0, f"Expected R[0]={expected_r0}, got {sim.R[0]}"
        assert sim.pc == expected_pc, f"Expected PC={expected_pc}, got {sim.pc}"
        
        instructions = disasm.disassemble_file(binary_file)
        assert len(instructions) > 0 and instruction_name in instructions[0][1].upper()

