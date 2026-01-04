"""Main ISA parser class using object-oriented design.

This parser uses textX object models exclusively, avoiding regex-based
content manipulation except where absolutely necessary (see documentation).

Key design principles:
1. Parse files separately, use scope provider for cross-file references
2. Merge ISASpecification objects after parsing (not content merging)
3. Use textX object model for all data extraction
4. Document what requires regex and why
"""

import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from textx import metamodel_from_file

from .comment_processor import CommentProcessor
from .include_processor import IncludeProcessor
from .scope_provider import IncludeScopeProvider
from .textx_model_converter import TextXModelConverter
from .model_merger import ModelMerger
from .assembly_syntax_processor import AssemblySyntaxProcessor
from .isa_model import ISASpecification
from .exceptions import (
    CircularDependencyError,
    MultipleInheritanceError,
    ArchitectureExtensionRequiredError,
    PartialDefinitionRequiredError,
)


class ISAParser:
    """Main parser class for ISA DSL files with multi-file support.
    
    This class orchestrates parsing, include resolution, and model merging
    using an object-oriented approach with textX object models.
    """
    
    def __init__(self):
        """Initialize the parser with required components."""
        self.comment_processor = CommentProcessor()
        self.include_processor = IncludeProcessor(self.comment_processor)
        self.model_converter = TextXModelConverter()
        self.model_merger = ModelMerger()
        self.assembly_processor = AssemblySyntaxProcessor()
        
        # Caches for included models (for scope provider)
        self._included_models_cache: Dict[str, ISASpecification] = {}
        self._included_textx_models_cache: Dict[str, Any] = {}
        
        # Metamodel (lazy-loaded)
        self._metamodel: Optional[Any] = None
    
    def parse_file(self, file_path: str) -> ISASpecification:
        """Parse an ISA specification file and return the model.
        
        Args:
            file_path: Path to the ISA file
            
        Returns:
            Parsed ISASpecification model
        """
        # Clear caches at start of parsing
        self._included_models_cache.clear()
        self._included_textx_models_cache.clear()
        
        file_path_obj = Path(file_path).resolve()
        
        # Check if file exists
        if not file_path_obj.exists():
            raise FileNotFoundError(f"ISA file not found: {file_path}")
        
        # Get or create metamodel
        mm = self._get_metamodel()
        
        # Check if file has includes
        content = file_path_obj.read_text()
        includes = self.include_processor.extract_includes(content)
        
        if includes:
            # Use include-aware parsing
            visited: Set[Path] = set()
            model, _ = self._parse_with_includes(file_path_obj, visited, mm)
            return model
        else:
            # No includes - parse directly
            return self._parse_single_file(file_path_obj, mm)
    
    def _get_metamodel(self):
        """Get or create the textX metamodel with scope provider.
        
        Returns:
            textX metamodel instance
        """
        if self._metamodel is None:
            grammar_file = Path(__file__).parent.parent / 'grammar' / 'isa.tx'
            
            # Create metamodel
            mm = metamodel_from_file(str(grammar_file), skipws=True)
            
            # Create scope provider
            scope_provider = IncludeScopeProvider(self._included_textx_models_cache)
            
            # Register scope providers - textX expects callable objects
            mm.register_scope_providers({
                'Instruction.format': scope_provider,
                'Instruction.bundle_format': scope_provider,
            })
            
            # Wrap model_from_file to handle assembly_syntax preprocessing
            original_model_from_file = mm.model_from_file
            
            def model_from_file_wrapper(file_path: str):
                """Wrapper that handles assembly_syntax preprocessing."""
                content = Path(file_path).read_text()
                
                # Check if this is a wrapped partial definition
                is_wrapped_partial = content.strip().startswith('architecture _temp_arch')
                if is_wrapped_partial:
                    return original_model_from_file(file_path)
                
                # Preprocess assembly_syntax
                modified_content, assembly_syntax_map = self.assembly_processor.preprocess_content(
                    self.comment_processor.strip_comments(content)
                )
                
                # Write to temp file and parse
                with tempfile.NamedTemporaryFile(mode='w', suffix='.isa', delete=False) as tmp_file:
                    tmp_file.write(modified_content)
                    tmp_file_path = tmp_file.name
                
                try:
                    textx_model = original_model_from_file(tmp_file_path)
                    # Inject assembly_syntax back
                    self.assembly_processor.inject_assembly_syntax(textx_model, assembly_syntax_map)
                    return textx_model
                finally:
                    Path(tmp_file_path).unlink()
            
            mm.model_from_file = model_from_file_wrapper
            mm._original_model_from_file = original_model_from_file
            
            self._metamodel = mm
        
        return self._metamodel
    
    def _parse_single_file(self, file_path: Path, mm) -> ISASpecification:
        """Parse a single ISA file without includes.
        
        Args:
            file_path: Path to the file
            mm: textX metamodel
            
        Returns:
            Parsed ISASpecification
        """
        # Parse with textX
        textx_model = mm.model_from_file(str(file_path))
        
        # Convert to ISASpecification using object model
        return self.model_converter.convert(textx_model)
    
    def _parse_with_includes(self, file_path: Path, visited: Set[Path], mm) -> Tuple[ISASpecification, bool]:
        """Parse a file with includes recursively.
        
        This method uses scope provider for cross-file references and
        merges ISASpecification objects after parsing (not content merging).
        
        Args:
            file_path: Path to the file to parse
            visited: Set of already visited files (for circular dependency detection)
            mm: textX metamodel
            
        Returns:
            Tuple of (parsed_model, has_architecture_block)
            
        Raises:
            CircularDependencyError: If circular includes are detected
            MultipleInheritanceError: If multiple architecture blocks in includes
            ArchitectureExtensionRequiredError: If architecture extension is required
            PartialDefinitionRequiredError: If partial definitions are required
        """
        file_path = file_path.resolve()
        
        # Check for circular dependency
        if file_path in visited:
            chain = list(visited) + [file_path]
            raise CircularDependencyError([str(p) for p in chain])
        
        visited.add(file_path)
        
        try:
            content = file_path.read_text()
        except FileNotFoundError:
            raise FileNotFoundError(f"Included file not found: {file_path}")
        
        # Check if file has architecture block (using textX object model would require parsing,
        # so we use a quick check here - this is documented as requiring regex)
        has_arch = self.include_processor.has_architecture_block(content)
        
        # Extract includes
        includes = self.include_processor.extract_includes(content)
        
        # Parse included files first
        # IMPORTANT: Parse and cache textX models BEFORE parsing ISASpecification models
        # This ensures the scope provider has access to formats when parsing instructions
        included_models: List[Tuple[ISASpecification, bool, Path]] = []
        included_has_arch: List[bool] = []
        
        for include_path_str in includes:
            include_path = self.include_processor.resolve_include_path(include_path_str, file_path)
            if not include_path.exists():
                raise FileNotFoundError(
                    f"Included file not found: {include_path} "
                    f"(resolved from '{include_path_str}' in {file_path})"
                )
            
            # FIRST: Parse to textX model and add to cache BEFORE parsing ISASpecification
            # This ensures the scope provider can resolve references when parsing other included files
            inc_content = self.comment_processor.strip_comments(include_path.read_text())
            inc_content = self.include_processor.remove_include_lines(inc_content)
            
            # Parse to textX model and cache it immediately
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.isa', delete=False) as tmp_file:
                    tmp_file.write(inc_content)
                    tmp_file_path = tmp_file.name
                try:
                    # Use model_from_file (not _original_model_from_file) to ensure scope provider is used
                    inc_textx_model = mm.model_from_file(tmp_file_path)
                    self._included_textx_models_cache[str(include_path)] = inc_textx_model
                finally:
                    Path(tmp_file_path).unlink()
            except Exception:
                # If parsing fails, skip - scope provider will handle it
                pass
            
            # THEN: Parse recursively to ISASpecification (this may reference formats from cache)
            inc_model, inc_has_arch = self._parse_with_includes(include_path, visited.copy(), mm)
            included_models.append((inc_model, inc_has_arch, include_path))
            included_has_arch.append(inc_has_arch)
            
            # Store in cache for ISASpecification merging
            self._included_models_cache[str(include_path)] = inc_model
        
        # Count architecture blocks in included files
        arch_count = sum(1 for h in included_has_arch if h)
        
        # Validate single inheritance constraint
        if arch_count > 1:
            arch_files = [str(path) for (_, _, path), has_arch in zip(included_models, included_has_arch) if has_arch]
            raise MultipleInheritanceError(arch_files)
        
        # Prepare content for parsing current file
        content_without_includes = self.include_processor.remove_include_lines(content)
        content_without_includes = self.comment_processor.strip_comments(content_without_includes)
        
        # Validate: if any included file has an architecture block, current file must also have one
        if arch_count > 0 and not has_arch:
            arch_file = next((inc_path for (_, inc_has_arch, inc_path) in included_models if inc_has_arch), None)
            if arch_file:
                raise ArchitectureExtensionRequiredError(str(arch_file))
        
        # Parse current file
        # For partial definitions (no architecture block), parse directly
        if not has_arch:
            # Parse using textX (will match ISASpecPartial)
            # Use model_from_file to ensure scope provider is called
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.isa', delete=False) as tmp_file:
                    tmp_file.write(content_without_includes)
                    tmp_file_path = tmp_file.name
                try:
                    temp_model_tx = mm.model_from_file(tmp_file_path)
                finally:
                    Path(tmp_file_path).unlink()
            except Exception:
                # If parsing fails, return empty model
                partial_model = ISASpecification(
                    name='',
                    properties=[],
                    registers=[],
                    formats=[],
                    instructions=[]
                )
                # Merge included partial definitions
                for inc_model, inc_has_arch, inc_path in included_models:
                    if inc_has_arch:
                        raise ArchitectureExtensionRequiredError(str(inc_path))
                    partial_model = self.model_merger.merge(
                        partial_model, inc_model, 
                        check_duplicates=False,
                        base_file=str(file_path),
                        additional_file=str(inc_path)
                    )
                return partial_model, False
            
            # Convert to ISASpecification
            partial_model = self.model_converter.convert(temp_model_tx)
            
            # Post-process: resolve format references from included files
            # (formats are in different files that will be merged later)
            # Collect all formats from included files
            all_formats = {}
            for inc_model, _, _ in included_models:
                for fmt in inc_model.formats:
                    all_formats[fmt.name] = fmt
            
            # Also get formats from the instance cache (from parent's included files)
            # This is needed when parsing a file with no includes that references formats
            # from files included by the parent
            for cached_model in self._included_models_cache.values():
                for fmt in cached_model.formats:
                    if fmt.name not in all_formats:
                        all_formats[fmt.name] = fmt
            
            # Resolve format references using formats from included files
            if all_formats and hasattr(temp_model_tx, 'instructions') and temp_model_tx.instructions:
                if hasattr(temp_model_tx.instructions, 'instructions'):
                    for i, instr_tx in enumerate(temp_model_tx.instructions.instructions):
                        if i < len(partial_model.instructions):
                            instr = partial_model.instructions[i]
                            if instr.format is None and hasattr(instr_tx, 'format') and instr_tx.format:
                                if hasattr(instr_tx.format, 'name'):
                                    fmt_name = instr_tx.format.name
                                    if fmt_name in all_formats:
                                        instr.format = all_formats[fmt_name]
            
            # Merge included partial definitions
            for inc_model, inc_has_arch, inc_path in included_models:
                if inc_has_arch:
                    raise ArchitectureExtensionRequiredError(str(inc_path))
                partial_model = self.model_merger.merge(
                    partial_model, inc_model,
                    check_duplicates=False,
                    base_file=str(file_path),
                    additional_file=str(inc_path)
                )
            
            return partial_model, False
        
        # Has architecture block - parse normally
        # Write to temp file for parsing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.isa', delete=False) as tmp_file:
            tmp_file.write(content_without_includes)
            tmp_file_path = tmp_file.name
        
        try:
            # Update scope provider cache before parsing
            # This allows format references to be resolved from included files
            # Parse current file
            current_model_tx = mm.model_from_file(tmp_file_path)
        finally:
            Path(tmp_file_path).unlink()
        
        # Convert to ISASpecification
        model = self.model_converter.convert(current_model_tx)
        
        # Now merge/extend with included files using ISASpecification objects
        if arch_count == 1:
            # Inheritance mode
            base_model = None
            base_path = None
            partial_models = []
            
            for inc_model, inc_has_arch, inc_path in included_models:
                if inc_has_arch:
                    base_model = inc_model
                    base_path = inc_path
                else:
                    partial_models.append(inc_model)
            
            # Validate that current file has architecture (required for inheritance)
            if not has_arch:
                raise ArchitectureExtensionRequiredError(str(base_path))
            
            # Merge partial definitions into base
            for inc_model, inc_has_arch, inc_path in included_models:
                if not inc_has_arch:
                    base_model = self.model_merger.merge(
                        base_model, inc_model,
                        check_duplicates=False,
                        base_file=str(base_path),
                        additional_file=str(inc_path)
                    )
            
            # Extend base with current file (allows overrides)
            final_model = self.model_merger.extend(base_model, model)
        else:
            # Merge mode (no architecture blocks in included files)
            # Validate that all included files are partial definitions
            for inc_model, inc_has_arch, inc_path in included_models:
                if inc_has_arch:
                    if not has_arch:
                        raise ArchitectureExtensionRequiredError(str(inc_path))
                    raise PartialDefinitionRequiredError(str(inc_path), "merge mode")
            
            # Validate that current file has architecture block (required in merge mode)
            if not has_arch:
                raise ValueError(
                    f"Main file '{file_path}' must have an architecture block "
                    "when including files in merge mode."
                )
            
            # Merge all included files into current model
            final_model = model
            for inc_model, inc_has_arch, inc_path in included_models:
                final_model = self.model_merger.merge(
                    final_model, inc_model,
                    check_duplicates=True,
                    base_file=str(file_path),
                    additional_file=str(inc_path)
                )
        
        return final_model, has_arch


# Global parser instance for backward compatibility
_parser = ISAParser()


def parse_isa_file(file_path: str) -> ISASpecification:
    """Parse an ISA specification file and return the model.
    
    This is the main entry point for backward compatibility.
    
    Args:
        file_path: Path to the ISA file
        
    Returns:
        Parsed ISASpecification model
    """
    return _parser.parse_file(file_path)

