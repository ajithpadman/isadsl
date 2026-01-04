"""Assembly syntax preprocessing for textX compatibility.

Note: This uses regex to work around textX's limitation with parsing
strings containing braces. The regex is necessary because:
1. textX's string parser may fail on certain patterns like "word{"
2. We need to extract these strings before parsing, then inject them back
3. This is a textX limitation, not something we can avoid with object model access

However, after parsing, we use the textX object model to access assembly_syntax.
"""

import re
import tempfile
from pathlib import Path
from typing import Dict, Optional


class AssemblySyntaxProcessor:
    """Handles preprocessing of assembly_syntax strings that contain braces.
    
    This is a workaround for textX's parsing limitations. After preprocessing,
    we use the textX object model to access the assembly_syntax values.
    """
    
    @staticmethod
    def preprocess_content(content: str) -> tuple[str, Dict[str, str]]:
        """Preprocess content to extract problematic assembly_syntax strings.
        
        Args:
            content: File content that may contain assembly_syntax with braces
            
        Returns:
            Tuple of (modified_content, assembly_syntax_map)
            where assembly_syntax_map maps instruction names to their syntax strings
        """
        lines = content.split('\n')
        assembly_syntax_map: Dict[str, str] = {}
        current_instruction: Optional[str] = None
        modified_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Track current instruction using regex (necessary for line-by-line processing)
            # This regex identifies instruction declarations
            instr_match = re.match(r'\s*instruction\s+(\w+)\s*\{', line)
            if instr_match:
                current_instruction = instr_match.group(1)
                modified_lines.append(line)
                i += 1
                continue
            
            # Check for assembly_syntax line
            if 'assembly_syntax' in line and ':' in line:
                # Extract the string content using regex
                # This regex is necessary because we need to extract the string
                # before textX parses it (to work around textX's brace parsing issue)
                asm_match = re.search(r'assembly_syntax\s*:\s*"([^"]*)"', line)
                if asm_match:
                    asm_content = asm_match.group(1)
                    # Check if it has problematic pattern (word immediately followed by {)
                    # This regex detects the problematic pattern
                    if re.search(r'[A-Za-z_][A-Za-z0-9_]*\{', asm_content):
                        # Store it and skip this line
                        if current_instruction:
                            assembly_syntax_map[current_instruction] = asm_content
                        # Don't add this line to modified_lines
                        i += 1
                        continue
            
            # Reset current_instruction when we see a closing brace
            if line.strip() == '}' and current_instruction:
                current_instruction = None
            
            modified_lines.append(line)
            i += 1
        
        modified_content = '\n'.join(modified_lines)
        return modified_content, assembly_syntax_map
    
    @staticmethod
    def inject_assembly_syntax(textx_model: any, assembly_syntax_map: Dict[str, str]) -> None:
        """Inject assembly_syntax strings back into textX model.
        
        After textX parsing, we inject the extracted strings back into the model.
        This allows us to access them via the textX object model later.
        
        Args:
            textx_model: The parsed textX model
            assembly_syntax_map: Map of instruction names to syntax strings
        """
        if hasattr(textx_model, 'instructions') and hasattr(textx_model.instructions, 'instructions'):
            for instr_tx in textx_model.instructions.instructions:
                instr_name = instr_tx.mnemonic if hasattr(instr_tx, 'mnemonic') else None
                if instr_name and instr_name in assembly_syntax_map:
                    # Set the assembly_syntax directly as a string
                    # The converter will extract it using str() which will work
                    setattr(instr_tx, 'assembly_syntax', assembly_syntax_map[instr_name])

