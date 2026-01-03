"""Tests for code generators."""

import pytest
from pathlib import Path
import tempfile
import shutil
from isa_dsl.model.parser import parse_isa_file
from isa_dsl.generators.simulator import SimulatorGenerator
from isa_dsl.generators.assembler import AssemblerGenerator
from isa_dsl.generators.disassembler import DisassemblerGenerator
from isa_dsl.generators.documentation import DocumentationGenerator


def test_simulator_generation():
    """Test simulator code generation."""
    isa_file = Path(__file__).parent.parent / 'examples' / 'sample_isa.isa'
    isa = parse_isa_file(str(isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        gen = SimulatorGenerator(isa)
        output_file = gen.generate(tmpdir)
        
        assert output_file.exists()
        code = output_file.read_text()
        assert 'class Simulator' in code
        assert 'SimpleRISC' in code


def test_assembler_generation():
    """Test assembler code generation."""
    isa_file = Path(__file__).parent.parent / 'examples' / 'sample_isa.isa'
    isa = parse_isa_file(str(isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        gen = AssemblerGenerator(isa)
        output_file = gen.generate(tmpdir)
        
        assert output_file.exists()
        code = output_file.read_text()
        assert 'class Assembler' in code


def test_disassembler_generation():
    """Test disassembler code generation."""
    isa_file = Path(__file__).parent.parent / 'examples' / 'sample_isa.isa'
    isa = parse_isa_file(str(isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        gen = DisassemblerGenerator(isa)
        output_file = gen.generate(tmpdir)
        
        assert output_file.exists()
        code = output_file.read_text()
        assert 'class Disassembler' in code


def test_documentation_generation():
    """Test documentation generation."""
    isa_file = Path(__file__).parent.parent / 'examples' / 'sample_isa.isa'
    isa = parse_isa_file(str(isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        gen = DocumentationGenerator(isa)
        output_file = gen.generate(tmpdir)
        
        assert output_file.exists()
        doc = output_file.read_text()
        assert 'SimpleRISC' in doc
        assert 'Instruction Set Architecture' in doc

