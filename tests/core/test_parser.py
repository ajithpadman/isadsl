"""Tests for ISA parser."""

import pytest
from pathlib import Path
from isa_dsl.model.parser import parse_isa_file


def test_parse_sample_isa():
    """Test parsing the sample ISA file."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'sample_isa.isa'
    isa = parse_isa_file(str(isa_file))
    
    assert isa.name == 'SimpleRISC'
    assert len(isa.registers) > 0
    assert len(isa.formats) > 0
    assert len(isa.instructions) > 0


def test_isa_properties():
    """Test ISA properties are parsed correctly."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'sample_isa.isa'
    isa = parse_isa_file(str(isa_file))
    
    word_size = isa.get_property('word_size')
    assert word_size == 32


def test_register_parsing():
    """Test register parsing."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'sample_isa.isa'
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
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'sample_isa.isa'
    isa = parse_isa_file(str(isa_file))
    
    r_type = isa.get_format('R_TYPE')
    assert r_type is not None
    assert r_type.width == 32
    assert len(r_type.fields) > 0


def test_instruction_parsing():
    """Test instruction parsing."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'sample_isa.isa'
    isa = parse_isa_file(str(isa_file))
    
    add_instr = isa.get_instruction('ADD')
    assert add_instr is not None
    assert add_instr.mnemonic == 'ADD'
    assert add_instr.format is not None
    assert len(add_instr.operands) > 0


# Tests for Phase 1: Identification Fields

def test_format_with_single_identification_field():
    """Test parsing format with single identification field."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'test_identification_fields.isa'
    isa = parse_isa_file(str(isa_file))
    
    short_format = isa.get_format('SHORT_16')
    assert short_format is not None
    assert short_format.identification_fields == ['opcode']
    
    # Test get_identification_fields() returns FormatField objects
    id_fields = short_format.get_identification_fields()
    assert len(id_fields) == 1
    assert id_fields[0].name == 'opcode'
    assert id_fields[0].lsb == 0
    assert id_fields[0].msb == 5
    
    # Test minimum bits calculation
    min_bits = short_format.get_minimum_bits_for_identification()
    assert min_bits == 6  # opcode is at [0:5], so need 6 bits


def test_format_with_multiple_identification_fields():
    """Test parsing format with multiple identification fields."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'test_identification_fields.isa'
    isa = parse_isa_file(str(isa_file))
    
    long_format = isa.get_format('LONG_32')
    assert long_format is not None
    assert long_format.identification_fields == ['opcode', 'funct']
    
    # Test get_identification_fields() returns both fields
    id_fields = long_format.get_identification_fields()
    assert len(id_fields) == 2
    field_names = [f.name for f in id_fields]
    assert 'opcode' in field_names
    assert 'funct' in field_names
    
    # Test minimum bits calculation (should be max of all identification fields)
    min_bits = long_format.get_minimum_bits_for_identification()
    # opcode is at [0:6] (7 bits), funct is at [7:10] (4 bits)
    # So we need 11 bits total (0-10)
    assert min_bits == 11


def test_format_with_distributed_identification_fields():
    """Test parsing format with distributed identification fields."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'test_identification_fields.isa'
    isa = parse_isa_file(str(isa_file))
    
    dist_format = isa.get_format('DIST_32')
    assert dist_format is not None
    assert dist_format.identification_fields == ['opcode_low', 'opcode_high']
    
    # Test get_identification_fields() returns both distributed fields
    id_fields = dist_format.get_identification_fields()
    assert len(id_fields) == 2
    field_names = [f.name for f in id_fields]
    assert 'opcode_low' in field_names
    assert 'opcode_high' in field_names
    
    # Find the fields
    opcode_low = next(f for f in id_fields if f.name == 'opcode_low')
    opcode_high = next(f for f in id_fields if f.name == 'opcode_high')
    assert opcode_low.lsb == 0
    assert opcode_low.msb == 3
    assert opcode_high.lsb == 20
    assert opcode_high.msb == 23
    
    # Test minimum bits calculation (should cover both fields)
    min_bits = dist_format.get_minimum_bits_for_identification()
    # opcode_high is at [20:23], so we need 24 bits total
    assert min_bits == 24


def test_format_without_identification_fields():
    """Test backward compatibility: format without identification_fields."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'test_identification_fields.isa'
    isa = parse_isa_file(str(isa_file))
    
    no_id_format = isa.get_format('NO_ID_32')
    assert no_id_format is not None
    assert no_id_format.identification_fields == []
    
    # Test get_identification_fields() returns empty list
    id_fields = no_id_format.get_identification_fields()
    assert len(id_fields) == 0
    
    # Test minimum bits calculation (should default to format width)
    min_bits = no_id_format.get_minimum_bits_for_identification()
    assert min_bits == 32  # Defaults to format width


def test_bundle_format_identification_fields():
    """Test parsing bundle format with identification fields."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'test_identification_fields.isa'
    isa = parse_isa_file(str(isa_file))
    
    bundle_format = isa.get_bundle_format('BUNDLE_64')
    assert bundle_format is not None
    # Bundle formats don't have fields, so identification_fields would be empty
    # But we can test that the attribute exists
    assert hasattr(bundle_format, 'identification_fields')
    assert bundle_format.identification_fields == []
    
    # Test minimum bits calculation for bundle
    min_bits = bundle_format.get_minimum_bits_for_identification()
    assert min_bits == 32  # Default for bundles


def test_bundle_instruction_format_identification_fields():
    """Test bundle instruction's format with identification fields."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'test_identification_fields.isa'
    isa = parse_isa_file(str(isa_file))
    
    # Test the BUNDLE_ID format used for bundle identification
    bundle_id_format = isa.get_format('BUNDLE_ID')
    assert bundle_id_format is not None
    assert bundle_id_format.identification_fields == ['bundle_opcode']
    
    id_fields = bundle_id_format.get_identification_fields()
    assert len(id_fields) == 1
    assert id_fields[0].name == 'bundle_opcode'
    assert id_fields[0].lsb == 0
    assert id_fields[0].msb == 7
    
    min_bits = bundle_id_format.get_minimum_bits_for_identification()
    assert min_bits == 8  # bundle_opcode is at [0:7], so need 8 bits


def test_backward_compatibility_existing_isa():
    """Test that existing ISAs without identification_fields still work."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'sample_isa.isa'
    isa = parse_isa_file(str(isa_file))
    
    r_type = isa.get_format('R_TYPE')
    assert r_type is not None
    # Should have empty identification_fields list
    assert r_type.identification_fields == []
    
    # Should default to format width for minimum bits
    min_bits = r_type.get_minimum_bits_for_identification()
    assert min_bits == 32  # R_TYPE is 32 bits
    
    # get_identification_fields() should return empty list
    id_fields = r_type.get_identification_fields()
    assert len(id_fields) == 0


def test_comprehensive_isa_backward_compatibility():
    """Test comprehensive ISA for backward compatibility."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'comprehensive.isa'
    isa = parse_isa_file(str(isa_file))
    
    # Test all formats have identification_fields attribute (even if empty)
    for fmt in isa.formats:
        assert hasattr(fmt, 'identification_fields')
        # Existing formats should have empty identification_fields
        assert isinstance(fmt.identification_fields, list)
    
    # Test all bundle formats have identification_fields attribute
    for bundle_fmt in isa.bundle_formats:
        assert hasattr(bundle_fmt, 'identification_fields')
        assert isinstance(bundle_fmt.identification_fields, list)
    
    # Test that minimum bits calculation works for all formats
    for fmt in isa.formats:
        min_bits = fmt.get_minimum_bits_for_identification()
        assert min_bits > 0
        assert min_bits <= fmt.width


def test_identification_fields_field_validation():
    """Test that identification_fields reference valid format fields."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'test_identification_fields.isa'
    isa = parse_isa_file(str(isa_file))
    
    short_format = isa.get_format('SHORT_16')
    # 'opcode' should be a valid field
    opcode_field = short_format.get_field('opcode')
    assert opcode_field is not None
    
    # get_identification_fields() should return the actual field
    id_fields = short_format.get_identification_fields()
    assert len(id_fields) == 1
    assert id_fields[0] == opcode_field


def test_minimum_bits_edge_cases():
    """Test minimum bits calculation for edge cases."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'test_identification_fields.isa'
    isa = parse_isa_file(str(isa_file))
    
    # Test format with identification field at bit 0
    short_format = isa.get_format('SHORT_16')
    min_bits = short_format.get_minimum_bits_for_identification()
    assert min_bits == 6  # opcode [0:5] needs 6 bits
    
    # Test format with identification field not starting at 0
    dist_format = isa.get_format('DIST_32')
    min_bits = dist_format.get_minimum_bits_for_identification()
    # opcode_high is at [20:23], so we need 24 bits
    assert min_bits == 24
    
    # Test format without identification_fields defaults to width
    no_id_format = isa.get_format('NO_ID_32')
    min_bits = no_id_format.get_minimum_bits_for_identification()
    assert min_bits == 32

