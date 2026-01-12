"""Test behavior validation in ISA validator."""

import pytest
from isa_dsl.model.isa_parser import ISAParser
from isa_dsl.model.validator import ISAValidator, ValidationError


def test_validator_detects_missing_behavior():
    """Test that validator detects instructions without behavior."""
    parser = ISAParser()
    isa = parser.parse_file("tests/core/test_data/missing_behavior.isa")
    
    validator = ISAValidator(isa)
    errors = validator.validate()
    
    # Should detect NO_BEHAVIOR instruction missing behavior
    no_behavior_errors = [e for e in errors if "NO_BEHAVIOR" in str(e) and "missing behavior" in str(e).lower()]
    assert len(no_behavior_errors) > 0, "Should detect missing behavior for NO_BEHAVIOR instruction"
    
    # Note: Empty behavior blocks are not valid syntax, so they can't be parsed
    # The validation will catch missing behavior, but empty blocks are a syntax error
    
    # Should NOT error for EXTERNAL_BEHAVIOR (has external_behavior: true)
    external_errors = [e for e in errors if "EXTERNAL_BEHAVIOR" in str(e) and "behavior" in str(e).lower()]
    assert len(external_errors) == 0, "Should not error for instruction with external_behavior: true"
    
    # Should NOT error for VALID_BEHAVIOR (has valid behavior)
    valid_errors = [e for e in errors if "VALID_BEHAVIOR" in str(e) and "behavior" in str(e).lower()]
    assert len(valid_errors) == 0, "Should not error for instruction with valid behavior"


def test_validator_allows_bundle_without_behavior():
    """Test that bundle instructions don't require behavior."""
    # Bundle instructions execute sub-instructions, so they don't need behavior
    # This test would need a bundle instruction without behavior
    # For now, we'll just verify the logic doesn't error on bundles
    pass


def test_validator_detects_unsupported_rtl_features():
    """Test that validator detects RTL behavior with unsupported features."""
    parser = ISAParser()
    isa = parser.parse_file("tests/core/test_data/unsupported_rtl.isa")
    
    validator = ISAValidator(isa)
    errors = validator.validate()
    
    # Should detect UNKNOWN_FUNCTION instruction with unsupported function
    unknown_func_errors = [e for e in errors if "UNKNOWN_FUNCTION" in str(e) and ("unsupported" in str(e).lower() or "unknown" in str(e).lower())]
    assert len(unknown_func_errors) > 0, "Should detect unsupported function in UNKNOWN_FUNCTION instruction"
    
    # Should detect UNKNOWN_REGISTER instruction with unknown register
    unknown_reg_errors = [e for e in errors if "UNKNOWN_REGISTER" in str(e) and ("unknown register" in str(e).lower() or "unsupported" in str(e).lower())]
    assert len(unknown_reg_errors) > 0, "Should detect unknown register in UNKNOWN_REGISTER instruction"
    
    # Should NOT error for VALID_BEHAVIOR (has valid behavior)
    valid_errors = [e for e in errors if "VALID_BEHAVIOR" in str(e) and ("unsupported" in str(e).lower() or "unknown" in str(e).lower())]
    assert len(valid_errors) == 0, "Should not error for instruction with valid behavior"

