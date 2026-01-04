"""Comment processing utilities for ISA DSL.

Note: textX can be configured to ignore comments, but we need to strip them
before parsing because #include statements are pre-processed. This is the
only place where regex/string manipulation is necessary for comments.
"""


class CommentProcessor:
    """Handles stripping of single-line (//) and multi-line (/* */) comments."""
    
    @staticmethod
    def strip_comments(content: str) -> str:
        """Strip single-line (//) and multi-line (/* */) comments from content.
        
        This cannot be fully replaced with textX because:
        1. #include statements are pre-processed before textX parsing
        2. We need to strip comments to correctly identify #include statements
        3. textX comment handling happens during parsing, not pre-processing
        
        Args:
            content: File content with comments
            
        Returns:
            Content with comments removed
        """
        lines = content.split('\n')
        result_lines = []
        in_multiline = False
        
        for line in lines:
            if in_multiline:
                # Look for closing */
                end_pos = line.find('*/')
                if end_pos != -1:
                    # Found closing, add remaining part after */
                    in_multiline = False
                    remaining = line[end_pos + 2:]
                    if remaining.strip():
                        result_lines.append(remaining)
                # Otherwise, skip this line (still in multiline comment)
                continue
            
            # Look for /* and */ on the same line
            multiline_start = line.find('/*')
            if multiline_start != -1:
                multiline_end = line.find('*/', multiline_start + 2)
                if multiline_end != -1:
                    # Both on same line, remove the comment
                    before = line[:multiline_start]
                    after = line[multiline_end + 2:]
                    line = before + after
                else:
                    # Start of multiline comment
                    in_multiline = True
                    result_lines.append(line[:multiline_start].rstrip())
                    continue
            
            # Look for single-line comment
            single_comment_pos = line.find('//')
            if single_comment_pos != -1:
                # Check if // is inside a string
                in_string = False
                quote_char = None
                for i, char in enumerate(line):
                    if char in ('"', "'") and (i == 0 or line[i-1] != '\\'):
                        if not in_string:
                            in_string = True
                            quote_char = char
                        elif char == quote_char:
                            in_string = False
                            quote_char = None
                    elif char == '/' and i < len(line) - 1 and line[i+1] == '/' and not in_string:
                        single_comment_pos = i
                        break
                
                line = line[:single_comment_pos].rstrip()
            
            if line.strip() or not result_lines:  # Keep empty lines if they're meaningful
                result_lines.append(line)
        
        return '\n'.join(result_lines)

