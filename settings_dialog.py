from PyQt5 import QtWidgets, QtGui, QtCore

class StyledButton(QtWidgets.QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)

class ShortcutEdit(QtWidgets.QKeySequenceEdit):
    def __init__(self, default_sequence="", parent=None):
        super().__init__(parent)
        self.default_sequence = default_sequence
        if default_sequence:
            self.setKeySequence(QtGui.QKeySequence(default_sequence))

    def reset(self):
        """Reset to default shortcut"""
        self.setKeySequence(QtGui.QKeySequence(self.default_sequence))

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.shortcuts = {}
        
        # Update default shortcuts to be platform-agnostic
        self.default_shortcuts = {
            'save': QtGui.QKeySequence.Save,  # This will be Ctrl+S on Windows/Linux, Cmd+S on Mac
            'play': 'F5',
            'record': 'F6'
        }
        
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)
        self.always_new_record = None
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Header with styled appearance matching main app
        header_frame = QtWidgets.QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 15px;
                margin-bottom: 10px;
            }
            QLabel {
                font-size: 14px;
            }
        """)
        # header_layout = QtWidgets.QVBoxLayout(header_frame)
        
        # title = QtWidgets.QLabel("Application Settings")
        # title.setStyleSheet("font-size: 16px; font-weight: bold;")
        # header_layout.addWidget(title)
        
        layout.addWidget(header_frame)
        
        # Tabs with styling
        tab_widget = QtWidgets.QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
            }
            QTabBar::tab {
                border: 1px solid #cccccc;
                padding: 8px 15px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                border-bottom: none;
            }
        """)
        layout.addWidget(tab_widget)
        
        # General tab
        general_tab = QtWidgets.QWidget()
        tab_widget.addTab(general_tab, "General")
        general_layout = QtWidgets.QVBoxLayout(general_tab)
        
        # Recording options group
        record_group = QtWidgets.QGroupBox("Recording Options")
        record_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 12px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        general_layout.addWidget(record_group)
        
        record_layout = QtWidgets.QVBoxLayout(record_group)
        
        self.always_new_record = QtWidgets.QCheckBox("Always start new record")
        self.always_new_record.setToolTip("When enabled, recording will always start fresh without asking")
        record_layout.addWidget(self.always_new_record)
        
        general_layout.addStretch()
        
        # Shortcuts tab
        shortcuts_tab = QtWidgets.QWidget()
        tab_widget.addTab(shortcuts_tab, "Keyboard Shortcuts")
        shortcuts_layout = QtWidgets.QVBoxLayout(shortcuts_tab)
        
        # Info section with consistent styling
        info_frame = QtWidgets.QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 12px;
                margin-bottom: 10px;
            }
            QLabel {
                line-height: 1.5;
            }
        """)
        info_layout = QtWidgets.QVBoxLayout(info_frame)
        
        info_text = QtWidgets.QLabel(
            "Configure keyboard shortcuts for quick access to common actions.\n"
            "Click on a shortcut field and press the desired key combination."
        )
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        shortcuts_layout.addWidget(info_frame)
        
        # Shortcuts group
        group = QtWidgets.QGroupBox("Action Shortcuts")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 12px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QKeySequenceEdit {
                padding: 5px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background: white;
            }
        """)
        shortcuts_layout.addWidget(group)
        
        grid = QtWidgets.QGridLayout(group)
        grid.setSpacing(10)
        
        # Column headers with consistent styling
        header_style = """
            QLabel {
                font-weight: bold;
                padding: 5px;
                font-size: 13px;
            }
        """
        headers = ["Action", "Shortcut", "Reset"]
        for col, text in enumerate(headers):
            label = QtWidgets.QLabel(text)
            label.setStyleSheet(header_style)
            grid.addWidget(label, 0, col)
        
        # Add shortcut rows
        self.add_shortcut_row(grid, 1, "Save Record", "save")
        self.add_shortcut_row(grid, 2, "Play Record", "play")
        self.add_shortcut_row(grid, 3, "Start / Stop Record", "record")  # Update label to reflect toggle behavior
        
        # Reset all button
        reset_all = QtWidgets.QPushButton("Reset All")
        reset_all.clicked.connect(self.reset_all_shortcuts)
        shortcuts_layout.addWidget(reset_all, alignment=QtCore.Qt.AlignRight)
        
        # Dialog buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def add_shortcut_row(self, layout, row, label, key):
        layout.addWidget(QtWidgets.QLabel(label), row, 0)
        
        shortcut_edit = ShortcutEdit(
            self.settings.value(f'shortcuts/{key}', 
                              QtGui.QKeySequence(self.default_shortcuts[key]).toString())
        )
        self.shortcuts[key] = shortcut_edit
        layout.addWidget(shortcut_edit, row, 1)
        
        reset_btn = QtWidgets.QPushButton("Reset")
        reset_btn.setFixedWidth(70)
        reset_btn.clicked.connect(shortcut_edit.reset)
        layout.addWidget(reset_btn, row, 2)
        
    def reset_all_shortcuts(self):
        """Reset all shortcuts to defaults"""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Reset All Shortcuts",
            "Are you sure you want to reset all shortcuts to their default values?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            for key, edit in self.shortcuts.items():
                edit.reset()
            
    def load_settings(self):
        """Load settings from QSettings"""
        # Load existing shortcuts
        for key, edit in self.shortcuts.items():
            value = self.settings.value(
                f'shortcuts/{key}',
                self.default_shortcuts[key]
            )
            edit.setKeySequence(QtGui.QKeySequence(value))
            
        # Load general settings
        self.always_new_record.setChecked(
            self.settings.value('general/always_new_record', False, type=bool)
        )
            
    def accept(self):
        """Validate and save settings when dialog is accepted"""
        # Check for duplicate shortcuts
        used_shortcuts = {}
        for key, edit in self.shortcuts.items():
            shortcut = edit.keySequence().toString()
            if shortcut in used_shortcuts:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Duplicate Shortcut",
                    f"The shortcut '{shortcut}' is already used for '{used_shortcuts[shortcut]}}}'.\n"
                    "Please assign a different shortcut."
                )
                return
            used_shortcuts[shortcut] = key
            
        # Save settings
        for key, edit in self.shortcuts.items():
            self.settings.setValue(
                f'shortcuts/{key}',
                edit.keySequence().toString()
            )
        
        # Save general settings
        self.settings.setValue(
            'general/always_new_record',
            self.always_new_record.isChecked()
        )
        
        super().accept()