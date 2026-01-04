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
            formats=base.formats.copy(),
            bundle_formats=base.bundle_formats.copy(),
            instructions=base.instructions.copy()
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
            formats=base.formats.copy(),
            bundle_formats=base.bundle_formats.copy(),
            instructions=base.instructions.copy()
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
        
        return extended

