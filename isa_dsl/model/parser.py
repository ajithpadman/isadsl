"""Parser for ISA DSL using textX.

This module is maintained for backward compatibility.
New code should use isa_parser.ISAParser or isa_parser.parse_isa_file.
"""

# Import from new parser for backward compatibility
from .isa_parser import ISAParser, parse_isa_file

# Re-export for backward compatibility
__all__ = ['parse_isa_file', 'ISAParser']
