"""Parser for ISA DSL using textX."""

from textx import metamodel_from_file
from pathlib import Path
from typing import Optional
from .isa_model import (
    ISASpecification, Property, Register, RegisterField, InstructionFormat,
    FormatField, Instruction, EncodingSpec, EncodingAssignment, RTLBlock,
    RTLStatement, RTLAssignment, RTLConditional, RTLMemoryAccess, RTLForLoop,
    RTLExpression, RTLTernary, RTLBinaryOp, RTLUnaryOp, RTLLValue,
    RegisterAccess, FieldAccess, RTLConstant, OperandReference,
    BundleFormat, BundleSlot, OperandSpec
)


def get_metamodel():
    """Get the textX metamodel for ISA DSL."""
    # Get grammar file relative to the package
    grammar_file = Path(__file__).parent.parent / 'grammar' / 'isa.tx'
    
    # Let textX create objects naturally - textX 4.x will create plain objects
    # We'll adapt them to our model classes in the wrapper
    # Use skipws to handle whitespace more carefully
    mm = metamodel_from_file(str(grammar_file), skipws=True)
    
    # Register object processors to handle operand list parsing
    def operand_list_processor(operands_field):
        """Process operand list to ensure proper termination."""
        if hasattr(operands_field, 'operands'):
            # Ensure the operand list is properly terminated
            pass
        return operands_field
    
    # Try to register processor if the field exists
    try:
        mm.register_obj_processors({'InstructionOperandsField': operand_list_processor})
    except:
        pass  # If registration fails, continue without it
    
    # Post-process to extract nested structures from blocks and adapt to our model
    original_model_from_file = mm.model_from_file
    
    def model_from_file_wrapper(file_path):
        # Pre-process: Extract and remove assembly_syntax strings that contain braces
        # This works around textX's limitation with strings containing braces
        import re
        lines = Path(file_path).read_text().split('\n')
        
        # Map instruction names to their assembly_syntax strings
        assembly_syntax_map = {}
        current_instruction = None
        modified_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Track current instruction
            instr_match = re.match(r'\s*instruction\s+(\w+)\s*\{', line)
            if instr_match:
                current_instruction = instr_match.group(1)
                modified_lines.append(line)
                i += 1
                continue
            
            # Check for assembly_syntax line
            if 'assembly_syntax' in line and ':' in line:
                # Extract the string content
                asm_match = re.search(r'assembly_syntax\s*:\s*"([^"]*)"', line)
                if asm_match:
                    asm_content = asm_match.group(1)
                    # Check if it has problematic pattern (word immediately followed by {)
                    if re.search(r'[A-Za-z_][A-Za-z0-9_]*\{', asm_content):
                        # Store it and skip this line
                        if current_instruction:
                            assembly_syntax_map[current_instruction] = asm_content
                        # Don't add this line to modified_lines
                        i += 1
                        continue
            
            # Reset current_instruction when we see a closing brace
            if line.strip() == '}' and current_instruction:
                current_instruction = None
            
            modified_lines.append(line)
            i += 1
        
        # Write modified content to temporary file and parse
        import tempfile
        modified_content = '\n'.join(modified_lines)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.isa', delete=False) as tmp_file:
            tmp_file.write(modified_content)
            tmp_file_path = tmp_file.name
        
        try:
            textx_model = original_model_from_file(tmp_file_path)
            
            # Post-process: Inject assembly_syntax strings back
            if hasattr(textx_model, 'instructions') and hasattr(textx_model.instructions, 'instructions'):
                for instr_tx in textx_model.instructions.instructions:
                    instr_name = instr_tx.mnemonic if hasattr(instr_tx, 'mnemonic') else None
                    if instr_name and instr_name in assembly_syntax_map:
                        # Set the assembly_syntax directly as a string
                        # The parser will extract it using str() which will work
                        setattr(instr_tx, 'assembly_syntax', assembly_syntax_map[instr_name])
        finally:
            # Clean up temp file
            Path(tmp_file_path).unlink()
        
        # Create our model object from textX model
        model = ISASpecification(
            name=textx_model.name,
            properties=[Property(name=p.name, value=p.value) for p in textx_model.properties] if hasattr(textx_model, 'properties') else [],
            registers=[],
            formats=[],
            instructions=[]
        )
        
        # Extract and convert registers
        if hasattr(textx_model, 'registers') and hasattr(textx_model.registers, 'registers'):
            for r in textx_model.registers.registers:
                vector_props = getattr(r, 'vector_props', None)
                element_width = None
                lanes = None
                if vector_props:
                    element_width = getattr(vector_props, 'element_width', None)
                    lanes = getattr(vector_props, 'lanes', None)
                
                reg = Register(
                    type=r.type,
                    name=r.name,
                    width=r.width,
                    count=getattr(r, 'count', None),
                    element_width=element_width,
                    lanes=lanes,
                    fields=[RegisterField(name=f.name, msb=f.msb, lsb=f.lsb) for f in r.fields] if hasattr(r, 'fields') else []
                )
                model.registers.append(reg)
        
        # Extract and convert formats
        if hasattr(textx_model, 'formats') and hasattr(textx_model.formats, 'formats'):
            for f in textx_model.formats.formats:
                # Regular instruction format
                # Extract identification_fields if present
                identification_fields = []
                if hasattr(f, 'identification_fields') and f.identification_fields:
                    id_list = f.identification_fields
                    if hasattr(id_list, 'first') and id_list.first:
                        identification_fields.append(str(id_list.first))
                    if hasattr(id_list, 'rest') and id_list.rest:
                        identification_fields.extend([str(name) for name in id_list.rest])
                
                fmt = InstructionFormat(
                    name=f.name,
                    width=f.width,
                    fields=[FormatField(name=field.name, msb=field.msb, lsb=field.lsb) for field in f.fields] if hasattr(f, 'fields') else [],
                    identification_fields=identification_fields
                )
                model.formats.append(fmt)
        
        # Extract and convert bundle formats
        if hasattr(textx_model, 'formats') and hasattr(textx_model.formats, 'bundle_formats'):
            for f in textx_model.formats.bundle_formats:
                slots = []
                if hasattr(f, 'slots'):
                    for slot_tx in f.slots:
                        slots.append(BundleSlot(
                            name=slot_tx.slot_name,
                            msb=slot_tx.msb,
                            lsb=slot_tx.lsb
                        ))
                instruction_start = 0
                if hasattr(f, 'instruction_start') and f.instruction_start is not None:
                    instruction_start = int(f.instruction_start)
                
                # Extract identification_fields if present
                identification_fields = []
                if hasattr(f, 'identification_fields') and f.identification_fields:
                    id_list = f.identification_fields
                    if hasattr(id_list, 'first') and id_list.first:
                        identification_fields.append(str(id_list.first))
                    if hasattr(id_list, 'rest') and id_list.rest:
                        identification_fields.extend([str(name) for name in id_list.rest])
                
                bundle_fmt = BundleFormat(
                    name=f.name,
                    width=f.width,
                    instruction_start=instruction_start,
                    slots=slots,
                    identification_fields=identification_fields
                )
                model.bundle_formats.append(bundle_fmt)
        
        # Extract and convert instructions
        if hasattr(textx_model, 'instructions') and hasattr(textx_model.instructions, 'instructions'):
            for instr_tx in textx_model.instructions.instructions:
                # Find format reference
                fmt_ref = None
                bundle_fmt_ref = None
                if hasattr(instr_tx, 'format') and instr_tx.format:
                    fmt_name = instr_tx.format.name if hasattr(instr_tx.format, 'name') else str(instr_tx.format)
                    fmt_ref = model.get_format(fmt_name)
                if hasattr(instr_tx, 'bundle_format') and instr_tx.bundle_format:
                    bundle_fmt_name = instr_tx.bundle_format.name if hasattr(instr_tx.bundle_format, 'name') else str(instr_tx.bundle_format)
                    bundle_fmt_ref = model.get_bundle_format(bundle_fmt_name)
                
                # Extract encoding
                encoding = None
                if hasattr(instr_tx, 'encoding') and instr_tx.encoding:
                    assignments = []
                    if hasattr(instr_tx.encoding, 'assignments'):
                        for a in instr_tx.encoding.assignments:
                            assignments.append(EncodingAssignment(field=a.field, value=a.value))
                    encoding = EncodingSpec(assignments=assignments)
                
                # Extract behavior - convert RTL statements from textX model to our model
                behavior = None
                if hasattr(instr_tx, 'behavior') and instr_tx.behavior:
                    statements = []
                    if hasattr(instr_tx.behavior, 'statements'):
                        for stmt_tx in instr_tx.behavior.statements:
                            converted_stmt = _convert_rtl_statement(stmt_tx, model)
                            if converted_stmt:
                                statements.append(converted_stmt)
                    behavior = RTLBlock(statements=statements)
                
                # Extract operands - handle both simple and distributed operands
                operands = []
                operand_specs = []
                if hasattr(instr_tx, 'operands_list') and instr_tx.operands_list:
                    op_list = instr_tx.operands_list
                    # Handle operands list pattern (operands+=OperandSpec) - alternative format
                    if hasattr(op_list, 'operands') and op_list.operands:
                        for op_spec in op_list.operands:
                            if hasattr(op_spec, 'distributed_operand') and op_spec.distributed_operand:
                                dist_op = op_spec.distributed_operand
                                field_names = []
                                if hasattr(dist_op, 'field_list') and dist_op.field_list:
                                    field_list = dist_op.field_list
                                    if hasattr(field_list, 'first'):
                                        field_names.append(str(field_list.first))
                                    if hasattr(field_list, 'rest') and field_list.rest:
                                        field_names.extend([str(f) for f in field_list.rest])
                                operand_specs.append(OperandSpec(
                                    name=str(dist_op.name),
                                    field_names=field_names
                                ))
                                operands.append(str(dist_op.name))
                            elif hasattr(op_spec, 'simple_operand'):
                                op_name = str(op_spec.simple_operand)
                                operand_specs.append(OperandSpec(name=op_name, field_names=[]))
                                operands.append(op_name)
                    # Handle recursive pattern: first=OperandSpec (',' rest=OperandList)?
                    elif hasattr(op_list, 'first'):
                        def extract_operand_spec(op_spec_tx):
                            """Extract OperandSpec from textX object."""
                            if hasattr(op_spec_tx, 'distributed_operand') and op_spec_tx.distributed_operand:
                                dist_op = op_spec_tx.distributed_operand
                                field_names = []
                                if hasattr(dist_op, 'field_list') and dist_op.field_list:
                                    field_list = dist_op.field_list
                                    if hasattr(field_list, 'first'):
                                        field_names.append(str(field_list.first))
                                    if hasattr(field_list, 'rest') and field_list.rest:
                                        field_names.extend([str(f) for f in field_list.rest])
                                return OperandSpec(name=str(dist_op.name), field_names=field_names), str(dist_op.name)
                            elif hasattr(op_spec_tx, 'simple_operand'):
                                op_name = str(op_spec_tx.simple_operand)
                                return OperandSpec(name=op_name, field_names=[]), op_name
                            return None, None
                        
                        def flatten_operand_list(op_list_tx):
                            """Flatten recursive OperandList structure."""
                            result_specs = []
                            result_names = []
                            
                            # Extract first operand
                            if hasattr(op_list_tx, 'first'):
                                spec, name = extract_operand_spec(op_list_tx.first)
                                if spec:
                                    result_specs.append(spec)
                                    result_names.append(name)
                            
                            # Handle recursive rest (if present)
                            if hasattr(op_list_tx, 'rest') and op_list_tx.rest:
                                # Recursive case: comma followed by another OperandList
                                nested_specs, nested_names = flatten_operand_list(op_list_tx.rest)
                                result_specs.extend(nested_specs)
                                result_names.extend(nested_names)
                            
                            return result_specs, result_names
                        
                        operand_specs, operands = flatten_operand_list(op_list)
                    else:
                        # Fallback: treat as simple list
                        if hasattr(op_list, '__iter__') and not isinstance(op_list, str):
                            operands = [str(op) for op in op_list]
                            operand_specs = [OperandSpec(name=str(op), field_names=[]) for op in op_list]
                        else:
                            operands = [str(op_list)]
                            operand_specs = [OperandSpec(name=str(op_list), field_names=[])]
                
                # Extract bundle instructions if this is a bundle (as string names for now)
                bundle_instr_names = []
                if hasattr(instr_tx, 'bundle_instructions_list') and instr_tx.bundle_instructions_list:
                    bundle_list = instr_tx.bundle_instructions_list
                    # Get instruction names as strings - these will be resolved after all instructions are parsed
                    if hasattr(bundle_list, 'first') and bundle_list.first:
                        bundle_instr_names.append(str(bundle_list.first))
                    if hasattr(bundle_list, 'rest') and bundle_list.rest:
                        bundle_instr_names.extend([str(name) for name in bundle_list.rest])
                
                # Extract assembly_syntax if present
                assembly_syntax = None
                if hasattr(instr_tx, 'assembly_syntax') and instr_tx.assembly_syntax:
                    # Remove quotes from string
                    # String content is already extracted by pre-processing step above
                    assembly_syntax = str(instr_tx.assembly_syntax).strip('"\'')
                
                instr = Instruction(
                    mnemonic=instr_tx.mnemonic,
                    format=fmt_ref,
                    bundle_format=bundle_fmt_ref,
                    encoding=encoding,
                    operands=operands,  # Legacy support
                    operand_specs=operand_specs,  # New distributed field support
                    assembly_syntax=assembly_syntax,
                    behavior=behavior,
                    bundle_instructions=[]  # Will be resolved after all instructions are parsed
                )
                model.instructions.append(instr)
        
        # Second pass: resolve bundle instruction references by name
        if hasattr(textx_model, 'instructions') and hasattr(textx_model.instructions, 'instructions'):
            for i, instr_tx in enumerate(textx_model.instructions.instructions):
                if hasattr(instr_tx, 'bundle_instructions_list') and instr_tx.bundle_instructions_list:
                    bundle_list = instr_tx.bundle_instructions_list
                    bundle_instr_names = []
                    if hasattr(bundle_list, 'first') and bundle_list.first:
                        bundle_instr_names.append(str(bundle_list.first))
                    if hasattr(bundle_list, 'rest') and bundle_list.rest:
                        bundle_instr_names.extend([str(name) for name in bundle_list.rest])
                    
                    # Resolve instruction names to actual instructions
                    for ref_name in bundle_instr_names:
                        ref_instr = model.get_instruction(ref_name)
                        if ref_instr:
                            model.instructions[i].bundle_instructions.append(ref_instr)
        
        return model
    
    mm.model_from_file = model_from_file_wrapper
    
    return mm




def _convert_rtl_statement(stmt_tx, isa_model) -> Optional[RTLStatement]:
    """Convert a textX RTL statement to our model."""
    # Check statement type by class name (textX uses class names)
    class_name = stmt_tx.__class__.__name__
    
    if class_name == 'RTLAssignment':
        target = _convert_rtl_lvalue(getattr(stmt_tx, 'target', None), isa_model)
        expr = _convert_rtl_expression(getattr(stmt_tx, 'expr', None), isa_model)
        if target and expr:
            return RTLAssignment(target=target, expr=expr)
    
    elif class_name == 'RTLConditional':
        condition = _convert_rtl_expression(getattr(stmt_tx, 'condition', None), isa_model)
        then_stmts = []
        if hasattr(stmt_tx, 'then_statements'):
            for then_stmt_tx in stmt_tx.then_statements:
                converted = _convert_rtl_statement(then_stmt_tx, isa_model)
                if converted:
                    then_stmts.append(converted)
        else_stmts = []
        if hasattr(stmt_tx, 'else_statements') and stmt_tx.else_statements:
            for else_stmt_tx in stmt_tx.else_statements:
                converted = _convert_rtl_statement(else_stmt_tx, isa_model)
                if converted:
                    else_stmts.append(converted)
        if condition:
            return RTLConditional(condition=condition, then_statements=then_stmts, else_statements=else_stmts)
    
    elif class_name == 'RTLMemoryAccess':
        # Check if it's a load or store
        is_load = hasattr(stmt_tx, 'memory_access') and stmt_tx.memory_access is not None
        address = _convert_rtl_expression(getattr(stmt_tx, 'address', None), isa_model)
        target = None
        value = None
        if is_load:
            target = _convert_rtl_lvalue(getattr(stmt_tx, 'memory_access', None), isa_model)
        else:
            value = _convert_rtl_expression(getattr(stmt_tx, 'value', None), isa_model)
        if address:
            return RTLMemoryAccess(is_load=is_load, address=address, target=target, value=value)
    
    elif class_name == 'RTLForLoop':
        init = _convert_rtl_statement(getattr(stmt_tx, 'init', None), isa_model)
        condition = _convert_rtl_expression(getattr(stmt_tx, 'condition', None), isa_model)
        update = _convert_rtl_statement(getattr(stmt_tx, 'update', None), isa_model)
        statements = []
        if hasattr(stmt_tx, 'statements'):
            for stmt_tx_inner in stmt_tx.statements:
                converted = _convert_rtl_statement(stmt_tx_inner, isa_model)
                if converted:
                    statements.append(converted)
        if init and condition and update:
            return RTLForLoop(init=init, condition=condition, update=update, statements=statements)
    
    return None


def _convert_rtl_lvalue(lvalue_tx, isa_model) -> Optional[RTLLValue]:
    """Convert a textX RTL lvalue to our model."""
    if not lvalue_tx:
        return None
    
    class_name = lvalue_tx.__class__.__name__
    
    # textX RTLLValue has register_access, field_access, or simple_register attributes
    if class_name == 'RTLLValue':
        if hasattr(lvalue_tx, 'register_access') and lvalue_tx.register_access:
            return _convert_rtl_lvalue(lvalue_tx.register_access, isa_model)
        elif hasattr(lvalue_tx, 'field_access') and lvalue_tx.field_access:
            return _convert_rtl_lvalue(lvalue_tx.field_access, isa_model)
        elif hasattr(lvalue_tx, 'simple_register') and lvalue_tx.simple_register:
            return str(lvalue_tx.simple_register)
    
    if class_name == 'RegisterAccess':
        reg_name = getattr(lvalue_tx, 'reg_name', None)
        index_expr = _convert_rtl_expression(getattr(lvalue_tx, 'index', None), isa_model)
        if reg_name and index_expr:
            # Note: lane_index is handled separately in RegisterAccess model
            return RegisterAccess(reg_name=reg_name, index=index_expr)
    
    elif class_name == 'FieldAccess':
        reg_name = getattr(lvalue_tx, 'reg_name', None)
        field_name = getattr(lvalue_tx, 'field_name', None)
        if reg_name and field_name:
            return FieldAccess(reg_name=reg_name, field_name=field_name)
    
    elif class_name == 'ID' or isinstance(lvalue_tx, str):
        # Simple register name (e.g., PC)
        reg_name = str(lvalue_tx) if not isinstance(lvalue_tx, str) else lvalue_tx
        return reg_name
    
    return None


def _convert_rtl_expression(expr_tx, isa_model) -> Optional[RTLExpression]:
    """Convert a textX RTL expression to our model."""
    if not expr_tx:
        return None
    
    class_name = expr_tx.__class__.__name__
    
    # Handle RTLExpressionAtom - it can contain RTLLValue, RTLConstant, OperandReference, or parenthesized expression
    if class_name == 'RTLExpressionAtom':
        # Check what's inside
        if hasattr(expr_tx, 'expr'):
            return _convert_rtl_expression(expr_tx.expr, isa_model)
        # Try other attributes
        for attr in ['value', 'register_access', 'field_access', 'simple_register']:
            if hasattr(expr_tx, attr) and getattr(expr_tx, attr) is not None:
                return _convert_rtl_expression(getattr(expr_tx, attr), isa_model)
    
    if class_name == 'RTLConstant':
        value = getattr(expr_tx, 'value', None)
        hex_value = getattr(expr_tx, 'hex_value', None)
        binary_value = getattr(expr_tx, 'binary_value', None)
        if value is not None:
            return RTLConstant(value=int(value))
        elif hex_value is not None:
            return RTLConstant(value=int(hex_value, 16))
        elif binary_value is not None:
            return RTLConstant(value=int(binary_value, 2))
    
    elif class_name == 'OperandReference':
        name = getattr(expr_tx, 'name', None)
        if name:
            return OperandReference(name=str(name))
    
    elif class_name == 'RTLTernary':
        condition = _convert_rtl_expression(getattr(expr_tx, 'condition', None), isa_model)
        then_expr = _convert_rtl_expression(getattr(expr_tx, 'then_expr', None), isa_model)
        else_expr = _convert_rtl_expression(getattr(expr_tx, 'else_expr', None), isa_model)
        if condition and then_expr and else_expr:
            return RTLTernary(condition=condition, then_expr=then_expr, else_expr=else_expr)
    
    elif class_name == 'RTLBinaryOp':
        left = _convert_rtl_expression(getattr(expr_tx, 'left', None), isa_model)
        op = getattr(expr_tx, 'op', None)
        right = _convert_rtl_expression(getattr(expr_tx, 'right', None), isa_model)
        if left and op and right:
            return RTLBinaryOp(left=left, op=str(op), right=right)
    
    elif class_name == 'RTLUnaryOp':
        op = getattr(expr_tx, 'op', None)
        expr = _convert_rtl_expression(getattr(expr_tx, 'expr', None), isa_model)
        if op and expr:
            return RTLUnaryOp(op=str(op), expr=expr)
    
    elif class_name == 'RTLLValue':
        # RTLLValue can contain register_access, field_access, or simple_register
        if hasattr(expr_tx, 'register_access') and expr_tx.register_access:
            return _convert_rtl_expression(expr_tx.register_access, isa_model)
        elif hasattr(expr_tx, 'field_access') and expr_tx.field_access:
            return _convert_rtl_expression(expr_tx.field_access, isa_model)
        elif hasattr(expr_tx, 'simple_register') and expr_tx.simple_register:
            # Could be a register name (PC) or operand reference (imm, rd, etc.)
            # Treat as operand reference for now
            return OperandReference(name=str(expr_tx.simple_register))
    
    elif class_name == 'RegisterAccess':
        # Register access in expression (e.g., R[rs1])
        reg_name = getattr(expr_tx, 'reg_name', None)
        index_expr = _convert_rtl_expression(getattr(expr_tx, 'index', None), isa_model)
        if reg_name and index_expr:
            return RegisterAccess(reg_name=reg_name, index=index_expr)
    
    elif class_name == 'FieldAccess':
        reg_name = getattr(expr_tx, 'reg_name', None)
        field_name = getattr(expr_tx, 'field_name', None)
        if reg_name and field_name:
            return FieldAccess(reg_name=reg_name, field_name=field_name)
    
    elif class_name == 'ID' or isinstance(expr_tx, str):
        # Could be an operand reference or simple register
        name = str(expr_tx) if not isinstance(expr_tx, str) else expr_tx
        return OperandReference(name=name)
    
    # Handle parentheses - get the inner expression
    if hasattr(expr_tx, 'expr'):
        return _convert_rtl_expression(expr_tx.expr, isa_model)
    
    return None


def parse_isa_file(file_path: str) -> ISASpecification:
    """Parse an ISA specification file and return the model."""
    mm = get_metamodel()
    model = mm.model_from_file(file_path)
    return model

