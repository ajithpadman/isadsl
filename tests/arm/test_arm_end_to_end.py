"""ARM Cortex-A9 end-to-end workflow tests."""

import pytest
import tempfile
import sys
import importlib.util
from pathlib import Path

from isa_dsl.model.parser import parse_isa_file
from isa_dsl.generators.simulator import SimulatorGenerator
from isa_dsl.generators.assembler import AssemblerGenerator
from isa_dsl.generators.disassembler import DisassemblerGenerator
from tests.arm.test_helpers import ArmTestHelpers


def test_arm_cortex_a9_end_to_end_workflow(arm_cortex_a9_isa_file):
    """Test complete end-to-end workflow: assemble, simulate, disassemble."""
    isa = parse_isa_file(str(arm_cortex_a9_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        asm_file, sim_file, disasm_file = ArmTestHelpers.generate_all_tools(isa, tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            Assembler, Simulator, Disassembler = ArmTestHelpers.import_all_tools(
                asm_file, sim_file, disasm_file, tmpdir_path
            )
            
            assembler = Assembler()
            sim = Simulator()
            disassembler = Disassembler()
            
            assembly_code = "MOV R0, #10\nADD R1, R0, #5"
            machine_code = assembler.assemble(assembly_code)
            assert len(machine_code) >= 2
            
            sim.load_program(machine_code, start_address=0)
            assert sim.step() and sim.R[0] == 10
            assert sim.step() and sim.R[1] == 15
            
            tmp_file_path = tmpdir_path / "disassemble_test.bin"
            ArmTestHelpers.write_machine_code_to_file(machine_code, tmp_file_path)
            
            disassembly = disassembler.disassemble_file(str(tmp_file_path))
            assert len(disassembly) > 0
            
        finally:
            sys.path.remove(str(tmpdir_path))

