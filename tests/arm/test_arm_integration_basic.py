"""Basic ARM integration tests: parsing, tool generation, and integration."""

import pytest
import tempfile
import sys
import importlib.util
from pathlib import Path

from isa_dsl.model.parser import parse_isa_file
from isa_dsl.generators.simulator import SimulatorGenerator
from isa_dsl.generators.assembler import AssemblerGenerator


@pytest.fixture
def arm_isa_file():
    """Path to the ARM ISA subset file."""
    return Path(__file__).parent / "test_data" / "arm_subset.isa"


def test_arm_isa_parsing(arm_isa_file):
    """Test that ARM ISA file can be parsed correctly."""
    isa = parse_isa_file(str(arm_isa_file))
    
    assert isa.name == "ARMSubset"
    assert isa.get_property("word_size") == 32
    assert isa.get_property("endianness") == "little"
    
    gprs = [r for r in isa.registers if r.type == 'gpr']
    assert len(gprs) > 0
    
    assert isa.get_instruction("ADD_IMM") is not None
    assert isa.get_instruction("MOV_IMM") is not None
    assert isa.get_instruction("LDR") is not None
    assert isa.get_instruction("STR") is not None
    assert isa.get_instruction("B") is not None


def test_arm_tool_generation(arm_isa_file):
    """Test generation of all tools from ARM ISA."""
    isa = parse_isa_file(str(arm_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        from isa_dsl.generators.disassembler import DisassemblerGenerator
        from isa_dsl.generators.documentation import DocumentationGenerator
        
        sim_gen = SimulatorGenerator(isa)
        assert sim_gen.generate(tmpdir_path).exists()
        
        asm_gen = AssemblerGenerator(isa)
        assert asm_gen.generate(tmpdir_path).exists()
        
        disasm_gen = DisassemblerGenerator(isa)
        assert disasm_gen.generate(tmpdir_path).exists()
        
        doc_gen = DocumentationGenerator(isa)
        assert doc_gen.generate(tmpdir_path).exists()


def test_arm_assembler_simulator_integration(arm_isa_file):
    """Test ARM assembler and simulator integration."""
    isa = parse_isa_file(str(arm_isa_file))
    
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

