"""ARM integration end-to-end workflow tests."""

import pytest
import tempfile
import sys
import importlib.util
from pathlib import Path

from isa_dsl.model.parser import parse_isa_file
from isa_dsl.generators.simulator import SimulatorGenerator
from isa_dsl.generators.assembler import AssemblerGenerator
from isa_dsl.generators.disassembler import DisassemblerGenerator


@pytest.fixture
def arm_isa_file():
    """Path to the ARM ISA subset file."""
    return Path(__file__).parent / "test_data" / "arm_subset.isa"


def test_arm_end_to_end_workflow(arm_isa_file):
    """Test complete end-to-end workflow: assemble, simulate, disassemble."""
    from tests.arm.test_helpers_integration import ArmIntegrationTestHelpers
    
    isa = parse_isa_file(str(arm_isa_file))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        asm_file, sim_file, disasm_file = ArmIntegrationTestHelpers.generate_all_tools(isa, tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            Assembler, Simulator, Disassembler = ArmIntegrationTestHelpers.import_all_tools(
                asm_file, sim_file, disasm_file, tmpdir_path
            )
            
            assembler = Assembler()
            sim = Simulator()
            disassembler = Disassembler()
            
            assembly_code = "MOV_IMM R0, 10\nADD_IMM R1, R0, 5"
            machine_code = assembler.assemble(assembly_code)
            assert len(machine_code) >= 2
            
            sim.load_program(machine_code, start_address=0)
            sim.step()
            assert sim.R[0] == 10
            sim.step()
            assert sim.R[1] == 15
            
            tmp_file_path = tmpdir_path / "disassemble_test.bin"
            ArmIntegrationTestHelpers.write_machine_code_to_file(machine_code, tmp_file_path)
            
            disassembly = disassembler.disassemble_file(str(tmp_file_path))
            assert len(disassembly) > 0
            
        finally:
            sys.path.remove(str(tmpdir_path))

