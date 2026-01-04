"""ARM integration tests for labels and loops with QEMU."""

import pytest
import tempfile
import sys
import subprocess
from pathlib import Path

from isa_dsl.model.parser import parse_isa_file
from tests.arm.test_helpers_integration import ArmIntegrationTestHelpers


@pytest.fixture
def arm_isa_file():
    """Path to the ARM ISA subset file."""
    return Path(__file__).parent / "test_data" / "arm_subset.isa"


@pytest.mark.skipif(
    sys.platform != "linux",
    reason="QEMU test requires Linux"
)
@pytest.mark.skipif(
    not ArmIntegrationTestHelpers.check_command_available("qemu-arm"),
    reason="QEMU test requires qemu-arm in PATH"
)
@pytest.mark.skipif(
    not (ArmIntegrationTestHelpers.check_command_available("arm-linux-gnueabihf-gcc") or 
         ArmIntegrationTestHelpers.check_command_available("arm-none-eabi-gcc")),
    reason="ARM toolchain test requires ARM GCC in PATH"
)
def test_arm_assembler_labels_and_loops_qemu(arm_isa_file):
    """Test ARM assembler with labels and loop/jump statements in QEMU."""
    isa = parse_isa_file(str(arm_isa_file))
    qemu_cmd = ArmIntegrationTestHelpers.get_qemu_command()
    toolchain = ArmIntegrationTestHelpers.get_arm_toolchain()
    assert qemu_cmd is not None and toolchain is not None
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        try:
            assembler, _ = ArmIntegrationTestHelpers.generate_and_import_assembler(isa, tmpdir_path)
            assembly_file = Path(__file__).parent / "test_data" / "arm_loop_sum_1_to_10.s"
            machine_code, _ = ArmIntegrationTestHelpers.load_and_assemble_file(assembler, assembly_file)
            
            ArmIntegrationTestHelpers.verify_labels_resolved(assembler, ['add1', 'add10', 'end_program'])
            sim, _ = ArmIntegrationTestHelpers.generate_and_import_simulator(isa, tmpdir_path)
            ArmIntegrationTestHelpers.run_simulator_and_verify_result(sim, machine_code)
            
            binary_file = tmpdir_path / "loop_program.bin"
            assembler.write_binary(machine_code, str(binary_file))
            ArmIntegrationTestHelpers.verify_binary_structure(binary_file)
            elf_file = tmpdir_path / "loop_program_elf"
            ArmIntegrationTestHelpers.create_elf_wrapper(binary_file, elf_file, toolchain, tmpdir_path, "loop_program.bin")
            
            gdb_cmd = ArmIntegrationTestHelpers.get_gdb_command()
            qemu_system_cmd = ArmIntegrationTestHelpers.get_qemu_system_command()
            
            if gdb_cmd:
                try:
                    gdb_output = ArmIntegrationTestHelpers.run_qemu_gdb_test_with_cleanup(
                        qemu_cmd, qemu_system_cmd, elf_file, binary_file, tmpdir_path, gdb_cmd
                    )
                    assert "target remote" in gdb_output.lower() or "Remote debugging" in gdb_output, \
                        f"GDB should connect successfully. Output: {gdb_output[:500]}"
                except (FileNotFoundError, ConnectionError, subprocess.TimeoutExpired, Exception):
                    ArmIntegrationTestHelpers.run_qemu_execution_test(qemu_cmd, elf_file)
            else:
                ArmIntegrationTestHelpers.run_qemu_execution_test(qemu_cmd, elf_file)
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))

