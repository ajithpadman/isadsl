"""ARM Cortex-A9 disassembler tests."""

import pytest
import tempfile
import sys
import subprocess
import importlib.util
from pathlib import Path

from isa_dsl.model.parser import parse_isa_file
from isa_dsl.generators.disassembler import DisassemblerGenerator
from tests.arm.test_helpers import ArmTestHelpers


@pytest.mark.skipif(
    sys.platform != "linux",
    reason="ARM toolchain test requires Linux"
)
@pytest.mark.skipif(
    not (ArmTestHelpers.check_command_available("arm-linux-gnueabihf-gcc") or 
         ArmTestHelpers.check_command_available("arm-none-eabi-gcc")),
    reason="ARM toolchain test requires ARM GCC in PATH"
)
def test_arm_cortex_a9_disassembler_toolchain_verification(arm_cortex_a9_isa_file, matrix_multiply_c_file):
    """Test ARM Cortex-A9 disassembler by round-trip verification with ARM toolchain."""
    isa = parse_isa_file(str(arm_cortex_a9_isa_file))
    toolchain = ArmTestHelpers.get_arm_toolchain()
    assert toolchain is not None
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        obj_file, original_binary = ArmTestHelpers.compile_and_extract_text_section(
            matrix_multiply_c_file, toolchain, tmpdir_path
        )
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            disassembler = ArmTestHelpers.generate_and_import_disassembler(isa, tmpdir_path)
            disassembly_results = disassembler.disassemble_file(str(original_binary), start_address=0)
            assert len(disassembly_results) > 0
            
            for addr, asm in disassembly_results:
                assert isinstance(addr, int) and isinstance(asm, str) and len(asm) > 0
            
            disassembled_asm_file = tmpdir_path / "disassembled_matrix.s"
            ArmTestHelpers.write_disassembly_to_file(disassembly_results, disassembled_asm_file)
            assert disassembled_asm_file.exists() and disassembled_asm_file.stat().st_size > 0
            
            disassembled_obj_file = tmpdir_path / "disassembled_matrix.o"
            try:
                result = subprocess.run([toolchain["gcc"], "-c", "-o", str(disassembled_obj_file), str(disassembled_asm_file)],
                    check=True, capture_output=True, text=True, timeout=10)
            except subprocess.CalledProcessError as e:
                pytest.fail(f"Failed to compile disassembled assembly file: {e.stderr[:500]}")
            except subprocess.TimeoutExpired:
                pytest.fail("ARM compilation of disassembled file timed out")
            
            assert disassembled_obj_file.exists() and disassembled_obj_file.stat().st_size > 0, \
                "Disassembled object file should be created"
            disassembled_binary = tmpdir_path / "disassembled_matrix_text.bin"
            assert ArmTestHelpers.extract_text_section_from_elf(disassembled_obj_file, disassembled_binary, toolchain["objcopy"]), \
                "Failed to extract .text section from disassembled ELF file"
            assert disassembled_binary.exists() and disassembled_binary.stat().st_size > 0
        finally:
            sys.path.remove(str(tmpdir_path))

