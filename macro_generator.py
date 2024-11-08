class MacroGenerator:
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        
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
            "def calculate_new_coordinates(original_x, original_y, original_width, original_height):",
            "    current_width, current_height = pyautogui.size()",
            "    new_x = int((original_x * current_width) / original_width)",
            "    new_y = int((original_y * current_height) / original_height)",
            "    return new_x, new_y",
            "",
            f"ORIGINAL_SCREEN_SIZE = ({self.screen_width}, {self.screen_height})",
            "",
            "def run_script():",
            "    screens_dir = Path('screens')",
            "    if not screens_dir.exists():",
            "        logging.error('Директория screens не найдена')",
            "        return",
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
                code.append(f"    pyautogui.moveTo({x}, {y}, _pause=False)")
            elif action[0] == 'mouseDown':
                _, x, y, button, _, screenshot_num = action
                if screenshot_num is not None:
                    code.append(f"    # Поиск и клик по изображению {screenshot_num}.png")
                    code.append(f"    image_path = str(screens_dir / '{screenshot_num}.png')")
                    code.append(f"    try:")
                    code.append(f"        target = pyautogui.locateOnScreen(image_path, confidence=0.9)")
                    code.append(f"        if target:")
                    code.append(f"            target_center = pyautogui.center(target)")
                    code.append(f"            pyautogui.mouseDown(target_center.x, target_center.y, button='{button}', _pause=False)")
                    code.append(f"        else:")
                    code.append(f"            raise pyautogui.ImageNotFoundException")
                    code.append(f"    except pyautogui.ImageNotFoundException:")
                    code.append(f"        logging.warning(f'Изображение {{image_path}} не найдено, используем относительные координаты')")
                    code.append(f"        new_x, new_y = calculate_new_coordinates({x}, {y}, *ORIGINAL_SCREEN_SIZE)")
                    code.append(f"        pyautogui.mouseDown(new_x, new_y, button='{button}', _pause=False)")
                else:
                    code.append(f"    new_x, new_y = calculate_new_coordinates({x}, {y}, *ORIGINAL_SCREEN_SIZE)")
                    code.append(f"    pyautogui.mouseDown(new_x, new_y, button='{button}', _pause=False)")
            elif action[0] == 'mouseUp':
                _, x, y, button, _ = action
                code.append(f"    pyautogui.mouseUp({x}, {y}, button='{button}', _pause=False)")
            elif action[0] == 'scroll':
                _, x, y, _, delta, _ = action
                code.append(f"    pyautogui.scroll({delta}, x={x}, y={y})")
            elif action[0] == 'keydown':
                _, key, _ = action
                if len(key) == 1:
                    code.append(f"    pyautogui.press('{key}', _pause=False)")
                else:
                    code.append(f"    pyautogui.keyDown('{key}', _pause=False)")
            elif action[0] == 'keyup':
                _, key, _ = action
                if len(key) > 1:
                    code.append(f"    pyautogui.keyUp('{key}', _pause=False)")
            
            last_time = action[-1]
        
        code.append("")
        code.append("if __name__ == '__main__':")
        code.append("    run_script()")
        
        return "\n".join(code) 