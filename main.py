from PySide6 import QtWidgets, QtCore
from libs.recorder import Recorder
from libs.player import ActionPlayer
from gui import MainWindow

def main():
    app = QtWidgets.QApplication([])
    
    # Initialize components
    recorder = Recorder()
    player = ActionPlayer()
    settings = QtCore.QSettings('PyAutoGUI-Macro', 'Recorder')
    
    # Create and show main window
    window = MainWindow(recorder, player, settings)
    window.show()
    
    return app.exec()  # Changed from exec_() to exec()

if __name__ == "__main__":
    main()