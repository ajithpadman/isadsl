grammar Isa

// ISA DSL Grammar for Langium
// Converted from textX grammar (isa_dsl/grammar/isa.tx)

// Root rule: can be either a full architecture spec or a partial spec
// Includes are handled as pre-processing directives and are not part of the AST
entry ISASpec:
    (includes+=Include)*
    (ISASpecFull | ISASpecPartial)
;

// Include directive (pre-processed, not part of AST structure)
Include:
    '#include' path=STRING
;

// Full ISA specification with architecture block
// All blocks are optional since they can be provided by included files
ISASpecFull:
    'architecture' name=ID '{'
        (properties+=Property)*
        (registers=RegisterBlock)?
        (formats=FormatBlock)?
        (instructions=InstructionBlock)?
    '}'
;

// Partial ISA specification for included files - all blocks are optional
// Must have at least one element to avoid empty consumption
ISASpecPartial:
    (properties+=Property | registers+=RegisterBlock | formats+=FormatBlock | instructions+=InstructionBlock)+
;

Property:
    name=ID ':' value=PropertyValue
;

PropertyValue returns string:
    INT | STRING | ID
;

RegisterBlock:
    'registers' '{'
        (registers+=Register)*
    '}'
;

Register:
    type=RegisterType name=ID width=INT ('[' count=INT ']')? (vector_props=VectorProperties)? ('{'
        (fields+=RegisterField)*
    '}')?
;

VectorProperties:
    '<' element_width=INT ',' lanes=INT '>'
;

RegisterType returns string:
    'gpr' | 'sfr' | 'vec'
;

RegisterField:
    name=ID ':' '[' lsb=INT ':' msb=INT ']'
;

FormatBlock:
    'formats' '{'
        (formats+=InstructionFormat | bundle_formats+=BundleFormat)*
    '}'
;

InstructionFormat:
    'format' name=ID width=INT '{'
        (fields+=FormatField)*
        ('identification_fields' ':' identification_fields=IdentificationFieldList)?
    '}'
;

BundleFormat:
    'bundle' 'format' name=ID width=INT '{'
        ('instruction_start' ':' instruction_start=INT)?
        ('identification_fields' ':' identification_fields=IdentificationFieldList)?
        (slots+=BundleSlot)*
    '}'
;

BundleSlot:
    slot_name=ID ':' '[' lsb=INT ':' msb=INT ']'
;

FormatField:
    name=ID ':' '[' lsb=INT ':' msb=INT ']'
;

InstructionBlock:
    'instructions' '{'
        (instructions+=Instruction)*
    '}'
;

Instruction:
    'instruction' mnemonic=ID '{'
        ('format' ':' format=[InstructionFormat])?
        ('bundle_format' ':' bundle_format=[BundleFormat])?
        ('encoding' ':' encoding=EncodingSpec)?
        ('operands' ':' operands_list=OperandList)?
        ('assembly_syntax' ':' assembly_syntax=STRING)?
        ('behavior' ':' behavior=RTLBlock)?
    '}'
;

OperandList:
    first=OperandSpec (',' rest=OperandList)?
;

OperandSpec:
    distributed_operand=DistributedOperand | simple_operand=ID
;

DistributedOperand:
    name=ID '(' field_list=FieldList ')'
;

FieldList:
    first=ID (',' rest+=ID)*
;

IdentificationFieldList:
    first=ID (',' rest+=ID)*
;

EncodingSpec:
    '{' (assignments+=EncodingAssignment (',' assignments+=EncodingAssignment)*)? '}'
;

EncodingAssignment:
    field=ID '=' value=INT
;

RTLBlock:
    '{' (statements+=RTLStatement)+ '}'
;

RTLStatement:
    RTLAssignment | RTLConditional | RTLMemoryAccess | RTLForLoop
;

RTLAssignment:
    target=RTLLValue '=' expr=RTLExpression ';'
;

RTLConditional:
    'if' '(' condition=RTLExpression ')' '{' (then_statements+=RTLStatement)* '}' ('else' '{' (else_statements+=RTLStatement)* '}')?
;

RTLMemoryAccess:
    memory_access=RTLLValue '=' 'MEM' '[' address=RTLExpression ']' ';' |
    'MEM' '[' address=RTLExpression ']' '=' value=RTLExpression ';'
;

RTLForLoop:
    'for' '(' init=RTLAssignment condition=RTLExpression ';' update=RTLAssignment ')' '{' (statements+=RTLStatement)+ '}'
;

RTLExpression:
    RTLTernary | RTLBinaryOp | RTLUnaryOp | RTLAtom
;

RTLAtom:
    RTLParenthesized | RTLLValue | RTLConstant | OperandReference
;

RTLParenthesized:
    '(' expression=RTLExpression ')'
;

OperandReference:
    name=ID
;

RTLTernary:
    condition=RTLAtom '?' then_expr=RTLExpression ':' else_expr=RTLExpression
;

RTLBinaryOp:
    left=RTLAtom op=BinaryOperator right=RTLExpression
;

BinaryOperator returns string:
    '<<' | '>>' | '<=' | '>=' | '==' | '!=' | '<' | '>' | '+' | '-' | '*' | '/' | '%' | '&' | '|' | '^'
;

RTLUnaryOp:
    op=UnaryOperator expr=RTLAtom
;

UnaryOperator returns string:
    '-' | '!' | '~'
;

RTLLValue:
    register_access=RegisterAccess | field_access=FieldAccess | simple_register=ID
;

RegisterAccess:
    reg_name=ID '[' index=RTLExpression ']' (lane_access=LaneAccess)?
;

LaneAccess:
    '[' lane_index=LaneIndex ']'
;

LaneIndex:
    RTLConstant | OperandReference | ID
;

FieldAccess:
    reg_name=ID '.' field_name=ID
;

RTLConstant:
    hex_value=HEX | binary_value=BINARY | value=INT
;

// Terminal definitions
hidden terminal WS: /\s+/;

terminal ID: /[_a-zA-Z][\w_]*/;

terminal INT returns number: /[0-9]+/;

terminal STRING: /"(\\.|[^"\\])*"|'(\\.|[^'\\])*'/;

terminal HEX: /0[xX][0-9a-fA-F]+/;

terminal BINARY: /0[bB][01]+/;

hidden terminal ML_COMMENT: /\/\*[\s\S]*?\*\//;

hidden terminal SL_COMMENT: /\/\/[^\n\r]*/;
