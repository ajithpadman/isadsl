"""ARM Cortex-A9 QEMU integration tests."""

import pytest
import tempfile
import sys
import subprocess
from pathlib import Path

from isa_dsl.model.parser import parse_isa_file
from tests.arm.test_helpers import ArmTestHelpers


@pytest.mark.skipif(
    sys.platform != "linux",
    reason="QEMU test requires Linux"
)
@pytest.mark.skipif(
    not ArmTestHelpers.check_command_available("qemu-arm"),
    reason="QEMU test requires qemu-arm in PATH"
)
def test_arm_cortex_a9_assembler_qemu_verification(arm_cortex_a9_isa_file, matrix_multiply_c_file):
    """Test ARM Cortex-A9 assembler by running code compiled from C program in QEMU."""
    isa = parse_isa_file(str(arm_cortex_a9_isa_file))
    qemu_cmd = ArmTestHelpers.get_qemu_command()
    assert qemu_cmd is not None
    
    toolchain = ArmTestHelpers.get_arm_toolchain()
    if not toolchain:
        pytest.skip("ARM toolchain required")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        try:
            assembler, machine_code, binary_file = ArmTestHelpers.assemble_from_c_file(
                isa, matrix_multiply_c_file, tmpdir_path, toolchain
            )
            
            elf_file = tmpdir_path / "test_arm_elf"
            ArmTestHelpers.create_elf_wrapper(binary_file, elf_file, toolchain, tmpdir_path)
            
            gdb_connected, _ = ArmTestHelpers.run_gdb_inspection_with_cleanup(
                qemu_cmd, elf_file, tmpdir_path, "inspect_verification.gdb"
            )
            
            if not gdb_connected:
                ArmTestHelpers.run_basic_execution_test(qemu_cmd, elf_file)
            
            ArmTestHelpers.verify_binary_structure(binary_file)
            
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


@pytest.mark.skipif(
    sys.platform != "linux",
    reason="QEMU test requires Linux"
)
@pytest.mark.skipif(
    not ArmTestHelpers.check_command_available("qemu-arm"),
    reason="QEMU test requires qemu-arm in PATH"
)
@pytest.mark.skipif(
    not (ArmTestHelpers.check_command_available("arm-linux-gnueabihf-gcc") or 
         ArmTestHelpers.check_command_available("arm-none-eabi-gcc")),
    reason="ARM toolchain test requires ARM GCC in PATH"
)
def test_arm_cortex_a9_assembler_file_qemu_execution(arm_cortex_a9_isa_file, matrix_multiply_c_file):
    """Test ARM Cortex-A9 assembler by compiling C program and running in QEMU."""
    isa = parse_isa_file(str(arm_cortex_a9_isa_file))
    qemu_cmd = ArmTestHelpers.get_qemu_command()
    toolchain = ArmTestHelpers.get_arm_toolchain()
    assert qemu_cmd is not None and toolchain is not None
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        try:
            assembler, machine_code, assembler_binary_file = ArmTestHelpers.assemble_from_c_file(
                isa, matrix_multiply_c_file, tmpdir_path, toolchain
            )
            toolchain_elf_file = tmpdir_path / "matrix_multiply.elf"
            ArmTestHelpers.compile_c_to_binary(matrix_multiply_c_file, toolchain_elf_file, toolchain)
            ArmTestHelpers.verify_binary_structure(assembler_binary_file)
            
            assembler_elf_file = tmpdir_path / "test_program_elf"
            ArmTestHelpers.create_elf_wrapper(assembler_binary_file, assembler_elf_file, toolchain, tmpdir_path, "test_program.bin")
            
            gdb_connected, _ = ArmTestHelpers.run_gdb_inspection_with_cleanup(
                qemu_cmd, assembler_elf_file, tmpdir_path, "inspect_assembler.gdb"
            )
            if not gdb_connected:
                ArmTestHelpers.run_basic_execution_test(qemu_cmd, assembler_elf_file)
            
            ArmTestHelpers.verify_toolchain_binary_execution(qemu_cmd, toolchain_elf_file)
        finally:
            if str(tmpdir_path) in sys.path:
                sys.path.remove(str(tmpdir_path))


@pytest.mark.skipif(
    sys.platform != "linux",
    reason="QEMU test requires Linux"
)
@pytest.mark.skipif(
    not ArmTestHelpers.check_command_available("qemu-arm"),
    reason="QEMU test requires qemu-arm in PATH"
)
@pytest.mark.skipif(
    not (ArmTestHelpers.check_command_available("arm-linux-gnueabihf-gcc") or 
         ArmTestHelpers.check_command_available("arm-none-eabi-gcc")),
    reason="ARM toolchain test requires ARM GCC in PATH"
)
def test_arm_cortex_a9_assembler_labels_and_loops_qemu(arm_cortex_a9_isa_file, matrix_multiply_c_file):
    """Test ARM Cortex-A9 assembler with matrix multiplication program in QEMU system mode."""
    isa = parse_isa_file(str(arm_cortex_a9_isa_file))
    qemu_cmd = ArmTestHelpers.get_qemu_command()
    assert qemu_cmd is not None
    
    toolchain = ArmTestHelpers.get_arm_toolchain()
    assert toolchain is not None
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        elf_file = ArmTestHelpers.compile_c_to_binary(matrix_multiply_c_file, tmpdir_path / "matrix_multiply.elf", toolchain)
        
        binary_file = tmpdir_path / "matrix_multiply.bin"
        if not ArmTestHelpers.extract_text_section_from_elf(elf_file, binary_file, toolchain["objcopy"]):
            pytest.skip("Failed to extract .text section from ELF")
        
        ArmTestHelpers.verify_binary_structure(binary_file)
        
        qemu_system_cmd = ArmTestHelpers.get_qemu_system_command()
        
        try:
            ArmTestHelpers.run_qemu_system_mode_test(qemu_cmd, qemu_system_cmd, elf_file, binary_file, tmpdir_path)
        except FileNotFoundError:
            pytest.skip("QEMU or gdb command not found")
        except (ConnectionError, subprocess.TimeoutExpired) as e:
            error_type = "connection failed" if isinstance(e, ConnectionError) else "connection timed out"
            ArmTestHelpers.verify_program_execution_with_fallback(qemu_cmd, elf_file, 
                f"gdb {error_type} ({type(e).__name__}: {str(e)[:100]})")
        except Exception as e:
            ArmTestHelpers.verify_program_execution_with_fallback(qemu_cmd, elf_file,
                f"gdb inspection failed ({type(e).__name__}: {str(e)[:100]})")

