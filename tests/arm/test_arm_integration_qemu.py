"""ARM integration QEMU tests."""

import pytest
import tempfile
import sys
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
def test_arm_assembler_qemu_verification(arm_isa_file):
    """Test ARM assembler by running generated code in QEMU."""
    isa = parse_isa_file(str(arm_isa_file))
    qemu_cmd = ArmIntegrationTestHelpers.get_qemu_command()
    assert qemu_cmd is not None
    
    toolchain = ArmIntegrationTestHelpers.get_arm_toolchain()
    if not toolchain:
        pytest.skip("ARM toolchain required")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        try:
            assembler, _ = ArmIntegrationTestHelpers.generate_and_import_assembler(isa, tmpdir_path)
            
            assembly_code = "MOV R0, #42\nADD R1, R0, #5"
            machine_code, binary_file = ArmIntegrationTestHelpers.assemble_and_write_binary(
                assembler, assembly_code, tmpdir_path
            )
            
            elf_file = tmpdir_path / "test_arm_elf"
            ArmIntegrationTestHelpers.create_elf_wrapper(binary_file, elf_file, toolchain, tmpdir_path)
            
            ArmIntegrationTestHelpers.run_qemu_execution_test(qemu_cmd, elf_file)
            ArmIntegrationTestHelpers.verify_binary_structure(binary_file)
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


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
def test_arm_assembler_file_qemu_execution(arm_isa_file):
    """Test ARM assembler by loading assembly from file and running in QEMU."""
    isa = parse_isa_file(str(arm_isa_file))
    qemu_cmd = ArmIntegrationTestHelpers.get_qemu_command()
    assert qemu_cmd is not None
    
    toolchain = ArmIntegrationTestHelpers.get_arm_toolchain()
    assert toolchain is not None
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        try:
            assembler, _ = ArmIntegrationTestHelpers.generate_and_import_assembler(isa, tmpdir_path)
            
            test_data_dir = Path(__file__).parent / "test_data"
            assembly_file = test_data_dir / "arm_test_program.s"
            assert assembly_file.exists(), f"Assembly file not found: {assembly_file}"
            
            machine_code, assembly_code = ArmIntegrationTestHelpers.load_and_assemble_file(assembler, assembly_file)
            
            binary_file = tmpdir_path / "test_program.bin"
            assembler.write_binary(machine_code, str(binary_file))
            ArmIntegrationTestHelpers.verify_binary_structure(binary_file)
            
            elf_file = tmpdir_path / "test_program_elf"
            ArmIntegrationTestHelpers.create_elf_wrapper(binary_file, elf_file, toolchain, tmpdir_path, "test_program.bin")
            
            ArmIntegrationTestHelpers.run_qemu_execution_test(qemu_cmd, elf_file)
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))

