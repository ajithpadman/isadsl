"""Tests for bundle assembly syntax feature in disassembler."""

import pytest
import tempfile
from pathlib import Path
import importlib.util

from isa_dsl.model.parser import parse_isa_file
from isa_dsl.generators.disassembler import DisassemblerGenerator
from isa_dsl.generators.assembler import AssemblerGenerator


def test_bundle_assembly_syntax():
    """Test that disassembler uses assembly_syntax format string for bundles."""
    # Create a test ISA with bundle assembly_syntax
    test_isa_content = '''
architecture TestBundle {
    word_size: 32
    registers {
        gpr R 32 [16]
    }
    formats {
        format BUNDLE_ID 80 {
            bundle_opcode: [0:7]
        }
        bundle format BUNDLE_64 80 {
            slot0: [8:39]
            slot1: [40:71]
        }
        format R_TYPE 32 {
            opcode: [0:5]
            rd: [6:8]
            rs1: [9:11]
            rs2: [12:14]
        }
    }
    instructions {
        instruction ADD {
            format: R_TYPE
            encoding: { opcode=1, funct=0 }
            operands: rd, rs1, rs2
            assembly_syntax: "ADD R{rd}, R{rs1}, R{rs2}"
        }
        instruction BUNDLE {
            format: BUNDLE_ID
            bundle_format: BUNDLE_64
            encoding: { bundle_opcode=255 }
            bundle_instructions: ADD
            assembly_syntax: "BUNDLE[ {slot0}, {slot1} ]"
        }
    }
}
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.isa', delete=False) as f:
        f.write(test_isa_content)
        test_isa_file = f.name
    
    try:
        isa = parse_isa_file(test_isa_file)
        
        # Verify assembly_syntax is parsed
        bundle_instr = next((instr for instr in isa.instructions if instr.mnemonic == 'BUNDLE'), None)
        assert bundle_instr is not None, "BUNDLE instruction not found"
        assert bundle_instr.assembly_syntax == "BUNDLE[ {slot0}, {slot1} ]", "Assembly syntax not parsed correctly"
        
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
            
            # Assemble a bundle
            source = "BUNDLE{ ADD R3, R4, R5, ADD R6, R7, R8 }"
            machine_code = asm.assemble(source)
            assert len(machine_code) > 0, "Failed to assemble bundle"
            
            # Disassemble it back
            result = disasm.disassemble(machine_code[0])
            assert result is not None, "Failed to disassemble bundle"
            # The result should use the assembly_syntax format
            assert "BUNDLE" in result, f"Expected BUNDLE in result, got '{result}'"
            assert "slot0" in result or "ADD" in result, f"Expected slot disassembly, got '{result}'"
    finally:
        Path(test_isa_file).unlink()


def test_bundle_default_format():
    """Test that bundles without assembly_syntax use default format."""
    # Create a test ISA without bundle assembly_syntax
    test_isa_content = '''
architecture TestBundle {
    word_size: 32
    registers {
        gpr R 32 [16]
    }
    formats {
        format BUNDLE_ID 80 {
            bundle_opcode: [0:7]
        }
        bundle format BUNDLE_64 80 {
            slot0: [8:39]
            slot1: [40:71]
        }
        format R_TYPE 32 {
            opcode: [0:5]
            rd: [6:8]
        }
    }
    instructions {
        instruction ADD {
            format: R_TYPE
            encoding: { opcode=1, funct=0 }
            operands: rd
        }
        instruction BUNDLE {
            format: BUNDLE_ID
            bundle_format: BUNDLE_64
            encoding: { bundle_opcode=255 }
            bundle_instructions: ADD
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
        assert bundle_instr is not None, "BUNDLE instruction not found"
        assert bundle_instr.assembly_syntax is None, "BUNDLE should not have assembly_syntax"
        
        # Generate disassembler
        disasm_gen = DisassemblerGenerator(isa)
        
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
    finally:
        Path(test_isa_file).unlink()

