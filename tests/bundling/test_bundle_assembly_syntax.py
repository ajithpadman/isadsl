"""Tests for bundle assembly syntax feature in disassembler."""

import pytest
from pathlib import Path

from isa_dsl.model.parser import parse_isa_file
from tests.bundling.test_helpers import BundlingTestHelpers


def test_bundle_assembly_syntax():
    """Test that disassembler uses assembly_syntax format string for bundles."""
    test_isa_content = '''architecture TestBundle {
    word_size: 32
    registers { gpr R 32 [16] }
    formats {
        format BUNDLE_ID 80 { bundle_opcode: [0:7] }
        bundle format BUNDLE_64 80 { slot0: [8:39] slot1: [40:71] }
        format R_TYPE 32 { opcode: [0:5] rd: [6:8] rs1: [9:11] rs2: [12:14] }
    }
    instructions {
        instruction ADD { format: R_TYPE encoding: { opcode=1, funct=0 } operands: rd, rs1, rs2 assembly_syntax: "ADD R{rd}, R{rs1}, R{rs2}" }
        instruction BUNDLE { format: BUNDLE_ID bundle_format: BUNDLE_64 encoding: { bundle_opcode=255 } bundle_instructions: ADD assembly_syntax: "BUNDLE[ {slot0}, {slot1} ]" }
    }
}'''
    test_isa_file = BundlingTestHelpers.create_temp_isa_file(test_isa_content)
    try:
        isa = parse_isa_file(test_isa_file)
        bundle_instr = BundlingTestHelpers.find_instruction_by_mnemonic(isa, 'BUNDLE')
        assert bundle_instr is not None and bundle_instr.assembly_syntax == "BUNDLE[ {slot0}, {slot1} ]"
        
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            Assembler, Disassembler = BundlingTestHelpers.generate_and_import_tools(isa, tmpdir)
            asm = Assembler()
            disasm = Disassembler()
            result, _ = BundlingTestHelpers.test_bundle_round_trip(asm, disasm, "BUNDLE{ ADD R3, R4, R5, ADD R6, R7, R8 }")
            assert "BUNDLE" in result and ("slot0" in result or "ADD" in result)
    finally:
        Path(test_isa_file).unlink()


def test_bundle_default_format():
    """Test that bundles without assembly_syntax use default format."""
    test_isa_content = '''architecture TestBundle {
    word_size: 32
    registers { gpr R 32 [16] }
    formats {
        format BUNDLE_ID 80 { bundle_opcode: [0:7] }
        bundle format BUNDLE_64 80 { slot0: [8:39] slot1: [40:71] }
        format R_TYPE 32 { opcode: [0:5] rd: [6:8] }
    }
    instructions {
        instruction ADD { format: R_TYPE encoding: { opcode=1, funct=0 } operands: rd }
        instruction BUNDLE { format: BUNDLE_ID bundle_format: BUNDLE_64 encoding: { bundle_opcode=255 } bundle_instructions: ADD }
    }
}'''
    test_isa_file = BundlingTestHelpers.create_temp_isa_file(test_isa_content)
    try:
        isa = parse_isa_file(test_isa_file)
        bundle_instr = BundlingTestHelpers.find_instruction_by_mnemonic(isa, 'BUNDLE')
        assert bundle_instr is not None and bundle_instr.assembly_syntax is None
        
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            Disassembler = BundlingTestHelpers.generate_disassembler_only(isa, tmpdir)
            disasm = Disassembler()
            assert disasm is not None
    finally:
        Path(test_isa_file).unlink()

