from PyQt5 import QtWidgets, QtCore
from recorder import Recorder
from player import ActionPlayer
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
    
    return app.exec_()

if __name__ == "__main__":
    main()