import sys
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton, QScrollArea, QWidget, QGridLayout, QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from pathlib import Path

class ImageGallery(QDialog):
    def __init__(self, parent, image_dir):
        super().__init__(parent)
        self.setWindowTitle("Screenshot Gallery")
        self.resize(800, 600)
        self.setModal(True)

        # Main layout
        layout = QVBoxLayout(self)

        # Close button
        self.close_button = QPushButton("Close", self)
        self.close_button.clicked.connect(self.accept)  # Change from self.close to self.accept
        layout.addWidget(self.close_button)

        # Scroll area
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        # Container widget for grid
        container = QWidget()
        self.grid_layout = QGridLayout(container)
        scroll.setWidget(container)

        # Load and display images
        self.load_images(image_dir)

        # Center window
        self.center_window(parent)

    def center_window(self, parent):
        """Center the gallery window relative to the parent window"""
        parent_geometry = parent.geometry()
        x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
        y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
        self.move(x, y)

    def load_images(self, image_dir):
        images = sorted(Path(image_dir).glob("*.png"),
                       key=lambda x: int(x.stem))
        columns = 3
        padding = 10

        for i, img_path in enumerate(images):
            row = i // columns
            col = i % columns

            try:
                # Create container for image and caption
                container = QWidget()
                container_layout = QVBoxLayout(container)

                # Load and scale image
                pixmap = QPixmap(str(img_path))
                scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)

                # Image label
                img_label = QLabel()
                img_label.setPixmap(scaled_pixmap)
                container_layout.addWidget(img_label)

                # Caption label
                text_label = QLabel(img_path.name)
                text_label.setWordWrap(True)
                text_label.setAlignment(Qt.AlignCenter)
                container_layout.addWidget(text_label)

                # Add to grid
                self.grid_layout.addWidget(container, row, col, 1, 1)

            except Exception as e:
                print(f"Error loading image {img_path}: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QDialog()
    main_window.setGeometry(100, 100, 800, 600)
    image_dir = "../screens"  # Replace with your image directory path
    gallery = ImageGallery(main_window, image_dir)
    gallery.show()  # Change from exec_() to show()
    main_window.show()
    sys.exit(app.exec_())