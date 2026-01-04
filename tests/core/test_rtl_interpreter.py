"""Tests for RTL interpreter."""

import pytest
from isa_dsl.runtime.rtl_interpreter import RTLInterpreter
from isa_dsl.model.isa_model import (
    RTLConstant, RTLBinaryOp, RTLUnaryOp, RegisterAccess,
    RTLAssignment, RTLExpression
)


def test_rtl_constant():
    """Test RTL constant evaluation."""
    registers = {'R': [0] * 8}
    interpreter = RTLInterpreter(registers)
    
    const = RTLConstant(42)
    result = interpreter._evaluate_expression(const)
    assert result == 42


def test_rtl_binary_operations():
    """Test RTL binary operations."""
    registers = {'R': [10, 20, 0] * 8}
    interpreter = RTLInterpreter(registers)
    
    # Test addition
    add_expr = RTLBinaryOp(
        RTLConstant(5),
        '+',
        RTLConstant(3)
    )
    result = interpreter._evaluate_expression(add_expr)
    assert result == 8
    
    # Test subtraction
    sub_expr = RTLBinaryOp(
        RTLConstant(10),
        '-',
        RTLConstant(3)
    )
    result = interpreter._evaluate_expression(sub_expr)
    assert result == 7


def test_register_access():
    """Test register access in RTL."""
    registers = {'R': [10, 20, 30, 0, 0, 0, 0, 0]}
    interpreter = RTLInterpreter(registers)
    
    reg_access = RegisterAccess('R', RTLConstant(1))
    result = interpreter._evaluate_expression(reg_access)
    assert result == 20


def test_rtl_assignment():
    """Test RTL assignment."""
    registers = {'R': [0] * 8}
    interpreter = RTLInterpreter(registers)
    
    assignment = RTLAssignment(
        RegisterAccess('R', RTLConstant(0)),
        RTLConstant(42)
    )
    interpreter._execute_assignment(assignment)
    
    assert registers['R'][0] == 42

