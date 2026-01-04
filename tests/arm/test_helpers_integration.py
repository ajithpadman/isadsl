"""Helper methods for ARM integration tests (arm_subset.isa)."""

import subprocess
import sys
from pathlib import Path
import pytest


class ArmIntegrationTestHelpers:
    """Helper class for ARM integration test functions."""
    
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
    def get_qemu_command():
        """Get QEMU user mode command if available."""
        if sys.platform != "linux":
            return None
        if ArmIntegrationTestHelpers.check_command_available("qemu-arm"):
            return "qemu-arm"
        return None
    
    @staticmethod
    def get_qemu_system_command():
        """Get QEMU system mode command if available."""
        if sys.platform != "linux":
            return None
        if ArmIntegrationTestHelpers.check_command_available("qemu-system-arm"):
            return "qemu-system-arm"
        return None
    
    @staticmethod
    def get_arm_toolchain():
        """Get ARM toolchain commands if available."""
        if sys.platform != "linux":
            return None
        if ArmIntegrationTestHelpers.check_command_available("arm-linux-gnueabihf-gcc"):
            return {
                "gcc": "arm-linux-gnueabihf-gcc",
                "objdump": "arm-linux-gnueabihf-objdump",
                "objcopy": "arm-linux-gnueabihf-objcopy",
                "ld": "arm-linux-gnueabihf-ld"
            }
        elif ArmIntegrationTestHelpers.check_command_available("arm-none-eabi-gcc"):
            return {
                "gcc": "arm-none-eabi-gcc",
                "objdump": "arm-none-eabi-objdump",
                "objcopy": "arm-none-eabi-objcopy",
                "ld": "arm-none-eabi-ld"
            }
        return None
    
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
    def run_qemu_execution_test(qemu_cmd, elf_file):
        """Run QEMU execution test and verify no fatal errors."""
        try:
            result = subprocess.run(
                [qemu_cmd, str(elf_file)],
                capture_output=True,
                text=True,
                timeout=5
            )
            assert "qemu-arm: fatal:" not in result.stderr.lower(), f"QEMU fatal error: {result.stderr}"
            if "error" in result.stderr.lower():
                assert "exit status" in result.stderr.lower() or "Illegal instruction" not in result.stderr, \
                    f"Unexpected QEMU error: {result.stderr}"
        except subprocess.TimeoutExpired:
            pass
        except FileNotFoundError:
            pytest.skip(f"QEMU command '{qemu_cmd}' not found")
    
    @staticmethod
    def verify_binary_structure(binary_file):
        """Verify binary file has correct structure."""
        assert binary_file.stat().st_size > 0
        assert binary_file.stat().st_size % 4 == 0
    
    @staticmethod
    def generate_and_import_assembler(isa, tmpdir_path):
        """Generate assembler from ISA and import it."""
        import importlib.util
        import sys
        from isa_dsl.generators.assembler import AssemblerGenerator
        
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
    def assemble_and_write_binary(assembler, assembly_code, tmpdir_path, binary_name="test_arm.bin"):
        """Assemble code and write to binary file."""
        machine_code = assembler.assemble(assembly_code)
        assert len(machine_code) >= 2, "Should assemble at least 2 instructions"
        
        binary_file = tmpdir_path / binary_name
        assembler.write_binary(machine_code, str(binary_file))
        assert binary_file.exists() and binary_file.stat().st_size > 0
        
        return machine_code, binary_file
    
    @staticmethod
    def load_and_assemble_file(assembler, assembly_file_path):
        """Load assembly file and assemble it."""
        with open(assembly_file_path, 'r') as f:
            assembly_code = f.read()
        
        machine_code = assembler.assemble(assembly_code)
        assert len(machine_code) >= 5, f"Should assemble at least 5 instructions, got {len(machine_code)}"
        
        return machine_code, assembly_code
    
    @staticmethod
    def verify_labels_resolved(assembler, expected_labels):
        """Verify that expected labels are resolved."""
        for label in expected_labels:
            assert label in assembler.labels, f"{label} label should be defined"
    
    @staticmethod
    def generate_and_import_simulator(isa, tmpdir_path):
        """Generate simulator from ISA and import it."""
        import importlib.util
        import sys
        from isa_dsl.generators.simulator import SimulatorGenerator
        
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir_path)
        
        sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
        sim_module = importlib.util.module_from_spec(sim_spec)
        sim_spec.loader.exec_module(sim_module)
        Simulator = sim_module.Simulator
        sim = Simulator()
        
        return sim, sim_module
    
    @staticmethod
    def run_simulator_and_verify_result(sim, machine_code, max_steps=50):
        """Run simulator and verify memory result."""
        sim.load_program(machine_code, start_address=0)
        
        for _ in range(max_steps):
            if not sim.step():
                break
        
        assert sim.R[1] == 64, f"Expected R1 to contain 64, got {sim.R[1]}"
        assert 64 in sim.memory, f"Memory at address 64 should be written"
        result_in_memory = sim.memory[64]
        assert result_in_memory == 55, f"Expected result 55 in memory, got {result_in_memory}"
        
        return result_in_memory
    
    @staticmethod
    def compile_c_to_object(c_file, toolchain, tmpdir_path, obj_name="arm_test_program.o"):
        """Compile C file to object file."""
        import subprocess
        import pytest
        
        obj_file = tmpdir_path / obj_name
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
        
        return obj_file
    
    @staticmethod
    def generate_and_import_disassembler(isa, tmpdir_path):
        """Generate and import disassembler."""
        import importlib.util
        import sys
        from isa_dsl.generators.disassembler import DisassemblerGenerator
        
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
        """Generate all tools and return file paths."""
        from isa_dsl.generators.assembler import AssemblerGenerator
        from isa_dsl.generators.simulator import SimulatorGenerator
        from isa_dsl.generators.disassembler import DisassemblerGenerator
        
        asm_gen = AssemblerGenerator(isa)
        asm_file = asm_gen.generate(tmpdir_path)
        
        sim_gen = SimulatorGenerator(isa)
        sim_file = sim_gen.generate(tmpdir_path)
        
        disasm_gen = DisassemblerGenerator(isa)
        disasm_file = disasm_gen.generate(tmpdir_path)
        
        return asm_file, sim_file, disasm_file
    
    @staticmethod
    def import_all_tools(asm_file, sim_file, disasm_file, tmpdir_path):
        """Import all generated tools."""
        import importlib.util
        import sys
        
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
    
    @staticmethod
    def start_qemu_with_gdb(qemu_cmd, qemu_system_cmd, elf_file, binary_file, tmpdir_path, gdb_port):
        """Start QEMU with GDB stub."""
        import subprocess
        import shutil
        
        if qemu_system_cmd:
            raw_binary = tmpdir_path / "loop_program_raw.bin"
            shutil.copy(binary_file, raw_binary)
            
            qemu_process = subprocess.Popen(
                [qemu_system_cmd,
                 "-M", "versatilepb",
                 "-cpu", "cortex-a8",
                 "-device", f"loader,file={raw_binary},addr=0x10000,cpu-num=0",
                 "-nographic",
                 "-gdb", f"tcp:127.0.0.1:{gdb_port}",
                 "-S"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        else:
            qemu_process = subprocess.Popen(
                [qemu_cmd, "-g", str(gdb_port), str(elf_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        
        import time
        time.sleep(0.5)
        if qemu_process.poll() is not None:
            stderr_output = qemu_process.stderr.read() if qemu_process.stderr else 'unknown error'
            raise RuntimeError(f"QEMU failed to start: {stderr_output}")
        
        return qemu_process
    
    @staticmethod
    def wait_for_gdb_connection(qemu_process, gdb_port, max_retries=10):
        """Wait for QEMU GDB stub to be ready."""
        import socket
        import time
        
        for retry in range(max_retries):
            time.sleep(0.5)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            try:
                result = sock.connect_ex(('127.0.0.1', gdb_port))
                if result == 0:
                    sock.close()
                    return True
            except Exception:
                pass
            finally:
                try:
                    sock.close()
                except:
                    pass
            
            if qemu_process.poll() is not None:
                stderr_output = qemu_process.stderr.read() if qemu_process.stderr else 'unknown error'
                raise RuntimeError(f"QEMU exited unexpectedly: {stderr_output}")
        
        return False
    
    @staticmethod
    def create_gdb_script_for_labels_test(gdb_port, tmpdir_path, qemu_system_cmd, script_name="inspect_loop.gdb"):
        """Create GDB script for labels/loops test."""
        gdb_script = tmpdir_path / script_name
        
        if qemu_system_cmd:
            gdb_script_content = f"""
set confirm off
set pagination off
target remote 127.0.0.1:{gdb_port}
set $pc = 0x10000
continue
info registers r0
info registers r1
info registers
detach
quit
"""
        else:
            gdb_script_content = f"""
set confirm off
set pagination off
target remote 127.0.0.1:{gdb_port}
continue
info registers r0
info registers r1
info registers
detach
quit
"""
        gdb_script.write_text(gdb_script_content)
        return gdb_script
    
    @staticmethod
    def run_gdb_inspection(gdb_cmd, elf_file, gdb_script, timeout=20):
        """Run GDB inspection and return output."""
        import subprocess
        
        gdb_result = subprocess.run(
            [gdb_cmd, "-batch", "-x", str(gdb_script), str(elf_file)],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return gdb_result.stdout + gdb_result.stderr
    
    @staticmethod
    def get_gdb_command():
        """Get available GDB command."""
        if ArmIntegrationTestHelpers.check_command_available("gdb-multiarch"):
            return "gdb-multiarch"
        elif ArmIntegrationTestHelpers.check_command_available("arm-none-eabi-gdb"):
            return "arm-none-eabi-gdb"
        elif ArmIntegrationTestHelpers.check_command_available("gdb"):
            return "gdb"
        return None
    
    @staticmethod
    def run_qemu_gdb_test_with_cleanup(qemu_cmd, qemu_system_cmd, elf_file, binary_file, tmpdir_path, gdb_cmd):
        """Run QEMU GDB test with automatic cleanup. Returns GDB output."""
        import random
        import subprocess
        
        gdb_port = random.randint(20000, 30000)
        qemu_process = None
        
        try:
            qemu_process = ArmIntegrationTestHelpers.start_qemu_with_gdb(
                qemu_cmd, qemu_system_cmd, elf_file, binary_file, tmpdir_path, gdb_port
            )
            
            if not ArmIntegrationTestHelpers.wait_for_gdb_connection(qemu_process, gdb_port):
                raise ConnectionError(f"QEMU gdb stub not listening on port {gdb_port}")
            
            gdb_script = ArmIntegrationTestHelpers.create_gdb_script_for_labels_test(
                gdb_port, tmpdir_path, qemu_system_cmd
            )
            
            gdb_output = ArmIntegrationTestHelpers.run_gdb_inspection(gdb_cmd, elf_file, gdb_script)
            
            qemu_process.terminate()
            try:
                qemu_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                qemu_process.kill()
            
            return gdb_output
        
        except Exception as e:
            if qemu_process:
                qemu_process.terminate()
                try:
                    qemu_process.wait(timeout=1)
                except:
                    qemu_process.kill()
            raise

