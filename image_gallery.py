import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from pathlib import Path
import math

class ImageGallery(tk.Toplevel):
    def __init__(self, parent, image_dir):
        super().__init__(parent)
        self.title("Галерея скриншотов")
        self.geometry("800x600")
        
        # Делаем окно модальным
        self.transient(parent)
        self.grab_set()
        
        # Создаем кнопку закрытия
        self.close_button = ttk.Button(
            self, 
            text="Закрыть", 
            command=self.destroy
        )
        self.close_button.pack(pady=5)
        
        # Создаем холст с прокруткой
        self.canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Размещаем элементы
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Загружаем и отображаем изображения
        self.load_images(image_dir)
        
        # Центрируем окно относительно родителя
        self.center_window(parent)
        
    def center_window(self, parent):
        """Центрирует окно галереи относительно родительского окна"""
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
                       key=lambda x: int(x.stem))  # Сортировка по номеру
        columns = 3
        padding = 10
        
        for i, img_path in enumerate(images):
            row = i // columns
            col = i % columns
            
            # Создаем фрейм для изображения и подписи
            frame = ttk.Frame(self.scrollable_frame)
            frame.grid(row=row, column=col, padx=padding, pady=padding)
            
            try:
                # Загружаем и масштабируем изображение
                img = Image.open(img_path)
                img.thumbnail((200, 200))
                photo = ImageTk.PhotoImage(img)
                
                # Сохраняем ссылку на PhotoImage
                frame.photo = photo
                
                # Отображаем изображение и подпись
                label_img = ttk.Label(frame, image=photo)
                label_img.pack()
                
                label_text = ttk.Label(frame, text=img_path.name, wraplength=200)
                label_text.pack()
            except Exception as e:
                print(f"Ошибка при загрузке изображения {img_path}: {e}")