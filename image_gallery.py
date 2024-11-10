import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from pathlib import Path
import math

class ImageGallery(tk.Toplevel):
    def __init__(self, parent, image_dir):
        super().__init__(parent)
        self.title("Screenshot Gallery")
        self.geometry("800x600")
        
        # Make the window modal
        self.transient(parent)
        self.grab_set()
        
        # Create a close button
        self.close_button = ttk.Button(
            self, 
            text="Close", 
            command=self.destroy
        )
        self.close_button.pack(pady=5)
        
        # Create a scrollable canvas
        self.canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Place elements
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Load and display images
        self.load_images(image_dir)
        
        # Center the window relative to the parent
        self.center_window(parent)
        
    def center_window(self, parent):
        """Center the gallery window relative to the parent window"""
        parent.update_idletasks()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        
        width = self.winfo_width()
        height = self.winfo_height()
        
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        self.geometry(f"+{x}+{y}")
        
    def load_images(self, image_dir):
        images = sorted(Path(image_dir).glob("*.png"), 
                       key=lambda x: int(x.stem))  # Sort by number
        columns = 3
        padding = 10
        
        for i, img_path in enumerate(images):
            row = i // columns
            col = i % columns
            
            # Create a frame for the image and caption
            frame = ttk.Frame(self.scrollable_frame)
            frame.grid(row=row, column=col, padx=padding, pady=padding)
            
            try:
                # Load and scale the image
                img = Image.open(img_path)
                img.thumbnail((200, 200))
                photo = ImageTk.PhotoImage(img)
                
                # Save a reference to PhotoImage
                frame.photo = photo
                
                # Display the image and caption
                label_img = ttk.Label(frame, image=photo)
                label_img.pack()
                
                label_text = ttk.Label(frame, text=img_path.name, wraplength=200)
                label_text.pack()
            except Exception as e:
                print(f"Error loading image {img_path}: {e}")