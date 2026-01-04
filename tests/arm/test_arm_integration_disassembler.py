"""ARM integration disassembler tests."""

import pytest
import tempfile
import sys
import subprocess
import importlib.util
from pathlib import Path

from isa_dsl.model.parser import parse_isa_file
from isa_dsl.generators.disassembler import DisassemblerGenerator
from tests.arm.test_helpers_integration import ArmIntegrationTestHelpers


@pytest.fixture
def arm_isa_file():
    """Path to the ARM ISA subset file."""
    return Path(__file__).parent / "test_data" / "arm_subset.isa"


@pytest.mark.skipif(
    sys.platform != "linux",
    reason="ARM toolchain test requires Linux"
)
@pytest.mark.skipif(
    not (ArmIntegrationTestHelpers.check_command_available("arm-linux-gnueabihf-gcc") or 
         ArmIntegrationTestHelpers.check_command_available("arm-none-eabi-gcc")),
    reason="ARM toolchain test requires ARM GCC in PATH"
)
def test_arm_disassembler_toolchain_verification(arm_isa_file):
    """Test ARM disassembler by round-trip verification with ARM toolchain."""
    isa = parse_isa_file(str(arm_isa_file))
    toolchain = ArmIntegrationTestHelpers.get_arm_toolchain()
    assert toolchain is not None
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        test_data_dir = Path(__file__).parent / "test_data"
        c_file = test_data_dir / "arm_test_program.c"
        if not c_file.exists():
            pytest.skip(f"C file not found: {c_file}")
        
        obj_file = ArmIntegrationTestHelpers.compile_c_to_object(c_file, toolchain, tmpdir_path)
        
        original_binary = tmpdir_path / "arm_test_program_text.bin"
        if not ArmIntegrationTestHelpers.extract_text_section_from_elf(obj_file, original_binary, toolchain["objcopy"]):
            pytest.skip("Failed to extract .text section from ELF file")
        
        assert original_binary.exists() and original_binary.stat().st_size > 0
        
        sys.path.insert(0, str(tmpdir_path))
        try:
            disassembler = ArmIntegrationTestHelpers.generate_and_import_disassembler(isa, tmpdir_path)
            
            disassembly_results = disassembler.disassemble_file(str(original_binary), start_address=0)
            assert len(disassembly_results) > 0
            
            for addr, asm in disassembly_results:
                assert isinstance(addr, int) and isinstance(asm, str) and len(asm) > 0
            
            disassembled_asm_file = tmpdir_path / "disassembled_program.s"
            ArmIntegrationTestHelpers.write_disassembly_to_file(disassembly_results, disassembled_asm_file)
            assert disassembled_asm_file.exists() and disassembled_asm_file.stat().st_size > 0
            
        finally:
            sys.path.remove(str(tmpdir_path))

