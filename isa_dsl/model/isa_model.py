"""ISA model classes representing the parsed DSL structure."""

from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field


# Base class for textX model objects
class TextXObject:
    """Base class for textX model objects."""
    pass


@dataclass
class Property(TextXObject):
    """Architecture property (e.g., word_size, endianness)."""
    name: str
    value: Any


@dataclass
class RegisterField(TextXObject):
    """A field within a register (e.g., flag bits)."""
    name: str
    msb: int
    lsb: int

    def width(self) -> int:
        """Return the width of the field in bits."""
        return self.msb - self.lsb + 1


@dataclass
class Register(TextXObject):
    """A register definition (GPR, SFR, or vector)."""
    type: str  # 'gpr', 'sfr', or 'vec'
    name: str
    width: int
    count: Optional[int] = None  # For register files
    element_width: Optional[int] = None  # For vector registers: width of each element
    lanes: Optional[int] = None  # For vector registers: number of lanes
    fields: List[RegisterField] = field(default_factory=list)

    def is_register_file(self) -> bool:
        """Check if this is a register file (has count)."""
        return self.count is not None and self.count > 0

    def is_vector_register(self) -> bool:
        """Check if this is a vector register."""
        return self.type == 'vec'

    def get_field(self, name: str) -> Optional[RegisterField]:
        """Get a field by name."""
        for field in self.fields:
            if field.name == name:
                return field
        return None


@dataclass
class VirtualRegisterComponent(TextXObject):
    """A component of a virtual register (can be simple register or indexed register)."""
    reg_name: str
    index: Optional[int] = None  # None for simple registers, int for indexed registers
    
    def is_indexed(self) -> bool:
        """Check if this is an indexed register (e.g., R[0])."""
        return self.index is not None


@dataclass
class VirtualRegister(TextXObject):
    """A virtual register formed by concatenating physical registers."""
    name: str
    width: int
    components: List[VirtualRegisterComponent]  # List of register components to concatenate
    
    def get_component_registers(self, isa: 'ISASpecification') -> List[Tuple[Register, Optional[int]]]:
        """Get the physical registers that form this virtual register.
        
        Returns:
            List of tuples (Register, index) where index is None for simple registers
            and an int for indexed registers from register files.
        """
        result = []
        for comp in self.components:
            reg = isa.get_register(comp.reg_name)
            if reg:
                result.append((reg, comp.index))
        return result


@dataclass
class RegisterAlias(TextXObject):
    """An alias name for a register."""
    alias_name: str
    target_reg_name: str  # Name of the register file or simple register
    target_index: Optional[int] = None  # Index if targeting register file element
    
    def is_indexed(self) -> bool:
        """Check if alias targets an indexed register."""
        return self.target_index is not None
    
    def resolve(self, isa: 'ISASpecification') -> Optional[Tuple[Register, Optional[int]]]:
        """Resolve alias to actual register and index.
        
        Returns:
            Tuple of (Register, index) where index is None for simple registers
            and an int for indexed registers from register files.
        """
        reg = isa.get_register(self.target_reg_name)
        if reg:
            return (reg, self.target_index)
        return None


@dataclass
class InstructionAlias(TextXObject):
    """An alias mnemonic for an instruction."""
    alias_mnemonic: str
    target_mnemonic: str  # Mnemonic of the actual instruction
    assembly_syntax: Optional[str] = None  # Optional custom assembly syntax
    
    def resolve(self, isa: 'ISASpecification') -> Optional['Instruction']:
        """Resolve alias to actual instruction."""
        return isa.get_instruction(self.target_mnemonic)


@dataclass
class FormatField(TextXObject):
    """A field within an instruction format."""
    name: str
    msb: int
    lsb: int
    constant_value: Optional[int] = None

    def has_constant(self) -> bool:
        """Check if this field has a constant value."""
        return self.constant_value is not None

    def width(self) -> int:
        """Return the width of the field in bits."""
        return self.msb - self.lsb + 1

    def mask(self) -> int:
        """Return the bit mask for this field."""
        width = self.width()
        if width <= 0:
            return 0
        return ((1 << width) - 1) << self.lsb

    def extract(self, instruction: int) -> int:
        """Extract the field value from an instruction word."""
        width = self.width()
        if width <= 0:
            return 0
        return (instruction >> self.lsb) & ((1 << width) - 1)

    def encode(self, value: int, instruction: int) -> int:
        """Encode a value into the instruction word at this field position."""
        mask = self.mask()
        return (instruction & ~mask) | ((value << self.lsb) & mask)
    
    def encode_constant(self, instruction: int) -> int:
        """Encode the constant value into the instruction word at this field position."""
        if self.constant_value is not None:
            return self.encode(self.constant_value, instruction)
        return instruction


@dataclass
class InstructionFormat(TextXObject):
    """An instruction encoding format."""
    name: str
    width: int
    fields: List[FormatField] = field(default_factory=list)
    identification_fields: List[str] = field(default_factory=list)  # Fields used for instruction identification

    def get_field(self, name: str) -> Optional[FormatField]:
        """Get a field by name."""
        for field in self.fields:
            if field.name == name:
                return field
        return None

    def get_identification_fields(self) -> List[FormatField]:
        """Get fields used for instruction identification."""
        if self.identification_fields:
            return [f for f in self.fields if f.name in self.identification_fields]
        # Default: return empty list (backward compatible - will use all encoding fields)
        return []

    def get_minimum_bits_for_identification(self) -> int:
        """Get minimum number of bits needed to identify instructions using this format."""
        id_fields = self.get_identification_fields()
        if id_fields:
            max_bit = max((f.msb for f in id_fields), default=0)
            return max_bit + 1
        # Default: use format width (backward compatible)
        return self.width

    def total_field_width(self) -> int:
        """Calculate total width of all fields."""
        return sum(f.width() for f in self.fields)

    def validate_fields(self) -> bool:
        """Validate that fields don't overlap and fit in width."""
        # Check for overlaps and total width
        used_bits = set()
        for field in self.fields:
            for bit in range(field.lsb, field.msb + 1):
                if bit in used_bits:
                    return False
                used_bits.add(bit)
        return len(used_bits) <= self.width


@dataclass
class EncodingAssignment(TextXObject):
    """An encoding assignment (e.g., opcode=0x01)."""
    field: str
    value: int


@dataclass
class EncodingSpec(TextXObject):
    """Instruction encoding specification."""
    assignments: List[EncodingAssignment] = field(default_factory=list)

    def get_value(self, field: str) -> Optional[int]:
        """Get the encoding value for a field."""
        for assignment in self.assignments:
            if assignment.field == field:
                return assignment.value
        return None


@dataclass
class OperandSpec(TextXObject):
    """An operand specification - can be simple or distributed across multiple fields."""
    name: str
    field_names: List[str] = field(default_factory=list)  # Empty list means use operand name as field name
    
    def is_distributed(self) -> bool:
        """Check if this operand is distributed across multiple fields."""
        return len(self.field_names) > 0


@dataclass
class Instruction(TextXObject):
    """An instruction definition."""
    mnemonic: str
    format: Optional[InstructionFormat] = None
    bundle_format: Optional['BundleFormat'] = None  # Forward reference
    encoding: Optional[EncodingSpec] = None
    operands: List[str] = field(default_factory=list)  # Legacy: simple operand names
    operand_specs: List[OperandSpec] = field(default_factory=list)  # New: operand specifications with field mappings
    assembly_syntax: Optional[str] = None  # Format string for disassembly (e.g., "ADD R{rd}, R{rs1}, R{rs2}")
    behavior: Optional['RTLBlock'] = None
    external_behavior: bool = False  # If True, behavior is externally defined and implemented by user

    def is_bundle(self) -> bool:
        """Check if this is a bundle instruction."""
        return self.bundle_format is not None

    def matches_encoding(self, instruction_word: int) -> bool:
        """Check if an instruction word matches this instruction's encoding."""
        # For bundle instructions, check encoding using format
        if self.is_bundle():
            if not self.format or not self.encoding:
                return False
            # Bundle instructions use format for identification
            for assignment in self.encoding.assignments:
                field = self.format.get_field(assignment.field)
                if not field:
                    return False
                extracted = field.extract(instruction_word)
                if extracted != assignment.value:
                    return False
            return True
        
        # Regular instructions
        if not self.format or not self.encoding:
            return False

        for assignment in self.encoding.assignments:
            field = self.format.get_field(assignment.field)
            if not field:
                return False
            extracted = field.extract(instruction_word)
            if extracted != assignment.value:
                return False
        return True

    def decode_operands(self, instruction_word: int) -> Dict[str, int]:
        """Decode operand values from an instruction word."""
        if not self.format:
            return {}

        operands = {}
        
        # Use operand_specs if available, otherwise fall back to legacy operands list
        if self.operand_specs:
            for operand_spec in self.operand_specs:
                if operand_spec.is_distributed():
                    # Combine multiple fields
                    value = 0
                    shift = 0
                    for field_name in operand_spec.field_names:
                        field = self.format.get_field(field_name)
                        if field:
                            field_value = field.extract(instruction_word)
                            value |= (field_value << shift)
                            shift += field.width()
                    operands[operand_spec.name] = value
                else:
                    # Simple operand - use operand name as field name
                    field = self.format.get_field(operand_spec.name)
                    if field:
                        operands[operand_spec.name] = field.extract(instruction_word)
        else:
            # Legacy: simple operand names
            for operand_name in self.operands:
                field = self.format.get_field(operand_name)
                if field:
                    operands[operand_name] = field.extract(instruction_word)
        
        return operands
    
    def get_operand_fields(self, operand_name: str) -> List[FormatField]:
        """Get all fields that compose an operand."""
        if not self.format:
            return []
        
        # Check operand_specs first
        if self.operand_specs:
            for operand_spec in self.operand_specs:
                if operand_spec.name == operand_name:
                    if operand_spec.is_distributed():
                        fields = []
                        for field_name in operand_spec.field_names:
                            field = self.format.get_field(field_name)
                            if field:
                                fields.append(field)
                        return fields
                    else:
                        field = self.format.get_field(operand_spec.name)
                        return [field] if field else []
        
        # Legacy: check if operand name matches a field name
        field = self.format.get_field(operand_name)
        return [field] if field else []

    def encode_instruction(self, operand_values: Dict[str, int]) -> int:
        """Encode an instruction with given operand values."""
        if not self.format:
            return 0

        instruction = 0

        # Set encoding fields
        if self.encoding:
            for assignment in self.encoding.assignments:
                field = self.format.get_field(assignment.field)
                if field:
                    instruction = field.encode(assignment.value, instruction)

        # Set operand fields
        for operand_name, value in operand_values.items():
            fields = self.get_operand_fields(operand_name)
            if fields:
                if len(fields) == 1:
                    # Simple field
                    instruction = fields[0].encode(value, instruction)
                else:
                    # Distributed fields - split value across fields
                    remaining_value = value
                    for field in fields:
                        field_value = remaining_value & ((1 << field.width()) - 1)
                        instruction = field.encode(field_value, instruction)
                        remaining_value >>= field.width()

        return instruction


@dataclass
class RTLBlock(TextXObject):
    """A block of RTL statements."""
    statements: List['RTLStatement'] = field(default_factory=list)


@dataclass
class RTLStatement(TextXObject):
    """Base class for RTL statements."""
    pass


@dataclass
class RTLAssignment(RTLStatement, TextXObject):
    """An RTL assignment statement."""
    target: 'RTLLValue'
    expr: 'RTLExpression'


@dataclass
class RTLConditional(RTLStatement, TextXObject):
    """An RTL conditional statement."""
    condition: 'RTLExpression'
    then_statements: List[RTLStatement] = field(default_factory=list)
    else_statements: List[RTLStatement] = field(default_factory=list)


@dataclass
class RTLMemoryAccess(RTLStatement, TextXObject):
    """An RTL memory access statement."""
    is_load: bool  # True for load, False for store
    address: 'RTLExpression'
    target: Optional['RTLLValue'] = None  # For load
    value: Optional['RTLExpression'] = None  # For store


@dataclass
class RTLForLoop(RTLStatement, TextXObject):
    """An RTL for loop statement."""
    init: 'RTLAssignment'  # Loop initialization
    condition: 'RTLExpression'  # Loop condition
    update: 'RTLAssignment'  # Loop update
    statements: List[RTLStatement] = field(default_factory=list)  # Loop body


@dataclass
class RTLExpression(TextXObject):
    """Base class for RTL expressions."""
    pass


@dataclass
class RTLTernary(RTLExpression, TextXObject):
    """Ternary conditional expression."""
    condition: RTLExpression
    then_expr: RTLExpression
    else_expr: RTLExpression


@dataclass
class RTLBinaryOp(RTLExpression, TextXObject):
    """Binary operation expression."""
    left: RTLExpression
    op: str
    right: RTLExpression


@dataclass
class RTLUnaryOp(RTLExpression, TextXObject):
    """Unary operation expression."""
    op: str
    expr: RTLExpression


@dataclass
class RTLLValue(TextXObject):
    """Base class for left-hand values."""
    pass


@dataclass
class RegisterAccess(RTLLValue, TextXObject):
    """Register access (e.g., R[rd])."""
    reg_name: str
    index: RTLExpression


@dataclass
class FieldAccess(RTLLValue, TextXObject):
    """Register field access (e.g., FLAGS.Z)."""
    reg_name: str
    field_name: str


@dataclass
class Variable(RTLLValue, TextXObject):
    """Temporary variable (e.g., temp, result)."""
    name: str


@dataclass
class RTLConstant(RTLExpression, TextXObject):
    """Constant value."""
    value: int


@dataclass
class OperandReference(RTLExpression, TextXObject):
    """Reference to an instruction operand (e.g., rd, rs1)."""
    name: str


@dataclass
class RTLBitfieldAccess(RTLExpression, TextXObject):
    """Bitfield extraction from a value (e.g., R[0][15:8])."""
    base: RTLExpression
    msb: RTLExpression
    lsb: RTLExpression


@dataclass
class RTLFunctionCall(RTLExpression, TextXObject):
    """Built-in function call (e.g., sign_extend(value, bits))."""
    function_name: str
    args: List[RTLExpression] = field(default_factory=list)


@dataclass
class BundleSlot(TextXObject):
    """A slot within a bundle format for a sub-instruction."""
    name: str
    msb: int
    lsb: int

    def width(self) -> int:
        """Return the width of the slot in bits."""
        return self.msb - self.lsb + 1

    def extract(self, bundle_word: int) -> int:
        """Extract the sub-instruction word from this slot."""
        width = self.width()
        if width <= 0:
            return 0
        return (bundle_word >> self.lsb) & ((1 << width) - 1)

    def encode(self, instruction_word: int, bundle_word: int) -> int:
        """Encode a sub-instruction into this slot of the bundle."""
        mask = ((1 << self.width()) - 1) << self.lsb
        return (bundle_word & ~mask) | ((instruction_word << self.lsb) & mask)


@dataclass
class BundleFormat(TextXObject):
    """A bundle format defining how instructions are packed."""
    name: str
    width: int
    instruction_start: int = 0  # Starting bit position for instructions (to avoid bundle_opcode conflict)
    slots: List[BundleSlot] = field(default_factory=list)
    identification_fields: List[str] = field(default_factory=list)  # Fields used for bundle identification

    def get_slot(self, name: str) -> Optional[BundleSlot]:
        """Get a slot by name."""
        for slot in self.slots:
            if slot.name == name:
                return slot
        return None

    def get_minimum_bits_for_identification(self) -> int:
        """Get minimum number of bits needed to identify bundle."""
        # For bundles, identification is typically in the first few bits
        # (e.g., bundle_opcode field). If identification_fields are specified,
        # we need to find the format that contains these fields (from the bundle instruction's format).
        # For now, default to 32 bits (first word) for backward compatibility.
        if self.identification_fields:
            # In practice, bundle identification fields are usually in the first byte or word
            # This will be refined when we have access to the bundle instruction's format
            return 32
        return 32

    def extract_instructions(self, bundle_word: int) -> List[Tuple[str, int]]:
        """Extract all sub-instructions from a bundle word."""
        instructions = []
        for slot in self.slots:
            sub_instr = slot.extract(bundle_word)
            instructions.append((slot.name, sub_instr))
        return instructions

    def encode_bundle(self, instruction_words: Dict[str, int]) -> int:
        """Encode multiple instructions into a bundle word."""
        bundle_word = 0
        for slot in self.slots:
            if slot.name in instruction_words:
                bundle_word = slot.encode(instruction_words[slot.name], bundle_word)
        return bundle_word


@dataclass
class ISASpecification(TextXObject):
    """Top-level ISA specification."""
    name: str
    properties: List[Property] = field(default_factory=list)
    registers: List[Register] = field(default_factory=list)
    virtual_registers: List[VirtualRegister] = field(default_factory=list)
    register_aliases: List[RegisterAlias] = field(default_factory=list)
    formats: List[InstructionFormat] = field(default_factory=list)
    bundle_formats: List[BundleFormat] = field(default_factory=list)
    instructions: List[Instruction] = field(default_factory=list)
    instruction_aliases: List[InstructionAlias] = field(default_factory=list)

    def get_property(self, name: str) -> Optional[Any]:
        """Get a property value by name."""
        for prop in self.properties:
            if prop.name == name:
                return prop.value
        return None

    def get_register(self, name: str) -> Optional[Register]:
        """Get a register by name, checking aliases."""
        # First check direct register names
        for reg in self.registers:
            if reg.name == name:
                return reg
        # Check virtual registers
        for vreg in self.virtual_registers:
            if vreg.name == name:
                # Virtual registers are not returned as Register objects
                # They need special handling
                return None
        # Check register aliases
        for alias in self.register_aliases:
            if alias.alias_name == name:
                reg = self.get_register(alias.target_reg_name)
                return reg
        return None
    
    def get_virtual_register(self, name: str) -> Optional[VirtualRegister]:
        """Get a virtual register by name."""
        for vreg in self.virtual_registers:
            if vreg.name == name:
                return vreg
        return None

    def get_format(self, name: str) -> Optional[InstructionFormat]:
        """Get an instruction format by name."""
        for fmt in self.formats:
            if fmt.name == name:
                return fmt
        return None

    def get_bundle_format(self, name: str) -> Optional[BundleFormat]:
        """Get a bundle format by name."""
        for bundle_fmt in self.bundle_formats:
            if bundle_fmt.name == name:
                return bundle_fmt
        return None

    def get_instruction(self, mnemonic: str) -> Optional[Instruction]:
        """Get an instruction by mnemonic, checking aliases."""
        # First check direct instruction mnemonics
        for instr in self.instructions:
            if instr.mnemonic == mnemonic:
                return instr
        # Check instruction aliases
        for alias in self.instruction_aliases:
            if alias.alias_mnemonic == mnemonic:
                return alias.resolve(self)
        return None

    def decode_instruction(self, instruction_word: int) -> Optional[Instruction]:
        """Decode an instruction word to find matching instruction."""
        for instr in self.instructions:
            if instr.matches_encoding(instruction_word):
                return instr
        return None

