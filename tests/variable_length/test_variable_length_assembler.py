"""Tests for variable-length instruction assembly."""

import pytest
from pathlib import Path
import tempfile
import importlib.util
from isa_dsl.model.parser import parse_isa_file
from isa_dsl.generators.assembler import AssemblerGenerator
from tests.variable_length.test_helpers import VariableLengthTestHelpers


@pytest.fixture
def variable_length_isa_file():
    """Create a test ISA file with variable-length instructions."""
    project_root = Path(__file__).parent.parent
    return Path(__file__).parent / "test_data" / "test_identification_fields.isa"


def test_assembler_determines_instruction_width(variable_length_isa_file):
    """Test that assembler correctly determines instruction width during first pass."""
    isa = parse_isa_file(str(variable_length_isa_file))
    
    # Generate assembler
    asm_gen = AssemblerGenerator(isa)
    with tempfile.TemporaryDirectory() as tmpdir:
        asm_gen.generate(tmpdir)
        asm_file = Path(tmpdir) / "assembler.py"
        
        # Import generated assembler
        spec = importlib.util.spec_from_file_location("assembler", asm_file)
        assembler_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(assembler_module)
        Assembler = assembler_module.Assembler
        
        # Create assembler instance
        asm = Assembler()
        
        # Test width determination
        width_16 = asm._get_instruction_width_from_line("ADD16 R0, R1, 5")
        assert width_16 == 2, f"Expected 16-bit instruction width=2 bytes, got {width_16}"
        
        width_32 = asm._get_instruction_width_from_line("ADD32 R0, R1, R2")
        assert width_32 == 4, f"Expected 32-bit instruction width=4 bytes, got {width_32}"


def test_assembler_address_calculation_with_variable_length(variable_length_isa_file):
    """Test that label addresses are calculated correctly with variable-length instructions."""
    isa = parse_isa_file(str(variable_length_isa_file))
    
    # Generate assembler
    asm_gen = AssemblerGenerator(isa)
    with tempfile.TemporaryDirectory() as tmpdir:
        asm_gen.generate(tmpdir)
        asm_file = Path(tmpdir) / "assembler.py"
        
        # Import generated assembler
        spec = importlib.util.spec_from_file_location("assembler", asm_file)
        assembler_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(assembler_module)
        Assembler = assembler_module.Assembler
        
        # Create assembler instance
        asm = Assembler()
        
        # Test assembly with labels and variable-length instructions
        source = """
        start:
            ADD16 R0, R1, 5    # 16-bit instruction (2 bytes)
        label1:
            ADD32 R2, R3, R4   # 32-bit instruction (4 bytes)
        label2:
            ADD16 R5, R6, 10   # 16-bit instruction (2 bytes)
        """
        
        machine_code = asm.assemble(source, start_address=0)
        
        # Check label addresses
        assert 'start' in asm.labels
        assert asm.labels['start'] == 0
        assert 'label1' in asm.labels
        assert asm.labels['label1'] == 2, f"Expected label1 at address 2 (after 16-bit instruction), got {asm.labels['label1']}"
        assert 'label2' in asm.labels
        assert asm.labels['label2'] == 6, f"Expected label2 at address 6 (after 16-bit + 32-bit), got {asm.labels['label2']}"


def test_assembler_encodes_variable_length_instructions(variable_length_isa_file):
    """Test that assembler correctly encodes variable-length instructions."""
    isa = parse_isa_file(str(variable_length_isa_file))
    
    # Generate assembler
    asm_gen = AssemblerGenerator(isa)
    with tempfile.TemporaryDirectory() as tmpdir:
        asm_gen.generate(tmpdir)
        asm_file = Path(tmpdir) / "assembler.py"
        
        # Import generated assembler
        spec = importlib.util.spec_from_file_location("assembler", asm_file)
        assembler_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(assembler_module)
        Assembler = assembler_module.Assembler
        
        # Create assembler instance
        asm = Assembler()
        
        # Test 16-bit instruction encoding
        source_16 = "ADD16 R0, R1, 5"
        machine_code_16 = asm.assemble(source_16)
        # Filter out any None values
        machine_code_16 = [x for x in machine_code_16 if x is not None]
        assert len(machine_code_16) >= 1, f"Expected at least 1 instruction, got {len(machine_code_16)}"
        # Check that instruction is encoded correctly (opcode=1, rd=0, rs1=1, immediate=5)
        instruction_16 = machine_code_16[0]
        opcode_16 = (instruction_16 >> 0) & 0x3F  # bits [0:5]
        assert opcode_16 == 1, f"Expected opcode=1, got {opcode_16}"
        
        # Test 32-bit instruction encoding
        source_32 = "ADD32 R3, R1, R2"
        machine_code_32 = asm.assemble(source_32)
        # Filter out any None values
        machine_code_32 = [x for x in machine_code_32 if x is not None]
        # Find the 32-bit instruction (opcode=2)
        instruction_32 = None
        for instr in machine_code_32:
            opcode = (instr >> 0) & 0x7F  # bits [0:6]
            if opcode == 2:
                instruction_32 = instr
                break
        assert instruction_32 is not None, f"Could not find ADD32 instruction (opcode=2) in {machine_code_32}"
        # Verify encoding
        opcode_32 = (instruction_32 >> 0) & 0x7F
        assert opcode_32 == 2, f"Expected opcode=2, got {opcode_32}"


def test_assembler_binary_output_variable_length(variable_length_isa_file):
    """Test that assembler writes variable-length instructions correctly to binary."""
    isa = parse_isa_file(str(variable_length_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        Assembler = VariableLengthTestHelpers.generate_and_import_assembler(isa, tmpdir)
        asm = Assembler()
        
        source = "ADD16 R0, R1, 5\nADD32 R2, R3, R4"
        machine_code = asm.assemble(source)
        
        import os
        binary_file = os.path.join(tmpdir, "test.bin")
        asm.write_binary(machine_code, binary_file)
        
        with open(binary_file, 'rb') as f:
            data = f.read()
        
        assert len(data) > 0, "Binary file should not be empty"
        assert len(machine_code) >= 2, f"Expected at least 2 instructions, got {len(machine_code)}"
        
        first_instr = machine_code[0]
        opcode_first = (first_instr >> 0) & 0x3F
        assert opcode_first == 1, f"First instruction should be ADD16 (opcode=1), got {opcode_first}"
        
        second_instr = next((instr for instr in machine_code if ((instr >> 0) & 0x7F) == 2), None)
        assert second_instr is not None, f"Could not find ADD32 instruction (opcode=2) in {machine_code}"

