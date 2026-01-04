"""Include statement processing for ISA DSL.

Note: Include extraction requires regex because:
1. #include statements are pre-processed before textX parsing
2. They are not part of the textX grammar (they're meta-statements)
3. We need to extract them to resolve file dependencies before parsing
"""

import re
from pathlib import Path
from typing import List
from .comment_processor import CommentProcessor


class IncludeProcessor:
    """Handles #include statement extraction and path resolution."""
    
    def __init__(self, comment_processor: CommentProcessor):
        """Initialize with a comment processor.
        
        Args:
            comment_processor: CommentProcessor instance for stripping comments
        """
        self.comment_processor = comment_processor
    
    def extract_includes(self, content: str) -> List[str]:
        """Extract #include statements from file content.
        
        This requires regex because:
        - #include is a pre-processing directive, not part of the textX grammar
        - We need to extract includes before parsing to resolve dependencies
        - textX doesn't have built-in support for #include directives
        
        Args:
            content: File content that may contain #include statements
            
        Returns:
            List of include paths (as strings)
        """
        includes = []
        lines = content.split('\n')
        
        for line in lines:
            # Strip comments from line first
            stripped = self.comment_processor.strip_comments(line)
            stripped = stripped.strip()
            
            # Match #include "path" or #include 'path'
            # This regex is necessary because includes are pre-processed
            match = re.match(r'#include\s+["\']([^"\']+)["\']', stripped)
            if match:
                includes.append(match.group(1))
        
        return includes
    
    @staticmethod
    def resolve_include_path(include_path: str, including_file: Path) -> Path:
        """Resolve include path relative to the including file's directory.
        
        Args:
            include_path: Path from #include statement (may be relative or absolute)
            including_file: Path to the file containing the #include
            
        Returns:
            Resolved absolute path
        """
        include_path_obj = Path(include_path)
        
        if include_path_obj.is_absolute():
            return include_path_obj
        
        # Resolve relative to the including file's directory
        return (including_file.parent / include_path_obj).resolve()
    
    @staticmethod
    def remove_include_lines(content: str) -> str:
        """Remove all #include lines from content.
        
        This regex is necessary because:
        - #include statements are not part of the textX grammar
        - We need to remove them before passing content to textX
        
        Args:
            content: File content with #include statements
            
        Returns:
            Content with #include lines removed
        """
        # Remove include lines using regex (necessary for pre-processing)
        pattern = re.compile(r'#include\s+["\'][^"\']+["\'].*?$', re.MULTILINE)
        return pattern.sub('', content)
    
    def has_architecture_block(self, content: str) -> bool:
        """Check if file content contains an architecture block.
        
        This can be done by parsing with textX, but for quick detection
        during dependency resolution, we use a simple check.
        
        Args:
            content: File content to check
            
        Returns:
            True if content contains an architecture block
        """
        # Strip comments first
        stripped = self.comment_processor.strip_comments(content)
        # Look for 'architecture' keyword followed by ID and {
        # This regex is used for quick detection - could be replaced by parsing
        pattern = r'architecture\s+\w+\s*\{'
        return bool(re.search(pattern, stripped))

