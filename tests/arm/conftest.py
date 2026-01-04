"""Shared fixtures for ARM Cortex-A9 tests."""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def arm_cortex_a9_isa_file():
    """Path to the ARM Cortex-A9 ISA file from examples folder."""
    examples_dir = project_root / "examples"
    isa_file = examples_dir / "arm_cortex_a9.isa"
    if not isa_file.exists():
        pytest.skip(f"ARM Cortex-A9 ISA file not found: {isa_file}")
    return isa_file


@pytest.fixture
def matrix_multiply_c_file():
    """Path to the matrix multiplication C file."""
    test_data_dir = Path(__file__).parent / "test_data"
    c_file = test_data_dir / "matrix_multiply.c"
    if not c_file.exists():
        pytest.skip(f"Matrix multiply C file not found: {c_file}")
    return c_file

