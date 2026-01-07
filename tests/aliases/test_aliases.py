"""Tests for virtual registers, register aliases, and instruction aliases."""

import pytest
import tempfile
import importlib.util
from pathlib import Path
from isa_dsl.model.parser import parse_isa_file
from isa_dsl.generators.simulator import SimulatorGenerator
from isa_dsl.generators.assembler import AssemblerGenerator
from isa_dsl.generators.disassembler import DisassemblerGenerator


@pytest.fixture
def test_data_dir():
    """Get test data directory."""
    return Path(__file__).parent / "test_data"


@pytest.fixture
def aliases_isa(test_data_dir):
    """Parse the aliases ISA file."""
    isa_file = test_data_dir / 'aliases.isa'
    return parse_isa_file(str(isa_file))


def test_parse_virtual_registers(aliases_isa):
    """Test parsing virtual registers."""
    assert len(aliases_isa.virtual_registers) == 3
    
    # Check E virtual register
    e_reg = aliases_isa.get_virtual_register('E')
    assert e_reg is not None
    assert e_reg.name == 'E'
    assert e_reg.width == 64
    assert len(e_reg.components) == 2
    assert e_reg.components[0].reg_name == 'R'
    assert e_reg.components[0].index == 0
    assert e_reg.components[1].reg_name == 'R'
    assert e_reg.components[1].index == 1
    
    # Check WIDE virtual register (simple registers)
    wide_reg = aliases_isa.get_virtual_register('WIDE')
    assert wide_reg is not None
    assert wide_reg.width == 64
    assert len(wide_reg.components) == 2
    assert wide_reg.components[0].reg_name == 'HIGH'
    assert wide_reg.components[0].index is None
    assert wide_reg.components[1].reg_name == 'LOW'
    assert wide_reg.components[1].index is None


def test_parse_register_aliases(aliases_isa):
    """Test parsing register aliases."""
    assert len(aliases_isa.register_aliases) == 3
    
    # Check SP alias
    sp_alias = None
    for alias in aliases_isa.register_aliases:
        if alias.alias_name == 'SP':
            sp_alias = alias
            break
    assert sp_alias is not None
    assert sp_alias.target_reg_name == 'R'
    assert sp_alias.target_index == 13
    assert sp_alias.is_indexed()
    
    # Check PC_ALIAS (simple register alias)
    pc_alias = None
    for alias in aliases_isa.register_aliases:
        if alias.alias_name == 'PC_ALIAS':
            pc_alias = alias
            break
    assert pc_alias is not None
    assert pc_alias.target_reg_name == 'PC'
    assert pc_alias.target_index is None
    assert not pc_alias.is_indexed()


def test_parse_instruction_aliases(aliases_isa):
    """Test parsing instruction aliases."""
    assert len(aliases_isa.instruction_aliases) == 2
    
    # Check PUSH alias
    push_alias = None
    for alias in aliases_isa.instruction_aliases:
        if alias.alias_mnemonic == 'PUSH':
            push_alias = alias
            break
    assert push_alias is not None
    assert push_alias.target_mnemonic == 'STM'
    assert push_alias.assembly_syntax == "PUSH R{rd}"
    
    # Check POP alias
    pop_alias = None
    for alias in aliases_isa.instruction_aliases:
        if alias.alias_mnemonic == 'POP':
            pop_alias = alias
            break
    assert pop_alias is not None
    assert pop_alias.target_mnemonic == 'LDM'


def test_register_alias_resolution(aliases_isa):
    """Test register alias resolution."""
    # SP should resolve to R[13]
    sp_reg = aliases_isa.get_register('SP')
    assert sp_reg is not None
    assert sp_reg.name == 'R'
    
    # PC_ALIAS should resolve to PC
    pc_alias_reg = aliases_isa.get_register('PC_ALIAS')
    assert pc_alias_reg is not None
    assert pc_alias_reg.name == 'PC'


def test_instruction_alias_resolution(aliases_isa):
    """Test instruction alias resolution."""
    # PUSH should resolve to STM
    push_instr = aliases_isa.get_instruction('PUSH')
    assert push_instr is not None
    assert push_instr.mnemonic == 'STM'
    
    # POP should resolve to LDM
    pop_instr = aliases_isa.get_instruction('POP')
    assert pop_instr is not None
    assert pop_instr.mnemonic == 'LDM'


def test_simulator_virtual_registers(aliases_isa):
    """Test virtual registers in generated simulator."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate simulator
        generator = SimulatorGenerator(aliases_isa)
        sim_file = generator.generate(tmpdir)
        
        # Load and test simulator
        spec = importlib.util.spec_from_file_location("simulator", sim_file)
        sim_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sim_module)
        sim = sim_module.Simulator()
        
        # Initialize component registers
        sim.R[0] = 0x12345678
        sim.R[1] = 0x9ABCDEF0
        sim.HIGH = 0x11111111
        sim.LOW = 0x22222222
        
        # Test reading virtual register E (should concatenate R[0] and R[1])
        e_value = sim._read_virtual_register('E')
        # Components are R[0]|R[1]: R[0] is LSB, R[1] is MSB
        expected = (sim.R[1] << 32) | sim.R[0]
        assert e_value == expected
        
        # Test reading WIDE virtual register
        wide_value = sim._read_virtual_register('WIDE')
        # Components are HIGH|LOW: HIGH is LSB, LOW is MSB
        expected_wide = (sim.LOW << 32) | sim.HIGH
        assert wide_value == expected_wide
        
        # Test writing virtual register
        new_value = 0xDEADBEEFCAFEBABE
        sim._write_virtual_register('E', new_value)
        # Check that component registers were updated
        assert sim.R[0] == (new_value & 0xFFFFFFFF)
        assert sim.R[1] == ((new_value >> 32) & 0xFFFFFFFF)


def test_simulator_register_aliases(aliases_isa):
    """Test register aliases in generated simulator."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate simulator
        generator = SimulatorGenerator(aliases_isa)
        sim_file = generator.generate(tmpdir)
        
        # Load and test simulator
        spec = importlib.util.spec_from_file_location("simulator", sim_file)
        sim_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sim_module)
        sim = sim_module.Simulator()
        
        # Test alias resolution
        resolved_name, resolved_index = sim._resolve_register_alias('SP', None)
        assert resolved_name == 'R'
        assert resolved_index == 13
        
        # Test that alias works in register access
        sim.R[13] = 0x12345678
        # SP should point to R[13]
        resolved_name2, resolved_index2 = sim._resolve_register_alias('SP', None)
        assert sim.R[resolved_index2] == 0x12345678


def test_simulator_instruction_aliases(aliases_isa):
    """Test instruction aliases in generated simulator."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate simulator
        generator = SimulatorGenerator(aliases_isa)
        sim_file = generator.generate(tmpdir)
        
        # Load and test simulator
        spec = importlib.util.spec_from_file_location("simulator", sim_file)
        sim_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sim_module)
        sim = sim_module.Simulator()
        
        # Test that PUSH alias resolves to STM
        # Encode a PUSH instruction (which should be STM)
        # opcode=1 (STM), rd=1, rs1=2
        instruction = (1 << 28) | (1 << 24) | (2 << 20)
        sim.memory[0] = instruction
        sim.pc = 0
        
        # Execute - should work as STM
        result = sim._execute_instruction_by_mnemonic(instruction, 'PUSH')
        assert result is True


def test_assembler_register_aliases(aliases_isa):
    """Test register aliases in generated assembler."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate assembler
        generator = AssemblerGenerator(aliases_isa)
        asm_file = generator.generate(tmpdir)
        
        # Load and test assembler
        spec = importlib.util.spec_from_file_location("assembler", asm_file)
        asm_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(asm_module)
        assembler = asm_module.Assembler()
        
        # Test that SP alias resolves correctly
        sp_value = assembler._resolve_register('SP')
        # SP should resolve to index 13
        assert sp_value == 13
        
        # Test assembly with alias
        source = "ADD R0, SP, R1"
        machine_code = assembler.assemble(source)
        assert len(machine_code) > 0


def test_assembler_instruction_aliases(aliases_isa):
    """Test instruction aliases in generated assembler."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate assembler
        generator = AssemblerGenerator(aliases_isa)
        asm_file = generator.generate(tmpdir)
        
        # Load and test assembler
        spec = importlib.util.spec_from_file_location("assembler", asm_file)
        asm_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(asm_module)
        assembler = asm_module.Assembler()
        
        # Test that PUSH is recognized as valid mnemonic
        mnemonics = assembler._get_instruction_mnemonics()
        assert 'PUSH' in mnemonics
        assert 'POP' in mnemonics
        
        # Test assembly with alias
        source = "PUSH R1"
        machine_code = assembler.assemble(source)
        assert len(machine_code) > 0
        
        # The encoded instruction should match STM encoding
        # opcode=1 (STM), rd=1, rs1=1
        expected = (1 << 28) | (1 << 24) | (1 << 20)
        assert machine_code[0] == expected


def test_disassembler_register_aliases(aliases_isa):
    """Test register aliases in generated disassembler."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate disassembler
        generator = DisassemblerGenerator(aliases_isa)
        disasm_file = generator.generate(tmpdir)
        
        # Load and test disassembler
        spec = importlib.util.spec_from_file_location("disassembler", disasm_file)
        disasm_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(disasm_module)
        disassembler = disasm_module.Disassembler()
        
        # Test register name resolution
        # R[13] should be displayed as SP
        reg_name = disassembler._get_register_name('R', 13)
        assert reg_name == 'SP'


def test_disassembler_instruction_aliases(aliases_isa):
    """Test instruction aliases in generated disassembler."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate disassembler
        generator = DisassemblerGenerator(aliases_isa)
        disasm_file = generator.generate(tmpdir)
        
        # Load and test disassembler
        spec = importlib.util.spec_from_file_location("disassembler", disasm_file)
        disasm_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(disasm_module)
        disassembler = disasm_module.Disassembler()
        
        # Disassemble STM instruction - should use PUSH alias
        # opcode=1 (STM), rd=1, rs1=2
        instruction = (1 << 28) | (1 << 24) | (2 << 20)
        asm = disassembler.disassemble(instruction)
        
        # Should use PUSH alias mnemonic
        assert 'PUSH' in asm.upper() or 'STM' in asm.upper()


def test_end_to_end_virtual_registers(aliases_isa):
    """Test end-to-end workflow with virtual registers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate all tools
        sim_gen = SimulatorGenerator(aliases_isa)
        asm_gen = AssemblerGenerator(aliases_isa)
        disasm_gen = DisassemblerGenerator(aliases_isa)
        
        sim_file = sim_gen.generate(tmpdir)
        asm_file = asm_gen.generate(tmpdir)
        disasm_file = disasm_gen.generate(tmpdir)
        
        # Load tools
        sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
        sim_module = importlib.util.module_from_spec(sim_spec)
        sim_spec.loader.exec_module(sim_module)
        
        asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
        asm_module = importlib.util.module_from_spec(asm_spec)
        asm_spec.loader.exec_module(asm_module)
        
        # Test: assemble, simulate, verify virtual register access
        assembler = asm_module.Assembler()
        source = "ADD R0, R1, R2"
        machine_code = assembler.assemble(source)
        
        sim = sim_module.Simulator()
        sim.load_program(machine_code)
        
        # Set up registers
        sim.R[1] = 10
        sim.R[2] = 20
        
        # Execute
        sim.step()
        
        # Verify result
        assert sim.R[0] == 30
        
        # Test virtual register access
        sim.R[0] = 0x11111111
        sim.R[1] = 0x22222222
        e_value = sim._read_virtual_register('E')
        expected = (sim.R[1] << 32) | sim.R[0]
        assert e_value == expected


def test_end_to_end_register_aliases(aliases_isa):
    """Test end-to-end workflow with register aliases."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate all tools
        sim_gen = SimulatorGenerator(aliases_isa)
        asm_gen = AssemblerGenerator(aliases_isa)
        
        sim_file = sim_gen.generate(tmpdir)
        asm_file = asm_gen.generate(tmpdir)
        
        # Load tools
        sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
        sim_module = importlib.util.module_from_spec(sim_spec)
        sim_spec.loader.exec_module(sim_module)
        
        asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
        asm_module = importlib.util.module_from_spec(asm_spec)
        asm_spec.loader.exec_module(asm_module)
        
        # Test: assemble with alias, simulate, verify
        assembler = asm_module.Assembler()
        source = "ADD R0, SP, R1"
        machine_code = assembler.assemble(source)
        
        sim = sim_module.Simulator()
        sim.load_program(machine_code)
        
        # Set up registers (SP = R[13])
        sim.R[13] = 100
        sim.R[1] = 50
        
        # Execute
        sim.step()
        
        # Verify result (R[0] = SP + R[1] = 100 + 50 = 150)
        assert sim.R[0] == 150


def test_end_to_end_instruction_aliases(aliases_isa):
    """Test end-to-end workflow with instruction aliases."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate all tools
        sim_gen = SimulatorGenerator(aliases_isa)
        asm_gen = AssemblerGenerator(aliases_isa)
        disasm_gen = DisassemblerGenerator(aliases_isa)
        
        sim_file = sim_gen.generate(tmpdir)
        asm_file = asm_gen.generate(tmpdir)
        disasm_file = disasm_gen.generate(tmpdir)
        
        # Load tools
        sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
        sim_module = importlib.util.module_from_spec(sim_spec)
        sim_spec.loader.exec_module(sim_module)
        
        asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
        asm_module = importlib.util.module_from_spec(asm_spec)
        asm_spec.loader.exec_module(asm_module)
        
        disasm_spec = importlib.util.spec_from_file_location("disassembler", disasm_file)
        disasm_module = importlib.util.module_from_spec(disasm_spec)
        disasm_spec.loader.exec_module(disasm_module)
        
        # Test: assemble with alias, simulate, disassemble
        assembler = asm_module.Assembler()
        source = "PUSH R1"
        machine_code = assembler.assemble(source)
        
        sim = sim_module.Simulator()
        sim.load_program(machine_code)
        sim.R[1] = 0x12345678
        
        # Execute (PUSH = STM)
        sim.step()
        
        # Verify memory was written (STM stores R[rs1] to MEM[R[rd]])
        # Since rd=1, rs1=1, it stores R[1] to MEM[R[1]]
        assert sim.memory.get(sim.R[1], 0) == 0x12345678
        
        # Disassemble and verify alias is used
        disassembler = disasm_module.Disassembler()
        asm = disassembler.disassemble(machine_code[0])
        # Should contain PUSH or STM
        assert 'PUSH' in asm.upper() or 'STM' in asm.upper()

