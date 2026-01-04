"""Converter from textX models to ISASpecification objects.

This class uses the textX object model to extract all information,
avoiding regex-based content manipulation.
"""

from typing import Optional
from .isa_model import (
    ISASpecification, Property, Register, RegisterField, InstructionFormat,
    FormatField, Instruction, EncodingSpec, EncodingAssignment, RTLBlock,
    RTLStatement, RTLAssignment, RTLConditional, RTLMemoryAccess, RTLForLoop,
    RTLExpression, RTLTernary, RTLBinaryOp, RTLUnaryOp, RTLLValue,
    RegisterAccess, FieldAccess, RTLConstant, OperandReference,
    BundleFormat, BundleSlot, OperandSpec
)


class TextXModelConverter:
    """Converts textX model objects to ISASpecification objects.
    
    This class uses the textX object model directly, avoiding regex-based
    content extraction. All information is extracted from the parsed
    textX model structure.
    """
    
    def convert(self, textx_model: any, isa_model: Optional[ISASpecification] = None) -> ISASpecification:
        """Convert a textX model to ISASpecification.
        
        Args:
            textx_model: The textX model (ISASpecFull or ISASpecPartial)
            isa_model: Optional existing ISASpecification to populate
                      (used for resolving format references)
            
        Returns:
            ISASpecification object
        """
        # Determine if this is a full or partial spec
        class_name = textx_model.__class__.__name__
        spec_obj = textx_model
        
        # Create or use existing model
        if isa_model is None:
            model = ISASpecification(
                name=spec_obj.name if hasattr(spec_obj, 'name') else 'Unknown',
                properties=[],
                registers=[],
                formats=[],
                instructions=[]
            )
        else:
            model = isa_model
        
        # Extract properties using textX object model
        if hasattr(spec_obj, 'properties'):
            for p in spec_obj.properties:
                model.properties.append(Property(name=p.name, value=p.value))
        
        # Extract registers using textX object model
        if hasattr(spec_obj, 'registers') and spec_obj.registers is not None:
            if hasattr(spec_obj.registers, 'registers'):
                for r in spec_obj.registers.registers:
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
                        fields=[RegisterField(name=f.name, msb=f.msb, lsb=f.lsb) 
                                for f in r.fields] if hasattr(r, 'fields') else []
                    )
                    model.registers.append(reg)
        
        # Extract formats using textX object model
        if hasattr(spec_obj, 'formats') and spec_obj.formats is not None:
            if hasattr(spec_obj.formats, 'formats'):
                for f in spec_obj.formats.formats:
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
                        fields=[FormatField(name=field.name, msb=field.msb, lsb=field.lsb) 
                                for field in f.fields] if hasattr(f, 'fields') else [],
                        identification_fields=identification_fields
                    )
                    model.formats.append(fmt)
            
            # Extract bundle formats using textX object model
            if hasattr(spec_obj.formats, 'bundle_formats'):
                for f in spec_obj.formats.bundle_formats:
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
        
        # Extract instructions using textX object model
        if hasattr(spec_obj, 'instructions') and spec_obj.instructions is not None:
            if hasattr(spec_obj.instructions, 'instructions'):
                for instr_tx in spec_obj.instructions.instructions:
                    # Resolve format references using textX object model
                    fmt_ref = None
                    bundle_fmt_ref = None
                    fmt_name = None
                    bundle_fmt_name = None
                    
                    if hasattr(instr_tx, 'format') and instr_tx.format is not None:
                        # textX scope provider should have resolved this to a format object
                        # Check if it's already a resolved format object
                        if hasattr(instr_tx.format, 'name'):
                            # Format is resolved - get its name and find it in our model
                            fmt_name = instr_tx.format.name
                            fmt_ref = model.get_format(fmt_name)
                        elif isinstance(instr_tx.format, str):
                            # Format is a string (unresolved reference name)
                            fmt_name = instr_tx.format
                            fmt_ref = model.get_format(fmt_name)
                        else:
                            # Try to extract name from textX reference object
                            fmt_name = None
                            try:
                                fmt_name = (getattr(instr_tx.format, 'name', None) or
                                           getattr(instr_tx.format, '_tx_obj_name', None) or
                                           str(instr_tx.format))
                                if fmt_name and '.' in str(fmt_name):
                                    fmt_name = str(fmt_name).split('.')[-1]
                                fmt_ref = model.get_format(fmt_name) if fmt_name else None
                            except:
                                fmt_ref = None
                    
                    if hasattr(instr_tx, 'bundle_format') and instr_tx.bundle_format:
                        if hasattr(instr_tx.bundle_format, 'name'):
                            bundle_fmt_name = instr_tx.bundle_format.name
                        elif isinstance(instr_tx.bundle_format, str):
                            bundle_fmt_name = instr_tx.bundle_format
                        else:
                            try:
                                bundle_fmt_name = getattr(instr_tx.bundle_format, 'name', None) or str(instr_tx.bundle_format)
                            except:
                                bundle_fmt_name = None
                        
                        if bundle_fmt_name:
                            bundle_fmt_ref = model.get_bundle_format(bundle_fmt_name)
                            
                            if bundle_fmt_ref is None and hasattr(spec_obj, 'formats') and spec_obj.formats:
                                if hasattr(spec_obj.formats, 'bundle_formats'):
                                    for fmt_tx in spec_obj.formats.bundle_formats:
                                        if hasattr(fmt_tx, 'name') and fmt_tx.name == bundle_fmt_name:
                                            bundle_fmt_ref = model.get_bundle_format(bundle_fmt_name)
                                            break
                    
                    # Extract encoding using textX object model
                    encoding = None
                    if hasattr(instr_tx, 'encoding') and instr_tx.encoding:
                        assignments = []
                        if hasattr(instr_tx.encoding, 'assignments'):
                            for a in instr_tx.encoding.assignments:
                                assignments.append(EncodingAssignment(field=a.field, value=a.value))
                        encoding = EncodingSpec(assignments=assignments)
                    
                    # Extract behavior using textX object model
                    behavior = None
                    if hasattr(instr_tx, 'behavior') and instr_tx.behavior:
                        statements = []
                        if hasattr(instr_tx.behavior, 'statements'):
                            for stmt_tx in instr_tx.behavior.statements:
                                converted_stmt = self._convert_rtl_statement(stmt_tx, model)
                                if converted_stmt:
                                    statements.append(converted_stmt)
                        behavior = RTLBlock(statements=statements)
                    
                    # Extract operands using textX object model
                    operands = []
                    operand_specs = []
                    if hasattr(instr_tx, 'operands_list') and instr_tx.operands_list:
                        op_list = instr_tx.operands_list
                        if hasattr(op_list, 'first'):
                            operand_specs, operands = self._flatten_operand_list(op_list)
                    
                    # Extract assembly_syntax using textX object model (no regex needed)
                    assembly_syntax = None
                    if hasattr(instr_tx, 'assembly_syntax') and instr_tx.assembly_syntax:
                        assembly_syntax = str(instr_tx.assembly_syntax).strip('"\'')
                    
                    # Extract bundle_instructions using textX object model
                    bundle_instructions = []
                    if hasattr(instr_tx, 'bundle_instructions_list') and instr_tx.bundle_instructions_list:
                        bundle_list = instr_tx.bundle_instructions_list
                        if hasattr(bundle_list, 'first') and bundle_list.first:
                            bundle_instructions.append(str(bundle_list.first))
                        if hasattr(bundle_list, 'rest') and bundle_list.rest:
                            bundle_instructions.extend([str(name) for name in bundle_list.rest])
                    
                    instr = Instruction(
                        mnemonic=instr_tx.mnemonic,
                        format=fmt_ref,
                        bundle_format=bundle_fmt_ref,
                        encoding=encoding,
                        operands=operands,
                        operand_specs=operand_specs,
                        assembly_syntax=assembly_syntax,
                        behavior=behavior,
                        bundle_instructions=[]  # Will be resolved after all instructions are parsed
                    )
                    model.instructions.append(instr)
        
        # Second pass: resolve bundle instruction references by name
        if hasattr(spec_obj, 'instructions') and hasattr(spec_obj.instructions, 'instructions'):
            for i, instr_tx in enumerate(spec_obj.instructions.instructions):
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
        
        # Third pass: resolve any format references that weren't resolved by textX scope provider
        # Even though the scope provider finds formats, textX might not assign them to the instruction
        # So we need to check the textX model and resolve format references manually
        for i, instr in enumerate(model.instructions):
            if instr.format is None:
                # Get the corresponding textX instruction
                if hasattr(spec_obj, 'instructions') and spec_obj.instructions:
                    if hasattr(spec_obj.instructions, 'instructions') and i < len(spec_obj.instructions.instructions):
                        instr_tx = spec_obj.instructions.instructions[i]
                        if hasattr(instr_tx, 'format'):
                            fmt_name = None
                            
                            # Check if format is resolved in textX model
                            if instr_tx.format is not None:
                                # Format is resolved - get its name
                                if hasattr(instr_tx.format, 'name'):
                                    fmt_name = instr_tx.format.name
                                elif isinstance(instr_tx.format, str):
                                    fmt_name = instr_tx.format
                            else:
                                # Format is None - scope provider didn't resolve it
                                # This shouldn't happen if scope provider is working, but handle it anyway
                                pass
                            
                            # If we got a format name, try to resolve it in our model
                            if fmt_name:
                                fmt_ref = model.get_format(fmt_name)
                                if fmt_ref:
                                    instr.format = fmt_ref
        
        return model
    
    def _flatten_operand_list(self, op_list_tx):
        """Flatten recursive OperandList structure using textX object model."""
        result_specs = []
        result_names = []
        
        def extract_operand_spec(op_spec_tx):
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
        
        # Extract first operand
        if hasattr(op_list_tx, 'first'):
            spec, name = extract_operand_spec(op_list_tx.first)
            if spec:
                result_specs.append(spec)
                result_names.append(name)
        
        # Handle recursive rest (if present)
        if hasattr(op_list_tx, 'rest') and op_list_tx.rest:
            nested_specs, nested_names = self._flatten_operand_list(op_list_tx.rest)
            result_specs.extend(nested_specs)
            result_names.extend(nested_names)
        
        return result_specs, result_names
    
    def _convert_rtl_statement(self, stmt_tx, isa_model) -> Optional[RTLStatement]:
        """Convert a textX RTL statement to our model."""
        class_name = stmt_tx.__class__.__name__
        
        if class_name == 'RTLAssignment':
            target = self._convert_rtl_lvalue(getattr(stmt_tx, 'target', None), isa_model)
            expr = self._convert_rtl_expression(getattr(stmt_tx, 'expr', None), isa_model)
            if target and expr:
                return RTLAssignment(target=target, expr=expr)
        
        elif class_name == 'RTLConditional':
            condition = self._convert_rtl_expression(getattr(stmt_tx, 'condition', None), isa_model)
            then_stmts = []
            if hasattr(stmt_tx, 'then_statements'):
                for then_stmt_tx in stmt_tx.then_statements:
                    converted = self._convert_rtl_statement(then_stmt_tx, isa_model)
                    if converted:
                        then_stmts.append(converted)
            else_stmts = []
            if hasattr(stmt_tx, 'else_statements') and stmt_tx.else_statements:
                for else_stmt_tx in stmt_tx.else_statements:
                    converted = self._convert_rtl_statement(else_stmt_tx, isa_model)
                    if converted:
                        else_stmts.append(converted)
            if condition:
                return RTLConditional(condition=condition, then_statements=then_stmts, else_statements=else_stmts)
        
        elif class_name == 'RTLMemoryAccess':
            is_load = hasattr(stmt_tx, 'memory_access') and stmt_tx.memory_access is not None
            address = self._convert_rtl_expression(getattr(stmt_tx, 'address', None), isa_model)
            target = None
            value = None
            if is_load:
                target = self._convert_rtl_lvalue(getattr(stmt_tx, 'memory_access', None), isa_model)
            else:
                value = self._convert_rtl_expression(getattr(stmt_tx, 'value', None), isa_model)
            if address:
                return RTLMemoryAccess(is_load=is_load, address=address, target=target, value=value)
        
        elif class_name == 'RTLForLoop':
            init = self._convert_rtl_statement(getattr(stmt_tx, 'init', None), isa_model)
            condition = self._convert_rtl_expression(getattr(stmt_tx, 'condition', None), isa_model)
            update = self._convert_rtl_statement(getattr(stmt_tx, 'update', None), isa_model)
            statements = []
            if hasattr(stmt_tx, 'statements'):
                for stmt_tx_inner in stmt_tx.statements:
                    converted = self._convert_rtl_statement(stmt_tx_inner, isa_model)
                    if converted:
                        statements.append(converted)
            if init and condition and update:
                return RTLForLoop(init=init, condition=condition, update=update, statements=statements)
        
        return None
    
    def _convert_rtl_lvalue(self, lvalue_tx, isa_model) -> Optional[RTLLValue]:
        """Convert a textX RTL lvalue to our model."""
        if not lvalue_tx:
            return None
        
        class_name = lvalue_tx.__class__.__name__
        
        if class_name == 'RTLLValue':
            if hasattr(lvalue_tx, 'register_access') and lvalue_tx.register_access:
                return self._convert_rtl_lvalue(lvalue_tx.register_access, isa_model)
            elif hasattr(lvalue_tx, 'field_access') and lvalue_tx.field_access:
                return self._convert_rtl_lvalue(lvalue_tx.field_access, isa_model)
            elif hasattr(lvalue_tx, 'simple_register') and lvalue_tx.simple_register:
                return str(lvalue_tx.simple_register)
        
        if class_name == 'RegisterAccess':
            reg_name = getattr(lvalue_tx, 'reg_name', None)
            index_expr = self._convert_rtl_expression(getattr(lvalue_tx, 'index', None), isa_model)
            if reg_name and index_expr:
                return RegisterAccess(reg_name=reg_name, index=index_expr)
        
        elif class_name == 'FieldAccess':
            reg_name = getattr(lvalue_tx, 'reg_name', None)
            field_name = getattr(lvalue_tx, 'field_name', None)
            if reg_name and field_name:
                return FieldAccess(reg_name=reg_name, field_name=field_name)
        
        elif class_name == 'ID' or isinstance(lvalue_tx, str):
            reg_name = str(lvalue_tx) if not isinstance(lvalue_tx, str) else lvalue_tx
            return reg_name
        
        return None
    
    def _convert_rtl_expression(self, expr_tx, isa_model) -> Optional[RTLExpression]:
        """Convert a textX RTL expression to our model."""
        if not expr_tx:
            return None
        
        class_name = expr_tx.__class__.__name__
        
        if class_name == 'RTLExpressionAtom':
            if hasattr(expr_tx, 'expr'):
                return self._convert_rtl_expression(expr_tx.expr, isa_model)
            for attr in ['value', 'register_access', 'field_access', 'simple_register']:
                if hasattr(expr_tx, attr) and getattr(expr_tx, attr) is not None:
                    return self._convert_rtl_expression(getattr(expr_tx, attr), isa_model)
        
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
            condition = self._convert_rtl_expression(getattr(expr_tx, 'condition', None), isa_model)
            then_expr = self._convert_rtl_expression(getattr(expr_tx, 'then_expr', None), isa_model)
            else_expr = self._convert_rtl_expression(getattr(expr_tx, 'else_expr', None), isa_model)
            if condition and then_expr and else_expr:
                return RTLTernary(condition=condition, then_expr=then_expr, else_expr=else_expr)
        
        elif class_name == 'RTLBinaryOp':
            left = self._convert_rtl_expression(getattr(expr_tx, 'left', None), isa_model)
            op = getattr(expr_tx, 'op', None)
            right = self._convert_rtl_expression(getattr(expr_tx, 'right', None), isa_model)
            if left and op and right:
                return RTLBinaryOp(left=left, op=str(op), right=right)
        
        elif class_name == 'RTLUnaryOp':
            op = getattr(expr_tx, 'op', None)
            expr = self._convert_rtl_expression(getattr(expr_tx, 'expr', None), isa_model)
            if op and expr:
                return RTLUnaryOp(op=str(op), expr=expr)
        
        elif class_name == 'RTLLValue':
            if hasattr(expr_tx, 'register_access') and expr_tx.register_access:
                return self._convert_rtl_expression(expr_tx.register_access, isa_model)
            elif hasattr(expr_tx, 'field_access') and expr_tx.field_access:
                return self._convert_rtl_expression(expr_tx.field_access, isa_model)
            elif hasattr(expr_tx, 'simple_register') and expr_tx.simple_register:
                return OperandReference(name=str(expr_tx.simple_register))
        
        elif class_name == 'RegisterAccess':
            reg_name = getattr(expr_tx, 'reg_name', None)
            index_expr = self._convert_rtl_expression(getattr(expr_tx, 'index', None), isa_model)
            if reg_name and index_expr:
                return RegisterAccess(reg_name=reg_name, index=index_expr)
        
        elif class_name == 'FieldAccess':
            reg_name = getattr(expr_tx, 'reg_name', None)
            field_name = getattr(expr_tx, 'field_name', None)
            if reg_name and field_name:
                return FieldAccess(reg_name=reg_name, field_name=field_name)
        
        elif class_name == 'ID' or isinstance(expr_tx, str):
            name = str(expr_tx) if not isinstance(expr_tx, str) else expr_tx
            return OperandReference(name=name)
        
        if hasattr(expr_tx, 'expr'):
            return self._convert_rtl_expression(expr_tx.expr, isa_model)
        
        return None

