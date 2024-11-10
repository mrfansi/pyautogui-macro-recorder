import re
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.formats = {}
        
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))  # VSCode blue
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            "and", "as", "assert", "break", "class", "continue", "def",
            "del", "elif", "else", "except", "False", "finally", "for",
            "from", "global", "if", "import", "in", "is", "lambda", "None",
            "nonlocal", "not", "or", "pass", "raise", "return", "True",
            "try", "while", "with", "yield"
        ]
        self.formats["keyword"] = (keyword_format, r'\b(?:' + '|'.join(keywords) + r')\b')
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))  # VSCode orange
        self.formats["string"] = (string_format, r'"[^"\\]*(\\.[^"\\]*)*"|\'[^\'\\]*(\\.[^\'\\]*)*\'')
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#B5CEA8"))  # VSCode light green
        self.formats["number"] = (number_format, r'\b[0-9]+\b')
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))  # VSCode green
        self.formats["comment"] = (comment_format, r'#[^\n]*')
        
        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#DCDCAA"))  # VSCode yellow
        function_format.setFontWeight(QFont.Bold)
        self.formats["function"] = (function_format, r'\b[A-Za-z0-9_]+(?=\s*\()')

    def highlightBlock(self, text):
        for format_type, (format, pattern) in self.formats.items():
            index = 0
            while index < len(text):
                match = re.search(pattern, text[index:])
                if not match:
                    break
                start = match.start() + index
                length = match.end() - match.start()
                self.setFormat(start, length, format)
                index = start + length