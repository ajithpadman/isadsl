"""Tests for curly braces in assembly syntax."""

import pytest
import tempfile
from pathlib import Path
import importlib.util

from isa_dsl.model.parser import parse_isa_file
from isa_dsl.generators.disassembler import DisassemblerGenerator
from isa_dsl.generators.assembler import AssemblerGenerator


def test_literal_braces_in_assembly_syntax():
    """Test that literal curly braces can be used in assembly_syntax."""
    test_isa_content = '''
architecture TestBraces {
    word_size: 32
    registers {
        gpr R 32 [16]
    }
    formats {
        format R_TYPE 32 {
            opcode: [0:5]
            rd: [6:8]
            rs1: [9:11]
        }
        format BUNDLE_ID 80 {
            bundle_opcode: [0:7]
        }
        bundle format BUNDLE_64 80 {
            slot0: [8:39]
            slot1: [40:71]
        }
    }
    instructions {
        instruction ADD {
            format: R_TYPE
            encoding: { opcode=1, funct=0 }
            operands: rd, rs1
            assembly_syntax: "ADD R{rd}, R{rs1}"
        }
        instruction BUNDLE {
            format: BUNDLE_ID
            bundle_format: BUNDLE_64
            encoding: { bundle_opcode=255 }
            bundle_instructions: ADD
            assembly_syntax: "BUNDLE{{ {slot0}, {slot1} }}"
        }
    }
}
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.isa', delete=False) as f:
        f.write(test_isa_content)
        test_isa_file = f.name
    
    try:
        isa = parse_isa_file(test_isa_file)
        
        # Test regular instruction
        add_instr = next((instr for instr in isa.instructions if instr.mnemonic == 'ADD'), None)
        assert add_instr is not None
        assert add_instr.assembly_syntax == "ADD R{rd}, R{rs1}"
        
        # Test formatting regular instruction
        result = add_instr.assembly_syntax.format(rd=3, rs1=4)
        assert result == "ADD R3, R4"
        
        # Test bundle instruction
        bundle_instr = next((instr for instr in isa.instructions if instr.mnemonic == 'BUNDLE'), None)
        assert bundle_instr is not None
        assert bundle_instr.assembly_syntax == "BUNDLE{{ {slot0}, {slot1} }}"
        
        # Test formatting bundle instruction
        result = bundle_instr.assembly_syntax.format(slot0="ADD R3, R4", slot1="ADD R5, R6")
        assert result == "BUNDLE{ ADD R3, R4, ADD R5, R6 }", f"Expected 'BUNDLE{{ ADD R3, R4, ADD R5, R6 }}', got '{result}'"
        
    finally:
        Path(test_isa_file).unlink()


def test_nested_braces():
    """Test nested braces in assembly syntax."""
    test_isa_content = '''
architecture TestNested {
    word_size: 32
    registers {
        gpr R 32 [16]
    }
    formats {
        format R_TYPE 32 {
            opcode: [0:5]
            rd: [6:8]
        }
        format BUNDLE_ID 80 {
            bundle_opcode: [0:7]
        }
        bundle format BUNDLE_64 80 {
            slot0: [8:39]
        }
    }
    instructions {
        instruction ADD {
            format: R_TYPE
            encoding: { opcode=1 }
            operands: rd
            assembly_syntax: "ADD R{rd}"
        }
        instruction BUNDLE {
            format: BUNDLE_ID
            bundle_format: BUNDLE_64
            encoding: { bundle_opcode=255 }
            bundle_instructions: ADD
            assembly_syntax: "{{ {slot0} }}"
        }
    }
}
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.isa', delete=False) as f:
        f.write(test_isa_content)
        test_isa_file = f.name
    
    try:
        isa = parse_isa_file(test_isa_file)
        
        bundle_instr = next((instr for instr in isa.instructions if instr.mnemonic == 'BUNDLE'), None)
        assert bundle_instr is not None
        assert bundle_instr.assembly_syntax == "{{ {slot0} }}"
        
        # Test formatting
        result = bundle_instr.assembly_syntax.format(slot0="ADD R3, R4")
        assert result == "{ ADD R3, R4 }", f"Expected '{{ ADD R3, R4 }}', got '{result}'"
        
    finally:
        Path(test_isa_file).unlink()


def test_multiple_literal_braces():
    """Test multiple literal braces in assembly syntax."""
    test_isa_content = '''
architecture TestMultiple {
    word_size: 32
    registers {
        gpr R 32 [16]
    }
    formats {
        format R_TYPE 32 {
            opcode: [0:5]
            rd: [6:8]
        }
        format BUNDLE_ID 80 {
            bundle_opcode: [0:7]
        }
        bundle format BUNDLE_64 80 {
            slot0: [8:39]
        }
    }
    instructions {
        instruction ADD {
            format: R_TYPE
            encoding: { opcode=1 }
            operands: rd
            assembly_syntax: "ADD R{rd}"
        }
        instruction BUNDLE {
            format: BUNDLE_ID
            bundle_format: BUNDLE_64
            encoding: { bundle_opcode=255 }
            bundle_instructions: ADD
            assembly_syntax: "BUNDLE{{{{ {slot0} }}}}"
        }
    }
}
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.isa', delete=False) as f:
        f.write(test_isa_content)
        test_isa_file = f.name
    
    try:
        isa = parse_isa_file(test_isa_file)
        
        bundle_instr = next((instr for instr in isa.instructions if instr.mnemonic == 'BUNDLE'), None)
        assert bundle_instr is not None
        assert bundle_instr.assembly_syntax == "BUNDLE{{{{ {slot0} }}}}"
        
        # Test formatting - four braces become two literal braces
        result = bundle_instr.assembly_syntax.format(slot0="ADD R3, R4")
        assert result == "BUNDLE{{ ADD R3, R4 }}", f"Expected 'BUNDLE{{{{ ADD R3, R4 }}}}', got '{result}'"
        
    finally:
        Path(test_isa_file).unlink()


def test_braces_with_operands():
    """Test braces with operand placeholders."""
    test_isa_content = '''
architecture TestOperands {
    word_size: 32
    registers {
        gpr R 32 [16]
    }
    formats {
        format R_TYPE 32 {
            opcode: [0:5]
            rd: [6:8]
            immediate: [9:15]
        }
    }
    instructions {
        instruction MOV {
            format: R_TYPE
            encoding: { opcode=2 }
            operands: rd, immediate
            assembly_syntax: "MOV R{rd}, {{imm={immediate}}}"
        }
    }
}
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.isa', delete=False) as f:
        f.write(test_isa_content)
        test_isa_file = f.name
    
    try:
        isa = parse_isa_file(test_isa_file)
        
        mov_instr = next((instr for instr in isa.instructions if instr.mnemonic == 'MOV'), None)
        assert mov_instr is not None
        assert mov_instr.assembly_syntax == "MOV R{rd}, {{imm={immediate}}}"
        
        # Test formatting
        result = mov_instr.assembly_syntax.format(rd=3, immediate=10)
        assert result == "MOV R3, {imm=10}", f"Expected 'MOV R3, {{imm=10}}', got '{result}'"
        
    finally:
        Path(test_isa_file).unlink()

