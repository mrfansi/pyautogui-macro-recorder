import shutil
import threading
from PySide6 import QtWidgets, QtGui, QtCore
from pathlib import Path
import logging
import time
import sys

import pyautogui
try:
    from .settings_dialog import SettingsDialog
    from .syntax_highlighter import PythonHighlighter
    from .code_editor import CodeEditor
except ImportError:
    from settings_dialog import SettingsDialog
    from syntax_highlighter import PythonHighlighter
    from code_editor import CodeEditor

class MainWindow(QtWidgets.QMainWindow):
    # Define signals with new syntax
    playbackFinishedSignal = QtCore.Signal()
    playbackErrorSignal = QtCore.Signal() 
    failSafeSignal = QtCore.Signal()
    logSignal = QtCore.Signal(str)
    
    def __init__(self, recorder, player, settings):
        super().__init__()
        
        # Add debug logging
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        
        # Verify recorder
        if recorder is None:
            raise RuntimeError("Recorder object is None")
            
        try:
            # Test recorder methods exist
            if not hasattr(recorder, 'start') or not hasattr(recorder, 'stop'):
                raise RuntimeError("Recorder missing required methods")
                
            self.recorder = recorder
            self.player = player
            self.settings = settings
            
            self.logger.debug("Recorder initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize recorder: {e}")
            QtWidgets.QMessageBox.critical(self, "Error", 
                f"Failed to initialize recorder:\n{str(e)}")
            sys.exit(1)
        
        # Application states
        self.is_recording = False
        self.is_playing = False
        self.recording_active = False
        self.shortcut_bindings = []
        
        self.setWindowTitle("PyAutoGUI Macro Recorder")
        self.setGeometry(100, 100, 1200, 800)
        
        # Connect signals first
        self.playbackFinishedSignal.connect(self.playback_finished)
        self.playbackErrorSignal.connect(self.playback_error)
        self.failSafeSignal.connect(self.handle_failsafe)
        self.logSignal.connect(self.add_log)
        
        # Then setup UI and load shortcuts
        self.setup_ui()
        self.load_shortcuts()

    def setup_ui(self):
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setSpacing(0)  # Reduce spacing between elements
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Main horizontal split
        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        main_splitter.setHandleWidth(1)  # Thinner splitter handle
        main_layout.addWidget(main_splitter)
        
        # Left side container (buttons + code)
        left_container = QtWidgets.QWidget()
        left_container.setContentsMargins(0, 0, 0, 0)
        left_layout = QtWidgets.QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)  # Reduce spacing between elements
        
        # Button frame with better alignment
        button_frame = QtWidgets.QFrame()
        button_frame.setFrameStyle(QtWidgets.QFrame.NoFrame)
        button_layout = QtWidgets.QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 0, 0, 5)  # Add small bottom margin only
        button_layout.setSpacing(5)  # Consistent spacing between buttons
        
        # Add buttons
        self.save_button = QtWidgets.QPushButton("💾 Save")
        self.save_button.setFixedHeight(40)
        button_layout.addWidget(self.save_button)
        
        self.play_button = QtWidgets.QPushButton("▶ Play")
        self.play_button.setFixedHeight(40)
        button_layout.addWidget(self.play_button)
        
        self.record_button = QtWidgets.QPushButton("● Record")
        self.record_button.setFixedHeight(40)
        self.record_button.setCheckable(True)
        button_layout.addWidget(self.record_button)
        
        settings_button = QtWidgets.QPushButton("⚙ Settings")
        settings_button.setFixedHeight(40)
        settings_button.clicked.connect(self.show_settings)
        button_layout.addWidget(settings_button)
        
        left_layout.addWidget(button_frame)
        
        # Code editor container for better alignment
        code_container = QtWidgets.QFrame()
        code_container.setFrameStyle(QtWidgets.QFrame.NoFrame)
        code_container.setContentsMargins(0, 0, 0, 0)
        code_layout = QtWidgets.QVBoxLayout(code_container)
        code_layout.setContentsMargins(0, 0, 0, 0)
        code_layout.setSpacing(0)
        
        # Code text area with proper styling
        self.code_text = CodeEditor()
        self.syntax_highlighter = PythonHighlighter(self.code_text.document())
        
        # Apply font and styling
        font = self.get_monospace_font()
        self.code_text.setFont(font)
        self.code_text.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                selection-background-color: #264f78;
                border: 1px solid #2d2d2d;
                border-radius: 4px;
            }
        """)
        
        code_layout.addWidget(self.code_text)
        left_layout.addWidget(code_container)
        
        # Add left container to splitter
        main_splitter.addWidget(left_container)
        
        # Right side container with matching style
        right_container = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_container)
        right_layout.setContentsMargins(5, 0, 0, 0)  # Add left margin for separation
        right_layout.setSpacing(5)
        
        # Gallery section
        gallery_label = QtWidgets.QLabel("Screenshots")
        right_layout.addWidget(gallery_label)
        
        self.gallery_scroll_area = QtWidgets.QScrollArea()
        self.gallery_scroll_area.setWidgetResizable(True)
        self.gallery_scroll_area.setMinimumHeight(200)  # Set minimum height
        
        self.gallery_content = QtWidgets.QWidget()
        self.gallery_layout = QtWidgets.QGridLayout(self.gallery_content)
        self.gallery_scroll_area.setWidget(self.gallery_content)
        right_layout.addWidget(self.gallery_scroll_area)
        
        # Log section
        log_label = QtWidgets.QLabel("Log:")
        right_layout.addWidget(log_label)
        
        self.log_text = QtWidgets.QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)  # Limit log height
        right_layout.addWidget(self.log_text)
        
        # Add right container to splitter
        main_splitter.addWidget(right_container)
        
        # Set better initial splitter sizes (65% left, 35% right)
        main_splitter.setSizes([650, 350])
        
        # Connect signals and load shortcuts
        self.connect_signals()
        self.load_initial_state()

    def connect_signals(self):
        """Connect all button signals"""
        self.save_button.clicked.connect(self.save_project)
        self.play_button.clicked.connect(self.start_playback)
        self.record_button.clicked.connect(self.toggle_recording)

    def load_initial_state(self):
        """Load initial states and shortcuts"""
        # Load shortcuts
        save_shortcut = self.settings.value('shortcuts/save', 
                                          QtGui.QKeySequence(QtGui.QKeySequence.Save).toString())
        play_shortcut = self.settings.value('shortcuts/play', 'Command+Option+F')
        record_shortcut = self.settings.value('shortcuts/record', 'Command+Option+C')
        
        # Set tooltips
        self.save_button.setToolTip(f"Save macro ({save_shortcut})")
        self.play_button.setToolTip(f"Play macro ({play_shortcut})")
        self.record_button.setToolTip(f"Toggle recording ({record_shortcut})")

    def update_gallery(self):
        """Update gallery with adaptive grid"""
        # Clear gallery
        for i in reversed(range(self.gallery_layout.count())):
            widget = self.gallery_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        
        # Load images
        images = sorted(Path(self.recorder.screens_dir).glob("*.png"), 
                       key=lambda x: int(x.stem))
        
        if not images:
            return
        
        # Get current gallery width - fix width calculation
        try:
            gallery_width = self.gallery_scroll_area.width() - 20  # Use scroll area width instead
        except AttributeError:
            gallery_width = 200  # Fallback width
        
        # Calculate optimal thumbnail size and number of columns
        desired_columns = max(1, gallery_width // 200)
        thumbnail_width = int((gallery_width - (desired_columns + 1) * 10) // desired_columns)
        
        # Place images in grid
        for i, img_path in enumerate(images):
            try:
                row = i // desired_columns
                col = i % desired_columns
                
                # Load and resize image
                img = QtGui.QImage(str(img_path))
                aspect_ratio = float(img.height()) / float(img.width())
                thumbnail_height = int(thumbnail_width * aspect_ratio)
                img = img.scaled(
                    int(thumbnail_width), 
                    int(thumbnail_height), 
                    QtCore.Qt.KeepAspectRatio, 
                    QtCore.Qt.SmoothTransformation
                )
                
                # Create label for image
                label_img = QtWidgets.QLabel()
                label_img.setPixmap(QtGui.QPixmap.fromImage(img))
                label_img.setAlignment(QtCore.Qt.AlignCenter)
                label_img.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
                label_img.customContextMenuRequested.connect(
                    lambda pos, path=img_path: self.show_screenshot_menu(pos, path)
                )
                
                self.gallery_layout.addWidget(label_img, row, col)
                
            except Exception as e:
                print(f"Error loading image {img_path}: {str(e)}")
                logging.error(f"Gallery error: {str(e)}")

    def show_screenshot_menu(self, pos, screenshot_path):
        """Show context menu for screenshot"""
        menu = QtWidgets.QMenu()
        update_action = menu.addAction("Update screenshot (Ctrl+V)")
        update_action.triggered.connect(lambda: self.update_screenshot_from_clipboard(screenshot_path))
        new_action = menu.addAction("Take new area screenshot (Ctrl+N)")
        new_action.triggered.connect(lambda: self.take_new_screenshot(screenshot_path))
        menu.exec_(self.mapToGlobal(pos))
    
    def update_screenshot_from_clipboard(self, screenshot_path=None):
        """Update screenshot with image from clipboard"""
        try:
            path = screenshot_path or self.current_screenshot_path
            if not path:
                return
                
            # Get image from clipboard
            clipboard = QtWidgets.QApplication.clipboard()
            img = clipboard.image()
            
            if img.isNull():
                QtWidgets.QMessageBox.warning(self, "Warning", "Clipboard does not contain an image")
                return
                
            # Save new image
            img.save(str(path))
            
            # Update gallery
            self.update_gallery()
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to update screenshot:\n{str(e)}")
    
    def take_new_screenshot(self, screenshot_path=None):
        """Take new screenshot of selected area"""
        try:
            path = screenshot_path or self.current_screenshot_path
            if not path:
                return
                
            # Minimize window while taking screenshot
            self.showMinimized()
            QtCore.QTimer.singleShot(500, lambda: self._take_screenshot(path))
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to create screenshot:\n{str(e)}")
    
    def _take_screenshot(self, path):
        try:
            # Create screenshot of selected area
            screenshot = pyautogui.screenshot(region=pyautogui.select_area())
            screenshot.save(path)
            
            # Restore window and update gallery
            self.showNormal()
            self.update_gallery()
            
        except Exception as e:
            self.showNormal()
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to create screenshot:\n{str(e)}")
    
    def start_playback(self):
        if not self.is_playing and self.code_text.toPlainText().strip():
            self.is_playing = True
            self.update_button_states()
            
            try:
                code = self.code_text.toPlainText()
                if not code.strip():
                    return
                
                def play_thread():
                    try:
                        self.player.play(code)
                        self.playbackFinishedSignal.emit()
                        self.logSignal.emit(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - INFO - Macro playback finished")
                    except pyautogui.FailSafeException:
                        self.failSafeSignal.emit()
                    except Exception as e:
                        print(f"Error during playback: {str(e)}")
                        self.playbackErrorSignal.emit()
                
                thread = threading.Thread(target=play_thread, daemon=True)
                thread.start()
                
            except Exception as e:
                print(f"Error starting playback: {str(e)}")
                self.is_playing = False
                self.update_button_states()
    
    @QtCore.Slot()
    def playback_finished(self):
        """Playback finished handler"""
        self.is_playing = False
        self.update_button_states()
    
    @QtCore.Slot()
    def playback_error(self):
        """Playback error handler"""
        self.is_playing = False
        self.update_button_states()
        QtWidgets.QMessageBox.critical(self, "Error", "An error occurred while playing the macro")
    
    @QtCore.Slot()
    def handle_failsafe(self):
        """PyAutoGUI failsafe handler"""
        self.is_playing = False
        self.update_button_states()
        QtWidgets.QMessageBox.warning(
            self,
            "Interrupted",
            "Script execution interrupted!\n\n"
            "Reason: Mouse moved to screen corner (PyAutoGUI failsafe).\n\n"
            "To continue, move mouse away from the corner and run the script again."
        )
    
    def toggle_recording(self):
        """Toggle recording state"""
        try:
            if not self.recording_active:
                self.logger.debug("Starting recording...")
                
                # Verify recorder is still valid
                if not hasattr(self, 'recorder') or self.recorder is None:
                    raise RuntimeError("Recorder not available")
                    
                # Execute recorder.start() in try block
                try:
                    self.recording_active = True
                    self.record_button.setText("■ Stop")
                    self.record_button.setStyleSheet("QPushButton { color: red; }")
                    self.recorder.start()
                    self.logger.debug("Recording started successfully")
                    self.add_log("Recording started...")
                except Exception as e:
                    self.logger.error(f"Failed to start recording: {e}")
                    raise RuntimeError(f"Failed to start recording: {e}")
                    
            else:
                self.logger.debug("Stopping recording...")
                self.add_log("Stopping recording...")
                self.recording_active = False
                self.record_button.setText("● Record")
                self.record_button.setStyleSheet("")
                
                try:
                    recorded_code = self.recorder.stop()
                    if recorded_code:
                        self.code_text.setPlainText(recorded_code)
                        self.update_gallery()
                        self.add_log("Recording stopped, code generated.")
                    else:
                        self.add_log("No actions recorded.", "WARNING")
                except Exception as e:
                    self.add_log(f"Error stopping recording: {str(e)}", "ERROR")
                    raise
                    
        except Exception as e:
            self.logger.error(f"Recording error: {e}")
            # Reset state on any error
            self.recording_active = False
            self.record_button.setText("● Record")
            self.record_button.setChecked(False)
            self.record_button.setStyleSheet("")
            self.add_log(f"Recording error: {str(e)}", "ERROR")
            QtWidgets.QMessageBox.critical(self, "Error", f"Recording failed: {str(e)}")
        
        finally:
            self.update_button_states()

    def update_button_states(self):
        """Update button states based on current activity"""
        recording_or_playing = self.recording_active or self.is_playing
        self.play_button.setEnabled(not recording_or_playing)
        self.save_button.setEnabled(not recording_or_playing)
        self.record_button.setEnabled(not self.is_playing)
            
    def save_project(self):
        if not self.code_text.toPlainText().strip():
            QtWidgets.QMessageBox.warning(self, "Warning", "No code to save!")
            return
            
        project_name, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save project",
            "./projects",
            "Python files (*.py)"
        )
        
        if not project_name:
            return
            
        try:
            project_dir = Path(project_name).parent
            project_name = Path(project_name).stem
            project_path = project_dir / project_name
            project_path.mkdir(parents=True, exist_ok=True)
            
            # Create directory for screenshots
            screens_path = project_path / "screens"
            screens_path.mkdir(exist_ok=True)
            
            # Copy screenshots
            for screenshot in Path(self.recorder.screens_dir).glob("*.png"):
                shutil.copy2(screenshot, screens_path)
            
            # Save macro code
            main_file = project_path / "main.py"
            with open(main_file, 'w', encoding='utf-8') as f:
                f.write(self.code_text.toPlainText())
            
            QtWidgets.QMessageBox.information(
                self, 
                "Success", 
                f"Project saved to:\n{project_path}\n\n"
                f"To run, use file:\n{main_file}"
            )
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save project:\n{str(e)}")
    
    def add_log(self, message, level='INFO'):
        """Add message to log"""
        self.log_text.appendPlainText(message)
    
    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.settings, self)
        if (dialog.exec_() == QtWidgets.QDialog.Accepted):
            self.load_shortcuts()

    def load_shortcuts(self):
        """Load shortcuts from settings with QShortcut"""
        # Clear existing shortcuts
        for shortcut in self.shortcut_bindings:
            shortcut.setEnabled(False)
        self.shortcut_bindings.clear()
        
        # Create new shortcuts
        save_seq = QtGui.QKeySequence(self.settings.value('shortcuts/save', 
                                    QtGui.QKeySequence(QtGui.QKeySequence.Save).toString()))
        play_seq = QtGui.QKeySequence(self.settings.value('shortcuts/play', 'F5'))
        record_seq = QtGui.QKeySequence(self.settings.value('shortcuts/record', 'F6'))
        
        # Bind shortcuts - Change QtWidgets.QShortcut to QtGui.QShortcut
        save_shortcut = QtGui.QShortcut(save_seq, self)
        save_shortcut.activated.connect(self.save_project)
        self.shortcut_bindings.append(save_shortcut)
        
        play_shortcut = QtGui.QShortcut(play_seq, self)
        play_shortcut.activated.connect(self.start_playback)
        self.shortcut_bindings.append(play_shortcut)
        
        record_shortcut = QtGui.QShortcut(record_seq, self)
        record_shortcut.activated.connect(self.toggle_recording)
        self.shortcut_bindings.append(record_shortcut)
        
        # Update tooltips
        if hasattr(self, 'save_button'):
            self.save_button.setToolTip(f"Save macro ({save_seq.toString()})")
            self.play_button.setToolTip(f"Play macro ({play_seq.toString()})")
            self.record_button.setToolTip(f"Toggle recording ({record_seq.toString()})")

    def get_monospace_font(self):
        preferred_fonts = [
            "SF Mono",
            "Consolas",
            "DejaVu Sans Mono",
            "Menlo",
            "Monaco",
            "Fira Code",
            "Liberation Mono",
            "Courier New"
        ]
        
        for font_name in preferred_fonts:
            font = QtGui.QFont(font_name)
            if font.exactMatch():
                font.setPointSize(11)
                font.setFixedPitch(True)
                return font
        
        font = QtGui.QFont("Monospace")
        font.setPointSize(11)
        font.setFixedPitch(True)
        font.setStyleHint(QtGui.QFont.Monospace)
        return font