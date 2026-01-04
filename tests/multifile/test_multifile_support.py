"""Tests for multi-file ISA DSL support."""

import pytest
import tempfile
from pathlib import Path
from isa_dsl.model.parser import parse_isa_file

from isa_dsl.model.exceptions import (
    CircularDependencyError,
    DuplicateDefinitionError,
    MultipleInheritanceError,
    ArchitectureExtensionRequiredError,
    PartialDefinitionRequiredError,
)

# Get the test data directory path
TEST_DATA_DIR = Path(__file__).parent / "test_data"


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestCommentSupport:
    """Test comment support (single-line and multi-line)."""
    
    def test_single_line_comments(self, temp_dir):
        """Test that single-line comments are ignored."""
        isa_file = temp_dir / "test.isa"
        isa_file.write_text((TEST_DATA_DIR / "test_single_line_comments.isa").read_text())
        
        isa = parse_isa_file(str(isa_file))
        assert isa.name == 'TestISA'
        assert isa.get_property('word_size') == 32
        assert len(isa.registers) == 1
        assert isa.registers[0].name == 'R'
    
    def test_multi_line_comments(self, temp_dir):
        """Test that multi-line comments are ignored."""
        isa_file = temp_dir / "test.isa"
        isa_file.write_text((TEST_DATA_DIR / "test_multi_line_comments.isa").read_text())
        
        isa = parse_isa_file(str(isa_file))
        assert isa.name == 'TestISA'
        assert len(isa.registers) == 1
    
    def test_comments_in_included_files(self, temp_dir):
        """Test that comments work in included files."""
        registers_file = temp_dir / "test_registers_with_comments.isa"
        registers_file.write_text((TEST_DATA_DIR / "test_registers_with_comments.isa").read_text())
        
        main_file = temp_dir / "test_main_with_comments.isa"
        main_content = (TEST_DATA_DIR / "test_main_with_comments.isa").read_text()
        # Update include path to match the copied file name
        main_content = main_content.replace('test_registers_with_comments.isa', registers_file.name)
        main_file.write_text(main_content)
        
        isa = parse_isa_file(str(main_file))
        assert isa.name == 'TestISA'
        assert len(isa.registers) == 2
        assert isa.get_register('R') is not None
        assert isa.get_register('PC') is not None


class TestIncludeProcessing:
    """Test include statement processing."""
    
    def test_simple_include(self, temp_dir):
        """Test including a single file."""
        registers_file = temp_dir / "test_registers.isa"
        registers_file.write_text((TEST_DATA_DIR / "test_registers.isa").read_text())
        
        main_file = temp_dir / "test_main.isa"
        main_content = (TEST_DATA_DIR / "test_main.isa").read_text()
        # Update include path to match the copied file name
        main_content = main_content.replace('test_registers.isa', registers_file.name)
        main_file.write_text(main_content)
        
        isa = parse_isa_file(str(main_file))
        assert isa.name == 'TestISA'
        assert len(isa.registers) == 2
        assert isa.get_register('R') is not None
        assert isa.get_register('PC') is not None
    
    def test_multiple_includes(self, temp_dir):
        """Test including multiple files."""
        registers_file = temp_dir / "test_registers.isa"
        registers_file.write_text((TEST_DATA_DIR / "test_registers.isa").read_text())
        
        formats_file = temp_dir / "test_formats.isa"
        formats_file.write_text((TEST_DATA_DIR / "test_formats.isa").read_text())
        
        main_file = temp_dir / "test_main_multiple_includes.isa"
        main_content = (TEST_DATA_DIR / "test_main_multiple_includes.isa").read_text()
        # Update include paths to match the copied file names
        main_content = main_content.replace('test_registers.isa', registers_file.name)
        main_content = main_content.replace('test_formats.isa', formats_file.name)
        main_file.write_text(main_content)
        
        isa = parse_isa_file(str(main_file))
        assert isa.name == 'TestISA'
        assert len(isa.registers) == 2  # From included test_registers.isa
        assert len(isa.formats) == 1
        assert isa.get_format('R_TYPE') is not None
    
    def test_nested_includes(self, temp_dir):
        """Test nested includes (A includes B, B includes C)."""
        base_file = temp_dir / "test_base_nested.isa"
        base_file.write_text((TEST_DATA_DIR / "test_base_nested.isa").read_text())
        
        middle_file = temp_dir / "test_middle_nested.isa"
        middle_content = (TEST_DATA_DIR / "test_middle_nested.isa").read_text()
        middle_content = middle_content.replace('test_base_nested.isa', base_file.name)
        middle_file.write_text(middle_content)
        
        main_file = temp_dir / "test_main_nested.isa"
        main_content = (TEST_DATA_DIR / "test_main_nested.isa").read_text()
        main_content = main_content.replace('test_middle_nested.isa', middle_file.name)
        main_file.write_text(main_content)
        
        isa = parse_isa_file(str(main_file))
        assert isa.name == 'TestISA'
        assert len(isa.registers) == 2
        assert isa.get_register('R') is not None
        assert isa.get_register('PC') is not None
    
    def test_relative_path_resolution(self, temp_dir):
        """Test that relative paths are resolved correctly."""
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        
        registers_file = subdir / "test_subdir_registers.isa"
        registers_file.write_text((TEST_DATA_DIR / "test_subdir_registers.isa").read_text())
        
        main_file = temp_dir / "test_main_relative_path.isa"
        main_content = (TEST_DATA_DIR / "test_main_relative_path.isa").read_text()
        main_content = main_content.replace('subdir/test_subdir_registers.isa', f'subdir/{registers_file.name}')
        main_file.write_text(main_content)
        
        isa = parse_isa_file(str(main_file))
        assert len(isa.registers) == 1
        assert isa.get_register('R') is not None
    
    def test_circular_dependency_detection(self, temp_dir):
        """Test that circular dependencies are detected."""
        file_a = temp_dir / "test_circular_a.isa"
        file_a_content = (TEST_DATA_DIR / "test_circular_a.isa").read_text()
        file_a_content = file_a_content.replace('test_circular_b.isa', 'test_circular_b.isa')
        file_a.write_text(file_a_content)
        
        file_b = temp_dir / "test_circular_b.isa"
        file_b_content = (TEST_DATA_DIR / "test_circular_b.isa").read_text()
        file_b_content = file_b_content.replace('test_circular_a.isa', 'test_circular_a.isa')
        file_b.write_text(file_b_content)
        
        main_file = temp_dir / "test_main_circular.isa"
        main_content = (TEST_DATA_DIR / "test_main_circular.isa").read_text()
        main_content = main_content.replace('test_circular_a.isa', file_a.name)
        main_file.write_text(main_content)
        
        with pytest.raises(CircularDependencyError):
            parse_isa_file(str(main_file))


class TestMergeMode:
    """Test merge mode (all files are partial definitions)."""
    
    def test_merge_partial_definitions(self, temp_dir):
        """Test merging partial definitions from multiple files."""
        registers_file = temp_dir / "test_merge_registers.isa"
        registers_file.write_text((TEST_DATA_DIR / "test_merge_registers.isa").read_text())
        
        formats_file = temp_dir / "test_merge_formats.isa"
        formats_file.write_text((TEST_DATA_DIR / "test_merge_formats.isa").read_text())
        
        main_file = temp_dir / "test_main_merge.isa"
        main_content = (TEST_DATA_DIR / "test_main_merge.isa").read_text()
        main_content = main_content.replace('test_merge_registers.isa', registers_file.name)
        main_content = main_content.replace('test_merge_formats.isa', formats_file.name)
        main_file.write_text(main_content)
        
        isa = parse_isa_file(str(main_file))
        assert isa.name == 'TestISA'
        # Should have registers from both files
        assert len(isa.registers) == 3
        assert isa.get_register('R') is not None
        assert isa.get_register('PC') is not None
        assert isa.get_register('SP') is not None
        # Should have formats from both files
        assert len(isa.formats) == 2
        assert isa.get_format('R_TYPE') is not None
        assert isa.get_format('IMM_TYPE') is not None
    
    def test_duplicate_definition_error(self, temp_dir):
        """Test that duplicate definitions cause errors in merge mode."""
        registers_file = temp_dir / "test_duplicate_registers.isa"
        registers_file.write_text((TEST_DATA_DIR / "test_duplicate_registers.isa").read_text())
        
        main_file = temp_dir / "test_main_duplicate.isa"
        main_content = (TEST_DATA_DIR / "test_main_duplicate.isa").read_text()
        main_content = main_content.replace('test_duplicate_registers.isa', registers_file.name)
        main_file.write_text(main_content)
        
        with pytest.raises(DuplicateDefinitionError) as exc_info:
            parse_isa_file(str(main_file))
        assert 'R' in str(exc_info.value)


class TestInheritanceMode:
    """Test inheritance mode (single inheritance with overrides)."""
    
    def test_single_inheritance(self, temp_dir):
        """Test extending a base architecture."""
        base_file = temp_dir / "test_base_isa.isa"
        base_file.write_text((TEST_DATA_DIR / "test_base_isa.isa").read_text())
        
        extended_file = temp_dir / "test_extended_isa.isa"
        extended_content = (TEST_DATA_DIR / "test_extended_isa.isa").read_text()
        extended_content = extended_content.replace('test_base_isa.isa', base_file.name)
        extended_file.write_text(extended_content)
        
        isa = parse_isa_file(str(extended_file))
        assert isa.name == 'ExtendedISA'
        # Properties: word_size overridden, endianness inherited
        assert isa.get_property('word_size') == 64
        assert isa.get_property('endianness') == 'little'
        # Registers: R overridden, PC inherited, SP new
        assert len(isa.registers) == 3
        r_reg = isa.get_register('R')
        assert r_reg.width == 64
        assert r_reg.count == 32
        assert isa.get_register('PC') is not None
        assert isa.get_register('SP') is not None
        # Formats: R_TYPE overridden
        r_type = isa.get_format('R_TYPE')
        assert r_type.width == 64
        assert len(r_type.fields) == 4  # opcode, rd, rs1, funct3
        # Instructions: ADD overridden, SUB new
        assert len(isa.instructions) == 2
        assert isa.get_instruction('ADD') is not None
        assert isa.get_instruction('SUB') is not None
    
    def test_inheritance_with_partial_definitions(self, temp_dir):
        """Test inheritance mode with additional partial definition files."""
        base_file = temp_dir / "test_base_isa_simple.isa"
        base_file.write_text((TEST_DATA_DIR / "test_base_isa_simple.isa").read_text())
        
        additional_registers = temp_dir / "test_additional_registers.isa"
        additional_registers.write_text((TEST_DATA_DIR / "test_additional_registers.isa").read_text())
        
        extended_file = temp_dir / "test_extended_isa_with_partials.isa"
        extended_content = (TEST_DATA_DIR / "test_extended_isa_with_partials.isa").read_text()
        extended_content = extended_content.replace('test_base_isa_simple.isa', base_file.name)
        extended_content = extended_content.replace('test_additional_registers.isa', additional_registers.name)
        extended_file.write_text(extended_content)
        
        isa = parse_isa_file(str(extended_file))
        assert isa.name == 'ExtendedISA'
        # Should have: R (from base), STATUS, CONTROL (from additional), SP (from extended)
        assert len(isa.registers) == 4
        assert isa.get_register('R') is not None
        assert isa.get_register('STATUS') is not None
        assert isa.get_register('CONTROL') is not None
        assert isa.get_register('SP') is not None
    
    def test_multiple_inheritance_error(self, temp_dir):
        """Test that multiple inheritance is not allowed."""
        base1 = temp_dir / "test_base1.isa"
        base1.write_text((TEST_DATA_DIR / "test_base1.isa").read_text())
        
        base2 = temp_dir / "test_base2.isa"
        base2.write_text((TEST_DATA_DIR / "test_base2.isa").read_text())
        
        main_file = temp_dir / "test_main_multiple_inheritance.isa"
        main_content = (TEST_DATA_DIR / "test_main_multiple_inheritance.isa").read_text()
        main_content = main_content.replace('test_base1.isa', base1.name)
        main_content = main_content.replace('test_base2.isa', base2.name)
        main_file.write_text(main_content)
        
        with pytest.raises(MultipleInheritanceError):
            parse_isa_file(str(main_file))
    
    def test_architecture_extension_required_error(self, temp_dir):
        """Test that including an architecture requires extension."""
        base_file = temp_dir / "test_base_isa_simple.isa"
        base_file.write_text((TEST_DATA_DIR / "test_base_isa_simple.isa").read_text())
        
        # File without architecture block trying to include one with architecture
        main_file = temp_dir / "test_main_no_arch.isa"
        main_content = (TEST_DATA_DIR / "test_main_no_arch.isa").read_text()
        main_content = main_content.replace('test_base_isa_simple.isa', base_file.name)
        main_file.write_text(main_content)
        
        with pytest.raises((ArchitectureExtensionRequiredError, ValueError)):
            parse_isa_file(str(main_file))
    
    def test_partial_definition_required_error(self, temp_dir):
        """Test that non-base included files must be partial definitions in inheritance mode."""
        base_file = temp_dir / "test_base_isa_simple.isa"
        base_file.write_text((TEST_DATA_DIR / "test_base_isa_simple.isa").read_text())
        
        another_base = temp_dir / "test_another_base.isa"
        another_base.write_text((TEST_DATA_DIR / "test_another_base.isa").read_text())
        
        main_file = temp_dir / "test_main_partial_error.isa"
        main_content = (TEST_DATA_DIR / "test_main_partial_error.isa").read_text()
        main_content = main_content.replace('test_base_isa_simple.isa', base_file.name)
        main_content = main_content.replace('test_another_base.isa', another_base.name)
        main_file.write_text(main_content)
        
        with pytest.raises((MultipleInheritanceError, PartialDefinitionRequiredError)):
            parse_isa_file(str(main_file))

