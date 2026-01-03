"""CLI interface for ISA DSL tools."""

import click
from pathlib import Path
import sys

from isa_dsl.model.parser import parse_isa_file
from isa_dsl.model.validator import ISAValidator
from isa_dsl.generators.simulator import SimulatorGenerator
from isa_dsl.generators.assembler import AssemblerGenerator
from isa_dsl.generators.disassembler import DisassemblerGenerator
from isa_dsl.generators.documentation import DocumentationGenerator


@click.group()
def cli():
    """ISA DSL toolchain for generating simulators, assemblers, and documentation."""
    pass


@cli.command()
@click.argument('isa_file', type=click.Path(exists=True))
@click.option('--output', '-o', default='output', help='Output directory')
@click.option('--simulator/--no-simulator', default=True, help='Generate simulator')
@click.option('--assembler/--no-assembler', default=True, help='Generate assembler')
@click.option('--disassembler/--no-disassembler', default=True, help='Generate disassembler')
@click.option('--docs/--no-docs', default=True, help='Generate documentation')
def generate(isa_file, output, simulator, assembler, disassembler, docs):
    """Generate tools from an ISA specification."""
    click.echo(f"Parsing ISA specification: {isa_file}")
    
    try:
        isa = parse_isa_file(isa_file)
        click.echo(f"Successfully parsed ISA: {isa.name}")
    except Exception as e:
        click.echo(f"Error parsing ISA file: {e}", err=True)
        sys.exit(1)
    
    # Validate
    click.echo("Validating ISA specification...")
    validator = ISAValidator(isa)
    errors = validator.validate()
    
    if errors:
        click.echo("Validation errors found:", err=True)
        for error in errors:
            click.echo(f"  {error}", err=True)
        click.echo("\nGeneration aborted due to validation errors.", err=True)
        sys.exit(1)
    
    click.echo("Validation passed!")
    
    # Create output directory
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate tools
    if simulator:
        click.echo("Generating simulator...")
        try:
            gen = SimulatorGenerator(isa)
            output_file = gen.generate(str(output_path))
            click.echo(f"  Generated: {output_file}")
        except Exception as e:
            click.echo(f"  Error generating simulator: {e}", err=True)
    
    if assembler:
        click.echo("Generating assembler...")
        try:
            gen = AssemblerGenerator(isa)
            output_file = gen.generate(str(output_path))
            click.echo(f"  Generated: {output_file}")
        except Exception as e:
            click.echo(f"  Error generating assembler: {e}", err=True)
    
    if disassembler:
        click.echo("Generating disassembler...")
        try:
            gen = DisassemblerGenerator(isa)
            output_file = gen.generate(str(output_path))
            click.echo(f"  Generated: {output_file}")
        except Exception as e:
            click.echo(f"  Error generating disassembler: {e}", err=True)
    
    if docs:
        click.echo("Generating documentation...")
        try:
            gen = DocumentationGenerator(isa)
            output_file = gen.generate(str(output_path))
            click.echo(f"  Generated: {output_file}")
        except Exception as e:
            click.echo(f"  Error generating documentation: {e}", err=True)
    
    click.echo(f"\nGeneration complete! Output directory: {output_path}")


@cli.command()
@click.argument('isa_file', type=click.Path(exists=True))
def validate(isa_file):
    """Validate an ISA specification."""
    click.echo(f"Validating ISA specification: {isa_file}")
    
    try:
        isa = parse_isa_file(isa_file)
        click.echo(f"Successfully parsed ISA: {isa.name}")
    except Exception as e:
        click.echo(f"Error parsing ISA file: {e}", err=True)
        sys.exit(1)
    
    validator = ISAValidator(isa)
    errors = validator.validate()
    
    if errors:
        click.echo(f"\nFound {len(errors)} validation error(s):", err=True)
        for error in errors:
            click.echo(f"  {error}", err=True)
        sys.exit(1)
    else:
        click.echo("Validation passed! No errors found.")


@cli.command()
@click.argument('isa_file', type=click.Path(exists=True))
def info(isa_file):
    """Display information about an ISA specification."""
    try:
        isa = parse_isa_file(isa_file)
    except Exception as e:
        click.echo(f"Error parsing ISA file: {e}", err=True)
        sys.exit(1)
    
    click.echo(f"ISA: {isa.name}")
    click.echo(f"  Registers: {len(isa.registers)}")
    click.echo(f"  Formats: {len(isa.formats)}")
    click.echo(f"  Instructions: {len(isa.instructions)}")
    
    click.echo("\nRegisters:")
    for reg in isa.registers:
        if reg.is_register_file():
            click.echo(f"  {reg.name}: {reg.type.upper()} [{reg.count}] x {reg.width} bits")
        else:
            click.echo(f"  {reg.name}: {reg.type.upper()} {reg.width} bits")
    
    click.echo("\nInstruction Formats:")
    for fmt in isa.formats:
        click.echo(f"  {fmt.name}: {fmt.width} bits, {len(fmt.fields)} fields")
    
    click.echo("\nInstructions:")
    for instr in isa.instructions:
        operands = ", ".join(instr.operands) if instr.operands else "none"
        click.echo(f"  {instr.mnemonic.upper()}: {operands}")


if __name__ == '__main__':
    cli()

