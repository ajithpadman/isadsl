"""Custom textX scope provider for resolving format references across included files."""

from typing import Dict, Optional, Any, Tuple


class IncludeScopeProvider:
    """Scope provider that resolves InstructionFormat and BundleFormat references from included files.
    
    This uses textX's scoping mechanism to find format definitions in:
    1. The current model being parsed
    2. Previously parsed included file models (stored in cache)
    """
    
    def __init__(self, included_textx_models_cache: Dict[str, Any]):
        """Initialize the scope provider.
        
        Args:
            included_textx_models_cache: Dictionary mapping file paths to their textX models
        """
        self.included_textx_models_cache = included_textx_models_cache
    
    def __call__(self, obj: Any, attr_ref: Any, obj_ref: Any) -> Optional[Any]:
        """Make the scope provider callable - this is what textX expects.
        
        Args:
            obj: The object containing the reference (Instruction)
            attr_ref: The textX attribute reference object
            obj_ref: The textX object reference (contains obj_name)
            
        Returns:
            Matching format/bundle_format object or None
        """
        return self.resolve_format_reference(obj, attr_ref, obj_ref)
    
    def resolve_format_reference(self, obj: Any, attr_ref: Any, obj_ref: Any) -> Optional[Any]:
        """Resolve a format or bundle_format reference.
        
        Args:
            obj: The object containing the reference (Instruction)
            attr_ref: The textX attribute reference object
            obj_ref: The textX object reference (contains obj_name)
            
        Returns:
            Matching format/bundle_format object or None
        """
        # Get the reference name (the format name being referenced)
        obj_name = None
        
        # Try multiple ways to extract the format name from obj_ref
        if obj_ref is not None:
            # Method 1: Check for obj_name attribute (textX reference object) - this is the primary method
            if hasattr(obj_ref, 'obj_name'):
                obj_name = obj_ref.obj_name
            # Method 2: Check if obj_ref is a string directly
            elif isinstance(obj_ref, str):
                obj_name = obj_ref
            # Method 3: Check for name attribute
            elif hasattr(obj_ref, 'name'):
                obj_name = obj_ref.name
            # Method 4: Check for _tx_obj_name (textX internal)
            elif hasattr(obj_ref, '_tx_obj_name'):
                obj_name = obj_ref._tx_obj_name
            # Method 5: Try to get it as a string representation
            else:
                try:
                    obj_name = str(obj_ref)
                except:
                    pass
        
        
        # If we still don't have a name, try to get it from attr_ref
        if not obj_name and attr_ref is not None:
            if isinstance(attr_ref, str):
                obj_name = attr_ref
            elif hasattr(attr_ref, 'obj_name'):
                obj_name = attr_ref.obj_name
            elif hasattr(attr_ref, 'name'):
                obj_name = attr_ref.name
            elif hasattr(attr_ref, '_tx_obj_name'):
                obj_name = attr_ref._tx_obj_name
        
        # If still no name, check if obj has a format attribute that's a string
        if not obj_name and obj is not None:
            if hasattr(obj, 'format') and isinstance(obj.format, str):
                obj_name = obj.format
        
        if not obj_name:
            return None
        
        # Determine if this is format or bundle_format
        is_format, is_bundle_format = self._determine_format_type(obj, attr_ref)
        
        # Get the textX root model from the object
        model = self._get_root_model(obj)
        
        # Search in current model first
        if model:
            found = self._search_formats_in_model(model, obj_name, is_format, is_bundle_format)
            if found:
                return found[0]
        
        # Then look in included textX models
        for file_path, textx_model in self.included_textx_models_cache.items():
            found = self._search_formats_in_model(textx_model, obj_name, is_format, is_bundle_format)
            if found:
                return found[0]
        
        # If not found, return None to let textX handle it
        return None
    
    def _determine_format_type(self, obj: Any, attr_ref: Any) -> Tuple[bool, bool]:
        """Determine if we're looking for a format or bundle_format.
        
        Args:
            obj: The instruction object
            attr_ref: The attribute reference
            
        Returns:
            Tuple of (is_format, is_bundle_format)
        """
        obj_format = getattr(obj, 'format', None)
        obj_bundle_format = getattr(obj, 'bundle_format', None)
        
        is_format = False
        is_bundle_format = False
        
        # Try to compare - but be careful with None values
        try:
            if obj_format is not None and obj_format == attr_ref:
                is_format = True
        except:
            pass
        
        try:
            if obj_bundle_format is not None and obj_bundle_format == attr_ref:
                is_bundle_format = True
        except:
            pass
        
        # If we can't determine from the object, use heuristics
        if not is_format and not is_bundle_format:
            if hasattr(obj, 'bundle_format') and obj.bundle_format is None and hasattr(obj, 'format') and obj.format is not None:
                is_bundle_format = True
            else:
                is_format = True
        
        return is_format, is_bundle_format
    
    def _get_root_model(self, obj: Any) -> Optional[Any]:
        """Get the root textX model from an object.
        
        Args:
            obj: Any object in the textX model hierarchy
            
        Returns:
            Root model (ISASpecFull or ISASpecPartial) or None
        """
        model = None
        if hasattr(obj, '_tx_model'):
            model = obj._tx_model
        
        # If _tx_model is not available, try traversing up the parent chain
        if model is None:
            current = obj
            for _ in range(10):  # Limit depth to avoid infinite loops
                if hasattr(current, '_tx_model'):
                    model = current._tx_model
                    break
                if hasattr(current, '_parent'):
                    current = current._parent
                    if current and (hasattr(current, 'name') or hasattr(current, 'formats')):
                        model = current
                        break
                elif hasattr(current, 'parent'):
                    current = getattr(current, 'parent', None)
                    if current and (hasattr(current, 'name') or hasattr(current, 'formats')):
                        model = current
                        break
                else:
                    break
        
        return model
    
    def _search_formats_in_model(self, textx_model: Any, target_name: str, 
                                  search_format: bool = True, 
                                  search_bundle: bool = False) -> list:
        """Search for formats in a textX model.
        
        Args:
            textx_model: The textX model to search
            target_name: Name of the format to find
            search_format: Whether to search for InstructionFormat
            search_bundle: Whether to search for BundleFormat
            
        Returns:
            List of matching format objects
        """
        found = []
        if textx_model is None:
            return found
        
        # Check if this is ISASpecFull or ISASpecPartial
        # In textX, formats are stored in a FormatBlock object
        if hasattr(textx_model, 'formats') and textx_model.formats is not None:
            fmt_block = textx_model.formats
            
            # Check for InstructionFormat objects
            if search_format and hasattr(fmt_block, 'formats') and fmt_block.formats:
                for fmt_tx in fmt_block.formats:
                    fmt_name = getattr(fmt_tx, 'name', None)
                    if fmt_name == target_name:
                        found.append(fmt_tx)
            
            # Check for BundleFormat objects
            if search_bundle and hasattr(fmt_block, 'bundle_formats') and fmt_block.bundle_formats:
                for fmt_tx in fmt_block.bundle_formats:
                    fmt_name = getattr(fmt_tx, 'name', None)
                    if fmt_name == target_name:
                        found.append(fmt_tx)
        
        return found

