import time
import threading
import keyboard
# import mouse
import pyautogui
import os
from pathlib import Path
import shutil
from image_gallery import ImageGallery
import logging
from pynput import mouse

class MacroGenerator:
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        # Добавляем отступ от края экрана для безопасности
        self.safe_margin = 5
        
    def _adjust_coordinates(self, x, y):
        """Корректирует координаты, чтобы избежать срабатывания защиты PyAutoGUI"""
        safe_x = max(self.safe_margin, min(x, self.screen_width - self.safe_margin))
        safe_y = max(self.safe_margin, min(y, self.screen_height - self.safe_margin))
        if safe_x != x or safe_y != y:
            logging.debug(f"Координаты скорректированы: ({x}, {y}) -> ({safe_x}, {safe_y})")
        return safe_x, safe_y
    
    def generate_code(self, actions):
        """Генерирует код макроса из списка действий"""
        code = [
            "import pyautogui",
            "import time",
            "from pathlib import Path",
            "import logging",
            "",
            "# Установка безопасных настроек",
            "pyautogui.FAILSAFE = True",
            "pyautogui.PAUSE = 0.05",
            "",
            "def adjust_coordinates(x, y, screen_width, screen_height, margin=5):",
            "    '''Корректирует координаты для избежания срабатывания защиты'''",
            "    safe_x = max(margin, min(x, screen_width - margin))",
            "    safe_y = max(margin, min(y, screen_height - margin))",
            "    return safe_x, safe_y",
            "",
            "def calculate_new_coordinates(original_x, original_y, original_width, original_height):",
            "    current_width, current_height = pyautogui.size()",
            "    new_x = int((original_x * current_width) / original_width)",
            "    new_y = int((original_y * current_height) / original_height)",
            "    return adjust_coordinates(new_x, new_y, current_width, current_height)",
            "",
            f"ORIGINAL_SCREEN_SIZE = ({self.screen_width}, {self.screen_height})",
            "",
            "def run_script():",
            "    screens_dir = Path('screens')",
            "    if not screens_dir.exists():",
            "        logging.error('Директория screens не найдена')",
            "        return",
            "    ",
            "    # Получаем текущие размеры экрана",
            "    current_width, current_height = pyautogui.size()",
            "    logging.info(f'Размер экрана: {current_width}x{current_height}')",
            ""
        ]
        
        if not actions:
            code.append("    print('Нет записанных действий')")
            code.append("    return")
            code.append("")
            return "\n".join(code)
        
        last_time = 0
        for action in actions:
            delay = action[-1] - last_time
            if delay > 0.05:
                code.append(f"    time.sleep({delay:.2f})")
            
            if action[0] == 'move':
                _, x, y, _ = action
                code.append(f"    # Перемещение мыши в позицию ({x}, {y})")
                code.append(f"    safe_x, safe_y = adjust_coordinates({x}, {y}, current_width, current_height)")
                code.append(f"    pyautogui.moveTo(safe_x, safe_y, _pause=False)")
            elif action[0] == 'mouseDown':
                _, x, y, button, _, screenshot_num = action
                if screenshot_num is not None:
                    code.append(f"    # Поиск и клик по изображению {screenshot_num}.png")
                    code.append(f"    image_path = str(screens_dir / '{screenshot_num}.png')")
                    code.append(f"    try:")
                    code.append(f"        target = pyautogui.locateOnScreen(image_path, confidence=0.9)")
                    code.append(f"        if target:")
                    code.append(f"            target_center = pyautogui.center(target)")
                    code.append(f"            safe_x, safe_y = adjust_coordinates(target_center.x, target_center.y, current_width, current_height)")
                    code.append(f"            logging.info(f'Найдено изображение {screenshot_num}.png в позиции ({{safe_x}}, {{safe_y}})')")
                    code.append(f"            pyautogui.click(safe_x, safe_y, button='{button}', _pause=False)")
                    code.append(f"        else:")
                    code.append(f"            raise pyautogui.ImageNotFoundException")
                    code.append(f"    except pyautogui.ImageNotFoundException:")
                    code.append(f"        logging.warning(f'Изображение {{image_path}} не найдено, используем относительные координаты')")
                    code.append(f"        new_x, new_y = calculate_new_coordinates({x}, {y}, *ORIGINAL_SCREEN_SIZE)")
                    code.append(f"        pyautogui.click(new_x, new_y, button='{button}', _pause=False)")
                else:
                    code.append(f"    # Клик мышью в позиции ({x}, {y})")
                    code.append(f"    new_x, new_y = calculate_new_coordinates({x}, {y}, *ORIGINAL_SCREEN_SIZE)")
                    code.append(f"    pyautogui.click(new_x, new_y, button='{button}', _pause=False)")
            elif action[0] == 'mouseUp':
                _, x, y, button, _ = action
                code.append(f"    # Отпускание кнопки мыши в позиции ({x}, {y})")
                code.append(f"    safe_x, safe_y = adjust_coordinates({x}, {y}, current_width, current_height)")
                code.append(f"    pyautogui.mouseUp(safe_x, safe_y, button='{button}', _pause=False)")
            elif action[0] == 'scroll':
                _, x, y, _, delta, _ = action
                code.append(f"    # Прокрутка колеса мыши в позиции ({x}, {y})")
                code.append(f"    safe_x, safe_y = adjust_coordinates({x}, {y}, current_width, current_height)")
                code.append(f"    pyautogui.scroll({delta}, x=safe_x, y=safe_y)")
            elif action[0] == 'keydown':
                _, key, _ = action
                code.append(f"    # Нажатие клавиши {key}")
                if len(key) == 1:
                    code.append(f"    pyautogui.press('{key}', _pause=False)")
                else:
                    code.append(f"    pyautogui.keyDown('{key}', _pause=False)")
            elif action[0] == 'keyup':
                _, key, _ = action
                if len(key) > 1:
                    code.append(f"    # Отпускание клавиши {key}")
                    code.append(f"    pyautogui.keyUp('{key}', _pause=False)")
            elif action[0] == 'doubleClick':
                _, x, y, timestamp, screenshot_num = action
                if screenshot_num is not None:
                    code.append(f"    # Двойной клик по изображению {screenshot_num}.png")
                    code.append(f"    image_path = str(screens_dir / '{screenshot_num}.png')")
                    code.append(f"    try:")
                    code.append(f"        target = pyautogui.locateOnScreen(image_path, confidence=0.9)")
                    code.append(f"        if target:")
                    code.append(f"            target_center = pyautogui.center(target)")
                    code.append(f"            safe_x, safe_y = adjust_coordinates(target_center.x, target_center.y, current_width, current_height)")
                    code.append(f"            logging.info(f'Найдено изображение {screenshot_num}.png в позиции ({{safe_x}}, {{safe_y}})')")
                    code.append(f"            pyautogui.doubleClick(safe_x, safe_y, _pause=False)")
                    code.append(f"        else:")
                    code.append(f"            raise pyautogui.ImageNotFoundException")
                    code.append(f"    except pyautogui.ImageNotFoundException:")
                    code.append(f"        logging.warning(f'Изображение {{image_path}} не найдено, используем относительные координаты')")
                    code.append(f"        new_x, new_y = calculate_new_coordinates({x}, {y}, *ORIGINAL_SCREEN_SIZE)")
                    code.append(f"        pyautogui.doubleClick(new_x, new_y, _pause=False)")
                else:
                    code.append(f"    # Двойной клик в позиции ({x}, {y})")
                    code.append(f"    new_x, new_y = calculate_new_coordinates({x}, {y}, *ORIGINAL_SCREEN_SIZE)")
                    code.append(f"    pyautogui.doubleClick(new_x, new_y, _pause=False)")
            
            last_time = action[-1]
        
        code.append("")
        code.append("if __name__ == '__main__':")
        code.append("    run_script()")
        
        return "\n".join(code)

class Recorder:
    def __init__(self):
        self.actions = []
        self.start_time = None
        self.running = False
        self.last_mouse_position = (0, 0)
        self.position_check_interval = 0.05
        self.is_dragging = False
        self.screenshot_counter = 0
        self.screens_dir = Path("screens")
        self.clear_screens_directory()
        self.macro_generator = MacroGenerator()
        
        # Добавляем словарь замены клавиш
        self.key_replacements = {
            'left windows': 'winleft',
            'right windows': 'winright',
            'enter': 'return',
            'esc': 'escape',
            'spacebar': 'space',
            'page up': 'pageup',
            'page down': 'pagedown',
            'left ctrl': 'ctrlleft',
            'right ctrl': 'ctrlright',
            'left alt': 'altleft',
            'right alt': 'altright',
            'left shift': 'shiftleft',
            'right shift': 'shiftright',
            'caps lock': 'capslock',
            'num lock': 'numlock',
            'scroll lock': 'scrolllock',
            'print screen': 'printscreen',
        }
        
        # Параметры для отслеживания двойного клика
        self.last_down_sequence = []  # последовательность нажатий
        self.last_up_sequence = []    # последовательность отпусаний
        self.double_click_threshold = 0.2  # время между кликами в секундах
        
        # Параметры для фильтрации повторяющихся событий
        self.last_event_type = None
        self.last_action_time = 0
        self.min_event_interval = 0.05
        
        # Настройка логирования
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.mouse_listener = None
        self.keyboard_listener = None
    
    def clear_screens_directory(self):
        """Очищает директорию скриншотов"""
        if self.screens_dir.exists():
            shutil.rmtree(self.screens_dir)
        self.screens_dir.mkdir(exist_ok=True)
        
    def take_screenshot_around_click(self, x, y):
        # Определяем область вокруг клика (например, 100x100 пикселей)
        region_size = 100
        left = max(x - region_size//2, 0)
        top = max(y - region_size//2, 0)
        
        # Делаем скриншот области
        self.screenshot_counter += 1
        screenshot_path = self.screens_dir / f"{self.screenshot_counter}.png"
        
        try:
            screenshot = pyautogui.screenshot(region=(left, top, region_size, region_size))
            screenshot.save(screenshot_path)
            return self.screenshot_counter
        except Exception as e:
            print(f"Ошибка при создании скриншота: {e}")
            return None
    
    def is_double_click(self, x, y, timestamp, event_type='down'):
        """Проверяет, является ли текущий клик частью двойного клика"""
        # Выбираем нужную последовательность в зависимости от типа события
        sequence = self.last_down_sequence if event_type == 'down' else self.last_up_sequence
        
        # Добавляем текущее время в последовательность
        sequence.append(timestamp)
        
        # Оставляем только последние два события
        if len(sequence) > 2:
            sequence.pop(0)
        
        # Если это первое событие в последовательности
        if len(sequence) < 2:
            logging.debug(f"First {event_type} in sequence at ({x}, {y})")
            return False
        
        # Вычисляем время между событиями
        time_diff = sequence[1] - sequence[0]
        
        logging.debug(f"Time between {event_type}s: {time_diff:.3f}s (threshold: {self.double_click_threshold}s)")
        
        # Проверяем время между событиями
        is_double = time_diff <= self.double_click_threshold
        
        if is_double:
            logging.info(f"Double click detected by {event_type} events!")
            sequence.clear()  # Очищаем последовательность
            # Очищаем также вторую последовательность
            if event_type == 'down':
                self.last_up_sequence.clear()
            else:
                self.last_down_sequence.clear()
        
        return is_double
    
    def start(self):
        # Сбрасываем список действий перед новой записью
        self.actions = []
        self.screenshot_counter = 0
        
        # Очищаем обработчики логирования
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Настраиваем логирование заново
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            force=True  # Принудительно пересоздаем конфигурацию
        )
        
        # Очищаем последовательности кликов
        self.last_down_sequence.clear()
        self.last_up_sequence.clear()
        
        # Запускаем прослушивание
        self.start_listening()
    
    def stop(self):
        self.running = False
        keyboard.unhook_all()
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        
        # Ждем завершения потока отслеживания мыши
        if hasattr(self, 'mouse_thread') and self.mouse_thread.is_alive():
            self.mouse_thread.join(timeout=1.0)
            
        return self.macro_generator.generate_code(self.actions)
    
    def track_mouse_movement(self):
        while self.running:
            if not self.is_dragging:
                current_pos = pyautogui.position()
                if current_pos != self.last_mouse_position:
                    self.actions.append(('move', current_pos[0], current_pos[1], 
                                       time.time() - self.start_time))
                    self.last_mouse_position = current_pos
            time.sleep(self.position_check_interval)
    
    def on_keyboard_event(self, event):
        if not self.running:
            return
        
        # Нормализуем название клавиши
        normalized_key = self._normalize_key(event.name)
        
        if event.event_type == 'down':
            self.actions.append(('keydown', normalized_key, 
                               time.time() - self.start_time))
        elif event.event_type == 'up':
            self.actions.append(('keyup', normalized_key, 
                               time.time() - self.start_time))
    
    def filter_repeated_event(self, timestamp, event_type, x, y):
        """Фильтрует слишком частые повторяющиеся события"""
        current_event = (event_type, x, y)
        time_diff = timestamp - self.last_action_time
        
        if (current_event == self.last_event_type and 
            time_diff < self.min_event_interval):
            return True
            
        self.last_event_type = current_event
        self.last_action_time = timestamp
        return False
    
    def on_mouse_event(self, x, y, button=None, pressed=None, delta=0):
        if not self.running:
            return
        
        timestamp = time.time() - self.start_time
        event_type = 'ButtonEvent' if pressed else 'ButtonReleaseEvent'
        
        # Фильтруем частые повторяющиеся события
        if self.filter_repeated_event(timestamp, event_type, x, y):
            return
        
        if event_type == 'ButtonEvent':
            if button == mouse.Button.left:
                if pressed:
                    logging.debug(f"Left mouse button down at ({x}, {y})")
                    try:
                        if self.is_double_click(x, y, timestamp, 'down'):
                            # Удаляем предыдущие события одиночного клика
                            while self.actions and self.actions[-1][0] in ('mouseUp', 'mouseDown'):
                                removed_action = self.actions.pop()
                                logging.debug(f"Removing action: {removed_action}")
                            
                            # Добавляем событие двойного клика
                            screenshot_num = self.take_screenshot_around_click(x, y)
                            self.actions.append(('doubleClick', x, y, timestamp, screenshot_num))
                            logging.info(f"Added double click action at ({x}, {y})")
                        else:
                            # Обычный клик
                            screenshot_num = self.take_screenshot_around_click(x, y)
                            self.actions.append(('mouseDown', x, y, button.name, timestamp, screenshot_num))
                    except Exception as e:
                        logging.error(f"Error processing mouse event: {e}")
                
                    self.is_dragging = True
                    self.last_mouse_position = (x, y)
                else:
                    logging.debug(f"Left mouse button up at ({x}, {y})")
                    try:
                        if self.is_double_click(x, y, timestamp, 'up'):
                            # Удаляем предыдущие события одиночного клика
                            while self.actions and self.actions[-1][0] in ('mouseUp', 'mouseDown'):
                                removed_action = self.actions.pop()
                                logging.debug(f"Removing action: {removed_action}")
                            
                            # Добавляем событие двойного клика
                            screenshot_num = self.take_screenshot_around_click(x, y)
                            self.actions.append(('doubleClick', x, y, timestamp, screenshot_num))
                            logging.info(f"Added double click action at ({x}, {y})")
                        else:
                            if self.is_dragging:
                                self.actions.append(('move', x, y, timestamp))
                            self.actions.append(('mouseUp', x, y, button.name, timestamp))
                    except Exception as e:
                        logging.error(f"Error processing mouse event: {e}")
                
                    self.is_dragging = False
            else:  # другие кнопки мыши
                if pressed:
                    self.actions.append(('mouseDown', x, y, button.name, timestamp, None))
                else:
                    self.actions.append(('mouseUp', x, y, button.name, timestamp))
                
        elif event_type == 'WheelEvent':
            self.actions.append(('scroll', x, y, 0, delta, timestamp))
            
        elif event_type == 'MoveEvent' and self.is_dragging:
            if (x, y) != self.last_mouse_position:
                self.actions.append(('move', x, y, timestamp))
                self.last_mouse_position = (x, y)
    
    def start_listening(self):
        """Начинает прослушивание событий клавиатуры и мыши"""
        self.running = True
        self.start_time = time.time()
        
        # Запускаем отслеживание движений мыши в отдельном потоке
        self.mouse_thread = threading.Thread(target=self.track_mouse_movement)
        self.mouse_thread.daemon = True
        self.mouse_thread.start()
        
        # Устанавливаем обработчики событий
        keyboard.hook(self.on_keyboard_event)
        self.mouse_listener = mouse.Listener(
            on_move=self.on_mouse_event,
            on_click=self.on_mouse_event,
            on_scroll=self.on_mouse_event
        )
        self.mouse_listener.start()

    def _normalize_key(self, key):
        """Преобразует название клавиши в орректный формат для PyAutoGUI"""
        return self.key_replacements.get(key.lower(), key)