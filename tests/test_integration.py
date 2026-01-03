"""Integration tests for end-to-end workflow."""

import pytest
from pathlib import Path
import tempfile
import subprocess
import sys
from isa_dsl.model.parser import parse_isa_file
from isa_dsl.model.validator import ISAValidator
from isa_dsl.generators.simulator import SimulatorGenerator
from isa_dsl.generators.assembler import AssemblerGenerator
from isa_dsl.generators.disassembler import DisassemblerGenerator
from isa_dsl.generators.documentation import DocumentationGenerator


def test_end_to_end_generation():
    """Test end-to-end code generation from ISA spec."""
    isa_file = Path(__file__).parent.parent / 'examples' / 'sample_isa.isa'
    isa = parse_isa_file(str(isa_file))
    
    # Validate
    validator = ISAValidator(isa)
    errors = validator.validate()
    assert len(errors) == 0
    
    # Generate all tools
    with tempfile.TemporaryDirectory() as tmpdir:
        # Simulator
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir)
        assert sim_file.exists()
        
        # Assembler
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir)
        assert asm_file.exists()
        
        # Disassembler
        disasm_gen = DisassemblerGenerator(isa)
        disasm_file = disasm_gen.generate(tmpdir)
        assert disasm_file.exists()
        
        # Documentation
        doc_gen = DocumentationGenerator(isa)
        doc_file = doc_gen.generate(tmpdir)
        assert doc_file.exists()


def test_instruction_encoding_decoding():
    """Test that instructions can be encoded and decoded."""
    isa_file = Path(__file__).parent.parent / 'examples' / 'sample_isa.isa'
    isa = parse_isa_file(str(isa_file))
    
    add_instr = isa.get_instruction('ADD')
    assert add_instr is not None
    
    # Encode an instruction
    operand_values = {'rd': 1, 'rs1': 2, 'rs2': 3}
    encoded = add_instr.encode_instruction(operand_values)
    
    # Decode it back
    decoded_operands = add_instr.decode_operands(encoded)
    
    # Check that operands match
    assert decoded_operands['rd'] == 1
    assert decoded_operands['rs1'] == 2
    assert decoded_operands['rs2'] == 3
    
    # Check that instruction matches its own encoding
    assert add_instr.matches_encoding(encoded)

