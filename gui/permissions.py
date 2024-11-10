from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QProgressBar
from PyQt5.QtCore import Qt, QTimer
import os
import sys
import keyboard

class PermissionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Permission Required")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        # Instructions
        self.instructions = QLabel(
            "This app needs the following permissions:\n\n"
            "1. Input Monitoring\n"
            "2. Accessibility\n\n"
            "Steps:\n"
            "1. Click 'Open Settings' below\n"
            "2. Click the lock icon to make changes\n"
            "3. Find and enable this app in both sections\n"
            "4. Restart the app when done\n\n"
            "Note: You may need to quit and reopen the app\n"
            "after granting permissions."
        )
        self.instructions.setWordWrap(True)
        layout.addWidget(self.instructions)
        
        # Progress indicator
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Infinite progress
        layout.addWidget(self.progress)
        
        # Status label
        self.status = QLabel("Waiting for permissions...")
        layout.addWidget(self.status)
        
        # Buttons
        self.settings_btn = QPushButton("Open Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        layout.addWidget(self.settings_btn)
        
        self.quit_btn = QPushButton("Quit and Reopen")
        self.quit_btn.clicked.connect(self.quit_app)
        layout.addWidget(self.quit_btn)
        
        # Add restart button
        self.restart_btn = QPushButton("Restart Application")
        self.restart_btn.clicked.connect(self.restart_app)
        layout.addWidget(self.restart_btn)
        
        self.setLayout(layout)
        
        # Check permissions periodically
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_permission)
        self.check_timer.start(2000)  # Check every 2 seconds
    
    def open_settings(self):
        """Open both required permission panels"""
        if sys.platform == 'darwin':
            # Open Input Monitoring
            os.system("open 'x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent'")
            # Wait a bit before opening next panel
            QTimer.singleShot(1000, self.open_accessibility_settings)
    
    def open_accessibility_settings(self):
        """Open Accessibility settings panel"""
        if sys.platform == 'darwin':
            os.system("open 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'")
    
    def quit_app(self):
        os.execl(sys.executable, sys.executable, *sys.argv)
    
    def restart_app(self):
        """Restart the application"""
        self.accept()  # Close dialog
        os.execl(sys.executable, sys.executable, *sys.argv)
        
    def check_permission(self):
        try:
            keyboard.hook(lambda _: None)
            keyboard.unhook_all()
            self.status.setText("✅ Permissions granted!")
            self.progress.setRange(0, 100)
            self.progress.setValue(100)
            QTimer.singleShot(1000, self.accept)  # Auto-close after success
        except:
            self.status.setText("⚠️ Waiting for permissions...")