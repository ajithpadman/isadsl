"""Tests for generated assembler and simulator functionality."""

import pytest
from pathlib import Path
import tempfile
import subprocess
import sys
import importlib.util
from isa_dsl.model.parser import parse_isa_file
from isa_dsl.generators.simulator import SimulatorGenerator
from isa_dsl.generators.assembler import AssemblerGenerator


def test_assembler_basic_functionality():
    """Test that generated assembler can assemble simple instructions."""
    isa_file = Path(__file__).parent.parent / 'examples' / 'minimal.isa'
    isa = parse_isa_file(str(isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate assembler
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir)
        assert asm_file.exists()
        
        # Import the generated assembler module
        spec = importlib.util.spec_from_file_location("assembler", asm_file)
        assembler_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(assembler_module)
        Assembler = assembler_module.Assembler
        
        # Create assembler instance
        assembler = Assembler()
        
        # Test assembly of ADD instruction
        assembly_code = "ADD R1, R0, 5"
        machine_code = assembler.assemble(assembly_code)
        
        assert len(machine_code) > 0, "Assembler should produce machine code"
        assert isinstance(machine_code[0], int), "Machine code should be integers"


def test_simulator_basic_functionality():
    """Test that generated simulator can execute instructions."""
    isa_file = Path(__file__).parent.parent / 'examples' / 'minimal.isa'
    isa = parse_isa_file(str(isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate simulator
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir)
        assert sim_file.exists()
        
        # Import the generated simulator module
        spec = importlib.util.spec_from_file_location("simulator", sim_file)
        simulator_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(simulator_module)
        Simulator = simulator_module.Simulator
        
        # Create simulator instance
        sim = Simulator()
        
        # Test that simulator initializes correctly
        assert hasattr(sim, 'R'), "Simulator should have R register file"
        assert hasattr(sim, 'PC'), "Simulator should have PC register"
        assert hasattr(sim, 'memory'), "Simulator should have memory"
        assert sim.PC == 0, "PC should initialize to 0"
        assert len(sim.R) == 4, "R register file should have 4 registers"


def test_assembler_simulator_integration():
    """Test full workflow: assemble code and run it on simulator."""
    isa_file = Path(__file__).parent.parent / 'examples' / 'minimal.isa'
    isa = parse_isa_file(str(isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate both assembler and simulator
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir)
        
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir)
        
        # Import modules
        asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
        asm_module = importlib.util.module_from_spec(asm_spec)
        asm_spec.loader.exec_module(asm_module)
        
        sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
        sim_module = importlib.util.module_from_spec(sim_spec)
        sim_spec.loader.exec_module(sim_module)
        
        Assembler = asm_module.Assembler
        Simulator = sim_module.Simulator
        
        # Create instances
        assembler = Assembler()
        sim = Simulator()
        
        # Assemble a simple program: R[1] = R[0] + 5
        # Assuming R[0] starts at 0, R[1] should become 5
        assembly_code = "ADD R1, R0, 5"
        machine_code = assembler.assemble(assembly_code)
        
        assert len(machine_code) > 0, "Should assemble at least one instruction"
        
        # Load program into simulator
        sim.load_program(machine_code, start_address=0)
        
        # Execute one step
        executed = sim.step()
        assert executed, "Instruction should execute successfully"
        
        # Check that R[1] was updated (R[0] + 5 = 0 + 5 = 5)
        assert sim.R[1] == 5, f"R[1] should be 5 after ADD R1, R0, 5, got {sim.R[1]}"
        assert sim.pc == 4, "PC should advance by 4 after one instruction"


def test_assembler_simulator_multiple_instructions():
    """Test assembling and running multiple instructions."""
    isa_file = Path(__file__).parent.parent / 'examples' / 'minimal.isa'
    isa = parse_isa_file(str(isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate tools
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir)
        
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir)
        
        # Import modules
        asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
        asm_module = importlib.util.module_from_spec(asm_spec)
        asm_spec.loader.exec_module(asm_module)
        
        sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
        sim_module = importlib.util.module_from_spec(sim_spec)
        sim_spec.loader.exec_module(sim_module)
        
        Assembler = asm_module.Assembler
        Simulator = sim_module.Simulator
        
        # Create instances
        assembler = Assembler()
        sim = Simulator()
        
        # Assemble a program with multiple instructions
        # R[1] = R[0] + 10  (R[1] = 10)
        # R[2] = R[1] - 3  (R[2] = 7)
        assembly_code = """ADD R1, R0, 10
SUB R2, R1, 3"""
        
        machine_code = assembler.assemble(assembly_code)
        assert len(machine_code) == 2, "Should assemble 2 instructions"
        
        # Load and run program
        sim.load_program(machine_code, start_address=0)
        
        # Execute first instruction
        assert sim.step(), "First instruction should execute"
        assert sim.R[1] == 10, f"R[1] should be 10, got {sim.R[1]}"
        assert sim.pc == 4, "PC should be 4 after first instruction"
        
        # Execute second instruction
        assert sim.step(), "Second instruction should execute"
        assert sim.R[2] == 7, f"R[2] should be 7 (10 - 3), got {sim.R[2]}"
        assert sim.pc == 8, "PC should be 8 after second instruction"


def test_assembler_binary_output():
    """Test that assembler can write binary files."""
    isa_file = Path(__file__).parent.parent / 'examples' / 'minimal.isa'
    isa = parse_isa_file(str(isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate assembler
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir)
        
        # Import module
        asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
        asm_module = importlib.util.module_from_spec(asm_spec)
        asm_spec.loader.exec_module(asm_module)
        
        Assembler = asm_module.Assembler
        
        # Create assembler and assemble code
        assembler = Assembler()
        assembly_code = "ADD R1, R0, 5"
        machine_code = assembler.assemble(assembly_code)
        
        # Write binary file
        binary_file = Path(tmpdir) / "test.bin"
        assembler.write_binary(machine_code, str(binary_file))
        
        assert binary_file.exists(), "Binary file should be created"
        assert binary_file.stat().st_size > 0, "Binary file should not be empty"
        
        # Verify binary file can be read back
        with open(binary_file, 'rb') as f:
            data = f.read()
            assert len(data) >= 4, "Binary file should contain at least one 32-bit word"


def test_simulator_binary_file_loading():
    """Test that simulator can load and execute from binary file."""
    isa_file = Path(__file__).parent.parent / 'examples' / 'minimal.isa'
    isa = parse_isa_file(str(isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate tools
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir)
        
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir)
        
        # Import modules
        asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
        asm_module = importlib.util.module_from_spec(asm_spec)
        asm_spec.loader.exec_module(asm_module)
        
        sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
        sim_module = importlib.util.module_from_spec(sim_spec)
        sim_spec.loader.exec_module(sim_module)
        
        Assembler = asm_module.Assembler
        Simulator = sim_module.Simulator
        
        # Assemble code and write binary
        assembler = Assembler()
        assembly_code = "ADD R1, R0, 42"
        machine_code = assembler.assemble(assembly_code)
        
        binary_file = Path(tmpdir) / "program.bin"
        assembler.write_binary(machine_code, str(binary_file))
        
        # Load binary into simulator
        sim = Simulator()
        sim.load_binary_file(str(binary_file), start_address=0)
        
        # Execute
        assert sim.step(), "Instruction should execute"
        assert sim.R[1] == 42, f"R[1] should be 42, got {sim.R[1]}"


def test_simulator_with_sample_isa():
    """Test simulator with the full sample_isa.isa."""
    isa_file = Path(__file__).parent.parent / 'examples' / 'sample_isa.isa'
    isa = parse_isa_file(str(isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate tools
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir)
        
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir)
        
        # Import modules
        asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
        asm_module = importlib.util.module_from_spec(asm_spec)
        asm_spec.loader.exec_module(asm_module)
        
        sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
        sim_module = importlib.util.module_from_spec(sim_spec)
        sim_spec.loader.exec_module(sim_module)
        
        Assembler = asm_module.Assembler
        Simulator = sim_module.Simulator
        
        # Create instances
        assembler = Assembler()
        sim = Simulator()
        
        # Assemble a program: ADD R1, R2, R3
        # This should compute R[1] = R[2] + R[3]
        # Initialize R[2] = 10, R[3] = 20 manually (since we can't set registers directly)
        # Actually, we need to set registers first, but the simulator doesn't expose that
        # So we'll test with default values (0)
        assembly_code = "ADD R1, R2, R3"
        machine_code = assembler.assemble(assembly_code)
        
        # Load and execute
        sim.load_program(machine_code, start_address=0)
        
        # Set initial register values manually
        sim.R[2] = 10
        sim.R[3] = 20
        
        # Execute
        assert sim.step(), "ADD instruction should execute"
        
        # Check result: R[1] = R[2] + R[3] = 10 + 20 = 30
        assert sim.R[1] == 30, f"R[1] should be 30 (10 + 20), got {sim.R[1]}"


def test_assembler_handles_comments():
    """Test that assembler correctly handles comments in assembly code."""
    isa_file = Path(__file__).parent.parent / 'examples' / 'minimal.isa'
    isa = parse_isa_file(str(isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate assembler
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir)
        
        # Import module
        asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
        asm_module = importlib.util.module_from_spec(asm_spec)
        asm_spec.loader.exec_module(asm_module)
        
        Assembler = asm_module.Assembler
        
        # Test assembly with comments
        assembly_code = """# This is a comment
ADD R1, R0, 5  # Add 5 to R0 and store in R1
# Another comment"""
        
        assembler = Assembler()
        machine_code = assembler.assemble(assembly_code)
        
        # Should only assemble one instruction (comments should be ignored)
        assert len(machine_code) == 1, "Should assemble one instruction, ignoring comments"


def test_simulator_instruction_counting():
    """Test that simulator correctly counts executed instructions."""
    isa_file = Path(__file__).parent.parent / 'examples' / 'minimal.isa'
    isa = parse_isa_file(str(isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate simulator
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir)
        
        # Import module
        sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
        sim_module = importlib.util.module_from_spec(sim_spec)
        sim_spec.loader.exec_module(sim_module)
        
        Simulator = sim_module.Simulator
        
        # Generate assembler too
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir)
        
        asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
        asm_module = importlib.util.module_from_spec(asm_spec)
        asm_spec.loader.exec_module(asm_module)
        
        Assembler = asm_module.Assembler
        
        # Create instances
        assembler = Assembler()
        sim = Simulator()
        
        # Assemble program with 3 instructions
        assembly_code = """ADD R1, R0, 5
ADD R2, R0, 10
SUB R3, R2, 5"""
        
        machine_code = assembler.assemble(assembly_code)
        sim.load_program(machine_code, start_address=0)
        
        # Execute all instructions
        assert sim.instruction_count == 0, "Instruction count should start at 0"
        assert sim.step(), "First instruction should execute"
        assert sim.instruction_count == 1, "Instruction count should be 1"
        assert sim.step(), "Second instruction should execute"
        assert sim.instruction_count == 2, "Instruction count should be 2"
        assert sim.step(), "Third instruction should execute"
        assert sim.instruction_count == 3, "Instruction count should be 3"

