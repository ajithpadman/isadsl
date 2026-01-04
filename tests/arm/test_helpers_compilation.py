"""Compilation and assembly helper methods for ARM Cortex-A9 tests."""

import subprocess
import sys
import importlib.util
from pathlib import Path
import pytest

from isa_dsl.generators.assembler import AssemblerGenerator
from isa_dsl.generators.simulator import SimulatorGenerator
from isa_dsl.generators.disassembler import DisassemblerGenerator
from tests.arm.test_helpers_basic import ArmTestHelpersBasic


class ArmTestHelpersCompilation:
    """Helper methods for compilation and assembly operations."""
    
    @staticmethod
    def generate_and_import_assembler(isa, tmpdir_path):
        """Generate assembler from ISA and import it."""
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
        asm_module = importlib.util.module_from_spec(asm_spec)
        asm_spec.loader.exec_module(asm_module)
        Assembler = asm_module.Assembler
        assembler = Assembler()
        
        return assembler, asm_module
    
    @staticmethod
    def compile_c_to_assembly(c_file, output_asm, toolchain):
        """Compile C file to assembly using ARM toolchain."""
        try:
            subprocess.run(
                [toolchain["gcc"], "-S", "-fno-asynchronous-unwind-tables",
                 "-o", str(output_asm), str(c_file)],
                check=True,
                capture_output=True,
                timeout=10
            )
        except subprocess.CalledProcessError as e:
            pytest.skip(f"Failed to compile C to assembly: {e.stderr.decode()[:200]}")
        
        assert output_asm.exists(), "Assembly file should be created from C compilation"
        assert output_asm.stat().st_size > 0, "Assembly file should have content"
        return output_asm
    
    @staticmethod
    def assemble_code(assembler, assembly_code, tmpdir_path):
        """Assemble assembly code with error handling."""
        try:
            machine_code = assembler.assemble(assembly_code)
        except Exception as e:
            error_msg = f"Failed to assemble GCC-generated assembly code.\n"
            error_msg += f"Error: {type(e).__name__}: {str(e)}\n"
            error_msg += f"First 1000 characters of assembly code:\n{assembly_code[:1000]}\n"
            debug_asm_file = tmpdir_path / "debug_assembly.s"
            debug_asm_file.write_text(assembly_code)
            error_msg += f"Full assembly saved to: {debug_asm_file}"
            pytest.fail(error_msg)
        
        assert len(machine_code) > 0, f"Should assemble at least some instructions, got {len(machine_code)}. Assembly code:\n{assembly_code[:500]}"
        return machine_code
    
    @staticmethod
    def create_elf_wrapper(binary_file, elf_file, toolchain, tmpdir_path, binary_name_in_wrapper=None):
        """Create ELF wrapper around binary file."""
        if binary_name_in_wrapper is None:
            binary_name_in_wrapper = binary_file.name
        
        try:
            subprocess.run(
                [toolchain["objcopy"], 
                 "-I", "binary",
                 "-O", "elf32-littlearm",
                 "-B", "arm",
                 "--rename-section", ".data=.text",
                 "--set-section-flags", ".text=code",
                 str(binary_file),
                 str(elf_file)],
                check=True,
                capture_output=True,
                text=True,
                timeout=10
            )
        except subprocess.CalledProcessError:
            wrapper_asm = tmpdir_path / "wrapper.s"
            wrapper_text = f"""
.section .text
.global _start
_start:
    .incbin "{binary_name_in_wrapper}"
    mov r7, #1      @ syscall number for exit
    mov r0, #0      @ exit status
    svc #0          @ make syscall
"""
            wrapper_asm.write_text(wrapper_text)
            
            obj_file = tmpdir_path / "wrapper.o"
            subprocess.run(
                [toolchain["gcc"], "-c", "-o", str(obj_file), str(wrapper_asm)],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(tmpdir_path)
            )
            
            subprocess.run(
                [toolchain["gcc"], "-nostdlib", "-static", "-o", str(elf_file), str(obj_file)],
                check=True,
                capture_output=True,
                text=True,
                timeout=10
            )
        except subprocess.TimeoutExpired:
            pytest.skip("ELF creation timed out")
        
        assert elf_file.exists(), "ELF file should be created"
        assert elf_file.stat().st_size > 0, "ELF file should have content"
        return elf_file
    
    @staticmethod
    def compile_c_to_binary(c_file, output_elf, toolchain):
        """Compile C file to binary ELF using ARM toolchain."""
        try:
            subprocess.run(
                [toolchain["gcc"], "-static", "-o", str(output_elf), str(c_file)],
                check=True,
                capture_output=True,
                timeout=10
            )
        except subprocess.CalledProcessError as e:
            pytest.skip(f"Failed to compile C program: {e.stderr.decode()[:200]}")
        
        return output_elf
    
    @staticmethod
    def assemble_from_c_file(isa, c_file, tmpdir_path, toolchain):
        """Compile C to assembly, filter, and assemble. Returns (assembler, machine_code, binary_file)."""
        assembler, _ = ArmTestHelpersCompilation.generate_and_import_assembler(isa, tmpdir_path)
        
        asm_from_c = tmpdir_path / "matrix_multiply.s"
        ArmTestHelpersCompilation.compile_c_to_assembly(c_file, asm_from_c, toolchain)
        assembly_code = ArmTestHelpersBasic.filter_gcc_assembly(asm_from_c)
        assert len(assembly_code.strip()) > 0
        
        machine_code = ArmTestHelpersCompilation.assemble_code(assembler, assembly_code, tmpdir_path)
        
        binary_file = tmpdir_path / "test_arm.bin"
        assembler.write_binary(machine_code, str(binary_file))
        assert binary_file.exists() and binary_file.stat().st_size > 0
        
        return assembler, machine_code, binary_file
    
    @staticmethod
    def compile_and_extract_text_section(c_file, toolchain, tmpdir_path):
        """Compile C to object file and extract .text section. Returns (obj_file, binary_file)."""
        obj_file = tmpdir_path / "matrix_multiply.o"
        try:
            subprocess.run(
                [toolchain["gcc"], "-c", "-o", str(obj_file), str(c_file)],
                check=True,
                capture_output=True,
                text=True,
                timeout=10
            )
        except subprocess.CalledProcessError as e:
            pytest.skip(f"Failed to compile C program: {e.stderr}")
        except subprocess.TimeoutExpired:
            pytest.skip("ARM compilation timed out")
        
        binary_file = tmpdir_path / "matrix_multiply_text.bin"
        if not ArmTestHelpersBasic.extract_text_section_from_elf(obj_file, binary_file, toolchain["objcopy"]):
            pytest.skip("Failed to extract .text section from ELF file")
        
        assert binary_file.exists() and binary_file.stat().st_size > 0
        return obj_file, binary_file
    
    @staticmethod
    def generate_and_import_disassembler(isa, tmpdir_path):
        """Generate and import disassembler. Returns disassembler instance."""
        disasm_gen = DisassemblerGenerator(isa)
        disasm_file = disasm_gen.generate(tmpdir_path)
        
        sys.path.insert(0, str(tmpdir_path))
        disasm_spec = importlib.util.spec_from_file_location("disassembler", disasm_file)
        disasm_module = importlib.util.module_from_spec(disasm_spec)
        disasm_spec.loader.exec_module(disasm_module)
        return disasm_module.Disassembler()
    
    @staticmethod
    def write_disassembly_to_file(disassembly_results, output_file):
        """Write disassembly results to assembly file."""
        with open(output_file, 'w') as f:
            f.write(".section .text\n.global _start\n_start:\n")
            for addr, asm in disassembly_results:
                f.write(f"    {asm}\n")
    
    @staticmethod
    def generate_all_tools(isa, tmpdir_path):
        """Generate all tools (assembler, simulator, disassembler). Returns (asm_file, sim_file, disasm_file)."""
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir_path)
        
        disasm_gen = DisassemblerGenerator(isa)
        disasm_file = disasm_gen.generate(tmpdir_path)
        
        return asm_file, sim_file, disasm_file
    
    @staticmethod
    def import_all_tools(asm_file, sim_file, disasm_file, tmpdir_path):
        """Import all generated tools. Returns (Assembler, Simulator, Disassembler classes)."""
        sys.path.insert(0, str(tmpdir_path))
        
        asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
        asm_module = importlib.util.module_from_spec(asm_spec)
        asm_spec.loader.exec_module(asm_module)
        
        sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
        sim_module = importlib.util.module_from_spec(sim_spec)
        sim_spec.loader.exec_module(sim_module)
        
        disasm_spec = importlib.util.spec_from_file_location("disassembler", disasm_file)
        disasm_module = importlib.util.module_from_spec(disasm_spec)
        disasm_spec.loader.exec_module(disasm_module)
        
        return asm_module.Assembler, sim_module.Simulator, disasm_module.Disassembler
    
    @staticmethod
    def write_machine_code_to_file(machine_code, output_file):
        """Write machine code to binary file."""
        with open(output_file, 'wb') as f:
            for word in machine_code:
                f.write(word.to_bytes(4, byteorder='little'))

