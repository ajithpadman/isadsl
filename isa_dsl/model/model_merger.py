"""Model merging and extension utilities for ISASpecification objects."""

from typing import Optional
from .isa_model import ISASpecification
from .exceptions import DuplicateDefinitionError


class ModelMerger:
    """Handles merging and extending ISASpecification models."""
    
    @staticmethod
    def merge(base: ISASpecification, additional: ISASpecification, 
              check_duplicates: bool = True, 
              base_file: Optional[str] = None, 
              additional_file: Optional[str] = None) -> ISASpecification:
        """Merge two ISASpecification models. Returns a new merged model.
        
        Args:
            base: Base model to merge into
            additional: Additional model to merge
            check_duplicates: If True, raise error on duplicate definitions
            base_file: Optional file path for error reporting
            additional_file: Optional file path for error reporting
            
        Returns:
            New merged ISASpecification
            
        Raises:
            DuplicateDefinitionError: If check_duplicates is True and duplicates are found
        """
        merged = ISASpecification(
            name=base.name,  # Use base name
            properties=base.properties.copy(),
            registers=base.registers.copy(),
            virtual_registers=base.virtual_registers.copy(),
            register_aliases=base.register_aliases.copy(),
            formats=base.formats.copy(),
            bundle_formats=base.bundle_formats.copy(),
            instructions=base.instructions.copy(),
            instruction_aliases=base.instruction_aliases.copy()
        )
        
        # Merge properties
        for prop in additional.properties:
            existing = next((p for p in merged.properties if p.name == prop.name), None)
            if existing:
                if check_duplicates:
                    locations = []
                    if base_file:
                        locations.append((base_file, None))
                    if additional_file:
                        locations.append((additional_file, None))
                    raise DuplicateDefinitionError(prop.name, locations)
                # In override mode, replace
                merged.properties.remove(existing)
            merged.properties.append(prop)
        
        # Merge registers
        for reg in additional.registers:
            existing = next((r for r in merged.registers if r.name == reg.name), None)
            if existing:
                if check_duplicates:
                    locations = []
                    if base_file:
                        locations.append((base_file, None))
                    if additional_file:
                        locations.append((additional_file, None))
                    raise DuplicateDefinitionError(reg.name, locations)
                # In override mode, replace
                merged.registers.remove(existing)
            merged.registers.append(reg)
        
        # Merge formats
        for fmt in additional.formats:
            existing = next((f for f in merged.formats if f.name == fmt.name), None)
            if existing:
                if check_duplicates:
                    locations = []
                    if base_file:
                        locations.append((base_file, None))
                    if additional_file:
                        locations.append((additional_file, None))
                    raise DuplicateDefinitionError(fmt.name, locations)
                merged.formats.remove(existing)
            merged.formats.append(fmt)
        
        # Merge bundle formats
        for bundle_fmt in additional.bundle_formats:
            existing = next((f for f in merged.bundle_formats if f.name == bundle_fmt.name), None)
            if existing:
                if check_duplicates:
                    locations = []
                    if base_file:
                        locations.append((base_file, None))
                    if additional_file:
                        locations.append((additional_file, None))
                    raise DuplicateDefinitionError(bundle_fmt.name, locations)
                merged.bundle_formats.remove(existing)
            merged.bundle_formats.append(bundle_fmt)
        
        # Merge instructions
        for instr in additional.instructions:
            existing = next((i for i in merged.instructions if i.mnemonic == instr.mnemonic), None)
            if existing:
                if check_duplicates:
                    locations = []
                    if base_file:
                        locations.append((base_file, None))
                    if additional_file:
                        locations.append((additional_file, None))
                    raise DuplicateDefinitionError(instr.mnemonic, locations)
                merged.instructions.remove(existing)
            merged.instructions.append(instr)
        
        # Merge virtual registers
        for vreg in additional.virtual_registers:
            existing = next((v for v in merged.virtual_registers if v.name == vreg.name), None)
            if existing:
                if check_duplicates:
                    locations = []
                    if base_file:
                        locations.append((base_file, None))
                    if additional_file:
                        locations.append((additional_file, None))
                    raise DuplicateDefinitionError(vreg.name, locations)
                merged.virtual_registers.remove(existing)
            merged.virtual_registers.append(vreg)
        
        # Merge register aliases
        for alias in additional.register_aliases:
            existing = next((a for a in merged.register_aliases if a.alias_name == alias.alias_name), None)
            if existing:
                if check_duplicates:
                    locations = []
                    if base_file:
                        locations.append((base_file, None))
                    if additional_file:
                        locations.append((additional_file, None))
                    raise DuplicateDefinitionError(alias.alias_name, locations)
                merged.register_aliases.remove(existing)
            merged.register_aliases.append(alias)
        
        # Merge instruction aliases
        for alias in additional.instruction_aliases:
            existing = next((a for a in merged.instruction_aliases if a.alias_mnemonic == alias.alias_mnemonic), None)
            if existing:
                if check_duplicates:
                    locations = []
                    if base_file:
                        locations.append((base_file, None))
                    if additional_file:
                        locations.append((additional_file, None))
                    raise DuplicateDefinitionError(alias.alias_mnemonic, locations)
                merged.instruction_aliases.remove(existing)
            merged.instruction_aliases.append(alias)
        
        return merged
    
    @staticmethod
    def extend(base: ISASpecification, extending: ISASpecification) -> ISASpecification:
        """Extend base architecture with extending architecture. Overrides are allowed.
        
        Args:
            base: Base architecture to extend
            extending: Extending architecture (can override base definitions)
            
        Returns:
            New extended ISASpecification
        """
        # Start with base
        extended = ISASpecification(
            name=extending.name,  # Use extending architecture's name
            properties=base.properties.copy(),
            registers=base.registers.copy(),
            virtual_registers=base.virtual_registers.copy(),
            register_aliases=base.register_aliases.copy(),
            formats=base.formats.copy(),
            bundle_formats=base.bundle_formats.copy(),
            instructions=base.instructions.copy(),
            instruction_aliases=base.instruction_aliases.copy()
        )
        
        # Override/add properties
        for prop in extending.properties:
            existing = next((p for p in extended.properties if p.name == prop.name), None)
            if existing:
                extended.properties.remove(existing)
            extended.properties.append(prop)
        
        # Override/add registers
        for reg in extending.registers:
            existing = next((r for r in extended.registers if r.name == reg.name), None)
            if existing:
                extended.registers.remove(existing)
            extended.registers.append(reg)
        
        # Override/add formats
        for fmt in extending.formats:
            existing = next((f for f in extended.formats if f.name == fmt.name), None)
            if existing:
                extended.formats.remove(existing)
            extended.formats.append(fmt)
        
        # Override/add bundle formats
        for bundle_fmt in extending.bundle_formats:
            existing = next((f for f in extended.bundle_formats if f.name == bundle_fmt.name), None)
            if existing:
                extended.bundle_formats.remove(existing)
            extended.bundle_formats.append(bundle_fmt)
        
        # Override/add instructions
        for instr in extending.instructions:
            existing = next((i for i in extended.instructions if i.mnemonic == instr.mnemonic), None)
            if existing:
                extended.instructions.remove(existing)
            extended.instructions.append(instr)
        
        # Override/add virtual registers
        for vreg in extending.virtual_registers:
            existing = next((v for v in extended.virtual_registers if v.name == vreg.name), None)
            if existing:
                extended.virtual_registers.remove(existing)
            extended.virtual_registers.append(vreg)
        
        # Override/add register aliases
        for alias in extending.register_aliases:
            existing = next((a for a in extended.register_aliases if a.alias_name == alias.alias_name), None)
            if existing:
                extended.register_aliases.remove(existing)
            extended.register_aliases.append(alias)
        
        # Override/add instruction aliases
        for alias in extending.instruction_aliases:
            existing = next((a for a in extended.instruction_aliases if a.alias_mnemonic == alias.alias_mnemonic), None)
            if existing:
                extended.instruction_aliases.remove(existing)
            extended.instruction_aliases.append(alias)
        
        return extended

