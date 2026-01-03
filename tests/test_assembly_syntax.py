"""Tests for assembly syntax feature in disassembler."""

import pytest
import tempfile
from pathlib import Path
import importlib.util

from isa_dsl.model.parser import parse_isa_file
from isa_dsl.generators.disassembler import DisassemblerGenerator
from isa_dsl.generators.assembler import AssemblerGenerator


def test_assembly_syntax_formatting():
    """Test that disassembler uses assembly_syntax format string when provided."""
    isa = parse_isa_file('examples/comprehensive.isa')
    
    # Verify assembly_syntax is parsed
    add_instr = next((instr for instr in isa.instructions if instr.mnemonic == 'ADD'), None)
    assert add_instr is not None, "ADD instruction not found"
    assert add_instr.assembly_syntax == "ADD R{rd}, R{rs1}, R{rs2}", "Assembly syntax not parsed correctly"
    
    # Generate disassembler and assembler
    disasm_gen = DisassemblerGenerator(isa)
    asm_gen = AssemblerGenerator(isa)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        disasm_gen.generate(tmpdir)
        asm_gen.generate(tmpdir)
        
        disasm_file = Path(tmpdir) / "disassembler.py"
        asm_file = Path(tmpdir) / "assembler.py"
        
        # Load generated modules
        disasm_spec = importlib.util.spec_from_file_location("disassembler", disasm_file)
        disassembler_module = importlib.util.module_from_spec(disasm_spec)
        disasm_spec.loader.exec_module(disassembler_module)
        Disassembler = disassembler_module.Disassembler
        
        asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
        assembler_module = importlib.util.module_from_spec(asm_spec)
        asm_spec.loader.exec_module(assembler_module)
        Assembler = assembler_module.Assembler
        
        # Test round-trip: assemble -> disassemble
        asm = Assembler()
        disasm = Disassembler()
        
        source = "ADD R3, R4, R5"
        machine_code = asm.assemble(source)
        assert len(machine_code) > 0, "Failed to assemble instruction"
        
        result = disasm.disassemble(machine_code[0])
        assert result == "ADD R3, R4, R5", f"Expected 'ADD R3, R4, R5', got '{result}'"


def test_assembly_syntax_with_distributed_operands():
    """Test that assembly_syntax works with distributed operands."""
    isa = parse_isa_file('examples/comprehensive.isa')
    
    add_dist_instr = next((instr for instr in isa.instructions if instr.mnemonic == 'ADD_DIST'), None)
    assert add_dist_instr is not None, "ADD_DIST instruction not found"
    assert add_dist_instr.assembly_syntax == "ADD_DIST R{rd}, R{rs1}, R{rs2}", "Assembly syntax not parsed correctly"
    
    # Generate disassembler and assembler
    disasm_gen = DisassemblerGenerator(isa)
    asm_gen = AssemblerGenerator(isa)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        disasm_gen.generate(tmpdir)
        asm_gen.generate(tmpdir)
        
        disasm_file = Path(tmpdir) / "disassembler.py"
        asm_file = Path(tmpdir) / "assembler.py"
        
        # Load generated modules
        disasm_spec = importlib.util.spec_from_file_location("disassembler", disasm_file)
        disassembler_module = importlib.util.module_from_spec(disasm_spec)
        disasm_spec.loader.exec_module(disassembler_module)
        Disassembler = disassembler_module.Disassembler
        
        asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
        assembler_module = importlib.util.module_from_spec(asm_spec)
        asm_spec.loader.exec_module(assembler_module)
        Assembler = assembler_module.Assembler
        
        # Test round-trip: assemble -> disassemble
        asm = Assembler()
        disasm = Disassembler()
        
        source = "ADD_DIST R3, R4, R5"
        machine_code = asm.assemble(source)
        assert len(machine_code) > 0, "Failed to assemble instruction"
        
        result = disasm.disassemble(machine_code[0])
        # The result should use the assembly_syntax format
        assert "ADD_DIST" in result, f"Expected ADD_DIST in result, got '{result}'"
        assert "R3" in result or "R 3" in result, f"Expected register formatting, got '{result}'"


def test_backward_compatibility_no_assembly_syntax():
    """Test that instructions without assembly_syntax still work (backward compatibility)."""
    # Create a test ISA without assembly_syntax for some instructions
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
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.isa', delete=False) as f:
        f.write(test_isa_content)
        test_isa_file = f.name
    
    try:
        isa = parse_isa_file(test_isa_file)
        
        # SUB instruction doesn't have assembly_syntax
        sub_instr = next((instr for instr in isa.instructions if instr.mnemonic == 'SUB'), None)
        assert sub_instr is not None, "SUB instruction not found"
        assert sub_instr.assembly_syntax is None, "SUB should not have assembly_syntax"
        
        # Generate disassembler
        disasm_gen = DisassemblerGenerator(isa)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            disasm_gen.generate(tmpdir)
            
            # Import the generated disassembler
            disasm_path = Path(tmpdir) / 'disassembler.py'
            spec = importlib.util.spec_from_file_location('disassembler', disasm_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            Disassembler = module.Disassembler
            
            # Test disassembling without assembly_syntax (should use default format)
            disasm = Disassembler()
            # Create a simple instruction word for SUB (opcode=2)
            instruction_word = 2 << 0  # opcode=2
            result = disasm.disassemble(instruction_word)
            # Should use default format: "SUB <operands>"
            assert 'SUB' in result, f"Expected 'SUB' in result, got '{result}'"
    finally:
        Path(test_isa_file).unlink()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        disasm_gen.generate(tmpdir)
        
        disasm_file = Path(tmpdir) / "disassembler.py"
        
        # Load generated module
        disasm_spec = importlib.util.spec_from_file_location("disassembler", disasm_file)
        disassembler_module = importlib.util.module_from_spec(disasm_spec)
        disasm_spec.loader.exec_module(disassembler_module)
        Disassembler = disassembler_module.Disassembler
        
        # Verify disassembler was generated successfully
        disasm = Disassembler()
        assert disasm is not None, "Disassembler should be created successfully"


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

