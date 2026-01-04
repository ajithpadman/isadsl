"""Tests for ISA validator."""

import pytest
from pathlib import Path
from isa_dsl.model.parser import parse_isa_file
from isa_dsl.model.validator import ISAValidator


def test_validate_sample_isa():
    """Test validation of sample ISA."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'sample_isa.isa'
    isa = parse_isa_file(str(isa_file))
    
    validator = ISAValidator(isa)
    errors = validator.validate()
    
    # Sample ISA should be valid
    assert len(errors) == 0, f"Validation errors: {[str(e) for e in errors]}"


def test_format_validation():
    """Test format field validation."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'sample_isa.isa'
    isa = parse_isa_file(str(isa_file))
    
    # All formats should be valid
    validator = ISAValidator(isa)
    errors = validator.validate()
    
    format_errors = [e for e in errors if 'format' in e.message.lower()]
    assert len(format_errors) == 0


def test_instruction_validation():
    """Test instruction validation."""
    test_data_dir = Path(__file__).parent / "test_data"
    isa_file = test_data_dir / 'sample_isa.isa'
    isa = parse_isa_file(str(isa_file))
    
    validator = ISAValidator(isa)
    errors = validator.validate()
    
    # Check that all instructions reference valid formats
    instruction_errors = [e for e in errors if 'instruction' in e.message.lower()]
    assert len(instruction_errors) == 0

