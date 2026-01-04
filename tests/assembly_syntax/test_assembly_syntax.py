"""Tests for assembly syntax feature in disassembler."""

import pytest
import tempfile
from pathlib import Path

from isa_dsl.model.parser import parse_isa_file
from tests.assembly_syntax.test_helpers import AssemblySyntaxTestHelpers


def test_assembly_syntax_formatting():
    """Test that disassembler uses assembly_syntax format string when provided."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa = parse_isa_file(str(test_data_dir / 'comprehensive.isa'))
    
    add_instr = AssemblySyntaxTestHelpers.find_instruction_by_mnemonic(isa, 'ADD')
    assert add_instr is not None, "ADD instruction not found"
    assert add_instr.assembly_syntax == "ADD R{rd}, R{rs1}, R{rs2}", "Assembly syntax not parsed correctly"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        Assembler, Disassembler = AssemblySyntaxTestHelpers.generate_and_import_tools(isa, tmpdir)
        asm = Assembler()
        disasm = Disassembler()
        
        result, _ = AssemblySyntaxTestHelpers.test_round_trip(asm, disasm, "ADD R3, R4, R5")
        assert result == "ADD R3, R4, R5", f"Expected 'ADD R3, R4, R5', got '{result}'"


def test_assembly_syntax_with_distributed_operands():
    """Test that assembly_syntax works with distributed operands."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa = parse_isa_file(str(test_data_dir / 'comprehensive.isa'))
    
    add_dist_instr = AssemblySyntaxTestHelpers.find_instruction_by_mnemonic(isa, 'ADD_DIST')
    assert add_dist_instr is not None, "ADD_DIST instruction not found"
    assert add_dist_instr.assembly_syntax == "ADD_DIST R{rd}, R{rs1}, R{rs2}", "Assembly syntax not parsed correctly"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        Assembler, Disassembler = AssemblySyntaxTestHelpers.generate_and_import_tools(isa, tmpdir)
        asm = Assembler()
        disasm = Disassembler()
        
        result, _ = AssemblySyntaxTestHelpers.test_round_trip(asm, disasm, "ADD_DIST R3, R4, R5")
        assert "ADD_DIST" in result, f"Expected ADD_DIST in result, got '{result}'"
        assert "R3" in result or "R 3" in result, f"Expected register formatting, got '{result}'"


def test_backward_compatibility_no_assembly_syntax():
    """Test that instructions without assembly_syntax still work (backward compatibility)."""
    test_isa_content = '''
architecture TestNoAssemblySyntax {
    word_size: 32
    registers {
        gpr R 32 [16]
    }
    formats {
        format R_TYPE 32 {
            opcode: [0:5]
            rd: [6:8]
        }
    }
    instructions {
        instruction ADD {
            format: R_TYPE
            encoding: { opcode=1 }
            operands: rd
            assembly_syntax: "ADD R{rd}"
        }
        instruction SUB {
            format: R_TYPE
            encoding: { opcode=2 }
            operands: rd
        }
    }
}
'''
    test_isa_file = AssemblySyntaxTestHelpers.create_temp_isa_file(test_isa_content)
    
    try:
        isa = parse_isa_file(test_isa_file)
        sub_instr = AssemblySyntaxTestHelpers.find_instruction_by_mnemonic(isa, 'SUB')
        assert sub_instr is not None, "SUB instruction not found"
        assert sub_instr.assembly_syntax is None, "SUB should not have assembly_syntax"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            Disassembler = AssemblySyntaxTestHelpers.generate_disassembler_only(isa, tmpdir)
            disasm = Disassembler()
            instruction_word = 2 << 0
            result = disasm.disassemble(instruction_word)
            assert 'SUB' in result, f"Expected 'SUB' in result, got '{result}'"
    finally:
        Path(test_isa_file).unlink()


def test_assembly_syntax_format_string_substitution():
    """Test that format string substitution works correctly with various operand values."""
    # Test direct format string substitution
    operand_dict = {'rd': 3, 'rs1': 4, 'rs2': 5}
    format_str = "ADD R{rd}, R{rs1}, R{rs2}"
    result = format_str.format(**operand_dict)
    assert result == "ADD R3, R4, R5", f"Expected 'ADD R3, R4, R5', got '{result}'"
    
    # Test with different values
    operand_dict2 = {'rd': 0, 'rs1': 15, 'rs2': 7}
    result2 = format_str.format(**operand_dict2)
    assert result2 == "ADD R0, R15, R7", f"Expected 'ADD R0, R15, R7', got '{result2}'"
    
    # Test with vector registers
    vformat_str = "VADD V{vd}, V{vs1}, V{vs2}"
    voperand_dict = {'vd': 2, 'vs1': 3, 'vs2': 4}
    vresult = vformat_str.format(**voperand_dict)
    assert vresult == "VADD V2, V3, V4", f"Expected 'VADD V2, V3, V4', got '{vresult}'"

