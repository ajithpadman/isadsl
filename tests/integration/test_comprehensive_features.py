"""Test comprehensive features: distributed operands, bundling, and SIMD."""
import pytest
import tempfile
from pathlib import Path
import sys

from isa_dsl.model.parser import parse_isa_file
from tests.integration.test_helpers import IntegrationTestHelpers


@pytest.fixture
def comprehensive_isa_file():
    """Path to the comprehensive ISA file."""
    return Path(__file__).parent / "test_data" / "comprehensive.isa"


def test_parse_comprehensive_isa(comprehensive_isa_file):
    """Test parsing the comprehensive ISA with all features."""
    isa = parse_isa_file(str(comprehensive_isa_file))
    
    assert isa.name == "ComprehensiveISA"
    # Check properties
    assert hasattr(isa, 'properties')
    
    # Check instructions
    add_instr = isa.get_instruction("ADD")
    assert add_instr is not None
    assert len(add_instr.operand_specs) == 3
    
    add_dist_instr = isa.get_instruction("ADD_DIST")
    assert add_dist_instr is not None
    assert len(add_dist_instr.operand_specs) == 3
    # Check that rd is distributed
    rd_spec = add_dist_instr.operand_specs[0]
    assert rd_spec.name == "rd"
    assert rd_spec.is_distributed()
    assert rd_spec.field_names == ["rd_low", "rd_high"]
    
    bundle_instr = isa.get_instruction("BUNDLE")
    assert bundle_instr is not None
    assert bundle_instr.is_bundle()
    assert len(bundle_instr.bundle_instructions) == 3
    
    # Check bundle format has instruction_start
    bundle_format = isa.get_bundle_format("BUNDLE_64")
    assert bundle_format is not None
    assert bundle_format.instruction_start == 8


def test_distributed_operand_encoding_decoding(comprehensive_isa_file):
    """Test encoding and decoding of distributed operands."""
    isa = parse_isa_file(str(comprehensive_isa_file))
    add_dist = isa.get_instruction("ADD_DIST")
    
    # Test encoding: rd=10 (binary: 1010), split as rd_low=2 (010), rd_high=1 (001)
    # rd_low is 3 bits (6:8), rd_high is 3 bits (20:22)
    # rd = 2 + (1 << 3) = 2 + 8 = 10
    operand_values = {"rd": 10, "rs1": 3, "rs2": 4}
    encoded = add_dist.encode_instruction(operand_values)
    
    # Verify encoding
    assert encoded != 0
    
    # Test decoding
    decoded = add_dist.decode_operands(encoded)
    assert decoded["rd"] == 10
    assert decoded["rs1"] == 3
    assert decoded["rs2"] == 4


def test_comprehensive_end_to_end(comprehensive_isa_file):
    """Test end-to-end: generate tools, assemble, simulate, disassemble."""
    isa = parse_isa_file(str(comprehensive_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        IntegrationTestHelpers.generate_all_tools(isa, tmpdir_path)
        
        asm_content = "# Test comprehensive features\nADD R1, R2, R3\nADD_DIST R4, R5, R6\nbundle{ADD R0, R1, R2, ADD_DIST R3, R4, R5}\n"
        asm_source = IntegrationTestHelpers.create_test_assembly_file(tmpdir_path, asm_content)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            Assembler, Simulator = IntegrationTestHelpers.import_assembler_simulator(tmpdir_path)
            
            binary_file = tmpdir_path / "test.bin"
            assembler = Assembler()
            IntegrationTestHelpers.assemble_and_write_binary(assembler, asm_source, binary_file)
            assert binary_file.exists() and binary_file.stat().st_size > 0
            
            sim = Simulator()
            sim.load_binary_file(str(binary_file))
            IntegrationTestHelpers.setup_comprehensive_registers(sim)
            sim.R[5] = 5
            sim.R[6] = 15
            
            sim.run(max_steps=20)
            assert sim.R[1] == 30 and sim.R[4] == 20
            assert sim.R[0] == 40 and sim.R[3] == 25
            
            from disassembler import Disassembler
            disasm = Disassembler()
            instructions = disasm.disassemble_file(str(binary_file))
            assert len(instructions) > 0
            disasm_text = "\n".join([f"{addr:08x}: {asm}" for addr, asm in instructions])
            assert "ADD" in disasm_text and "ADD_DIST" in disasm_text
            assert "bundle" in disasm_text or "BUNDLE" in disasm_text
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_distributed_operand_in_bundle(comprehensive_isa_file):
    """Test that distributed operands work correctly in bundled instructions."""
    isa = parse_isa_file(str(comprehensive_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        IntegrationTestHelpers.generate_all_tools(isa, tmpdir_path)
        
        asm_content = "# Bundle with distributed operand\nbundle{ADD R0, R1, R2, ADD_DIST R3, R4, R5}\n"
        asm_source = IntegrationTestHelpers.create_test_assembly_file(tmpdir_path, asm_content)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            Assembler, Simulator = IntegrationTestHelpers.import_assembler_simulator(tmpdir_path)
            
            binary_file = tmpdir_path / "test_bundle.bin"
            assembler = Assembler()
            IntegrationTestHelpers.assemble_and_write_binary(assembler, asm_source, binary_file)
            
            sim = Simulator()
            sim.load_binary_file(str(binary_file))
            sim.R[1] = 30
            sim.R[2] = 40
            sim.R[4] = 25
            sim.R[5] = 35
            sim.pc = 0
            
            executed = sim.step()
            assert executed, "Bundle should execute"
            assert sim.R[0] == 70 and sim.R[3] == 60
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))
