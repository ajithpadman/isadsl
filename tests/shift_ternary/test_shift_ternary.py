"""Tests for shift operations and ternary expressions in RTL behavior."""

import pytest
import tempfile
import sys
import importlib.util
from pathlib import Path

from isa_dsl.model.parser import parse_isa_file
from isa_dsl.generators.simulator import SimulatorGenerator
from isa_dsl.generators.assembler import AssemblerGenerator


@pytest.fixture
def shift_ternary_isa_file():
    """Fixture providing path to shift/ternary test ISA file."""
    return Path(__file__).parent / "test_data" / "shift_ternary.isa"


def test_left_shift_operation(shift_ternary_isa_file):
    """Test left shift operation (<<) in RTL behavior."""
    isa = parse_isa_file(str(shift_ternary_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        sim_gen = SimulatorGenerator(isa)
        asm_gen = AssemblerGenerator(isa)
        
        sim_file = sim_gen.generate(tmpdir_path)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            
            Simulator = sim_module.Simulator
            Assembler = asm_module.Assembler
            
            assembler = Assembler()
            sim = Simulator()
            
            # Test: R[1] = R[0] << R[2]
            # R[0] = 5, R[2] = 2, expected: R[1] = 5 << 2 = 20
            sim.R[0] = 5
            sim.R[2] = 2
            
            assembly_code = "SHL R1, R0, R2"
            machine_code = assembler.assemble(assembly_code)
            assert len(machine_code) > 0, "Should assemble SHL instruction"
            
            from tests.tricore.test_helpers import TriCoreTestHelpers
            binary_file = tmpdir_path / "test.bin"
            TriCoreTestHelpers.write_machine_code_to_file(machine_code, binary_file)
            sim.load_binary_file(str(binary_file), start_address=0)
            
            executed = sim.step()
            assert executed, "SHL instruction should execute successfully"
            
            expected = (5 << 2) & 0xFFFFFFFF
            assert sim.R[1] == expected, f"R[1] should be {expected} (5 << 2), got {sim.R[1]}"
            
        finally:
            sys.path.remove(str(tmpdir_path))


def test_right_shift_operation(shift_ternary_isa_file):
    """Test right shift operation (>>) in RTL behavior."""
    isa = parse_isa_file(str(shift_ternary_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        sim_gen = SimulatorGenerator(isa)
        asm_gen = AssemblerGenerator(isa)
        
        sim_file = sim_gen.generate(tmpdir_path)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            
            Simulator = sim_module.Simulator
            Assembler = asm_module.Assembler
            
            assembler = Assembler()
            sim = Simulator()
            
            # Test: R[1] = R[0] >> R[2]
            # R[0] = 20, R[2] = 2, expected: R[1] = 20 >> 2 = 5
            sim.R[0] = 20
            sim.R[2] = 2
            
            assembly_code = "SHR R1, R0, R2"
            machine_code = assembler.assemble(assembly_code)
            assert len(machine_code) > 0, "Should assemble SHR instruction"
            
            from tests.tricore.test_helpers import TriCoreTestHelpers
            binary_file = tmpdir_path / "test.bin"
            TriCoreTestHelpers.write_machine_code_to_file(machine_code, binary_file)
            sim.load_binary_file(str(binary_file), start_address=0)
            
            executed = sim.step()
            assert executed, "SHR instruction should execute successfully"
            
            expected = (20 >> 2) & 0xFFFFFFFF
            assert sim.R[1] == expected, f"R[1] should be {expected} (20 >> 2), got {sim.R[1]}"
            
        finally:
            sys.path.remove(str(tmpdir_path))


def test_ternary_expression(shift_ternary_isa_file):
    """Test ternary conditional expression (? :) in RTL behavior."""
    isa = parse_isa_file(str(shift_ternary_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        sim_gen = SimulatorGenerator(isa)
        asm_gen = AssemblerGenerator(isa)
        
        sim_file = sim_gen.generate(tmpdir_path)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            
            Simulator = sim_module.Simulator
            Assembler = asm_module.Assembler
            
            assembler = Assembler()
            sim = Simulator()
            
            # Test: R[2] = (R[0] != 0) ? R[0] : R[1]
            # Case 1: R[0] != 0, should return R[0]
            sim.R[0] = 42
            sim.R[1] = 10
            
            assembly_code = "TERNARY R2, R0, R1"
            machine_code = assembler.assemble(assembly_code)
            assert len(machine_code) > 0, "Should assemble TERNARY instruction"
            
            from tests.tricore.test_helpers import TriCoreTestHelpers
            binary_file = tmpdir_path / "test.bin"
            TriCoreTestHelpers.write_machine_code_to_file(machine_code, binary_file)
            sim.load_binary_file(str(binary_file), start_address=0)
            
            executed = sim.step()
            assert executed, "TERNARY instruction should execute successfully"
            
            assert sim.R[2] == 42, f"R[2] should be 42 (R[0] since R[0] != 0), got {sim.R[2]}"
            
            # Case 2: R[0] == 0, should return R[1]
            sim2 = Simulator()
            sim2.R[0] = 0
            sim2.R[1] = 10
            
            machine_code2 = assembler.assemble(assembly_code)
            binary_file2 = tmpdir_path / "test2.bin"
            TriCoreTestHelpers.write_machine_code_to_file(machine_code2, binary_file2)
            sim2.load_binary_file(str(binary_file2), start_address=0)
            
            executed2 = sim2.step()
            assert executed2, "TERNARY instruction should execute successfully"
            
            assert sim2.R[2] == 10, f"R[2] should be 10 (R[1] since R[0] == 0), got {sim2.R[2]}"
            
        finally:
            sys.path.remove(str(tmpdir_path))


def test_ternary_with_shift(shift_ternary_isa_file):
    """Test ternary expression combined with shift operations."""
    isa = parse_isa_file(str(shift_ternary_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        sim_gen = SimulatorGenerator(isa)
        asm_gen = AssemblerGenerator(isa)
        
        sim_file = sim_gen.generate(tmpdir_path)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            
            Simulator = sim_module.Simulator
            Assembler = asm_module.Assembler
            
            assembler = Assembler()
            sim = Simulator()
            
            # Test: R[2] = (R[0] != 0) ? (R[0] << 2) : (R[1] >> 2)
            # Case: R[0] != 0, should return R[0] << 2
            sim.R[0] = 5
            sim.R[1] = 20
            
            assembly_code = "TERNARY_SHIFT R2, R0, R1"
            machine_code = assembler.assemble(assembly_code)
            assert len(machine_code) > 0, "Should assemble TERNARY_SHIFT instruction"
            
            from tests.tricore.test_helpers import TriCoreTestHelpers
            binary_file = tmpdir_path / "test.bin"
            TriCoreTestHelpers.write_machine_code_to_file(machine_code, binary_file)
            sim.load_binary_file(str(binary_file), start_address=0)
            
            executed = sim.step()
            assert executed, "TERNARY_SHIFT instruction should execute successfully"
            
            expected = (5 << 2) & 0xFFFFFFFF
            assert sim.R[2] == expected, f"R[2] should be {expected} (5 << 2), got {sim.R[2]}"
            
        finally:
            sys.path.remove(str(tmpdir_path))


def test_shift_with_immediate(shift_ternary_isa_file):
    """Test shift operations with immediate values."""
    isa = parse_isa_file(str(shift_ternary_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        sim_gen = SimulatorGenerator(isa)
        asm_gen = AssemblerGenerator(isa)
        
        sim_file = sim_gen.generate(tmpdir_path)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            
            Simulator = sim_module.Simulator
            Assembler = asm_module.Assembler
            
            assembler = Assembler()
            sim = Simulator()
            
            # Test: R[1] = R[0] << 3
            sim.R[0] = 4
            
            assembly_code = "SHL_IMM R1, R0, 3"
            machine_code = assembler.assemble(assembly_code)
            assert len(machine_code) > 0, "Should assemble SHL_IMM instruction"
            
            from tests.tricore.test_helpers import TriCoreTestHelpers
            binary_file = tmpdir_path / "test.bin"
            TriCoreTestHelpers.write_machine_code_to_file(machine_code, binary_file)
            sim.load_binary_file(str(binary_file), start_address=0)
            
            executed = sim.step()
            assert executed, "SHL_IMM instruction should execute successfully"
            
            expected = (4 << 3) & 0xFFFFFFFF
            assert sim.R[1] == expected, f"R[1] should be {expected} (4 << 3), got {sim.R[1]}"
            
        finally:
            sys.path.remove(str(tmpdir_path))


def test_nested_ternary_expression(shift_ternary_isa_file):
    """Test nested ternary expressions (sign function)."""
    isa = parse_isa_file(str(shift_ternary_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        sim_gen = SimulatorGenerator(isa)
        asm_gen = AssemblerGenerator(isa)
        
        sim_file = sim_gen.generate(tmpdir_path)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            
            Simulator = sim_module.Simulator
            Assembler = asm_module.Assembler
            
            assembler = Assembler()
            
            # Test: R[2] = (R[0] > 0) ? 1 : ((R[0] < 0) ? -1 : 0)
            # Case 1: Positive value
            sim = Simulator()
            sim.R[0] = 5
            
            assembly_code = "NESTED_TERNARY R2, R0, R1"
            machine_code = assembler.assemble(assembly_code)
            assert len(machine_code) > 0, "Should assemble NESTED_TERNARY instruction"
            
            from tests.tricore.test_helpers import TriCoreTestHelpers
            binary_file = tmpdir_path / "test.bin"
            TriCoreTestHelpers.write_machine_code_to_file(machine_code, binary_file)
            sim.load_binary_file(str(binary_file), start_address=0)
            
            executed = sim.step()
            assert executed, "NESTED_TERNARY instruction should execute successfully"
            
            assert sim.R[2] == 1, f"R[2] should be 1 (positive), got {sim.R[2]}"
            
            # Case 2: Negative value
            sim2 = Simulator()
            sim2.R[0] = -5  # Note: -5 in 32-bit two's complement is 0xFFFFFFFB
            
            machine_code2 = assembler.assemble(assembly_code)
            binary_file2 = tmpdir_path / "test2.bin"
            TriCoreTestHelpers.write_machine_code_to_file(machine_code2, binary_file2)
            sim2.load_binary_file(str(binary_file2), start_address=0)
            
            executed2 = sim2.step()
            assert executed2, "NESTED_TERNARY instruction should execute successfully"
            
            # -1 in 32-bit two's complement is 0xFFFFFFFF
            expected_neg = 0xFFFFFFFF
            assert sim2.R[2] == expected_neg, f"R[2] should be {expected_neg} (negative), got {sim2.R[2]}"
            
            # Case 3: Zero value
            sim3 = Simulator()
            sim3.R[0] = 0
            
            machine_code3 = assembler.assemble(assembly_code)
            binary_file3 = tmpdir_path / "test3.bin"
            TriCoreTestHelpers.write_machine_code_to_file(machine_code3, binary_file3)
            sim3.load_binary_file(str(binary_file3), start_address=0)
            
            executed3 = sim3.step()
            assert executed3, "NESTED_TERNARY instruction should execute successfully"
            
            assert sim3.R[2] == 0, f"R[2] should be 0 (zero), got {sim3.R[2]}"
            
        finally:
            sys.path.remove(str(tmpdir_path))

