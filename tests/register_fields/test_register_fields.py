"""Tests for register fields with C union-like behavior in simulator execution."""

import pytest
import tempfile
import sys
import importlib.util
from pathlib import Path

from isa_dsl.model.parser import parse_isa_file
from isa_dsl.generators.simulator import SimulatorGenerator
from isa_dsl.generators.assembler import AssemblerGenerator


@pytest.fixture
def register_fields_isa_file():
    """Fixture providing path to register fields test ISA file."""
    return Path(__file__).parent / "test_data" / "register_fields.isa"


def test_field_update_reflected_in_simulator(register_fields_isa_file):
    """
    Test that field updates in behavior are correctly reflected in simulator execution.
    
    This test verifies:
    1. Setting a field (PSW.V = 1) updates the field correctly
    2. The full register value reflects the field change
    3. Other fields remain unchanged
    """
    # Parse ISA
    isa = parse_isa_file(str(register_fields_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Generate simulator and assembler
        sim_gen = SimulatorGenerator(isa)
        asm_gen = AssemblerGenerator(isa)
        
        sim_file = sim_gen.generate(tmpdir_path)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            # Import generated tools using spec_from_file_location to avoid module caching
            # This ensures each test gets a fresh module instance
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            
            Simulator = sim_module.Simulator
            Assembler = asm_module.Assembler
            
            # Create fresh instances for each test
            assembler = Assembler()
            sim = Simulator()
            
            # Assemble SET_V instruction (sets PSW.V = 1)
            assembly_code = "SET_V R0"
            machine_code = assembler.assemble(assembly_code)
            
            # Load program into simulator
            from tests.tricore.test_helpers import TriCoreTestHelpers
            binary_file = tmpdir_path / "test.bin"
            TriCoreTestHelpers.write_machine_code_to_file(machine_code, binary_file)
            sim.load_binary_file(str(binary_file), start_address=0)
            
            # Initial state: PSW should be 0
            assert int(sim.PSW) == 0, "PSW should be 0 initially"
            assert sim.PSW.V == 0, "PSW.V should be 0 initially"
            assert sim.PSW.SV == 0, "PSW.SV should be 0 initially"
            assert sim.PSW.AV == 0, "PSW.AV should be 0 initially"
            assert sim.PSW.C == 0, "PSW.C should be 0 initially"
            
            # Execute SET_V instruction
            executed = sim.step()
            assert executed, "SET_V instruction should execute successfully"
            
            # Verify field was set
            assert sim.PSW.V == 1, "PSW.V should be 1 after SET_V"
            
            # Verify full register value reflects the field change
            # V is bit 30, so value should be 0x40000000 (1 << 30)
            expected_value = 1 << 30
            assert int(sim.PSW) == expected_value, f"PSW should be 0x{expected_value:x} after setting V flag"
            
            # Verify other fields remain unchanged
            assert sim.PSW.SV == 0, "PSW.SV should remain 0"
            assert sim.PSW.AV == 0, "PSW.AV should remain 0"
            assert sim.PSW.C == 0, "PSW.C should remain 0"
            
        finally:
            sys.path.remove(str(tmpdir_path))


def test_multiple_field_updates(register_fields_isa_file):
    """
    Test that multiple field updates work correctly.
    
    This test verifies:
    1. Setting multiple fields updates all fields correctly
    2. The full register value reflects all field changes
    """
    # Parse ISA
    isa = parse_isa_file(str(register_fields_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Generate simulator and assembler
        sim_gen = SimulatorGenerator(isa)
        asm_gen = AssemblerGenerator(isa)
        
        sim_file = sim_gen.generate(tmpdir_path)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            # Import generated tools using spec_from_file_location to avoid module caching
            # This ensures each test gets a fresh module instance
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            
            Simulator = sim_module.Simulator
            Assembler = asm_module.Assembler
            
            # Create fresh instances for each test
            assembler = Assembler()
            sim = Simulator()
            
            # Assemble SET_FLAGS instruction (sets all flags)
            assembly_code = "SET_FLAGS R0"
            machine_code = assembler.assemble(assembly_code)
            
            # Load program into simulator
            from tests.tricore.test_helpers import TriCoreTestHelpers
            binary_file = tmpdir_path / "test.bin"
            TriCoreTestHelpers.write_machine_code_to_file(machine_code, binary_file)
            sim.load_binary_file(str(binary_file), start_address=0)
            
            # Execute SET_FLAGS instruction
            executed = sim.step()
            assert executed, "SET_FLAGS instruction should execute successfully"
            
            # Verify all fields were set
            assert sim.PSW.V == 1, "PSW.V should be 1"
            assert sim.PSW.SV == 1, "PSW.SV should be 1"
            assert sim.PSW.AV == 1, "PSW.AV should be 1"
            assert sim.PSW.C == 1, "PSW.C should be 1"
            
            # Verify full register value
            # Bits: C=31, V=30, SV=29, AV=28
            # Value = (1 << 31) | (1 << 30) | (1 << 29) | (1 << 28)
            expected_value = (1 << 31) | (1 << 30) | (1 << 29) | (1 << 28)
            assert int(sim.PSW) == expected_value, f"PSW should be 0x{expected_value:x} after setting all flags"
            
        finally:
            sys.path.remove(str(tmpdir_path))


def test_field_clear(register_fields_isa_file):
    """
    Test that clearing a field works correctly.
    
    This test verifies:
    1. Clearing a field (PSW.V = 0) works correctly
    2. Other fields remain unchanged when clearing one field
    """
    # Parse ISA
    isa = parse_isa_file(str(register_fields_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Generate simulator and assembler
        sim_gen = SimulatorGenerator(isa)
        asm_gen = AssemblerGenerator(isa)
        
        sim_file = sim_gen.generate(tmpdir_path)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            # Import generated tools using spec_from_file_location to avoid module caching
            # This ensures each test gets a fresh module instance
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            
            Simulator = sim_module.Simulator
            Assembler = asm_module.Assembler
            
            # Create fresh instances for each test
            assembler = Assembler()
            sim = Simulator()
            
            # First set all flags
            sim.PSW.V = 1
            sim.PSW.SV = 1
            sim.PSW.AV = 1
            sim.PSW.C = 1
            
            # Verify all flags are set
            assert sim.PSW.V == 1, "PSW.V should be 1"
            assert sim.PSW.SV == 1, "PSW.SV should be 1"
            
            # Assemble CLEAR_V instruction (clears PSW.V = 0)
            assembly_code = "CLEAR_V R0"
            machine_code = assembler.assemble(assembly_code)
            
            # Load program into simulator
            from tests.tricore.test_helpers import TriCoreTestHelpers
            binary_file = tmpdir_path / "test.bin"
            TriCoreTestHelpers.write_machine_code_to_file(machine_code, binary_file)
            sim.load_binary_file(str(binary_file), start_address=0)
            
            # Execute CLEAR_V instruction
            executed = sim.step()
            assert executed, "CLEAR_V instruction should execute successfully"
            
            # Verify V was cleared
            assert sim.PSW.V == 0, "PSW.V should be 0 after CLEAR_V"
            
            # Verify other fields remain set
            assert sim.PSW.SV == 1, "PSW.SV should remain 1"
            assert sim.PSW.AV == 1, "PSW.AV should remain 1"
            assert sim.PSW.C == 1, "PSW.C should remain 1"
            
            # Verify full register value (V bit cleared, others remain)
            expected_value = (1 << 31) | (1 << 29) | (1 << 28)  # C, SV, AV set, V cleared
            assert int(sim.PSW) == expected_value, f"PSW should be 0x{expected_value:x} after clearing V"
            
        finally:
            sys.path.remove(str(tmpdir_path))


def test_full_register_update(register_fields_isa_file):
    """
    Test that full register updates are correctly reflected in fields.
    
    This test verifies:
    1. Setting the full register (PSW = value) updates all fields correctly
    2. Field values match the bit positions in the full register value
    """
    # Parse ISA
    isa = parse_isa_file(str(register_fields_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Generate simulator and assembler
        sim_gen = SimulatorGenerator(isa)
        asm_gen = AssemblerGenerator(isa)
        
        sim_file = sim_gen.generate(tmpdir_path)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            # Import generated tools using spec_from_file_location to avoid module caching
            # This ensures each test gets a fresh module instance
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            
            Simulator = sim_module.Simulator
            Assembler = asm_module.Assembler
            
            # Create fresh instances for each test
            assembler = Assembler()
            sim = Simulator()
            
            # Test value: set all flags (C, V, SV, AV)
            # Immediate field is bits 12-31 (20 bits), behavior shifts it left by 12
            # To set bits 28-31 in PSW, we need PSW = 0xF0000000
            # Since behavior does: PSW = imm << 12, we need imm = 0xF0000
            # So we pass 0xF0000 to the assembler
            test_value = (1 << 31) | (1 << 30) | (1 << 29) | (1 << 28)  # 0xF0000000
            imm_field_value = test_value >> 12  # 0xF0000 (20 bits)
            
            # Assemble SET_PSW instruction (sets PSW = imm << 12)
            assembly_code = f"SET_PSW R0, 0x{imm_field_value:x}"
            machine_code = assembler.assemble(assembly_code)
            assert len(machine_code) > 0, "Should assemble at least one instruction"
            
            # Load program into simulator
            from tests.tricore.test_helpers import TriCoreTestHelpers
            binary_file = tmpdir_path / "test.bin"
            TriCoreTestHelpers.write_machine_code_to_file(machine_code, binary_file)
            sim.load_binary_file(str(binary_file), start_address=0)
            
            # Execute SET_PSW instruction
            executed = sim.step()
            assert executed, "SET_PSW instruction should execute successfully"
            
            # Verify full register value
            psw_value = int(sim.PSW) if hasattr(sim.PSW, '__int__') else sim.PSW
            assert psw_value == test_value, f"PSW should be 0x{test_value:x}, got 0x{psw_value:x}"
            
            # Verify all fields are set correctly
            # PSW should be a Register object with fields
            if hasattr(sim.PSW, 'V'):
                assert sim.PSW.C == 1, "PSW.C should be 1 (bit 31)"
                assert sim.PSW.V == 1, "PSW.V should be 1 (bit 30)"
                assert sim.PSW.SV == 1, "PSW.SV should be 1 (bit 29)"
                assert sim.PSW.AV == 1, "PSW.AV should be 1 (bit 28)"
            else:
                # Fallback: check bits directly
                psw_int = int(sim.PSW) if hasattr(sim.PSW, '__int__') else sim.PSW
                assert (psw_int >> 31) & 1 == 1, "PSW.C should be 1 (bit 31)"
                assert (psw_int >> 30) & 1 == 1, "PSW.V should be 1 (bit 30)"
                assert (psw_int >> 29) & 1 == 1, "PSW.SV should be 1 (bit 29)"
                assert (psw_int >> 28) & 1 == 1, "PSW.AV should be 1 (bit 28)"
            
            # Test with different value: only V flag set - use a completely fresh setup
            # Create new assembler and simulator instances to avoid any state issues
            asm_gen2 = AssemblerGenerator(isa)
            asm_file2 = asm_gen2.generate(tmpdir_path)
            asm_spec2 = importlib.util.spec_from_file_location("assembler2", asm_file2)
            asm_module2 = importlib.util.module_from_spec(asm_spec2)
            asm_spec2.loader.exec_module(asm_module2)
            Assembler2 = asm_module2.Assembler
            assembler2 = Assembler2()
            
            sim2 = Simulator()
            test_value2 = 1 << 30  # Only V flag (bit 30)
            imm_field_value2 = test_value2 >> 12  # Extract immediate field value (0x40000)
            assembly_code2 = f"SET_PSW R0, 0x{imm_field_value2:x}"
            machine_code2 = assembler2.assemble(assembly_code2)
            assert len(machine_code2) > 0, "Should assemble SET_PSW instruction"
            
            binary_file2 = tmpdir_path / "test2.bin"  # Use a different file to avoid conflicts
            TriCoreTestHelpers.write_machine_code_to_file(machine_code2, binary_file2)
            sim2.load_binary_file(str(binary_file2), start_address=0)
            
            executed = sim2.step()
            assert executed, "SET_PSW instruction should execute successfully"
            
            # Verify only V flag is set
            psw_value2 = int(sim2.PSW) if hasattr(sim2.PSW, '__int__') else sim2.PSW
            assert psw_value2 == test_value2, f"PSW should be 0x{test_value2:x}, got 0x{psw_value2:x}"
            
            if hasattr(sim2.PSW, 'V'):
                assert sim2.PSW.V == 1, "PSW.V should be 1"
                assert sim2.PSW.SV == 0, "PSW.SV should be 0"
                assert sim2.PSW.AV == 0, "PSW.AV should be 0"
                assert sim2.PSW.C == 0, "PSW.C should be 0"
            else:
                # Fallback: check bits directly
                assert (psw_value2 >> 30) & 1 == 1, "PSW.V should be 1"
                assert (psw_value2 >> 29) & 1 == 0, "PSW.SV should be 0"
                assert (psw_value2 >> 28) & 1 == 0, "PSW.AV should be 0"
                assert (psw_value2 >> 31) & 1 == 0, "PSW.C should be 0"
            
        finally:
            sys.path.remove(str(tmpdir_path))


def test_field_read_in_condition(register_fields_isa_file):
    """
    Test that field reads in conditions work correctly.
    
    This test verifies:
    1. Reading a field in a condition (if (PSW.V)) works correctly
    2. The condition evaluates based on the field value
    """
    # Parse ISA
    isa = parse_isa_file(str(register_fields_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Generate simulator and assembler
        sim_gen = SimulatorGenerator(isa)
        asm_gen = AssemblerGenerator(isa)
        
        sim_file = sim_gen.generate(tmpdir_path)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            # Import generated tools using spec_from_file_location to avoid module caching
            # This ensures each test gets a fresh module instance
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            
            Simulator = sim_module.Simulator
            Assembler = asm_module.Assembler
            
            # Create fresh instances for each test
            assembler = Assembler()
            sim = Simulator()
            
            # First set V flag using SET_V instruction
            assembly_code_set = "SET_V R0"
            machine_code_set = assembler.assemble(assembly_code_set)
            
            from tests.tricore.test_helpers import TriCoreTestHelpers
            binary_file = tmpdir_path / "test.bin"
            TriCoreTestHelpers.write_machine_code_to_file(machine_code_set, binary_file)
            sim.load_binary_file(str(binary_file), start_address=0)
            
            # Execute SET_V to set PSW.V = 1
            executed = sim.step()
            assert executed, "SET_V instruction should execute successfully"
            
            # Verify V flag is set
            if hasattr(sim.PSW, 'V'):
                psw_v = sim.PSW.V
                assert psw_v == 1, f"PSW.V should be 1, got {psw_v}"
            else:
                psw_int = int(sim.PSW) if hasattr(sim.PSW, '__int__') else sim.PSW
                assert (psw_int >> 30) & 1 == 1, f"PSW.V should be 1, got {(psw_int >> 30) & 1}"
            
            # Assemble CHECK_V instruction (if (PSW.V) R[rd] = 1 else R[rd] = 0)
            assembly_code = "CHECK_V R1"
            machine_code = assembler.assemble(assembly_code)
            assert len(machine_code) > 0, "Should assemble CHECK_V instruction"
            
            # Combine both instructions and load fresh
            all_code = machine_code_set + machine_code
            TriCoreTestHelpers.write_machine_code_to_file(all_code, binary_file)
            sim.load_binary_file(str(binary_file), start_address=0)
            
            # Execute SET_V first
            executed1 = sim.step()
            assert executed1, "SET_V instruction should execute successfully"
            
            # Verify PSW.V is still 1 after SET_V
            if hasattr(sim.PSW, 'V'):
                psw_v_value = sim.PSW.V
                assert psw_v_value == 1, f"PSW.V should be 1 after SET_V, got {psw_v_value}"
            else:
                psw_int = int(sim.PSW) if hasattr(sim.PSW, '__int__') else sim.PSW
                psw_v_bit = (psw_int >> 30) & 1
                assert psw_v_bit == 1, f"PSW.V (bit 30) should be 1 after SET_V, got {psw_v_bit}"
            
            # Execute CHECK_V instruction
            executed = sim.step()
            assert executed, "CHECK_V instruction should execute successfully"
            
            # Verify R[1] was set to 1 because PSW.V was 1
            # Note: The condition `if (PSW.V != 0)` should evaluate to True when PSW.V == 1
            r1_value = sim.R[1]
            assert r1_value == 1, f"R[1] should be 1 when PSW.V is 1, got {r1_value}"
            
            # Now test with V flag cleared - create a new simulator instance
            sim2 = Simulator()
            
            # Use CLEAR_V instruction
            assembly_code_clear = "CLEAR_V R0"
            machine_code_clear = assembler.assemble(assembly_code_clear)
            
            # Combine CLEAR_V and CHECK_V
            all_code2 = machine_code_clear + machine_code
            TriCoreTestHelpers.write_machine_code_to_file(all_code2, binary_file)
            sim2.load_binary_file(str(binary_file), start_address=0)
            
            # Execute CLEAR_V first
            sim2.step()
            
            # Execute CHECK_V instruction
            executed = sim2.step()
            assert executed, "CHECK_V instruction should execute successfully"
            
            # Verify R[1] was set to 0 because PSW.V was 0
            assert sim2.R[1] == 0, f"R[1] should be 0 when PSW.V is 0, got {sim2.R[1]}"
            
        finally:
            sys.path.remove(str(tmpdir_path))


def test_field_to_field_copy(register_fields_isa_file):
    """
    Test that copying one field to another works correctly.
    
    This test verifies:
    1. Copying a field value to another field (PSW.SV = PSW.V) works
    2. Both fields have the correct values after the copy
    """
    # Parse ISA
    isa = parse_isa_file(str(register_fields_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Generate simulator and assembler
        sim_gen = SimulatorGenerator(isa)
        asm_gen = AssemblerGenerator(isa)
        
        sim_file = sim_gen.generate(tmpdir_path)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            # Import generated tools using spec_from_file_location to avoid module caching
            # This ensures each test gets a fresh module instance
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            
            Simulator = sim_module.Simulator
            Assembler = asm_module.Assembler
            
            # Create fresh instances for each test
            assembler = Assembler()
            sim = Simulator()
            
            # Set V flag
            sim.PSW.V = 1
            sim.PSW.SV = 0  # Ensure SV is initially 0
            assert sim.PSW.V == 1, "PSW.V should be 1"
            assert sim.PSW.SV == 0, "PSW.SV should be 0 initially"
            
            # Assemble COPY_V_TO_SV instruction (PSW.SV = PSW.V)
            assembly_code = "COPY_V_TO_SV R0"
            machine_code = assembler.assemble(assembly_code)
            
            # Load program into simulator
            from tests.tricore.test_helpers import TriCoreTestHelpers
            binary_file = tmpdir_path / "test.bin"
            TriCoreTestHelpers.write_machine_code_to_file(machine_code, binary_file)
            sim.load_binary_file(str(binary_file), start_address=0)
            
            # Execute COPY_V_TO_SV instruction
            executed = sim.step()
            assert executed, "COPY_V_TO_SV instruction should execute successfully"
            
            # Verify SV was set to V's value
            assert sim.PSW.SV == 1, "PSW.SV should be 1 after copying from PSW.V"
            assert sim.PSW.V == 1, "PSW.V should still be 1"
            
            # Verify full register value
            expected_value = (1 << 30) | (1 << 29)  # Both V and SV set
            assert int(sim.PSW) == expected_value, f"PSW should be 0x{expected_value:x} after copy"
            
        finally:
            sys.path.remove(str(tmpdir_path))


def test_integer_operations_on_register(register_fields_isa_file):
    """
    Test that integer operations on full register work correctly.
    
    This test verifies:
    1. Arithmetic operations on full register (PSW = PSW + 1) work
    2. Fields are updated correctly after the operation
    """
    # Parse ISA
    isa = parse_isa_file(str(register_fields_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Generate simulator and assembler
        sim_gen = SimulatorGenerator(isa)
        asm_gen = AssemblerGenerator(isa)
        
        sim_file = sim_gen.generate(tmpdir_path)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            # Import generated tools using spec_from_file_location to avoid module caching
            # This ensures each test gets a fresh module instance
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            
            Simulator = sim_module.Simulator
            Assembler = asm_module.Assembler
            
            # Create fresh instances for each test
            assembler = Assembler()
            sim = Simulator()
            
            # Set initial value using SET_PSW instruction
            initial_value = 0x40000000  # Only V flag set (bit 30)
            imm_field_value_init = initial_value >> 12  # Extract immediate field value
            
            # Assemble SET_PSW to set initial value
            assembly_code_set = f"SET_PSW R0, 0x{imm_field_value_init:x}"
            machine_code_set = assembler.assemble(assembly_code_set)
            
            # Assemble INC_PSW instruction (PSW = PSW + 1)
            assembly_code = "INC_PSW R0"
            machine_code = assembler.assemble(assembly_code)
            
            # Combine both instructions
            all_code = machine_code_set + machine_code
            
            # Load program into simulator
            from tests.tricore.test_helpers import TriCoreTestHelpers
            binary_file = tmpdir_path / "test.bin"
            TriCoreTestHelpers.write_machine_code_to_file(all_code, binary_file)
            sim.load_binary_file(str(binary_file), start_address=0)
            
            # Execute SET_PSW first
            executed = sim.step()
            assert executed, "SET_PSW instruction should execute successfully"
            
            # Verify initial value
            psw_initial = int(sim.PSW) if hasattr(sim.PSW, '__int__') else sim.PSW
            assert psw_initial == initial_value, f"PSW should be 0x{initial_value:x} initially"
            
            if hasattr(sim.PSW, 'V'):
                assert sim.PSW.V == 1, "PSW.V should be 1 initially"
            
            # Execute INC_PSW instruction
            executed = sim.step()
            assert executed, "INC_PSW instruction should execute successfully"
            
            # Verify register was incremented
            expected_value = (initial_value + 1) & 0xFFFFFFFF
            psw_final = int(sim.PSW) if hasattr(sim.PSW, '__int__') else sim.PSW
            assert psw_final == expected_value, f"PSW should be 0x{expected_value:x} after increment, got 0x{psw_final:x}"
            
            # Verify fields reflect the new value
            # After incrementing 0x40000000, we get 0x40000001
            # Bit 30 (V) should still be set, bit 0 is now set (but not a field)
            if hasattr(sim.PSW, 'V'):
                assert sim.PSW.V == 1, "PSW.V should still be 1 (bit 30)"
            else:
                assert (psw_final >> 30) & 1 == 1, "PSW.V should still be 1 (bit 30)"
            
        finally:
            sys.path.remove(str(tmpdir_path))

