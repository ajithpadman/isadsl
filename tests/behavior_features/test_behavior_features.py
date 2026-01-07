"""Comprehensive tests for behavior features: temporary variables, hex values, and external behavior."""

import pytest
import tempfile
import importlib.util
from pathlib import Path
from isa_dsl.model.parser import parse_isa_file
from isa_dsl.runtime.rtl_interpreter import RTLInterpreter
from isa_dsl.generators.simulator import SimulatorGenerator
from isa_dsl.generators.assembler import AssemblerGenerator
from isa_dsl.generators.disassembler import DisassemblerGenerator
from isa_dsl.model.isa_model import Variable, RTLConstant, OperandReference


@pytest.fixture
def test_data_dir():
    """Get test data directory."""
    return Path(__file__).parent / "test_data"


@pytest.fixture
def behavior_features_isa(test_data_dir):
    """Parse the behavior features ISA file."""
    isa_file = test_data_dir / 'behavior_features.isa'
    return parse_isa_file(str(isa_file))


# ============================================================================
# Tests for Temporary Variables
# ============================================================================

def test_parse_temporary_variables(behavior_features_isa):
    """Test parsing instructions with temporary variables."""
    instr = behavior_features_isa.get_instruction('ADD_TEMP')
    assert instr is not None
    assert instr.behavior is not None
    assert len(instr.behavior.statements) == 2
    
    # Check first statement: temp = R[rs1] + R[rs2]
    stmt1 = instr.behavior.statements[0]
    assert isinstance(stmt1.target, Variable)
    assert stmt1.target.name == 'temp'
    
    # Check second statement: R[rd] = temp
    stmt2 = instr.behavior.statements[1]
    assert hasattr(stmt2.target, 'reg_name')
    assert isinstance(stmt2.expr, OperandReference)
    assert stmt2.expr.name == 'temp'


def test_rtl_interpreter_temporary_variables(behavior_features_isa):
    """Test RTL interpreter with temporary variables."""
    registers = {'R': [0] * 16, 'PC': 0, 'FLAGS': 0}
    registers['R'][1] = 5
    registers['R'][2] = 3
    
    interpreter = RTLInterpreter(registers, isa=behavior_features_isa)
    interpreter.set_operands({'rd': 0, 'rs1': 1, 'rs2': 2})
    
    instr = behavior_features_isa.get_instruction('ADD_TEMP')
    result = interpreter.execute(instr)
    
    assert registers['R'][0] == 8, f"Expected R[0] = 8, got {registers['R'][0]}"
    assert 'temp' in interpreter.variables
    assert interpreter.variables['temp'] == 8


def test_multiple_temporary_variables(behavior_features_isa):
    """Test instructions with multiple temporary variables."""
    registers = {'R': [0] * 16, 'PC': 0, 'FLAGS': 0}
    registers['R'][1] = 2
    registers['R'][2] = 3
    
    interpreter = RTLInterpreter(registers, isa=behavior_features_isa)
    interpreter.set_operands({'rd': 0, 'rs1': 1, 'rs2': 2})
    
    instr = behavior_features_isa.get_instruction('COMPLEX_OP')
    interpreter.execute(instr)
    
    # sum = 2 + 3 = 5
    # product = 2 * 3 = 6
    # result = 5 + 6 = 11
    assert registers['R'][0] == 11, f"Expected R[0] = 11, got {registers['R'][0]}"
    assert interpreter.variables['sum'] == 5
    assert interpreter.variables['product'] == 6
    assert interpreter.variables['result'] == 11


def test_temporary_variable_in_conditional(behavior_features_isa):
    """Test temporary variables in conditional statements."""
    registers = {'R': [0] * 16, 'PC': 0, 'FLAGS': 0}
    
    # Test positive case
    registers['R'][1] = 10
    registers['R'][2] = 3
    
    interpreter = RTLInterpreter(registers, isa=behavior_features_isa)
    interpreter.set_operands({'rd': 0, 'rs1': 1, 'rs2': 2})
    
    instr = behavior_features_isa.get_instruction('COND_TEMP')
    interpreter.execute(instr)
    
    # diff = 10 - 3 = 7 > 0, so R[rd] = 7
    assert registers['R'][0] == 7
    
    # Test negative case
    registers['R'][1] = 3
    registers['R'][2] = 10
    interpreter.variables.clear()
    interpreter.set_operands({'rd': 0, 'rs1': 1, 'rs2': 2})
    interpreter.execute(instr)
    
    # diff = 3 - 10 = -7 < 0, so R[rd] = 0
    assert registers['R'][0] == 0


def test_simulator_temporary_variables(behavior_features_isa):
    """Test generated simulator with temporary variables."""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = SimulatorGenerator(behavior_features_isa)
        sim_file = generator.generate(tmpdir)
        
        spec = importlib.util.spec_from_file_location("simulator", sim_file)
        simulator_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(simulator_module)
        Simulator = simulator_module.Simulator
        
        sim = Simulator()
        sim.R[1] = 5
        sim.R[2] = 3
        
        # Assemble ADD_TEMP instruction
        asm_gen = AssemblerGenerator(behavior_features_isa)
        asm_file = asm_gen.generate(tmpdir)
        
        asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
        asm_module = importlib.util.module_from_spec(asm_spec)
        asm_spec.loader.exec_module(asm_module)
        Assembler = asm_module.Assembler
        
        assembler = Assembler()
        machine_code = assembler.assemble("ADD_TEMP R0, R1, R2")
        
        sim.load_program(machine_code)
        sim.step()
        
        assert sim.R[0] == 8, f"Expected R[0] = 8, got {sim.R[0]}"


# ============================================================================
# Tests for Hexadecimal Values
# ============================================================================

def test_parse_hex_values(behavior_features_isa):
    """Test parsing instructions with hexadecimal values."""
    instr = behavior_features_isa.get_instruction('ADD_HEX')
    assert instr is not None
    assert instr.behavior is not None
    
    # Check that hex value is parsed correctly
    stmt = instr.behavior.statements[0]
    assert isinstance(stmt.expr, type(stmt.expr))  # Should be a binary op
    # The right operand should be a constant with hex value
    if hasattr(stmt.expr, 'right'):
        assert isinstance(stmt.expr.right, RTLConstant)
        assert stmt.expr.right.value == 0x10


def test_rtl_interpreter_hex_values(behavior_features_isa):
    """Test RTL interpreter with hexadecimal values."""
    registers = {'R': [0] * 16, 'PC': 0, 'FLAGS': 0}
    registers['R'][1] = 10
    
    interpreter = RTLInterpreter(registers, isa=behavior_features_isa)
    interpreter.set_operands({'rd': 0, 'rs1': 1})
    
    instr = behavior_features_isa.get_instruction('ADD_HEX')
    interpreter.execute(instr)
    
    # R[rd] = R[rs1] + 0x10 = 10 + 16 = 26
    assert registers['R'][0] == 26, f"Expected R[0] = 26, got {registers['R'][0]}"


def test_hex_value_in_expression(behavior_features_isa):
    """Test hex values in complex expressions."""
    registers = {'R': [0] * 16, 'PC': 0, 'FLAGS': 0}
    registers['R'][1] = 1
    registers['R'][2] = 2
    
    interpreter = RTLInterpreter(registers, isa=behavior_features_isa)
    interpreter.set_operands({'rd': 0, 'rs1': 1, 'rs2': 2})
    
    instr = behavior_features_isa.get_instruction('ADD_HEX_EXPR')
    interpreter.execute(instr)
    
    # R[rd] = R[rs1] + R[rs2] + 0xFF = 1 + 2 + 255 = 258
    assert registers['R'][0] == 258, f"Expected R[0] = 258, got {registers['R'][0]}"


def test_multiple_hex_values(behavior_features_isa):
    """Test instructions with multiple hex values."""
    registers = {'R': [0] * 16, 'PC': 0, 'FLAGS': 0}
    registers['R'][1] = 5
    
    interpreter = RTLInterpreter(registers, isa=behavior_features_isa)
    interpreter.set_operands({'rd': 0, 'rs1': 1})
    
    instr = behavior_features_isa.get_instruction('HEX_MULTIPLE')
    interpreter.execute(instr)
    
    # temp = R[rs1] + 0x10 = 5 + 16 = 21
    # R[rd] = temp * 0x02 = 21 * 2 = 42
    assert registers['R'][0] == 42, f"Expected R[0] = 42, got {registers['R'][0]}"


def test_hex_value_with_temporary_variable(behavior_features_isa):
    """Test hex values combined with temporary variables."""
    registers = {'R': [0] * 16, 'PC': 0, 'FLAGS': 0}
    registers['R'][1] = 10
    registers['R'][2] = 5
    
    interpreter = RTLInterpreter(registers, isa=behavior_features_isa)
    interpreter.set_operands({'rd': 0, 'rs1': 1, 'rs2': 2})
    
    instr = behavior_features_isa.get_instruction('HEX_TEMP')
    interpreter.execute(instr)
    
    # temp = R[rs1] + 0x20 = 10 + 32 = 42
    # R[rd] = temp + R[rs2] = 42 + 5 = 47
    assert registers['R'][0] == 47, f"Expected R[0] = 47, got {registers['R'][0]}"


def test_complex_hex_temp_expression(behavior_features_isa):
    """Test complex expression with hex values and temporary variables."""
    registers = {'R': [0] * 16, 'PC': 0, 'FLAGS': 0}
    registers['R'][1] = 1
    registers['R'][2] = 2
    
    interpreter = RTLInterpreter(registers, isa=behavior_features_isa)
    interpreter.set_operands({'rd': 0, 'rs1': 1, 'rs2': 2})
    
    instr = behavior_features_isa.get_instruction('COMPLEX_HEX_TEMP')
    interpreter.execute(instr)
    
    # temp1 = R[rs1] + 0x100 = 1 + 256 = 257
    # temp2 = R[rs2] + 0x200 = 2 + 512 = 514
    # result = temp1 * temp2 = 257 * 514 = 132098
    # R[rd] = result & 0xFFFF = 132098 & 65535 = 1026 (truncated to 16 bits)
    assert registers['R'][0] == 1026, f"Expected R[0] = 1026, got {registers['R'][0]}"


def test_simulator_hex_values(behavior_features_isa):
    """Test generated simulator with hexadecimal values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = SimulatorGenerator(behavior_features_isa)
        sim_file = generator.generate(tmpdir)
        
        spec = importlib.util.spec_from_file_location("simulator", sim_file)
        simulator_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(simulator_module)
        Simulator = simulator_module.Simulator
        
        sim = Simulator()
        sim.R[1] = 10
        
        asm_gen = AssemblerGenerator(behavior_features_isa)
        asm_file = asm_gen.generate(tmpdir)
        
        asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
        asm_module = importlib.util.module_from_spec(asm_spec)
        asm_spec.loader.exec_module(asm_module)
        Assembler = asm_module.Assembler
        
        assembler = Assembler()
        machine_code = assembler.assemble("ADD_HEX R0, R1")
        
        sim.load_program(machine_code)
        sim.step()
        
        assert sim.R[0] == 26, f"Expected R[0] = 26, got {sim.R[0]}"


# ============================================================================
# Tests for External Behavior
# ============================================================================

def test_parse_external_behavior(behavior_features_isa):
    """Test parsing instructions with external_behavior flag."""
    instr = behavior_features_isa.get_instruction('EXTERNAL_OP')
    assert instr is not None
    assert instr.external_behavior == True
    assert instr.behavior is None  # External behavior doesn't have RTL behavior


def test_external_behavior_flag(behavior_features_isa):
    """Test that external_behavior flag is correctly set."""
    instr1 = behavior_features_isa.get_instruction('EXTERNAL_OP')
    assert instr1.external_behavior == True
    
    instr2 = behavior_features_isa.get_instruction('EXTERNAL_SINGLE')
    assert instr2.external_behavior == True
    
    # Regular instructions should have external_behavior = False
    instr3 = behavior_features_isa.get_instruction('ADD_TEMP')
    assert instr3.external_behavior == False


def test_simulator_external_behavior_class(behavior_features_isa):
    """Test that simulator generates ExternalBehaviorHandler class."""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = SimulatorGenerator(behavior_features_isa)
        sim_file = generator.generate(tmpdir)
        
        with open(sim_file, 'r') as f:
            code = f.read()
        
        # Check for ExternalBehaviorHandler class
        assert 'class ExternalBehaviorHandler' in code
        assert 'external_behavior' in code
        assert 'self.external_behavior' in code
        
        # Check for stub methods
        assert 'def external_op(' in code.lower()
        assert 'def external_single(' in code.lower()
        
        # Check that methods raise NotImplementedError
        assert 'NotImplementedError' in code
        assert 'ExternalBehaviorHandler' in code


def test_simulator_external_behavior_initialization(behavior_features_isa):
    """Test that simulator initializes external behavior handler."""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = SimulatorGenerator(behavior_features_isa)
        sim_file = generator.generate(tmpdir)
        
        spec = importlib.util.spec_from_file_location("simulator", sim_file)
        simulator_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(simulator_module)
        Simulator = simulator_module.Simulator
        
        sim = Simulator()
        
        # Check that external_behavior handler is initialized
        assert hasattr(sim, 'external_behavior')
        assert sim.external_behavior is not None
        assert hasattr(sim.external_behavior, 'simulator')


def test_external_behavior_not_implemented_error(behavior_features_isa):
    """Test that external behavior methods raise NotImplementedError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = SimulatorGenerator(behavior_features_isa)
        sim_file = generator.generate(tmpdir)
        
        spec = importlib.util.spec_from_file_location("simulator", sim_file)
        simulator_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(simulator_module)
        Simulator = simulator_module.Simulator
        
        sim = Simulator()
        
        # Try to call external behavior method - should raise NotImplementedError
        with pytest.raises(NotImplementedError):
            sim.external_behavior.external_op(0, 1, 2)
        
        with pytest.raises(NotImplementedError):
            sim.external_behavior.external_single(0)


def test_external_behavior_custom_implementation(behavior_features_isa):
    """Test custom implementation of external behavior."""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = SimulatorGenerator(behavior_features_isa)
        sim_file = generator.generate(tmpdir)
        
        spec = importlib.util.spec_from_file_location("simulator", sim_file)
        simulator_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(simulator_module)
        Simulator = simulator_module.Simulator
        ExternalBehaviorHandler = simulator_module.ExternalBehaviorHandler
        
        # Create custom handler
        class CustomHandler(ExternalBehaviorHandler):
            def external_op(self, rd, rs1, rs2):
                # Custom implementation: R[rd] = R[rs1] + R[rs2] + 100
                self.simulator.R[rd] = self.simulator.R[rs1] + self.simulator.R[rs2] + 100
        
        sim = Simulator()
        sim.external_behavior = CustomHandler(sim)
        sim.R[1] = 5
        sim.R[2] = 3
        
        # Execute external behavior
        sim.external_behavior.external_op(0, 1, 2)
        
        # R[0] = R[1] + R[2] + 100 = 5 + 3 + 100 = 108
        assert sim.R[0] == 108, f"Expected R[0] = 108, got {sim.R[0]}"


# ============================================================================
# Integration Tests
# ============================================================================

def test_end_to_end_temporary_variables(behavior_features_isa):
    """End-to-end test: assemble, simulate with temporary variables."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate tools
        sim_gen = SimulatorGenerator(behavior_features_isa)
        sim_file = sim_gen.generate(tmpdir)
        
        asm_gen = AssemblerGenerator(behavior_features_isa)
        asm_file = asm_gen.generate(tmpdir)
        
        # Import modules
        sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
        sim_module = importlib.util.module_from_spec(sim_spec)
        sim_spec.loader.exec_module(sim_module)
        Simulator = sim_module.Simulator
        
        asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
        asm_module = importlib.util.module_from_spec(asm_spec)
        asm_spec.loader.exec_module(asm_module)
        Assembler = asm_module.Assembler
        
        # Assemble and run
        assembler = Assembler()
        sim = Simulator()
        
        sim.R[1] = 10
        sim.R[2] = 20
        
        machine_code = assembler.assemble("COMPLEX_OP R0, R1, R2")
        sim.load_program(machine_code)
        sim.step()
        
        # sum = 10 + 20 = 30, product = 10 * 20 = 200, result = 30 + 200 = 230
        assert sim.R[0] == 230, f"Expected R[0] = 230, got {sim.R[0]}"


def test_end_to_end_hex_values(behavior_features_isa):
    """End-to-end test: assemble, simulate with hex values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sim_gen = SimulatorGenerator(behavior_features_isa)
        sim_file = sim_gen.generate(tmpdir)
        
        asm_gen = AssemblerGenerator(behavior_features_isa)
        asm_file = asm_gen.generate(tmpdir)
        
        sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
        sim_module = importlib.util.module_from_spec(sim_spec)
        sim_spec.loader.exec_module(sim_module)
        Simulator = sim_module.Simulator
        
        asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
        asm_module = importlib.util.module_from_spec(asm_spec)
        asm_spec.loader.exec_module(asm_module)
        Assembler = asm_module.Assembler
        
        assembler = Assembler()
        sim = Simulator()
        
        sim.R[1] = 1
        sim.R[2] = 2
        
        machine_code = assembler.assemble("ADD_HEX_EXPR R0, R1, R2")
        sim.load_program(machine_code)
        sim.step()
        
        # R[0] = R[1] + R[2] + 0xFF = 1 + 2 + 255 = 258
        assert sim.R[0] == 258, f"Expected R[0] = 258, got {sim.R[0]}"


def test_end_to_end_mixed_features(behavior_features_isa):
    """End-to-end test with mixed features: temp variables and hex values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sim_gen = SimulatorGenerator(behavior_features_isa)
        sim_file = sim_gen.generate(tmpdir)
        
        asm_gen = AssemblerGenerator(behavior_features_isa)
        asm_file = asm_gen.generate(tmpdir)
        
        sim_spec = importlib.util.spec_from_file_location("simulator", sim_file)
        sim_module = importlib.util.module_from_spec(sim_spec)
        sim_spec.loader.exec_module(sim_module)
        Simulator = sim_module.Simulator
        
        asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
        asm_module = importlib.util.module_from_spec(asm_spec)
        asm_spec.loader.exec_module(asm_module)
        Assembler = asm_module.Assembler
        
        assembler = Assembler()
        sim = Simulator()
        
        sim.R[1] = 1
        sim.R[2] = 2
        
        machine_code = assembler.assemble("COMPLEX_HEX_TEMP R0, R1, R2")
        sim.load_program(machine_code)
        sim.step()
        
        # temp1 = 1 + 0x100 = 257, temp2 = 2 + 0x200 = 514
        # result = 257 * 514 = 132098, R[0] = 132098 & 0xFFFF = 1026 (truncated to 16 bits)
        assert sim.R[0] == 1026, f"Expected R[0] = 1026, got {sim.R[0]}"


def test_disassembler_with_behavior_features(behavior_features_isa):
    """Test disassembler with instructions using behavior features."""
    with tempfile.TemporaryDirectory() as tmpdir:
        asm_gen = AssemblerGenerator(behavior_features_isa)
        asm_file = asm_gen.generate(tmpdir)
        
        disasm_gen = DisassemblerGenerator(behavior_features_isa)
        disasm_file = disasm_gen.generate(tmpdir)
        
        asm_spec = importlib.util.spec_from_file_location("assembler", asm_file)
        asm_module = importlib.util.module_from_spec(asm_spec)
        asm_spec.loader.exec_module(asm_module)
        Assembler = asm_module.Assembler
        
        disasm_spec = importlib.util.spec_from_file_location("disassembler", disasm_file)
        disasm_module = importlib.util.module_from_spec(disasm_spec)
        disasm_spec.loader.exec_module(disasm_module)
        Disassembler = disasm_module.Disassembler
        
        assembler = Assembler()
        disassembler = Disassembler()
        
        # Assemble instructions
        code = "ADD_TEMP R0, R1, R2\nADD_HEX R3, R4\nCOMPLEX_OP R5, R6, R7"
        machine_code = assembler.assemble(code)
        
        # Disassemble each instruction individually
        # disassemble() expects a single instruction word (int), not a list
        instructions = []
        for instr_word in machine_code:
            asm = disassembler.disassemble(instr_word)
            if asm:
                instructions.append((0, asm))  # Use dummy address
        
        assert len(instructions) >= 3
        # Check that disassembled instructions contain expected mnemonics
        asm_text = " ".join([asm for _, asm in instructions])
        assert "ADD_TEMP" in asm_text or "add_temp" in asm_text.lower()
        assert "ADD_HEX" in asm_text or "add_hex" in asm_text.lower()
        assert "COMPLEX_OP" in asm_text or "complex_op" in asm_text.lower()

