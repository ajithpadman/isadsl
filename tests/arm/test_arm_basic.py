"""Basic ARM Cortex-A9 tests: parsing, tool generation, and integration."""

import pytest
import tempfile
import sys
import importlib.util
from pathlib import Path

from isa_dsl.model.parser import parse_isa_file
from isa_dsl.generators.simulator import SimulatorGenerator
from isa_dsl.generators.assembler import AssemblerGenerator
from isa_dsl.generators.disassembler import DisassemblerGenerator
from isa_dsl.generators.documentation import DocumentationGenerator
from tests.arm.test_helpers import ArmTestHelpers


def test_arm_cortex_a9_isa_parsing(arm_cortex_a9_isa_file):
    """Test that ARM Cortex-A9 ISA file can be parsed correctly."""
    isa = parse_isa_file(str(arm_cortex_a9_isa_file))
    
    assert isa.name == "ARMCortexA9"
    assert isa.get_property("word_size") == 32
    assert isa.get_property("endianness") == "little"
    
    gprs = [r for r in isa.registers if r.type == 'gpr']
    sfrs = [r for r in isa.registers if r.type == 'sfr']
    assert len(gprs) > 0
    assert len(sfrs) > 0
    
    assert isa.get_instruction("ADD_IMM") is not None
    assert isa.get_instruction("LDR") is not None
    assert isa.get_instruction("B") is not None


def test_arm_cortex_a9_tool_generation(arm_cortex_a9_isa_file):
    """Test generation of all tools from ARM Cortex-A9 ISA."""
    isa = parse_isa_file(str(arm_cortex_a9_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        sim_gen = SimulatorGenerator(isa)
        assert sim_gen.generate(tmpdir_path).exists()
        
        asm_gen = AssemblerGenerator(isa)
        assert asm_gen.generate(tmpdir_path).exists()
        
        disasm_gen = DisassemblerGenerator(isa)
        assert disasm_gen.generate(tmpdir_path).exists()
        
        doc_gen = DocumentationGenerator(isa)
        assert doc_gen.generate(tmpdir_path).exists()


def test_arm_cortex_a9_assembler_simulator_integration(arm_cortex_a9_isa_file):
    """Test ARM Cortex-A9 assembler and simulator integration."""
    isa = parse_isa_file(str(arm_cortex_a9_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            
            assembler = asm_module.Assembler()
            sim = sim_module.Simulator()
            
            assembly_code = "MOV R0, #42\nADD R1, R0, #5"
            machine_code = assembler.assemble(assembly_code)
            
            assert len(machine_code) >= 2
            
            sim.load_program(machine_code, start_address=0)
            assert sim.step() and sim.R[0] == 42
            assert sim.step() and sim.R[1] == 47
            
        finally:
            sys.path.remove(str(tmpdir_path))

