from termcolor import colored
import re
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.util import ClassNotFound


class TextFormatter:
    @staticmethod
    def highlight_code_blocks(text: str) -> str:
        """Highlight code blocks in the text using Pygments."""
        pattern = r"```(\w+)?\n(.*?)\n```"

        def replace_code_block(match):
            language = match.group(1) or ''
            code = match.group(2)

            try:
                if language:
                    lexer = get_lexer_by_name(language)
                else:
                    lexer = guess_lexer(code)
                return "\n" + highlight(code, lexer, TerminalFormatter()) + "\n"
            except ClassNotFound:
                try:
                    lexer = guess_lexer(code)
                    return "\n" + highlight(code, lexer, TerminalFormatter()) + "\n"
                except ClassNotFound:
                    return "\n" + code + "\n"

        return re.sub(pattern, replace_code_block, text, flags=re.DOTALL)

    @staticmethod
    def enhance_text_formatting(text: str) -> str:
        """Enhance text with additional formatting while preserving code blocks."""
        # Store code blocks
        code_blocks = {}
        placeholder_pattern = 'CODE_BLOCK_PLACEHOLDER_{}'
        triple_code_pattern = r'```(?:\w+)?\n.*?\n```'

        def store_code_block(match):
            placeholder = placeholder_pattern.format(len(code_blocks))
            code_blocks[placeholder] = match.group(0)
            return placeholder

        text = re.sub(triple_code_pattern, store_code_block,
                      text, flags=re.DOTALL)

        # Format lists
        text = TextFormatter._format_lists(text)

        # Format inline elements
        text = TextFormatter._format_inline_elements(text)

        # Format headers
        text = TextFormatter._format_headers(text)

        # Restore code blocks
        for placeholder, code_block in code_blocks.items():
            text = text.replace(placeholder, code_block)

        return text

    @staticmethod
    def _format_lists(text: str) -> str:
        """Format numbered lists and bullet points."""
        # Numbered lists
        number_pattern = r'^(\s*)(\d+\.)(\s+)(.+)$'

        def number_replace(match):
            indent, number, spacing, content = match.groups()
            return f"{indent}{colored(number, 'yellow', attrs=['bold'])}{spacing}{colored(content, 'white')}"
        text = re.sub(number_pattern, number_replace, text, flags=re.MULTILINE)

        # Bullet points
        bullet_pattern = r'^(\s*)[•\-\*](\s+)(.+)$'

        def bullet_replace(match):
            indent, spacing, content = match.groups()
            bullet = colored('•', 'yellow')
            return f"{indent}{colored(bullet, 'yellow', attrs=['bold'])}{spacing}{colored(content, 'white')}"
        text = re.sub(bullet_pattern, bullet_replace, text, flags=re.MULTILINE)

        return text

    @staticmethod
    def _format_inline_elements(text: str) -> str:
        """Format inline code, bold text, italics, and URLs."""
        # Inline code
        text = re.sub(r'`([^`]+)`',
                      lambda m: colored(m.group(1), 'green',
                                        'on_grey', attrs=['bold']),
                      text)

        # Bold text
        text = re.sub(r'\*\*([^*]+)\*\*',
                      lambda m: colored(m.group(1), attrs=['bold']),
                      text)

        # Italics
        text = re.sub(r'\*([^*]+)\*',
                      lambda m: colored(m.group(1), attrs=['dark']),
                      text)

        # URLs
        text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)',
                      lambda m: colored(m.group(1), 'blue',
                                        attrs=['underline']),
                      text)

        return text

    @staticmethod
    def _format_headers(text: str) -> str:
        """Format markdown headers."""
        return re.sub(r'^(#{1,6})\s+(.+)$',
                      lambda m: '\n' +
                      colored(m.group(2), 'white', attrs=[
                              'bold', 'underline']) + '\n',
                      text,
                      flags=re.MULTILINE)
