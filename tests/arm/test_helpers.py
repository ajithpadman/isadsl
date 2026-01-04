"""
Unified helper interface for ARM Cortex-A9 tests.

This module re-exports all helper methods from specialized helper modules
to maintain backward compatibility.
"""

from tests.arm.test_helpers_basic import ArmTestHelpersBasic
from tests.arm.test_helpers_compilation import ArmTestHelpersCompilation
from tests.arm.test_helpers_qemu import ArmTestHelpersQemu


class ArmTestHelpers:
    """Unified helper class that combines all helper methods."""
    
    # Basic utilities
    check_command_available = staticmethod(ArmTestHelpersBasic.check_command_available)
    extract_text_section_from_elf = staticmethod(ArmTestHelpersBasic.extract_text_section_from_elf)
    filter_gcc_assembly = staticmethod(ArmTestHelpersBasic.filter_gcc_assembly)
    get_qemu_command = staticmethod(ArmTestHelpersBasic.get_qemu_command)
    get_qemu_system_command = staticmethod(ArmTestHelpersBasic.get_qemu_system_command)
    get_arm_toolchain = staticmethod(ArmTestHelpersBasic.get_arm_toolchain)
    verify_binary_structure = staticmethod(ArmTestHelpersBasic.verify_binary_structure)
    
    # Compilation and assembly
    generate_and_import_assembler = staticmethod(ArmTestHelpersCompilation.generate_and_import_assembler)
    compile_c_to_assembly = staticmethod(ArmTestHelpersCompilation.compile_c_to_assembly)
    assemble_code = staticmethod(ArmTestHelpersCompilation.assemble_code)
    create_elf_wrapper = staticmethod(ArmTestHelpersCompilation.create_elf_wrapper)
    compile_c_to_binary = staticmethod(ArmTestHelpersCompilation.compile_c_to_binary)
    assemble_from_c_file = staticmethod(ArmTestHelpersCompilation.assemble_from_c_file)
    compile_and_extract_text_section = staticmethod(ArmTestHelpersCompilation.compile_and_extract_text_section)
    generate_and_import_disassembler = staticmethod(ArmTestHelpersCompilation.generate_and_import_disassembler)
    write_disassembly_to_file = staticmethod(ArmTestHelpersCompilation.write_disassembly_to_file)
    generate_all_tools = staticmethod(ArmTestHelpersCompilation.generate_all_tools)
    import_all_tools = staticmethod(ArmTestHelpersCompilation.import_all_tools)
    write_machine_code_to_file = staticmethod(ArmTestHelpersCompilation.write_machine_code_to_file)
    
    # QEMU and GDB
    connect_to_qemu_gdb = staticmethod(ArmTestHelpersQemu.connect_to_qemu_gdb)
    get_gdb_command = staticmethod(ArmTestHelpersQemu.get_gdb_command)
    run_gdb_and_parse_registers = staticmethod(ArmTestHelpersQemu.run_gdb_and_parse_registers)
    verify_register_value = staticmethod(ArmTestHelpersQemu.verify_register_value)
    start_qemu_system_mode_with_gdb = staticmethod(ArmTestHelpersQemu.start_qemu_system_mode_with_gdb)
    wait_for_qemu_gdb_connection = staticmethod(ArmTestHelpersQemu.wait_for_qemu_gdb_connection)
    create_gdb_script_for_qemu = staticmethod(ArmTestHelpersQemu.create_gdb_script_for_qemu)
    run_gdb_with_script = staticmethod(ArmTestHelpersQemu.run_gdb_with_script)
    parse_r0_from_gdb_output = staticmethod(ArmTestHelpersQemu.parse_r0_from_gdb_output)
    verify_program_execution_with_fallback = staticmethod(ArmTestHelpersQemu.verify_program_execution_with_fallback)
    run_gdb_inspection_with_cleanup = staticmethod(ArmTestHelpersQemu.run_gdb_inspection_with_cleanup)
    run_basic_execution_test = staticmethod(ArmTestHelpersQemu.run_basic_execution_test)
    run_qemu_system_mode_test = staticmethod(ArmTestHelpersQemu.run_qemu_system_mode_test)
    verify_toolchain_binary_execution = staticmethod(ArmTestHelpersQemu.verify_toolchain_binary_execution)
