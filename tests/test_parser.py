"""Tests for ISA parser."""

import pytest
from pathlib import Path
from isa_dsl.model.parser import parse_isa_file


def test_parse_sample_isa():
    """Test parsing the sample ISA file."""
    isa_file = Path(__file__).parent.parent / 'examples' / 'sample_isa.isa'
    isa = parse_isa_file(str(isa_file))
    
    assert isa.name == 'SimpleRISC'
    assert len(isa.registers) > 0
    assert len(isa.formats) > 0
    assert len(isa.instructions) > 0


def test_isa_properties():
    """Test ISA properties are parsed correctly."""
    isa_file = Path(__file__).parent.parent / 'examples' / 'sample_isa.isa'
    isa = parse_isa_file(str(isa_file))
    
    word_size = isa.get_property('word_size')
    assert word_size == 32


def test_register_parsing():
    """Test register parsing."""
    isa_file = Path(__file__).parent.parent / 'examples' / 'sample_isa.isa'
    isa = parse_isa_file(str(isa_file))
    
    r_reg = isa.get_register('R')
    assert r_reg is not None
    assert r_reg.type == 'gpr'
    assert r_reg.is_register_file()
    assert r_reg.count == 8
    
    pc_reg = isa.get_register('PC')
    assert pc_reg is not None
    assert pc_reg.type == 'sfr'
    assert not pc_reg.is_register_file()


def test_format_parsing():
    """Test instruction format parsing."""
    isa_file = Path(__file__).parent.parent / 'examples' / 'sample_isa.isa'
    isa = parse_isa_file(str(isa_file))
    
    r_type = isa.get_format('R_TYPE')
    assert r_type is not None
    assert r_type.width == 32
    assert len(r_type.fields) > 0


def test_instruction_parsing():
    """Test instruction parsing."""
    isa_file = Path(__file__).parent.parent / 'examples' / 'sample_isa.isa'
    isa = parse_isa_file(str(isa_file))
    
    add_instr = isa.get_instruction('ADD')
    assert add_instr is not None
    assert add_instr.mnemonic == 'ADD'
    assert add_instr.format is not None
    assert len(add_instr.operands) > 0

