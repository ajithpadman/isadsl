"""TriCore end-to-end workflow tests."""

import pytest
import tempfile
import sys
from pathlib import Path

from isa_dsl.model.parser import parse_isa_file
from tests.tricore.test_helpers import TriCoreTestHelpers


@pytest.fixture
def tricore_isa_file():
    """Fixture providing path to TriCore ISA file."""
    return Path(__file__).parent / "test_data" / "arch.isa"


@pytest.fixture
def tricore_code_file():
    """Fixture providing path to TriCore assembly code file."""
    return Path(__file__).parent / "test_data" / "code.s"


def test_tricore_abs_instruction_end_to_end(tricore_isa_file, tricore_code_file):
    """
    Test complete end-to-end workflow for TriCore ABS instruction:
    1. Assemble code.s into binary using generated assembler
    2. Run it in simulator with D2 set to a negative value
    3. Verify D3 contains the absolute value of D2
    """
    # Parse ISA
    isa = parse_isa_file(str(tricore_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Generate all tools
        sim_file, asm_file, disasm_file = TriCoreTestHelpers.generate_all_tools(isa, tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            # Import generated tools
            Assembler, Simulator, Disassembler = TriCoreTestHelpers.import_all_tools(
                sim_file, asm_file, disasm_file, tmpdir_path
            )
            
            # Create instances
            assembler = Assembler()
            sim = Simulator()
            disassembler = Disassembler()
            
            # Read assembly code from file
            assembly_code = tricore_code_file.read_text().strip()
            assert "ABS" in assembly_code, "Assembly code should contain ABS instruction"
            
            # Assemble the code
            machine_code = assembler.assemble(assembly_code)
            assert len(machine_code) > 0, "Should assemble at least one instruction"
            
            # Write binary file for disassembler
            binary_file = tmpdir_path / "test.bin"
            TriCoreTestHelpers.write_machine_code_to_file(machine_code, binary_file)
            
            # Load program into simulator
            sim.load_binary_file(str(binary_file), start_address=0)
            
            # Set D2 to a negative value to test absolute value calculation
            test_value = -42
            sim.D[2] = test_value
            expected_abs_value = abs(test_value)  # Should be 42
            
            # Verify initial state
            assert sim.D[2] == test_value, f"D2 should be {test_value} initially"
            assert sim.D[3] == 0, "D3 should be 0 initially"
            
            # Execute the ABS instruction
            executed = sim.step()
            assert executed, "ABS instruction should execute successfully"
            
            # Verify D3 contains the absolute value of D2
            assert sim.D[3] == expected_abs_value, \
                f"D3 should contain absolute value of D2: expected {expected_abs_value}, got {sim.D[3]}"
            
            # Verify D2 is unchanged
            assert sim.D[2] == test_value, "D2 should remain unchanged"
            
            # Test with positive value
            sim.D[2] = 100
            sim.D[3] = 0
            sim.pc = 0
            sim.load_binary_file(str(binary_file), start_address=0)
            
            executed = sim.step()
            assert executed, "ABS instruction should execute successfully with positive value"
            assert sim.D[3] == 100, "D3 should contain 100 (absolute value of positive 100)"
            
            # Test disassembler
            disassembly = disassembler.disassemble_file(str(binary_file))
            assert len(disassembly) > 0, "Should disassemble at least one instruction"
            
            # Verify disassembly contains ABS instruction
            disasm_text = "\n".join([f"{addr:08x}: {asm}" for addr, asm in disassembly])
            assert "ABS" in disasm_text.upper(), "Disassembly should contain ABS instruction"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_tricore_abs_with_zero(tricore_isa_file, tricore_code_file):
    """Test ABS instruction with zero value."""
    isa = parse_isa_file(str(tricore_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        sim_file, asm_file, _ = TriCoreTestHelpers.generate_all_tools(isa, tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            Assembler, Simulator, _ = TriCoreTestHelpers.import_all_tools(
                sim_file, asm_file, None, tmpdir_path
            )
            
            assembler = Assembler()
            sim = Simulator()
            
            assembly_code = tricore_code_file.read_text()
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            TriCoreTestHelpers.write_machine_code_to_file(machine_code, binary_file)
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.D[2] = 0
            sim.D[3] = 0
            
            executed = sim.step()
            assert executed, "ABS instruction should execute successfully with zero"
            assert sim.D[3] == 0, "D3 should be 0 (absolute value of 0)"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_tricore_abs_with_max_negative(tricore_isa_file, tricore_code_file):
    """Test ABS instruction with maximum negative value."""
    isa = parse_isa_file(str(tricore_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        sim_file, asm_file, _ = TriCoreTestHelpers.generate_all_tools(isa, tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            Assembler, Simulator, _ = TriCoreTestHelpers.import_all_tools(
                sim_file, asm_file, None, tmpdir_path
            )
            
            assembler = Assembler()
            sim = Simulator()
            
            assembly_code = tricore_code_file.read_text()
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            TriCoreTestHelpers.write_machine_code_to_file(machine_code, binary_file)
            
            sim.load_binary_file(str(binary_file), start_address=0)
            # Maximum negative 32-bit signed integer
            max_negative = -0x80000000
            sim.D[2] = max_negative
            sim.D[3] = 0
            
            executed = sim.step()
            assert executed, "ABS instruction should execute successfully with max negative"
            # Absolute value of -0x80000000 is 0x80000000 (which is > 0x7FFFFFFF, so overflow flag should be set)
            expected_value = 0x80000000
            assert sim.D[3] == expected_value, \
                f"D3 should contain {expected_value:08x} (absolute value of max negative)"
            # PSW.V should be set due to overflow
            # PSW is stored as an integer, V is bit 30 (field V:[30:30])
            # Check if PSW_V attribute exists (generated by RTL interpreter), otherwise use bit manipulation
            if hasattr(sim, 'PSW_V'):
                psw_v = sim.PSW_V
            else:
                # Fallback: extract bit 30 from PSW register
                psw_v = (sim.PSW >> 30) & 1
            assert psw_v == 1, f"PSW.V should be set due to overflow, got {psw_v} (PSW=0x{sim.PSW:08x})"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_tricore_abs_b_with_run(tricore_isa_file, tricore_code_file):
    """Test ABS.B instruction using sim.run() to catch negative shift count issue."""
    isa = parse_isa_file(str(tricore_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        sim_file, asm_file, _ = TriCoreTestHelpers.generate_all_tools(isa, tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            Assembler, Simulator, _ = TriCoreTestHelpers.import_all_tools(
                sim_file, asm_file, None, tmpdir_path
            )
            
            assembler = Assembler()
            sim = Simulator()
            
            # Assemble code that includes ABS.B
            assembly_code = tricore_code_file.read_text()
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            TriCoreTestHelpers.write_machine_code_to_file(machine_code, binary_file)
            
            sim.load_binary_file(str(binary_file), start_address=0)
            # Set D2 to a value with negative bytes to test ABS.B
            # 0xFFF1F1F1 has negative bytes: 0xFF (-1), 0xF1 (-15), 0xF1 (-15), 0xF1 (-15)
            sim.D[2] = 0xFFF1F1F1
            sim.D[4] = 0
            
            # Use run() instead of step() to catch the negative shift count issue
            sim.run(max_steps=10)
            
            # After ABS.B, D4 should contain absolute values of each byte
            # 0xFF -> 0x01, 0xF1 -> 0x0F, 0xF1 -> 0x0F, 0xF1 -> 0x0F
            # Result: 0x010F0F0F
            expected_value = 0x010F0F0F
            assert sim.D[4] == expected_value, \
                f"D4 should contain 0x{expected_value:08x}, got 0x{sim.D[4]:08x}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))

