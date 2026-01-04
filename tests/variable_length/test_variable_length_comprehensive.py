"""Comprehensive tests for variable-length instructions."""

import pytest
from pathlib import Path
import tempfile
import os
from isa_dsl.model.parser import parse_isa_file
from tests.variable_length.test_helpers import VariableLengthTestHelpers


@pytest.fixture
def variable_length_isa_file():
    """Get the variable-length ISA example file."""
    project_root = Path(__file__).parent.parent
    isa_file = Path(__file__).parent / "test_data" / "variable_length.isa"
    if not isa_file.exists():
        pytest.skip(f"ISA file not found: {isa_file}")
    return isa_file


def test_16_bit_instruction_end_to_end(variable_length_isa_file):
    """Test complete flow for 16-bit instructions."""
    isa = parse_isa_file(str(variable_length_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        VariableLengthTestHelpers.test_instruction_end_to_end(isa, tmpdir, "ADD16 R0, R1, 10", 15, 2, "ADD16")


def test_32_bit_instruction_end_to_end(variable_length_isa_file):
    """Test complete flow for 32-bit instructions."""
    isa = parse_isa_file(str(variable_length_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        Simulator, Assembler, Disassembler = VariableLengthTestHelpers.generate_and_import_all_tools(isa, tmpdir)
        sim = Simulator()
        asm = Assembler()
        disasm = Disassembler()
        
        machine_code = asm.assemble("ADD32 R3, R1, R2")
        binary_file = os.path.join(tmpdir, "test.bin")
        asm.write_binary(machine_code, binary_file)
        
        sim.load_binary_file(binary_file)
        sim.R[1] = 10
        sim.R[2] = 20
        sim.step()
        
        assert sim.pc > 0, "PC should advance after instruction execution"
        instructions = disasm.disassemble_file(binary_file)
        assert len(instructions) > 0


def test_mixed_width_instructions(variable_length_isa_file):
    """Test mixed 16-bit and 32-bit instructions."""
    isa = parse_isa_file(str(variable_length_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        Simulator, Assembler, _ = VariableLengthTestHelpers.generate_and_import_all_tools(isa, tmpdir)
        sim = Simulator()
        asm = Assembler()
        
        source = "ADD16 R0, R1, 5\nADD32 R2, R3, R4\nADD16 R5, R6, 10"
        machine_code = asm.assemble(source)
        binary_file = os.path.join(tmpdir, "test.bin")
        asm.write_binary(machine_code, binary_file)
        
        sim.load_binary_file(binary_file)
        sim.R[1] = 1
        sim.R[3] = 10
        sim.R[4] = 20
        sim.R[6] = 2
        
        sim.step()
        assert sim.R[0] == 6 and sim.pc == 2
        
        initial_pc = sim.pc
        sim.step()
        assert sim.pc > initial_pc, "PC should advance after instruction"
        
        if sim.pc < 8:
            initial_pc = sim.pc
            sim.step()
            assert sim.pc > initial_pc, "PC should advance"


def test_distributed_opcode_identification(variable_length_isa_file):
    """Test identification using distributed opcode fields."""
    isa = parse_isa_file(str(variable_length_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        Simulator = VariableLengthTestHelpers.generate_and_import_simulator(isa, tmpdir)
        sim = Simulator()
        
        add_dist_word = (3 << 0) | (0 << 20) | (1 << 4) | (2 << 8) | (3 << 12)
        matched = sim._matches_ADD_DIST(add_dist_word)
        assert matched, "ADD_DIST should match with distributed opcode"


def test_bundle_with_variable_width_sub_instructions(variable_length_isa_file):
    """Test bundles containing variable-width sub-instructions."""
    isa = parse_isa_file(str(variable_length_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        Simulator, Assembler, _ = VariableLengthTestHelpers.generate_and_import_all_tools(isa, tmpdir)
        sim = Simulator()
        asm = Assembler()
        
        machine_code = asm.assemble("BUNDLE{ADD16 R0, R1, 5, ADD32 R2, R3, R4}")
        binary_file = os.path.join(tmpdir, "test.bin")
        asm.write_binary(machine_code, binary_file)
        
        sim.load_binary_file(binary_file)
        sim.R[1] = 10
        sim.R[3] = 20
        sim.R[4] = 30
        sim.step()
        
        assert sim.pc > 0, "PC should advance after bundle execution"

