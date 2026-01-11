"""Tests for new built-in functions: ssov, suov, carry, borrow, reverse16, leading_ones, leading_zeros, leading_signs."""

import pytest
import tempfile
import sys
from pathlib import Path

from isa_dsl.model.parser import parse_isa_file
from isa_dsl.runtime.rtl_interpreter import RTLInterpreter
from isa_dsl.model.isa_model import RTLFunctionCall, RTLConstant
from isa_dsl.generators.simulator import SimulatorGenerator
from isa_dsl.generators.assembler import AssemblerGenerator


@pytest.fixture
def builtins_isa_file():
    """Fixture providing path to ISA file with built-in function examples."""
    return Path(__file__).parent / "test_data" / "builtins.isa"


def test_rtl_interpreter_ssov():
    """Test ssov function in RTL interpreter directly"""
    registers = {'R': [0] * 16}
    interpreter = RTLInterpreter(registers)
    
    # Test positive overflow: 0x80000000 should saturate to 0x7FFFFFFF
    func_call = RTLFunctionCall("ssov", [RTLConstant(0x80000000), RTLConstant(32)])
    result = interpreter._apply_builtin_function("ssov", [0x80000000, 32])
    assert result == 0x7FFFFFFF, f"Expected 0x7FFFFFFF, got {result:08x}"
    
    # Test value in range: 0x7FFFFFFF should remain unchanged
    result = interpreter._apply_builtin_function("ssov", [0x7FFFFFFF, 32])
    assert result == 0x7FFFFFFF, f"Expected 0x7FFFFFFF, got {result:08x}"
    
    # Test negative value: 0xFFFFFFFF should remain unchanged
    result = interpreter._apply_builtin_function("ssov", [0xFFFFFFFF, 32])
    assert result == 0xFFFFFFFF, f"Expected 0xFFFFFFFF, got {result:08x}"
    
    # Test 16-bit: 0x8000 should saturate to 0x7FFF
    result = interpreter._apply_builtin_function("ssov", [0x8000, 16])
    assert result == 0x7FFF, f"Expected 0x7FFF, got {result:04x}"


def test_rtl_interpreter_suov():
    """Test suov function in RTL interpreter directly"""
    registers = {'R': [0] * 16}
    interpreter = RTLInterpreter(registers)
    
    # Test value exceeding 16-bit max: 0x10000 should saturate to 0xFFFF
    result = interpreter._apply_builtin_function("suov", [0x10000, 16])
    assert result == 0xFFFF, f"Expected 0xFFFF, got {result:04x}"
    
    # Test value in range: 0xFFFF should remain unchanged
    result = interpreter._apply_builtin_function("suov", [0xFFFF, 16])
    assert result == 0xFFFF, f"Expected 0xFFFF, got {result:04x}"
    
    # Test 32-bit max: 0xFFFFFFFF should remain unchanged
    result = interpreter._apply_builtin_function("suov", [0xFFFFFFFF, 32])
    assert result == 0xFFFFFFFF, f"Expected 0xFFFFFFFF, got {result:08x}"


def test_rtl_interpreter_carry():
    """Test carry function in RTL interpreter directly"""
    registers = {'R': [0] * 16}
    interpreter = RTLInterpreter(registers)
    
    # Test carry occurs: 0xFFFFFFFF + 1 = overflow
    result = interpreter._apply_builtin_function("carry", [0xFFFFFFFF, 1, 0])
    assert result == 1, f"Expected 1, got {result}"
    
    # Test no carry: 0x7FFFFFFF + 1 = no overflow
    result = interpreter._apply_builtin_function("carry", [0x7FFFFFFF, 1, 0])
    assert result == 0, f"Expected 0, got {result}"
    
    # Test carry with carry_in: 0xFFFFFFFF + 0 + 1 = overflow
    result = interpreter._apply_builtin_function("carry", [0xFFFFFFFF, 0, 1])
    assert result == 1, f"Expected 1, got {result}"


def test_rtl_interpreter_borrow():
    """Test borrow function in RTL interpreter directly"""
    registers = {'R': [0] * 16}
    interpreter = RTLInterpreter(registers)
    
    # Test borrow occurs: 0 < 1
    result = interpreter._apply_builtin_function("borrow", [0, 1, 0])
    assert result == 1, f"Expected 1, got {result}"
    
    # Test no borrow: 1 >= 0
    result = interpreter._apply_builtin_function("borrow", [1, 0, 0])
    assert result == 0, f"Expected 0, got {result}"
    
    # Test borrow with borrow_in: 1 < (1 + 1)
    result = interpreter._apply_builtin_function("borrow", [1, 1, 1])
    assert result == 1, f"Expected 1, got {result}"


def test_rtl_interpreter_reverse16():
    """Test reverse16 function in RTL interpreter directly"""
    registers = {'R': [0] * 16}
    interpreter = RTLInterpreter(registers)
    
    # Test: 0x1234 reversed = 0x2C48
    result = interpreter._apply_builtin_function("reverse16", [0x1234])
    assert result == 0x2C48, f"Expected 0x2C48, got {result:04x}"
    
    # Test: 0x8000 reversed = 0x0001
    result = interpreter._apply_builtin_function("reverse16", [0x8000])
    assert result == 0x0001, f"Expected 0x0001, got {result:04x}"
    
    # Test: 0x0001 reversed = 0x8000
    result = interpreter._apply_builtin_function("reverse16", [0x0001])
    assert result == 0x8000, f"Expected 0x8000, got {result:04x}"


def test_rtl_interpreter_leading_ones():
    """Test leading_ones function in RTL interpreter directly"""
    registers = {'R': [0] * 16}
    interpreter = RTLInterpreter(registers)
    
    # Test all ones: 0xFFFFFFFF
    result = interpreter._apply_builtin_function("leading_ones", [0xFFFFFFFF])
    assert result == 32, f"Expected 32, got {result}"
    
    # Test 4 leading ones: 0xF0000000
    result = interpreter._apply_builtin_function("leading_ones", [0xF0000000])
    assert result == 4, f"Expected 4, got {result}"
    
    # Test no leading ones: 0x0
    result = interpreter._apply_builtin_function("leading_ones", [0x0])
    assert result == 0, f"Expected 0, got {result}"


def test_rtl_interpreter_leading_zeros():
    """Test leading_zeros function in RTL interpreter directly"""
    registers = {'R': [0] * 16}
    interpreter = RTLInterpreter(registers)
    
    # Test all zeros: 0x0
    result = interpreter._apply_builtin_function("leading_zeros", [0x0])
    assert result == 32, f"Expected 32, got {result}"
    
    # Test 31 leading zeros: 0x00000001
    result = interpreter._apply_builtin_function("leading_zeros", [0x00000001])
    assert result == 31, f"Expected 31, got {result}"
    
    # Test no leading zeros: 0x80000000
    result = interpreter._apply_builtin_function("leading_zeros", [0x80000000])
    assert result == 0, f"Expected 0, got {result}"


def test_rtl_interpreter_leading_signs():
    """Test leading_signs function in RTL interpreter directly"""
    registers = {'R': [0] * 16}
    interpreter = RTLInterpreter(registers)
    
    # Test: 0xFFFFFFFF (sign bit = 1, bits 30-0 all 1, matches)
    result = interpreter._apply_builtin_function("leading_signs", [0xFFFFFFFF])
    assert result == 31, f"Expected 31, got {result}"
    
    # Test: 0x80000000 (sign bit = 1, bit 30 = 0, doesn't match)
    result = interpreter._apply_builtin_function("leading_signs", [0x80000000])
    assert result == 0, f"Expected 0, got {result}"
    
    # Test: 0xC0000000 (sign bit = 1, bit 30 = 1, matches)
    result = interpreter._apply_builtin_function("leading_signs", [0xC0000000])
    assert result == 1, f"Expected 1, got {result}"


def test_ssov_32_positive_overflow(builtins_isa_file):
    """Test ssov with 32-bit positive overflow in simulator"""
    isa = parse_isa_file(str(builtins_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir_path)
        
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            import importlib.util
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            Simulator = sim_module.Simulator
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            Assembler = asm_module.Assembler
            
            assembler = Assembler()
            sim = Simulator()
            
            # Test: ssov with value that would overflow (0x80000000 = 2147483648 > 0x7FFFFFFF)
            assembly_code = "SSOV_32 R0, R1"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0x80000000  # This should saturate to 0x7FFFFFFF
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # ssov(0x80000000, 32) should saturate to 0x7FFFFFFF (max signed 32-bit)
            expected = 0x7FFFFFFF
            assert sim.R[0] == expected, f"Expected {expected:08x}, got {sim.R[0]:08x}"
            
            # Test: ssov with value in range (0x7FFFFFFF should remain unchanged)
            sim.R[1] = 0x7FFFFFFF
            sim.R[0] = 0
            sim.pc = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            expected = 0x7FFFFFFF
            assert sim.R[0] == expected, f"Expected {expected:08x}, got {sim.R[0]:08x}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_ssov_16(builtins_isa_file):
    """Test ssov with 16-bit width in simulator"""
    isa = parse_isa_file(str(builtins_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir_path)
        
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            import importlib.util
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            Simulator = sim_module.Simulator
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            Assembler = asm_module.Assembler
            
            assembler = Assembler()
            sim = Simulator()
            
            # Test: ssov with 16-bit positive overflow (0x8000 should saturate to 0x7FFF)
            assembly_code = "SSOV_16 R0, R1"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0x8000  # Should saturate to 0x7FFF for 16-bit
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # ssov(0x8000, 16) should saturate to 0x7FFF (max signed 16-bit)
            expected = 0x7FFF
            assert sim.R[0] == expected, f"Expected {expected:08x}, got {sim.R[0]:08x}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_suov_32(builtins_isa_file):
    """Test suov with 32-bit unsigned saturation in simulator"""
    isa = parse_isa_file(str(builtins_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir_path)
        
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            import importlib.util
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            Simulator = sim_module.Simulator
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            Assembler = asm_module.Assembler
            
            assembler = Assembler()
            sim = Simulator()
            
            # Test: suov with max unsigned 32-bit value
            assembly_code = "SUOV_32 R0, R1"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0xFFFFFFFF  # Max unsigned 32-bit value
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # suov(0xFFFFFFFF, 32) should remain 0xFFFFFFFF (max unsigned 32-bit)
            expected = 0xFFFFFFFF
            assert sim.R[0] == expected, f"Expected {expected:08x}, got {sim.R[0]:08x}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_suov_16(builtins_isa_file):
    """Test suov with 16-bit unsigned saturation in simulator"""
    isa = parse_isa_file(str(builtins_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir_path)
        
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            import importlib.util
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            Simulator = sim_module.Simulator
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            Assembler = asm_module.Assembler
            
            assembler = Assembler()
            sim = Simulator()
            
            # Test: suov with value that exceeds 16-bit unsigned max
            assembly_code = "SUOV_16 R0, R1"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0x10000  # Exceeds 16-bit max (0xFFFF), should saturate to 0xFFFF
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # suov(0x10000, 16) should saturate to 0xFFFF (max unsigned 16-bit)
            expected = 0xFFFF
            assert sim.R[0] == expected, f"Expected {expected:08x}, got {sim.R[0]:08x}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_carry(builtins_isa_file):
    """Test carry function in simulator"""
    isa = parse_isa_file(str(builtins_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir_path)
        
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            import importlib.util
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            Simulator = sim_module.Simulator
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            Assembler = asm_module.Assembler
            
            assembler = Assembler()
            sim = Simulator()
            
            # Test: carry with values that produce carry (0xFFFFFFFF + 1 = overflow)
            assembly_code = "CARRY R0, R1, R2"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0xFFFFFFFF
            sim.R[2] = 1
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # carry(0xFFFFFFFF, 1, 0) should return 1 (carry occurs)
            expected = 1
            assert sim.R[0] == expected, f"Expected {expected}, got {sim.R[0]}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_carry_with_cin(builtins_isa_file):
    """Test carry function with carry_in in simulator"""
    isa = parse_isa_file(str(builtins_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir_path)
        
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            import importlib.util
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            Simulator = sim_module.Simulator
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            Assembler = asm_module.Assembler
            
            assembler = Assembler()
            sim = Simulator()
            
            # Test: carry with carry_in = 1
            assembly_code = "CARRY_WITH_CIN R0, R1, R2"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0xFFFFFFFF
            sim.R[2] = 0
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # carry(0xFFFFFFFF, 0, 1) should return 1 (carry occurs: 0xFFFFFFFF + 0 + 1 = 0x100000000)
            expected = 1
            assert sim.R[0] == expected, f"Expected {expected}, got {sim.R[0]}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_borrow(builtins_isa_file):
    """Test borrow function in simulator"""
    isa = parse_isa_file(str(builtins_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir_path)
        
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            import importlib.util
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            Simulator = sim_module.Simulator
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            Assembler = asm_module.Assembler
            
            assembler = Assembler()
            sim = Simulator()
            
            # Test: borrow when operand1 < operand2 (0 < 1 should borrow)
            assembly_code = "BORROW R0, R1, R2"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0
            sim.R[2] = 1
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # borrow(0, 1, 0) should return 1 (borrow occurs: 0 < 1)
            expected = 1
            assert sim.R[0] == expected, f"Expected {expected}, got {sim.R[0]}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_borrow_with_bin(builtins_isa_file):
    """Test borrow function with borrow_in in simulator"""
    isa = parse_isa_file(str(builtins_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir_path)
        
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            import importlib.util
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            Simulator = sim_module.Simulator
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            Assembler = asm_module.Assembler
            
            assembler = Assembler()
            sim = Simulator()
            
            # Test: borrow with borrow_in = 1
            assembly_code = "BORROW_WITH_BIN R0, R1, R2"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 1
            sim.R[2] = 1
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # borrow(1, 1, 1) should return 1 (borrow occurs: 1 < (1 + 1))
            expected = 1
            assert sim.R[0] == expected, f"Expected {expected}, got {sim.R[0]}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_reverse16(builtins_isa_file):
    """Test reverse16 function in simulator"""
    isa = parse_isa_file(str(builtins_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir_path)
        
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            import importlib.util
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            Simulator = sim_module.Simulator
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            Assembler = asm_module.Assembler
            
            assembler = Assembler()
            sim = Simulator()
            
            # Test: reverse16 with 0x1234
            assembly_code = "REVERSE16 R0, R1"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0x1234
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # reverse16(0x1234) should return 0x2C48
            expected = 0x2C48
            assert sim.R[0] == expected, f"Expected {expected:04x}, got {sim.R[0]:04x}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_leading_ones(builtins_isa_file):
    """Test leading_ones function in simulator"""
    isa = parse_isa_file(str(builtins_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir_path)
        
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            import importlib.util
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            Simulator = sim_module.Simulator
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            Assembler = asm_module.Assembler
            
            assembler = Assembler()
            sim = Simulator()
            
            # Test: leading_ones with 0xFFFFFFFF (all ones)
            assembly_code = "LEADING_ONES R0, R1"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0xFFFFFFFF
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # leading_ones(0xFFFFFFFF) should return 32 (all bits are ones)
            expected = 32
            assert sim.R[0] == expected, f"Expected {expected}, got {sim.R[0]}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_leading_zeros(builtins_isa_file):
    """Test leading_zeros function in simulator"""
    isa = parse_isa_file(str(builtins_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir_path)
        
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            import importlib.util
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            Simulator = sim_module.Simulator
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            Assembler = asm_module.Assembler
            
            assembler = Assembler()
            sim = Simulator()
            
            # Test: leading_zeros with 0x0 (all zeros)
            assembly_code = "LEADING_ZEROS R0, R1"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0x0
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # leading_zeros(0x0) should return 32 (all bits are zeros)
            expected = 32
            assert sim.R[0] == expected, f"Expected {expected}, got {sim.R[0]}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_leading_signs(builtins_isa_file):
    """Test leading_signs function in simulator"""
    isa = parse_isa_file(str(builtins_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir_path)
        
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            import importlib.util
            sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
            sim_module = importlib.util.module_from_spec(sim_spec)
            sim_spec.loader.exec_module(sim_module)
            Simulator = sim_module.Simulator
            
            asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
            asm_module = importlib.util.module_from_spec(asm_spec)
            asm_spec.loader.exec_module(asm_module)
            Assembler = asm_module.Assembler
            
            assembler = Assembler()
            sim = Simulator()
            
            # Test: leading_signs with 0xFFFFFFFF (negative, sign bit = 1)
            assembly_code = "LEADING_SIGNS R0, R1"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0xFFFFFFFF
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # leading_signs(0xFFFFFFFF) should return 31 (bits 30-0 all match sign bit 1)
            expected = 31
            assert sim.R[0] == expected, f"Expected {expected}, got {sim.R[0]}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))

