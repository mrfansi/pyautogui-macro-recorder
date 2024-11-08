import tkinter as tk
from tkinter import ttk
import threading
from recorder import Recorder
from player import ActionPlayer
from PIL import Image, ImageTk
from pathlib import Path
from tkcode import CodeEditor
from tkinter import filedialog, messagebox
import shutil
import pyautogui
import time

class ActionRecorderApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PyAutoGUI Macro Recorder")
        self.root.geometry("1200x800")
        
        # Состояния приложения
        self.is_recording = False
        self.is_playing = False
        
        # Инициализация компонентов
        self.recorder = Recorder()
        self.recorder.root = self.root
        self.player = ActionPlayer()
        
        # Регистрируем пользовательские события
        self.root.event_add('<<PlaybackFinished>>', 'None')
        self.root.event_add('<<PlaybackError>>', 'None')
        self.root.event_add('<<FailSafe>>', 'None')
        
        # Привязываем обработчики событий
        self.root.bind('<<PlaybackFinished>>', self.playback_finished)
        self.root.bind('<<PlaybackError>>', self.playback_error)
        self.root.bind('<<FailSafe>>', self.handle_failsafe)
        
        self.setup_ui()
    
    def setup_ui(self):
        # Основной контейнер
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Верхний контейнер для основного интерфейса
        top_container = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        top_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Левая панель с кнопками и кодом
        left_panel = ttk.Frame(top_container)
        top_container.add(left_panel, weight=1)
        
        # Правая панель для галереи
        self.gallery_frame = ttk.Frame(top_container)
        top_container.add(self.gallery_frame, weight=1)
        
        # Настройка левой панели
        # Создание фрейма для кнопок
        button_frame = ttk.Frame(left_panel)
        button_frame.pack(pady=10)
        
        # Добавляем кнопку сохранения
        self.save_button = ttk.Button(
            button_frame,
            text="💾",
            width=3,
            command=self.save_project
        )
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        # Кнопки управления
        self.play_button = ttk.Button(
            button_frame,
            text="▶",
            width=3,
            command=self.start_playback
        )
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        self.record_button = ttk.Button(
            button_frame,
            text="●",
            width=3,
            command=self.start_recording
        )
        self.record_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(
            button_frame,
            text="\u25A0",  # Unicode символ для квадрата
            width=3,
            command=self.stop_action,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Создаем фрейм для текстового поля и скроллбара
        text_frame = ttk.Frame(left_panel)
        text_frame.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # Текстовое поле для кода
        self.code_text = CodeEditor(
            text_frame,
            width=50,
            height=20,
            language="python",
            font="Consolas 10",
            highlighter="dracula",
            autofocus=True,
            blockcursor=True,
            insertofftime=0,
            padx=10,
            pady=10
        )
        
        # Только вертикальный скроллбар справа
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.code_text.yview)
        
        # Размещаем текстовое поле
        self.code_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Настройка правой панели (галерея)
        gallery_label = ttk.Label(self.gallery_frame, text="Скриншоты")
        gallery_label.pack(pady=5)
        
        # Создаем контекстное меню для скриншотов
        self.screenshot_menu = tk.Menu(self.root, tearoff=0)
        self.screenshot_menu.add_command(label="Обновить скриншот (Ctrl+V)", command=self.update_screenshot_from_clipboard)
        self.screenshot_menu.add_command(label="Сделать новый скриншот области (Ctrl+N)", command=self.take_new_screenshot)
        
        # Создаем холст с прокруткой для галереи
        self.gallery_canvas = tk.Canvas(self.gallery_frame)
        gallery_scrollbar = ttk.Scrollbar(self.gallery_frame, orient="vertical", 
                                        command=self.gallery_canvas.yview)
        
        self.gallery_content = ttk.Frame(self.gallery_canvas)
        
        # Настраиваем прокрутку
        def _on_mousewheel(event):
            self.gallery_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.gallery_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.gallery_content.bind("<Configure>", 
            lambda e: self.gallery_canvas.configure(scrollregion=self.gallery_canvas.bbox("all")))
        
        self.gallery_canvas.create_window((0, 0), window=self.gallery_content, anchor="nw")
        self.gallery_canvas.configure(yscrollcommand=gallery_scrollbar.set)
        
        self.gallery_canvas.pack(side="left", fill="both", expand=True)
        gallery_scrollbar.pack(side="right", fill="y")
        
        # Привязываем обработчик изменения размер окна
        self.gallery_frame.bind("<Configure>", self._on_gallery_resize)
        
        # Добавляем поле для логов внизу окна
        log_frame = ttk.Frame(main_container)
        log_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Метка "Лог"
        log_label = ttk.Label(log_frame, text="Лог:")
        log_label.pack(anchor=tk.W)
        
        # Создаем фрейм фиксированной высоты для лога
        log_container = ttk.Frame(log_frame, height=200)  # Фиксированная высота
        log_container.pack(fill=tk.X)
        log_container.pack_propagate(False)  # Запрещаем изменение размера
        
        # Текстовое поле для логов
        self.log_text = tk.Text(log_container, height=10, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Скроллбар для логов
        log_scrollbar = ttk.Scrollbar(self.log_text, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        # Настраиваем цвета для разных типов логов
        self.log_text.tag_configure('INFO', foreground='green')
        self.log_text.tag_configure('WARNING', foreground='orange')
        self.log_text.tag_configure('ERROR', foreground='red')
        
        # Делаем поле только для чтения
        self.log_text.config(state=tk.DISABLED)
    
    def _on_gallery_resize(self, event):
        """Обработчик изменения размера галереи"""
        if hasattr(self, '_resize_timer'):
            self.root.after_cancel(self._resize_timer)
        self._resize_timer = self.root.after(100, self.update_gallery)
    
    def update_gallery(self):
        """Обновление галереи с адаптивной сеткой"""
        # Очищаем галерею
        for widget in self.gallery_content.winfo_children():
            widget.destroy()
        
        # Загружаем изображения
        images = sorted(Path(self.recorder.screens_dir).glob("*.png"), 
                       key=lambda x: int(x.stem))
        
        if not images:
            return
        
        # Получаем актуальную ширину галереи
        gallery_width = self.gallery_frame.winfo_width() - 20  # Учитываем отступы и скроллбар
        
        # Вычисляем оптимальный размер миниатюры и количество столбцов
        desired_columns = max(1, gallery_width // 200)  # Примерно 200 пикселей на минитюру
        thumbnail_width = (gallery_width - (desired_columns + 1) * 10) // desired_columns  # Учитываем отступы между миниатюрами
        
        # Настраиваем grid конфигурацию
        for i in range(desired_columns):
            self.gallery_content.grid_columnconfigure(i, weight=1, uniform="column")
        
        # Размещаем изображения в сетке
        for i, img_path in enumerate(images):
            try:
                row = i // desired_columns
                col = i % desired_columns
                
                # Создаем фрейм для изображения и подписи
                frame = ttk.Frame(self.gallery_content)
                frame.grid(row=row, column=col, pady=5, padx=5, sticky="nsew")
                
                # Загружаем и масштабируем изображение
                img = Image.open(img_path)
                aspect_ratio = img.height / img.width
                thumbnail_height = int(thumbnail_width * aspect_ratio)
                img = img.resize((thumbnail_width, thumbnail_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                # Создаем контейнер для центрирования содержимого
                container = ttk.Frame(frame)
                container.pack(expand=True, fill="both")
                
                # Отображаем изображение и подпись
                label_img = ttk.Label(container, image=photo, cursor="hand2")
                label_img.image = photo
                label_img.pack(expand=True, fill="both")
                
                # Добавляем подсказку для изображения
                tooltip_text = "ПКМ - меню\nCtrl+V - вставить из буфера\nCtrl+N - новый скриншот"
                label_img.bind("<Enter>", lambda e, text=tooltip_text: self.show_tooltip(e, text))
                label_img.bind("<Leave>", self.hide_tooltip)
                
                # Добавляем текст с инструкциями под изображением
                label_text = ttk.Label(container, 
                                     text=f"{img_path.name}\nПКМ для редактирования", 
                                     wraplength=thumbnail_width,
                                     justify="center")
                label_text.pack(pady=(5, 0))
                
                # Привязываем контекстное меню и горячие клавиши
                label_img.bind("<Button-3>", lambda e, path=img_path: self.show_screenshot_menu(e, path))
                container.bind("<Control-v>", lambda e, path=img_path: self.update_screenshot_from_clipboard(path))
                container.bind("<Control-n>", lambda e, path=img_path: self.take_new_screenshot(path))
                
            except Exception as e:
                print(f"Ошибка при загрузке изображения {img_path}: {e}")
        
        # Обновляем область прокрутки
        self.gallery_canvas.update_idletasks()
        self.gallery_canvas.configure(scrollregion=self.gallery_canvas.bbox("all"))
    
    def show_screenshot_menu(self, event, screenshot_path):
        """Показывает контекстное меню для скриншота"""
        self.current_screenshot_path = screenshot_path
        self.screenshot_menu.post(event.x_root, event.y_root)
    
    def update_screenshot_from_clipboard(self, screenshot_path=None):
        """Обновляет скриншот изображением из буфера обмена"""
        try:
            path = screenshot_path or self.current_screenshot_path
            if not path:
                return
                
            # Получаем изображение из буфера обмена
            from PIL import ImageGrab
            img = ImageGrab.grabclipboard()
            
            if img is None:
                messagebox.showwarning(
                    "Предупреждение",
                    "Буфер обмена не содержит изображения"
                )
                return
                
            # Сохраняем новое изображение
            img.save(path)
            
            # Обновляем галерею
            self.update_gallery()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить скриншот:\n{str(e)}")
    
    def take_new_screenshot(self, screenshot_path=None):
        """Делает новый скриншот выбранной области"""
        try:
            path = screenshot_path or self.current_screenshot_path
            if not path:
                return
                
            # Минимизируем окно на время создания скриншота
            self.root.iconify()
            self.root.after(500, lambda: self._take_screenshot(path))
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать скриншот:\n{str(e)}")
    
    def _take_screenshot(self, path):
        try:
            # Создаем скриншот выбранной области
            screenshot = pyautogui.screenshot(region=pyautogui.select_area())
            screenshot.save(path)
            
            # Восстанавливаем окно и обновляем галерею
            self.root.deiconify()
            self.update_gallery()
            
        except Exception as e:
            self.root.deiconify()
            messagebox.showerror("Ошибка", f"Не удалось создать скриншот:\n{str(e)}")
    
    def start_recording(self):
        if not self.is_recording:
            # Очищаем код и скриншоты перед новой запись
            self.code_text.delete(1.0, tk.END)
            # Очищаем все скриншоты в директории
            for screenshot in Path(self.recorder.screens_dir).glob("*.png"):
                screenshot.unlink()
            # Очищаем галерею
            for widget in self.gallery_content.winfo_children():
                widget.destroy()
                
            self.is_recording = True
            self.update_button_states()
            self.recorder.start()
            
    def start_playback(self):
        if not self.is_playing and self.code_text.get(1.0, tk.END).strip():
            self.is_playing = True
            self.update_button_states()
            
            try:
                code = self.code_text.get(1.0, tk.END)
                if not code.strip():
                    return
                
                # Устанавливаем callback для логов
                self.player.log_callback = self.add_log
                
                def play_thread():
                    try:
                        self.player.play(code)
                        if self.root.winfo_exists():
                            self.root.event_generate('<<PlaybackFinished>>')
                            self.add_log(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - INFO - Macro playback finished")
                    except pyautogui.FailSafeException:
                        if self.root.winfo_exists():
                            self.root.event_generate('<<FailSafe>>')
                    except Exception as e:
                        print(f"Ошибка при воспроизведении: {str(e)}")
                        if self.root.winfo_exists():
                            self.root.event_generate('<<PlaybackError>>')
                
                thread = threading.Thread(target=play_thread, daemon=True)
                thread.start()
                
            except Exception as e:
                print(f"Ошибка при запуске воспроизведения: {str(e)}")
                self.is_playing = False
                self.update_button_states()
    
    def playback_finished(self, event=None):
        """Обработчик успешного завершения воспроизведения"""
        self.is_playing = False
        self.update_button_states()
    
    def playback_error(self, event=None):
        """Обработчик ошибки воспроизведения"""
        self.is_playing = False
        self.update_button_states()
        messagebox.showerror("Ошибка", "Произошла ошибка при воспроизведении макроса")
    
    def handle_failsafe(self, event=None):
        """Обработчик срабатывания защиты PyAutoGUI"""
        self.is_playing = False
        self.update_button_states()
        messagebox.showwarning(
            "Прервано",
            "Выполнение скрипта прервано!\n\n"
            "Причина: мышь попала в угол экрана (защитный механизм PyAutoGUI).\n\n"
            "Для продолжения уберите мышь из угла экрана и запустите скрипт снова."
        )
    
    def stop_action(self):
        if self.is_recording:
            self.is_recording = False
            recorded_code = self.recorder.stop()
            self.code_text.delete(1.0, tk.END)
            self.code_text.insert(1.0, recorded_code)
            self.update_gallery()
        elif self.is_playing:
            self.is_playing = False
            self.player.stop()
            # Генерируем событие завершения
            self.root.event_generate('<<PlaybackFinished>>')
        self.update_button_states()
        
    def update_button_states(self):
        if self.is_recording or self.is_playing:
            self.play_button.config(state=tk.DISABLED)
            self.record_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
        else:
            self.play_button.config(state=tk.NORMAL)
            self.record_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            
    def save_project(self):
        if not self.code_text.get(1.0, tk.END).strip():
            messagebox.showwarning("Предупреждение", "Нет кода для сохранения!")
            return
            
        project_name = filedialog.asksaveasfilename(
            title="Сохранить проект",
            initialdir="./projects",
            defaultextension=".py",
            filetypes=[("Python files", "*.py")]
        )
        
        if not project_name:
            return
            
        try:
            project_dir = Path(project_name).parent
            project_name = Path(project_name).stem
            project_path = project_dir / project_name
            project_path.mkdir(parents=True, exist_ok=True)
            
            # Создаем директорию для скриншотов
            screens_path = project_path / "screens"
            screens_path.mkdir(exist_ok=True)
            
            # Копируем скриншоты
            for screenshot in Path(self.recorder.screens_dir).glob("*.png"):
                shutil.copy2(screenshot, screens_path)
            
            # Сохраняем код макроса
            main_file = project_path / "main.py"
            with open(main_file, 'w', encoding='utf-8') as f:
                f.write(self.code_text.get(1.0, tk.END))
            
            messagebox.showinfo(
                "Успех", 
                f"Проект сохранен в:\n{project_path}\n\n"
                f"Для запуска используйте файл:\n{main_file}"
            )
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить проект:\n{str(e)}")
    
    def show_tooltip(self, event, text):
        """Показывает всплывающую подсказку"""
        x, y, _, _ = event.widget.bbox("insert")
        x += event.widget.winfo_rootx() + 25
        y += event.widget.winfo_rooty() + 20
        
        # Создаем всплывающее окно
        self.tooltip = tk.Toplevel()
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = ttk.Label(self.tooltip, text=text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1)
        label.pack()
    
    def hide_tooltip(self, event=None):
        """Скрывает всплывающую подсказку"""
        if hasattr(self, 'tooltip'):
            self.tooltip.destroy()
    
    def add_log(self, message, level='INFO'):
        """Добавляет сообщение в лог"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + '\n', level)
        self.log_text.see(tk.END)  # Прокрутка к последней строке
        self.log_text.config(state=tk.DISABLED)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ActionRecorderApp()
    app.run()