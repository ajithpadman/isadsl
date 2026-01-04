"""Basic helper utilities for ARM Cortex-A9 tests."""

import subprocess
import sys
from pathlib import Path


class ArmTestHelpersBasic:
    """Basic utility methods for ARM tests."""
    
    @staticmethod
    def check_command_available(cmd):
        """Check if a command is available in PATH."""
        try:
            subprocess.run(
                [cmd, "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    @staticmethod
    def extract_text_section_from_elf(elf_file, output_bin, objcopy_cmd):
        """Extract .text section from ELF file to raw binary."""
        try:
            subprocess.run(
                [objcopy_cmd, "-O", "binary", "--only-section=.text",
                 str(elf_file), str(output_bin)],
                check=True,
                capture_output=True,
                timeout=10
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    @staticmethod
    def filter_gcc_assembly(asm_file):
        """Filter GCC-generated assembly to extract only instructions and labels."""
        with open(asm_file, 'r') as f:
            lines = f.readlines()
        
        filtered_lines = []
        for line in lines:
            original_line = line.rstrip()
            stripped = original_line.strip()
            
            if not stripped:
                continue
            if stripped.startswith('.'):
                continue
            if stripped.startswith('@') or stripped.startswith('//'):
                continue
            if stripped == '#' or (stripped.startswith('#') and not any(c.isalnum() for c in stripped[1:3])):
                continue
            
            comment_pos = -1
            if '@' in stripped:
                comment_pos = stripped.find('@')
            elif '//' in stripped:
                comment_pos = stripped.find('//')
            
            if comment_pos >= 0:
                stripped = stripped[:comment_pos].strip()
                if not stripped:
                    continue
            
            is_label = stripped.endswith(':') and len(stripped.split()) == 1
            filtered_lines.append(stripped)
        
        return '\n'.join(filtered_lines)
    
    @staticmethod
    def get_qemu_command():
        """Get QEMU user mode command if available."""
        if sys.platform != "linux":
            return None
        if ArmTestHelpersBasic.check_command_available("qemu-arm"):
            return "qemu-arm"
        return None
    
    @staticmethod
    def get_qemu_system_command():
        """Get QEMU system mode command if available."""
        if sys.platform != "linux":
            return None
        if ArmTestHelpersBasic.check_command_available("qemu-system-arm"):
            return "qemu-system-arm"
        return None
    
    @staticmethod
    def get_arm_toolchain():
        """Get ARM toolchain commands if available."""
        if sys.platform != "linux":
            return None
        if ArmTestHelpersBasic.check_command_available("arm-linux-gnueabihf-gcc"):
            return {
                "gcc": "arm-linux-gnueabihf-gcc",
                "objdump": "arm-linux-gnueabihf-objdump",
                "objcopy": "arm-linux-gnueabihf-objcopy",
                "ld": "arm-linux-gnueabihf-ld"
            }
        elif ArmTestHelpersBasic.check_command_available("arm-none-eabi-gcc"):
            return {
                "gcc": "arm-none-eabi-gcc",
                "objdump": "arm-none-eabi-objdump",
                "objcopy": "arm-none-eabi-objcopy",
                "ld": "arm-none-eabi-ld"
            }
        return None
    
    @staticmethod
    def verify_binary_structure(binary_file):
        """Verify binary file has correct structure."""
        assert binary_file.stat().st_size > 0
        assert binary_file.stat().st_size % 4 == 0

