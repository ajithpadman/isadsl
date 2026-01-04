"""Helper methods for generator tests."""

import tempfile
import importlib.util
from pathlib import Path

from isa_dsl.generators.simulator import SimulatorGenerator
from isa_dsl.generators.assembler import AssemblerGenerator


class GeneratorTestHelpers:
    """Helper class for generator test functions."""
    
    @staticmethod
    def generate_and_import_assembler(isa, tmpdir_path):
        """Generate assembler and import it."""
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir_path)
        assert asm_file.exists()
        
        spec = importlib.util.spec_from_file_location("assembler", asm_file)
        assembler_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(assembler_module)
        return assembler_module.Assembler
    
    @staticmethod
    def generate_and_import_simulator(isa, tmpdir_path):
        """Generate simulator and import it."""
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir_path)
        assert sim_file.exists()
        
        spec = importlib.util.spec_from_file_location("simulator", sim_file)
        simulator_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(simulator_module)
        return simulator_module.Simulator
    
    @staticmethod
    def generate_and_import_both(isa, tmpdir_path):
        """Generate assembler and simulator and import them."""
        Assembler = GeneratorTestHelpers.generate_and_import_assembler(isa, tmpdir_path)
        Simulator = GeneratorTestHelpers.generate_and_import_simulator(isa, tmpdir_path)
        return Assembler, Simulator
    
    @staticmethod
    def verify_simulator_initialization(sim):
        """Verify simulator is initialized correctly."""
        assert hasattr(sim, 'R'), "Simulator should have R register file"
        assert hasattr(sim, 'PC'), "Simulator should have PC register"
        assert hasattr(sim, 'memory'), "Simulator should have memory"
        assert sim.PC == 0, "PC should initialize to 0"
        assert len(sim.R) == 4, "R register file should have 4 registers"

