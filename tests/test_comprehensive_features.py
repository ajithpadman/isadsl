"""
Test comprehensive features: distributed operands, bundling, and SIMD.
"""
import pytest
import tempfile
import os
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from isa_dsl.model.parser import parse_isa_file
from isa_dsl.generators.simulator import SimulatorGenerator
from isa_dsl.generators.assembler import AssemblerGenerator
from isa_dsl.generators.disassembler import DisassemblerGenerator


@pytest.fixture
def comprehensive_isa_file():
    """Path to the comprehensive ISA file."""
    return project_root / "examples" / "comprehensive.isa"


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
    
    # Write generated code to temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Generate simulator
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir_path)
        
        # Generate assembler
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir_path)
        
        # Generate disassembler
        disasm_gen = DisassemblerGenerator(isa)
        disasm_file = disasm_gen.generate(tmpdir_path)
        
        # Write test assembly code (using registers 0-7 for 3-bit encoding)
        asm_source = tmpdir_path / "test.asm"
        asm_source.write_text("""# Test comprehensive features
# Regular ADD instruction
ADD R1, R2, R3

# Distributed operand instruction
ADD_DIST R4, R5, R6

# Bundle with ADD and ADD_DIST (64-bit bundle)
bundle{ADD R0, R1, R2, ADD_DIST R3, R4, R5}
""")
        
        # Import and use assembler
        sys.path.insert(0, str(tmpdir_path))
        try:
            from assembler import Assembler
            
            # Assemble the code
            binary_file = tmpdir_path / "test.bin"
            assembler = Assembler()
            with open(asm_source, 'r') as f:
                source = f.read()
            machine_code = assembler.assemble(source)
            assembler.write_binary(machine_code, str(binary_file))
            
            # Verify binary file was created
            assert binary_file.exists()
            assert binary_file.stat().st_size > 0
            
            # Import and use simulator
            from simulator import Simulator
            
            # Create simulator and load binary
            sim = Simulator()
            sim.load_binary_file(str(binary_file))
            
            # Initialize register values (using registers 0-7)
            # For ADD R1, R2, R3: R[1] = R[2] + R[3]
            sim.R[2] = 10
            sim.R[3] = 20
            # For ADD_DIST R4, R5, R6: R[4] = R[5] + R[6]
            sim.R[5] = 5
            sim.R[6] = 15
            # For bundle: set values that won't conflict
            # Bundle ADD R0, R1, R2 uses R[1] and R[2] as sources
            # After ADD R1, R2, R3: R[1] = 30, R[2] = 10
            # So bundle will compute R[0] = 30 + 10 = 40
            # Bundle ADD_DIST R3, R4, R5 uses R[4] and R[5] as sources
            # After ADD_DIST R4, R5, R6: R[4] = 20, R[5] = 5
            # So bundle will compute R[3] = 20 + 5 = 25
            
            # Run simulator (execute all instructions)
            sim.run(max_steps=20)
            
            # Verify results
            # ADD R1, R2, R3: R1 = 10 + 20 = 30
            assert sim.R[1] == 30, f"Expected R[1]=30, got {sim.R[1]}"
            
            # ADD_DIST R4, R5, R6: R4 = 5 + 15 = 20
            assert sim.R[4] == 20, f"Expected R[4]=20, got {sim.R[4]}"
            
            # Bundle: ADD R0, R1, R2: R0 = R[1] + R[2] = 30 + 10 = 40
            #         ADD_DIST R3, R4, R5: R3 = R[4] + R[5] = 20 + 5 = 25
            # Note: R[2] is still 10 (from initial setup), R[4] is 20 (from ADD_DIST), R[5] is 5 (from initial setup)
            assert sim.R[0] == 40, f"Expected R[0]=40, got {sim.R[0]}"
            # R[3] might be overwritten by bundle's ADD_DIST, but let's check what it should be
            # After ADD_DIST R4, R5, R6: R[4] = 20, R[5] = 5 (unchanged)
            # Bundle ADD_DIST R3, R4, R5: R[3] = R[4] + R[5] = 20 + 5 = 25
            # But R[3] was initially 20, and might be used as source in first ADD
            # Actually, R[3] is not used as source in bundle, so it should be 25
            assert sim.R[3] == 25, f"Expected R[3]=25, got {sim.R[3]}"
            
            # Import and use disassembler
            from disassembler import Disassembler
            
            # Disassemble the binary
            disasm = Disassembler()
            instructions = disasm.disassemble_file(str(binary_file))
            
            # Verify disassembly output
            assert len(instructions) > 0
            disasm_text = "\n".join([f"{addr:08x}: {asm}" for addr, asm in instructions])
            
            # Check that instructions were disassembled
            assert "ADD" in disasm_text
            assert "ADD_DIST" in disasm_text
            assert "bundle" in disasm_text or "BUNDLE" in disasm_text
            
        finally:
            # Clean up sys.path
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_distributed_operand_in_bundle(comprehensive_isa_file):
    """Test that distributed operands work correctly in bundled instructions."""
    isa = parse_isa_file(str(comprehensive_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Generate tools
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir_path)
        
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir_path)
        
        # Write assembly with bundle containing distributed operand (using registers 0-7)
        asm_source = tmpdir_path / "test_bundle.asm"
        asm_source.write_text("""# Bundle with distributed operand
bundle{ADD R0, R1, R2, ADD_DIST R3, R4, R5}
""")
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            from assembler import Assembler
            from simulator import Simulator
            
            # Assemble
            binary_file = tmpdir_path / "test_bundle.bin"
            assembler = Assembler()
            with open(asm_source, 'r') as f:
                source = f.read()
            machine_code = assembler.assemble(source)
            assembler.write_binary(machine_code, str(binary_file))
            
            # Simulate
            sim = Simulator()
            sim.load_binary_file(str(binary_file))
            
            # Set register values before execution (using registers 0-7)
            sim.R[1] = 30  # For bundle ADD R0, R1, R2
            sim.R[2] = 40  # For bundle ADD R0, R1, R2
            sim.R[4] = 25  # For bundle ADD_DIST R3, R4, R5
            sim.R[5] = 35  # For bundle ADD_DIST R3, R4, R5
            
            # Execute bundle (64-bit bundle at address 0)
            # The bundle contains: ADD R0, R1, R2 and ADD_DIST R3, R4, R5
            sim.pc = 0
            executed = sim.step()
            
            # Verify bundle executed (both instructions in bundle)
            assert executed, "Bundle should execute"
            assert sim.R[0] == 70, f"Expected R[0]=70, got {sim.R[0]}"  # ADD R0, R1, R2: 30 + 40 = 70
            assert sim.R[3] == 60, f"Expected R[3]=60, got {sim.R[3]}"  # ADD_DIST R3, R4, R5: 25 + 35 = 60
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))
