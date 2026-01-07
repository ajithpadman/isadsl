"""Tests for RTL built-in functions and bitfield access."""

import pytest
import tempfile
import sys
from pathlib import Path

from isa_dsl.model.parser import parse_isa_file
from isa_dsl.generators.simulator import SimulatorGenerator
from isa_dsl.generators.assembler import AssemblerGenerator


@pytest.fixture
def builtins_isa_file():
    """Fixture providing path to ISA file with built-in function examples."""
    return Path(__file__).parent / "test_data" / "builtins.isa"


def test_bitfield_access(builtins_isa_file):
    """Test bitfield access syntax: value[msb:lsb]"""
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
            
            # Test: Extract bits [15:8] from a register
            # Set R[1] = 0x12345678
            # Extract bits [15:8] should give 0x56
            assembly_code = "EXTRACT_BITS R0, R1"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0x12345678
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # Bits [15:8] of 0x12345678 = 0x56
            expected = 0x56
            assert sim.R[0] == expected, f"Expected {expected:02x}, got {sim.R[0]:02x}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_sign_extend_2_args(builtins_isa_file):
    """Test sign_extend(value, from_bits) - extends to 32 bits by default"""
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
            
            # Test 1: Sign extend positive 8-bit value
            # 0x7F (127) sign-extended from 8 bits should remain 0x7F
            assembly_code = "SIGN_EXT_8 R0, R1"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0x7F  # Positive 8-bit value
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # Sign-extended 0x7F from 8 bits = 0x0000007F
            expected = 0x7F
            assert sim.R[0] == expected, f"Expected {expected:08x}, got {sim.R[0]:08x}"
            
            # Test 2: Sign extend negative 8-bit value
            # 0xFF (-1) sign-extended from 8 bits should become 0xFFFFFFFF
            sim.pc = 0
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0xFF  # Negative 8-bit value (-1)
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # Sign-extended 0xFF from 8 bits = 0xFFFFFFFF
            expected = 0xFFFFFFFF
            assert sim.R[0] == expected, f"Expected {expected:08x}, got {sim.R[0]:08x}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_sign_extend_3_args(builtins_isa_file):
    """Test sign_extend(value, from_bits, to_bits) - extends to specified width"""
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
            
            # Test: Sign extend 8-bit value to 16 bits
            # 0xFF (-1) sign-extended from 8 to 16 bits = 0xFFFF
            assembly_code = "SIGN_EXT_8_TO_16 R0, R1"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0xFF  # Negative 8-bit value
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # Sign-extended 0xFF from 8 to 16 bits = 0xFFFF (masked to 16 bits)
            expected = 0xFFFF
            assert (sim.R[0] & 0xFFFF) == expected, f"Expected {expected:04x}, got {sim.R[0]:04x}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_zero_extend_2_args(builtins_isa_file):
    """Test zero_extend(value, from_bits) - extends to 32 bits by default"""
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
            
            # Test: Zero extend 8-bit value
            # 0xFF zero-extended from 8 bits should become 0x000000FF (not 0xFFFFFFFF)
            assembly_code = "ZERO_EXT_8 R0, R1"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0xFF
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # Zero-extended 0xFF from 8 bits = 0x000000FF
            expected = 0xFF
            assert sim.R[0] == expected, f"Expected {expected:08x}, got {sim.R[0]:08x}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_zero_extend_3_args(builtins_isa_file):
    """Test zero_extend(value, from_bits, to_bits) - extends to specified width"""
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
            
            # Test: Zero extend 8-bit value to 16 bits
            # 0xFF zero-extended from 8 to 16 bits = 0x00FF
            assembly_code = "ZERO_EXT_8_TO_16 R0, R1"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0xFF
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # Zero-extended 0xFF from 8 to 16 bits = 0x00FF (masked to 16 bits)
            expected = 0x00FF
            assert (sim.R[0] & 0xFFFF) == expected, f"Expected {expected:04x}, got {sim.R[0]:04x}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_extract_bits_function(builtins_isa_file):
    """Test extract_bits(value, msb, lsb) function"""
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
            
            # Test: Extract bits [23:16] from 0x12345678 = 0x34
            assembly_code = "EXTRACT_BITS_FUNC R0, R1"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0x12345678
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # Bits [23:16] of 0x12345678 = 0x34
            expected = 0x34
            assert sim.R[0] == expected, f"Expected {expected:02x}, got {sim.R[0]:02x}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_bitfield_with_sign_extend(builtins_isa_file):
    """Test combining bitfield access with sign extension"""
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
            
            # Test: Extract bits [15:8] and sign-extend
            # 0x1234FF78: bits [15:8] = 0xFF, sign-extended = 0xFFFFFFFF
            assembly_code = "BITFIELD_SIGN_EXT R0, R1"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0x1234FF78
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # Bits [15:8] = 0xFF, sign-extended from 8 bits = 0xFFFFFFFF
            expected = 0xFFFFFFFF
            assert sim.R[0] == expected, f"Expected {expected:08x}, got {sim.R[0]:08x}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_sext_alias(builtins_isa_file):
    """Test sext alias for sign_extend"""
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
            
            # Test: Use sext alias
            assembly_code = "SEXT_ALIAS R0, R1"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0xFF  # Negative 8-bit value
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # Sign-extended 0xFF from 8 bits = 0xFFFFFFFF
            expected = 0xFFFFFFFF
            assert sim.R[0] == expected, f"Expected {expected:08x}, got {sim.R[0]:08x}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_zext_alias(builtins_isa_file):
    """Test zext alias for zero_extend"""
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
            
            # Test: Use zext alias
            assembly_code = "ZEXT_ALIAS R0, R1"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0xFF
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # Zero-extended 0xFF from 8 bits = 0x000000FF
            expected = 0xFF
            assert sim.R[0] == expected, f"Expected {expected:08x}, got {sim.R[0]:08x}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_to_signed_8(builtins_isa_file):
    """Test to_signed with 8-bit value"""
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
            
            # Test: to_signed with positive 8-bit value
            # 0x12345678: bits [7:0] = 0x78 (positive), sign-extended = 0x00000078
            assembly_code = "TO_SIGNED_8 R0, R1"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0x12345678
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # Bits [7:0] = 0x78, to_signed(0x78, 8) = 0x00000078
            expected = 0x78
            assert sim.R[0] == expected, f"Expected {expected:08x}, got {sim.R[0]:08x}"
            
            # Test: to_signed with negative 8-bit value
            sim.R[1] = 0x123456FF
            sim.R[0] = 0
            sim.pc = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # Bits [7:0] = 0xFF, to_signed(0xFF, 8) = 0xFFFFFFFF (sign-extended)
            expected = 0xFFFFFFFF
            assert sim.R[0] == expected, f"Expected {expected:08x}, got {sim.R[0]:08x}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_to_signed_16(builtins_isa_file):
    """Test to_signed with 16-bit value"""
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
            
            # Test: to_signed with positive 16-bit value
            # 0x12345678: bits [15:0] = 0x5678 (positive), sign-extended = 0x00005678
            assembly_code = "TO_SIGNED_16 R0, R1"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0x12345678
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # Bits [15:0] = 0x5678, to_signed(0x5678, 16) = 0x00005678
            expected = 0x5678
            assert sim.R[0] == expected, f"Expected {expected:08x}, got {sim.R[0]:08x}"
            
            # Test: to_signed with negative 16-bit value
            sim.R[1] = 0x1234FFFF
            sim.R[0] = 0
            sim.pc = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # Bits [15:0] = 0xFFFF, to_signed(0xFFFF, 16) = 0xFFFFFFFF (sign-extended)
            expected = 0xFFFFFFFF
            assert sim.R[0] == expected, f"Expected {expected:08x}, got {sim.R[0]:08x}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_to_unsigned_8(builtins_isa_file):
    """Test to_unsigned with 8-bit value"""
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
            
            # Test: to_unsigned with 8-bit value
            # 0x123456FF: bits [7:0] = 0xFF, zero-extended = 0x000000FF
            assembly_code = "TO_UNSIGNED_8 R0, R1"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0x123456FF
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # Bits [7:0] = 0xFF, to_unsigned(0xFF, 8) = 0x000000FF
            expected = 0xFF
            assert sim.R[0] == expected, f"Expected {expected:08x}, got {sim.R[0]:08x}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_to_unsigned_16(builtins_isa_file):
    """Test to_unsigned with 16-bit value"""
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
            
            # Test: to_unsigned with 16-bit value
            # 0x1234FFFF: bits [15:0] = 0xFFFF, zero-extended = 0x0000FFFF
            assembly_code = "TO_UNSIGNED_16 R0, R1"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0x1234FFFF
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # Bits [15:0] = 0xFFFF, to_unsigned(0xFFFF, 16) = 0x0000FFFF
            expected = 0xFFFF
            assert sim.R[0] == expected, f"Expected {expected:08x}, got {sim.R[0]:08x}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_to_signed_with_extract_bits(builtins_isa_file):
    """Test to_signed with extract_bits function"""
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
            
            # Test: Extract bits [15:8] and cast to signed
            # 0x1234FF78: bits [15:8] = 0xFF, to_signed = 0xFFFFFFFF
            assembly_code = "TO_SIGNED_EXTRACT R0, R1"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0x1234FF78
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # Bits [15:8] = 0xFF, to_signed(0xFF, 8) = 0xFFFFFFFF
            expected = 0xFFFFFFFF
            assert sim.R[0] == expected, f"Expected {expected:08x}, got {sim.R[0]:08x}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_to_unsigned_with_extract_bits(builtins_isa_file):
    """Test to_unsigned with extract_bits function"""
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
            
            # Test: Extract bits [15:8] and cast to unsigned
            # 0x1234FF78: bits [15:8] = 0xFF, to_unsigned = 0x000000FF
            assembly_code = "TO_UNSIGNED_EXTRACT R0, R1"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0x1234FF78
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # Bits [15:8] = 0xFF, to_unsigned(0xFF, 8) = 0x000000FF
            expected = 0xFF
            assert sim.R[0] == expected, f"Expected {expected:08x}, got {sim.R[0]:08x}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


def test_abs_bytes_packing(builtins_isa_file):
    """Test byte-wise absolute value calculation and packing with 0xFFF1F1F1"""
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
            
            # Test: Calculate absolute value of each byte in 0xFFF1F1F1
            # Byte breakdown: 0xFF (byte 3), 0xF1 (byte 2), 0xF1 (byte 1), 0xF1 (byte 0)
            # Byte 3 (0xFF): signed = -1, abs = 1 → 0x01
            # Byte 2 (0xF1): signed = -15, abs = 15 → 0x0F
            # Byte 1 (0xF1): signed = -15, abs = 15 → 0x0F
            # Byte 0 (0xF1): signed = -15, abs = 15 → 0x0F
            # Expected result: 0x010F0F0F
            assembly_code = "ABS_BYTES R0, R1"
            machine_code = assembler.assemble(assembly_code)
            
            binary_file = tmpdir_path / "test.bin"
            with open(binary_file, 'wb') as f:
                for word in machine_code:
                    f.write(word.to_bytes(4, byteorder='little'))
            
            sim.load_binary_file(str(binary_file), start_address=0)
            sim.R[1] = 0xFFF1F1F1
            sim.R[0] = 0
            
            executed = sim.step()
            assert executed, "Instruction should execute successfully"
            
            # Verify the packed result
            expected = 0x010F0F0F
            assert sim.R[0] == expected, f"Expected {expected:08x}, got {sim.R[0]:08x}"
            
            # Verify individual bytes are correct
            byte3 = (sim.R[0] >> 24) & 0xFF
            byte2 = (sim.R[0] >> 16) & 0xFF
            byte1 = (sim.R[0] >> 8) & 0xFF
            byte0 = sim.R[0] & 0xFF
            
            assert byte3 == 0x01, f"Byte 3 should be 0x01, got 0x{byte3:02x}"
            assert byte2 == 0x0F, f"Byte 2 should be 0x0F, got 0x{byte2:02x}"
            assert byte1 == 0x0F, f"Byte 1 should be 0x0F, got 0x{byte1:02x}"
            assert byte0 == 0x0F, f"Byte 0 should be 0x0F, got 0x{byte0:02x}"
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))

