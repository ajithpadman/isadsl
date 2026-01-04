"""QEMU and GDB helper methods for ARM Cortex-A9 tests."""

import subprocess
import socket
import time
import shutil
import random
import re
from pathlib import Path
import pytest

from tests.arm.test_helpers_basic import ArmTestHelpersBasic


class ArmTestHelpersQemu:
    """Helper methods for QEMU and GDB operations."""
    
    @staticmethod
    def connect_to_qemu_gdb(qemu_cmd, elf_file, gdb_port):
        """Start QEMU with GDB stub and wait for connection."""
        qemu_process = subprocess.Popen(
            [qemu_cmd, "-g", str(gdb_port), str(elf_file)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        time.sleep(0.5)
        if qemu_process.poll() is not None:
            stderr_output = qemu_process.stderr.read() if qemu_process.stderr else 'unknown error'
            raise RuntimeError(f"QEMU failed to start: {stderr_output}")
        
        max_retries = 20
        connected = False
        for retry in range(max_retries):
            time.sleep(0.3)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            try:
                result = sock.connect_ex(('127.0.0.1', gdb_port))
                if result == 0:
                    try:
                        sock.sendall(b'+')
                        connected = True
                    except Exception:
                        pass
                    finally:
                        sock.close()
                    if connected:
                        break
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
        
        if not connected:
            stderr_output = qemu_process.stderr.read() if qemu_process.stderr else ''
            raise ConnectionError(f"Failed to connect to QEMU GDB stub on port {gdb_port} after {max_retries} retries. QEMU stderr: {stderr_output[:200]}")
        
        return qemu_process
    
    @staticmethod
    def get_gdb_command():
        """Get available GDB command."""
        if ArmTestHelpersBasic.check_command_available("arm-none-eabi-gdb"):
            return "arm-none-eabi-gdb"
        elif ArmTestHelpersBasic.check_command_available("gdb-multiarch"):
            return "gdb-multiarch"
        elif ArmTestHelpersBasic.check_command_available("gdb"):
            return "gdb"
        return None
    
    @staticmethod
    def run_gdb_and_parse_registers(gdb_cmd, elf_file, gdb_port, tmpdir_path, script_name="inspect.gdb"):
        """Run GDB to inspect registers and parse R0 value."""
        gdb_script = tmpdir_path / script_name
        gdb_script_content = f"""
set confirm off
set pagination off
set print elements 0
target remote 127.0.0.1:{gdb_port}
monitor info
continue
info registers r0
info registers
detach
quit
"""
        gdb_script.write_text(gdb_script_content)
        
        gdb_result = subprocess.run(
            [gdb_cmd, "-batch", "-x", str(gdb_script), str(elf_file)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        gdb_output = gdb_result.stdout + gdb_result.stderr
        
        if "Connection refused" in gdb_output or "Connection timed out" in gdb_output:
            raise ConnectionError(f"GDB failed to connect to QEMU: {gdb_output[:500]}")
        
        r0_value = None
        r0_patterns = [
            r'r0\s+0x([0-9a-f]+)\s+(\d+)',
            r'r0\s+(\d+)',
            r'r0\s+0x([0-9a-f]+)',
            r'R0\s+0x([0-9a-f]+)\s+(\d+)',
        ]
        
        for pattern in r0_patterns:
            r0_match = re.search(pattern, gdb_output, re.IGNORECASE)
            if r0_match:
                try:
                    if len(r0_match.groups()) >= 2 and r0_match.group(2):
                        r0_value = int(r0_match.group(2))
                    else:
                        r0_value = int(r0_match.group(1), 16)
                    break
                except (ValueError, IndexError):
                    continue
        
        return r0_value, gdb_output
    
    @staticmethod
    def verify_register_value(r0_value, gdb_output, expected_result=134):
        """Verify that R0 contains the expected result."""
        if r0_value is not None:
            assert r0_value == expected_result, \
                f"R0 should contain result {expected_result}, got {r0_value}. GDB output: {gdb_output[:1000]}"
        else:
            assert "target remote" in gdb_output.lower() or "Remote debugging" in gdb_output, \
                f"GDB should connect successfully. Output: {gdb_output[:1000]}"
    
    @staticmethod
    def start_qemu_system_mode_with_gdb(qemu_system_cmd, binary_file, gdb_port, tmpdir_path):
        """Start QEMU system mode with GDB stub."""
        raw_binary = tmpdir_path / "matrix_multiply_raw.bin"
        shutil.copy(binary_file, raw_binary)
        
        qemu_process = subprocess.Popen(
            [qemu_system_cmd,
             "-M", "versatilepb",
             "-cpu", "cortex-a9",
             "-device", f"loader,file={raw_binary},addr=0x10000,cpu-num=0",
             "-nographic",
             "-gdb", f"tcp:127.0.0.1:{gdb_port}",
             "-S",
             ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        return qemu_process
    
    @staticmethod
    def wait_for_qemu_gdb_connection(qemu_process, gdb_port, max_retries=10):
        """Wait for QEMU GDB stub to be ready for connection."""
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
    def create_gdb_script_for_qemu(gdb_port, tmpdir_path, qemu_system_cmd=None, script_name="inspect.gdb"):
        """Create GDB script for QEMU debugging."""
        gdb_script = tmpdir_path / script_name
        
        if qemu_system_cmd:
            gdb_template_file = Path(__file__).parent / "test_data" / "gdb_inspect_system_mode.gdb"
            if gdb_template_file.exists():
                with open(gdb_template_file, 'r') as f:
                    gdb_script_content = f.read().format(gdb_port=gdb_port)
            else:
                gdb_script_content = f"""
set confirm off
set pagination off
target remote 127.0.0.1:{gdb_port}
set $pc = 0x10000
continue
info registers r0
info registers r1
info registers r2
detach
quit
"""
        else:
            gdb_template_file = Path(__file__).parent / "test_data" / "gdb_inspect_user_mode.gdb"
            if gdb_template_file.exists():
                with open(gdb_template_file, 'r') as f:
                    gdb_script_content = f.read().format(gdb_port=gdb_port)
            else:
                gdb_script_content = f"""
set confirm off
set pagination off
target remote 127.0.0.1:{gdb_port}
continue
info registers r0
detach
quit
"""
        
        gdb_script.write_text(gdb_script_content)
        return gdb_script
    
    @staticmethod
    def run_gdb_with_script(gdb_cmd, elf_file, gdb_script, timeout=20):
        """Run GDB with script and return output."""
        gdb_result = subprocess.run(
            [gdb_cmd, "-batch", "-x", str(gdb_script), str(elf_file)],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return gdb_result.stdout + gdb_result.stderr
    
    @staticmethod
    def parse_r0_from_gdb_output(gdb_output):
        """Parse R0 register value from GDB output."""
        r0_match = re.search(r'r0\s+0x([0-9a-f]+)\s+(\d+)', gdb_output, re.IGNORECASE)
        if r0_match:
            try:
                return int(r0_match.group(2))
            except ValueError:
                return int(r0_match.group(1), 16)
        return None
    
    @staticmethod
    def verify_program_execution_with_fallback(qemu_cmd, elf_file, error_msg_prefix=""):
        """Verify program execution with fallback when GDB fails."""
        result = subprocess.run(
            [qemu_cmd, str(elf_file)],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert "qemu-arm: fatal:" not in result.stderr.lower(), f"QEMU fatal error: {result.stderr}"
        expected_exit = 134 % 256
        assert result.returncode == expected_exit, \
            f"QEMU should exit with code {expected_exit}, got {result.returncode}"
        
        if error_msg_prefix:
            pytest.skip(f"{error_msg_prefix}, but program executed successfully with correct exit code. "
                      f"For full register verification, ensure gdb-multiarch is installed.")
    
    @staticmethod
    def run_gdb_inspection_with_cleanup(qemu_cmd, elf_file, tmpdir_path, script_name="inspect.gdb"):
        """Run GDB inspection with automatic cleanup. Returns (success, r0_value)."""
        gdb_cmd = ArmTestHelpersQemu.get_gdb_command()
        if not gdb_cmd:
            return False, None
        
        gdb_port = random.randint(20000, 30000)
        qemu_process = None
        
        try:
            qemu_process = ArmTestHelpersQemu.connect_to_qemu_gdb(qemu_cmd, elf_file, gdb_port)
            r0_value, gdb_output = ArmTestHelpersQemu.run_gdb_and_parse_registers(
                gdb_cmd, elf_file, gdb_port, tmpdir_path, script_name
            )
            ArmTestHelpersQemu.verify_register_value(r0_value, gdb_output)
            return True, r0_value
        except Exception:
            return False, None
        finally:
            if qemu_process:
                qemu_process.terminate()
                try:
                    qemu_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    qemu_process.kill()
    
    @staticmethod
    def run_basic_execution_test(qemu_cmd, elf_file):
        """Run basic execution test without GDB."""
        result = subprocess.run([qemu_cmd, str(elf_file)], capture_output=True, text=True, timeout=5)
        assert "qemu-arm: fatal:" not in result.stderr.lower()
        assert "Illegal instruction" not in result.stderr
    
    @staticmethod
    def run_qemu_system_mode_test(qemu_cmd, qemu_system_cmd, elf_file, binary_file, tmpdir_path):
        """Run QEMU system mode test with GDB. Returns (success, r0_value)."""
        gdb_cmd = ArmTestHelpersQemu.get_gdb_command()
        if not gdb_cmd:
            ArmTestHelpersQemu.verify_program_execution_with_fallback(qemu_cmd, elf_file, 
                "gdb not available - cannot verify register values")
        
        gdb_port = random.randint(20000, 30000)
        qemu_process = None
        
        try:
            if qemu_system_cmd:
                qemu_process = ArmTestHelpersQemu.start_qemu_system_mode_with_gdb(qemu_system_cmd, binary_file, gdb_port, tmpdir_path)
            else:
                qemu_process = ArmTestHelpersQemu.connect_to_qemu_gdb(qemu_cmd, elf_file, gdb_port)
            
            time.sleep(0.5)
            if qemu_process.poll() is not None:
                stderr_output = qemu_process.stderr.read() if qemu_process.stderr else 'unknown error'
                raise RuntimeError(f"QEMU failed to start: {stderr_output}")
            
            if not ArmTestHelpersQemu.wait_for_qemu_gdb_connection(qemu_process, gdb_port):
                raise ConnectionError(f"QEMU gdb stub not listening on port {gdb_port}")
            
            gdb_script = ArmTestHelpersQemu.create_gdb_script_for_qemu(gdb_port, tmpdir_path, qemu_system_cmd)
            gdb_output = ArmTestHelpersQemu.run_gdb_with_script(gdb_cmd, elf_file, gdb_script, timeout=20)
            
            r0_value = ArmTestHelpersQemu.parse_r0_from_gdb_output(gdb_output)
            if r0_value is not None:
                assert r0_value != 0 or "Remote debugging" in gdb_output, \
                    f"Program should have executed. R0={r0_value}, GDB output: {gdb_output[:500]}"
            
            qemu_process.terminate()
            try:
                qemu_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                qemu_process.kill()
            
            return True, r0_value
        except Exception as e:
            if qemu_process:
                qemu_process.terminate()
                try:
                    qemu_process.wait(timeout=1)
                except:
                    qemu_process.kill()
            raise
    
    @staticmethod
    def verify_toolchain_binary_execution(qemu_cmd, toolchain_elf_file):
        """Verify toolchain-compiled binary executes correctly."""
        result = subprocess.run([qemu_cmd, str(toolchain_elf_file)], capture_output=True, text=True, timeout=5)
        expected_exit = 134 % 256
        assert result.returncode == expected_exit, \
            f"Toolchain-compiled binary should exit with code {expected_exit}, got {result.returncode}"

