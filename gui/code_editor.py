from PySide6 import QtWidgets, QtGui, QtCore

class LineNumberArea(QtWidgets.QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QtCore.QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)

class CodeEditor(QtWidgets.QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        
        # Update signal connections for PySide6
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        
        self.updateLineNumberAreaWidth(0)
        
        # Make editor read-only
        self.setReadOnly(True)
        
        # Setup context menu
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Add copy button with different icon
        self.copy_button = QtWidgets.QPushButton(self)
        self.copy_icon = self.style().standardIcon(QtWidgets.QStyle.SP_FileIcon)
        self.copy_done_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DialogYesButton)
        self.copy_button.setIcon(self.copy_icon)
        self.copy_button.setToolTip("Click to copy all code")
        self.copy_button.clicked.connect(self.copy_all)
        self.copy_button.setCursor(QtCore.Qt.PointingHandCursor)
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: none;
                border-radius: 3px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
        """)

    def show_context_menu(self, position):
        menu = QtWidgets.QMenu()
        copy_action = menu.addAction("Copy")
        select_all_action = menu.addAction("Select All")
        
        copy_action.triggered.connect(self.copy)
        select_all_action.triggered.connect(self.selectAll)
        
        menu.exec_(self.mapToGlobal(position))

    def keyPressEvent(self, event):
        # Update key sequence matches for PySide6
        if event.matches(QtGui.QKeySequence.Copy) or \
           event.matches(QtGui.QKeySequence.SelectAll):
            super().keyPressEvent(event)

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        # Replace width() with horizontalAdvance()
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QtCore.QRect(cr.left(), cr.top(),
                                                    self.line_number_area_width(), cr.height()))
        # Position copy button in top right corner with padding
        button_size = 24
        padding = 5
        self.copy_button.setFixedSize(button_size, button_size)
        self.copy_button.move(
            self.width() - button_size - padding,
            padding
        )

    def lineNumberAreaPaintEvent(self, event):
        painter = QtGui.QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QtGui.QColor("#1e1e1e"))
        
        # Set same font as editor
        painter.setFont(self.font())

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        offset = self.contentOffset()
        top = self.blockBoundingGeometry(block).translated(offset).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QtGui.QColor("#858585"))
                painter.drawText(0, int(top), self.line_number_area.width(),
                               self.fontMetrics().height(),
                               QtCore.Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def copy_all(self):
        """Select all text and copy to clipboard"""
        self.selectAll()
        self.copy()
        self.textCursor().clearSelection()
        
        # Change icon and style for visual feedback
        self.copy_button.setIcon(self.copy_done_icon)
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #2d6d2d;  /* Green tint for success */
                border: none;
                border-radius: 3px;
                padding: 4px;
            }
        """)
        
        # Reset after delay
        QtCore.QTimer.singleShot(800, lambda: self.reset_copy_button())

    def reset_copy_button(self):
        """Reset button to original state"""
        self.copy_button.setIcon(self.copy_icon)
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: none;
                border-radius: 3px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
        """)