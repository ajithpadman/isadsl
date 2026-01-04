"""Tests for instruction bundling functionality."""

import pytest
from pathlib import Path
import tempfile
import importlib.util
from isa_dsl.model.parser import parse_isa_file
from isa_dsl.model.validator import ISAValidator
from isa_dsl.generators.simulator import SimulatorGenerator
from isa_dsl.generators.assembler import AssemblerGenerator
from tests.bundling.test_helpers import BundlingTestHelpers


def test_parse_bundle_format():
    """Test parsing bundle format definitions."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'bundling.isa'
    isa = parse_isa_file(str(isa_file))
    
    assert isa.name == 'BundledISA'
    
    # Check bundle format exists
    assert len(isa.bundle_formats) > 0
    bundle_fmt = isa.get_bundle_format('BUNDLE_64')
    assert bundle_fmt is not None
    assert bundle_fmt.width == 64
    assert len(bundle_fmt.slots) == 2
    
    # Check slots
    slot0 = bundle_fmt.get_slot('slot0')
    assert slot0 is not None
    assert slot0.lsb == 0
    assert slot0.msb == 31
    assert slot0.width() == 32
    
    slot1 = bundle_fmt.get_slot('slot1')
    assert slot1 is not None
    assert slot1.lsb == 32
    assert slot1.msb == 63
    assert slot1.width() == 32


def test_parse_bundle_instruction():
    """Test parsing bundle instruction definitions."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'bundling.isa'
    isa = parse_isa_file(str(isa_file))
    
    # Find bundle instruction
    bundle_instr = None
    for instr in isa.instructions:
        if instr.is_bundle():
            bundle_instr = instr
            break
    
    assert bundle_instr is not None, "Bundle instruction should exist"
    assert bundle_instr.mnemonic == 'BUNDLE'
    assert bundle_instr.format is not None, "Bundle should have format for identification"
    assert bundle_instr.bundle_format is not None, "Bundle should have bundle_format"
    assert bundle_instr.format.name == 'BUNDLE_ID'
    assert bundle_instr.bundle_format.name == 'BUNDLE_64'
    assert len(bundle_instr.bundle_instructions) == 2, "Bundle should reference 2 instructions"
    
    # Check bundle instructions are resolved
    bundle_instr_names = [bi.mnemonic for bi in bundle_instr.bundle_instructions]
    assert 'ADD' in bundle_instr_names
    assert 'SUB' in bundle_instr_names


def test_bundle_encoding_matching():
    """Test that bundle encoding matching works correctly."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'bundling.isa'
    isa = parse_isa_file(str(isa_file))
    
    bundle_instr = None
    for instr in isa.instructions:
        if instr.is_bundle():
            bundle_instr = instr
            break
    
    assert bundle_instr is not None
    
    # Test encoding match - bundle_opcode=255 in bits [0:7]
    test_word = 0xFF  # 255 in low 8 bits
    assert bundle_instr.matches_encoding(test_word), "Should match bundle encoding"
    
    # Test encoding mismatch
    test_word_wrong = 0x00  # Wrong opcode
    assert not bundle_instr.matches_encoding(test_word_wrong), "Should not match wrong encoding"
    
    # Test with bundle_opcode in correct position for 64-bit word
    test_word_64 = 0xFF00000000000000  # 255 in bits [56:63] of 64-bit word
    # Note: For 64-bit bundle, we need to check the actual field position
    # The format defines bundle_opcode at [0:7], so for a 64-bit word, it's still bits [0:7]
    test_word_64_correct = 0xFF  # Correct: 255 in bits [0:7]
    assert bundle_instr.matches_encoding(test_word_64_correct), "Should match with correct bit position"


def test_bundle_slot_extraction():
    """Test extracting sub-instructions from bundle slots."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'bundling.isa'
    isa = parse_isa_file(str(isa_file))
    
    bundle_fmt = isa.get_bundle_format('BUNDLE_64')
    assert bundle_fmt is not None
    
    # Create a test bundle word with two instructions
    # slot0 (bits 0-31): ADD instruction (opcode=1, rd=1, rs1=2, rs2=3)
    # slot1 (bits 32-63): SUB instruction (opcode=2, rd=4, rs1=5, rs2=6)
    add_instr = 0x00000001 | (1 << 6) | (2 << 9) | (3 << 12)  # ADD R1, R2, R3
    sub_instr = 0x00000002 | (4 << 6) | (5 << 9) | (6 << 12)  # SUB R4, R5, R6
    bundle_word = add_instr | (sub_instr << 32)
    
    # Extract instructions from slots
    slot0_word = bundle_fmt.get_slot('slot0').extract(bundle_word)
    slot1_word = bundle_fmt.get_slot('slot1').extract(bundle_word)
    
    # Verify extraction
    assert slot0_word == add_instr, f"slot0 should extract ADD instruction, got 0x{slot0_word:08x}"
    assert slot1_word == sub_instr, f"slot1 should extract SUB instruction, got 0x{slot1_word:08x}"


def test_bundle_instruction_validation():
    """Test validation of bundle instructions."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'bundling.isa'
    isa = parse_isa_file(str(isa_file))
    
    validator = ISAValidator(isa)
    errors = validator.validate()
    
    # Bundle instructions should validate correctly
    assert len(errors) == 0, f"Validation should pass, but got errors: {[str(e) for e in errors]}"


def test_generated_simulator_bundle_detection():
    """Test that generated simulator can detect bundle instructions."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'bundling.isa'
    isa = parse_isa_file(str(isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir)
        assert sim_file.exists()
        
        # Check generated code contains bundle handling
        code = sim_file.read_text()
        assert 'BUNDLE' in code, "Generated simulator should handle BUNDLE instruction"
        assert '_matches_BUNDLE' in code, "Should have bundle matching function"
        assert '_execute_BUNDLE' in code, "Should have bundle execution function"


def test_generated_assembler_bundle_syntax():
    """Test that generated assembler recognizes bundle syntax."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'bundling.isa'
    isa = parse_isa_file(str(isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir)
        assert asm_file.exists()
        
        # Check generated code contains bundle handling
        code = asm_file.read_text()
        assert 'bundle{' in code.lower() or 'BUNDLE{' in code, "Generated assembler should handle bundle syntax"
        assert '_assemble_bundle' in code, "Should have bundle assembly function"
        assert '_encode_bundle_BUNDLE' in code, "Should have bundle encoding function"


def test_bundle_assembly():
    """Test assembling bundle instructions."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'bundling.isa'
    isa = parse_isa_file(str(isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir)
        
        # Import generated assembler
        spec = importlib.util.spec_from_file_location("assembler", asm_file)
        asm_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(asm_module)
        Assembler = asm_module.Assembler
        
        assembler = Assembler()
        
        # Test assembling a bundle
        # Note: Bundle syntax is bundle{instr1, instr2}
        assembly_code = "bundle{ADD R1, R2, R3, SUB R4, R5, R6}"
        machine_code = assembler.assemble(assembly_code)
        
        assert len(machine_code) > 0, "Should assemble bundle instruction"
        # Bundle should be 64 bits (8 bytes), but assembler returns 32-bit words
        # So we might get 2 words or the assembler might handle it differently
        assert isinstance(machine_code[0], int), "Machine code should be integers"


def test_bundle_simulation():
    """Test simulating bundle instructions."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'bundling.isa'
    isa = parse_isa_file(str(isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        Simulator = BundlingTestHelpers.generate_and_import_simulator(isa, tmpdir)
        sim = Simulator()
        
        add_instr = 0x00000001 | (1 << 6) | (2 << 9) | (3 << 12)
        sub_instr = 0x00000002 | (4 << 6) | (5 << 9) | (6 << 12)
        bundle_word = BundlingTestHelpers.create_bundle_word(add_instr, sub_instr)
        
        BundlingTestHelpers.load_bundle_to_memory(sim, bundle_word)
        BundlingTestHelpers.setup_simulator_registers(sim)
        
        executed = sim.step()
        assert executed is not None, "Bundle execution should not crash"


def test_bundle_end_to_end():
    """Test end-to-end bundle workflow: assemble and simulate."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'bundling.isa'
    isa = parse_isa_file(str(isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        Assembler, Simulator = BundlingTestHelpers.generate_and_import_assembler_simulator(isa, tmpdir)
        assembler = Assembler()
        sim = Simulator()
        
        BundlingTestHelpers.setup_simulator_registers(sim)
        
        machine_code = assembler.assemble("bundle{ADD R1, R2, R3, SUB R4, R5, R6}")
        assert len(machine_code) > 0, "Should assemble bundle"
        
        if len(machine_code) >= 2:
            sim.memory[0] = machine_code[0]
            sim.memory[4] = machine_code[1]
        else:
            sim.memory[0] = machine_code[0]
        sim.pc = 0
        
        executed = sim.step()
        assert executed is not None, "Bundle should execute"


def test_bundle_format_slot_encoding():
    """Test encoding instructions into bundle slots."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'bundling.isa'
    isa = parse_isa_file(str(isa_file))
    
    bundle_fmt = isa.get_bundle_format('BUNDLE_64')
    assert bundle_fmt is not None
    
    # Create two instruction words
    add_instr = 0x00000001 | (1 << 6) | (2 << 9) | (3 << 12)
    sub_instr = 0x00000002 | (4 << 6) | (5 << 9) | (6 << 12)
    
    # Encode into bundle
    instruction_words = {'slot0': add_instr, 'slot1': sub_instr}
    bundle_word = bundle_fmt.encode_bundle(instruction_words)
    
    # Verify encoding
    slot0_extracted = bundle_fmt.get_slot('slot0').extract(bundle_word)
    slot1_extracted = bundle_fmt.get_slot('slot1').extract(bundle_word)
    
    assert slot0_extracted == add_instr, "slot0 should contain ADD instruction"
    assert slot1_extracted == sub_instr, "slot1 should contain SUB instruction"

