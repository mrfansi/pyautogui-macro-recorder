from PySide6.QtWidgets import (QDialog, QPushButton, QScrollArea, QWidget, 
                             QVBoxLayout, QHBoxLayout, QGridLayout, QLabel)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PIL import Image
from pathlib import Path
import math

class ImageGallery(QDialog):
    def __init__(self, parent, image_dir):
        super().__init__(parent)
        self.setWindowTitle("Screenshot Gallery")
        self.resize(800, 600)
        self.setModal(True)

        # Create main layout
        layout = QVBoxLayout(self)

        # Create close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button, alignment=Qt.AlignCenter)

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        # Create container widget for the grid
        container = QWidget()
        self.grid_layout = QGridLayout(container)
        scroll.setWidget(container)

        # Load and display images
        self.load_images(image_dir)

        # Center the window relative to the parent
        self.center_window(parent)

    def center_window(self, parent):
        """Center the gallery window relative to the parent window"""
        parent_geo = parent.geometry()
        geo = self.geometry()
        
        x = parent_geo.x() + (parent_geo.width() - geo.width()) // 2
        y = parent_geo.y() + (parent_geo.height() - geo.height()) // 2
        
        self.move(x, y)

    def load_images(self, image_dir):
        images = sorted(Path(image_dir).glob("*.png"), 
                       key=lambda x: int(x.stem))
        columns = 3
        
        for i, img_path in enumerate(images):
            row = i // columns
            col = i % columns
            
            try:
                # Create frame for image and caption
                frame = QWidget()
                frame_layout = QVBoxLayout(frame)
                
                # Load and scale the image
                pixmap = QPixmap(str(img_path))
                scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                # Display image and caption
                img_label = QLabel()
                img_label.setPixmap(scaled_pixmap)
                frame_layout.addWidget(img_label, alignment=Qt.AlignCenter)
                
                text_label = QLabel(img_path.name)
                text_label.setWordWrap(True)
                frame_layout.addWidget(text_label, alignment=Qt.AlignCenter)
                
                self.grid_layout.addWidget(frame, row, col)
            except Exception as e:
                print(f"Error loading image {img_path}: {e}")

if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Create test directory with sample images if needed
    test_dir = Path("test_screens")
    test_dir.mkdir(exist_ok=True)
    
    # Create a sample image if directory is empty
    if not list(test_dir.glob("*.png")):
        img = Image.new('RGB', (100, 100), color='red')
        img.save(test_dir / "1.png")
    
    # Create a dummy parent window
    from PySide6.QtWidgets import QMainWindow
    parent = QMainWindow()
    
    gallery = ImageGallery(parent, test_dir)
    gallery.show()
    
    sys.exit(app.exec())