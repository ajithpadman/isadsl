"""Custom exceptions for ISA DSL parsing."""


class ISAError(Exception):
    """Base exception for ISA DSL errors."""
    pass


class CircularDependencyError(ISAError):
    """Raised when a circular dependency is detected in included files."""
    
    def __init__(self, file_chain):
        self.file_chain = file_chain
        chain_str = " -> ".join(str(f) for f in file_chain)
        super().__init__(f"Circular dependency detected: {chain_str}")


class DuplicateDefinitionError(ISAError):
    """Raised when duplicate definitions are found in merge mode."""
    
    def __init__(self, name, locations):
        self.name = name
        self.locations = locations
        locations_str = ", ".join([f"{f} (line {l})" if l else f"{f}" for f, l in locations])
        super().__init__(f"Duplicate definition '{name}' found in: {locations_str}")


class MultipleInheritanceError(ISAError):
    """Raised when more than one included file has an architecture block."""
    
    def __init__(self, files_with_architecture):
        self.files_with_architecture = files_with_architecture
        files_str = ", ".join(files_with_architecture)
        super().__init__(f"Multiple inheritance not allowed. Architecture blocks found in: {files_str}")


class ArchitectureExtensionRequiredError(ISAError):
    """Raised when an included file has an architecture block but the including file doesn't."""
    
    def __init__(self, included_file):
        self.included_file = included_file
        super().__init__(f"Included file '{included_file}' has an architecture block, but the including file does not. Architecture extension is required.")


class PartialDefinitionRequiredError(ISAError):
    """Raised when in inheritance mode, a non-base included file has an architecture block."""
    
    def __init__(self, file_path, base_file):
        self.file_path = file_path
        self.base_file = base_file
        super().__init__(f"In inheritance mode, file '{file_path}' must be a partial definition (no architecture block). Base architecture is defined in '{base_file}'.")

