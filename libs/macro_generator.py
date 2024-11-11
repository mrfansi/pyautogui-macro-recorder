import logging
import pyautogui

class MacroGenerator:
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        # Add margin from the edge of the screen for safety
        self.safe_margin = 5
        
    def _adjust_coordinates(self, x, y):
        """Adjusts coordinates to avoid triggering PyAutoGUI's fail-safe"""
        safe_x = max(self.safe_margin, min(x, self.screen_width - self.safe_margin))
        safe_y = max(self.safe_margin, min(y, self.screen_height - self.safe_margin))
        if safe_x != x or safe_y != y:
            logging.debug(f"Coordinates adjusted: ({x}, {y}) -> ({safe_x}, {safe_y})")
        return safe_x, safe_y
    
    def generate_code(self, actions):
        """Generates macro code from a list of actions"""
        code = [
            "import pyautogui",
            "import time",
            "from pathlib import Path",
            "import logging",
            "",
            "# Set safe settings",
            "pyautogui.FAILSAFE = True",
            "pyautogui.PAUSE = 0.05",
            "",
            "def adjust_coordinates(x, y, screen_width, screen_height, margin=5):",
            "    '''Adjusts coordinates to avoid triggering fail-safe'''",
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
            "        logging.error('Directory screens not found')",
            "        return",
            "    ",
            "    # Get current screen size",
            "    current_width, current_height = pyautogui.size()",
            "    logging.info(f'Screen size: {current_width}x{current_height}')",
            ""
        ]
        
        if not actions:
            code.append("    print('No recorded actions')")
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
                code.append(f"    # Move mouse to position ({x}, {y})")
                code.append(f"    safe_x, safe_y = adjust_coordinates({x}, {y}, current_width, current_height)")
                code.append(f"    pyautogui.moveTo(safe_x, safe_y, _pause=False)")
            elif action[0] == 'mouseDown':
                _, x, y, button, _, screenshot_num = action
                if screenshot_num is not None:
                    code.append(f"    # Find and click on image {screenshot_num}.png")
                    code.append(f"    image_path = str(screens_dir / '{screenshot_num}.png')")
                    code.append(f"    try:")
                    code.append(f"        target = pyautogui.locateOnScreen(image_path, confidence=0.9)")
                    code.append(f"        if target:")
                    code.append(f"            target_center = pyautogui.center(target)")
                    code.append(f"            safe_x, safe_y = adjust_coordinates(target_center.x, target_center.y, current_width, current_height)")
                    code.append(f"            logging.info(f'Found image {screenshot_num}.png at position ({{safe_x}}, {{safe_y}})')")
                    code.append(f"            pyautogui.click(safe_x, safe_y, button='{button}', _pause=False)")
                    code.append(f"        else:")
                    code.append(f"            raise pyautogui.ImageNotFoundException")
                    code.append(f"    except pyautogui.ImageNotFoundException:")
                    code.append(f"        logging.warning(f'Image {{image_path}} not found, using relative coordinates')")
                    code.append(f"        new_x, new_y = calculate_new_coordinates({x}, {y}, *ORIGINAL_SCREEN_SIZE)")
                    code.append(f"        pyautogui.click(new_x, new_y, button='{button}', _pause=False)")
                else:
                    code.append(f"    # Mouse click at position ({x}, {y})")
                    code.append(f"    new_x, new_y = calculate_new_coordinates({x}, {y}, *ORIGINAL_SCREEN_SIZE)")
                    code.append(f"    pyautogui.click(new_x, new_y, button='{button}', _pause=False)")
            elif action[0] == 'mouseUp':
                _, x, y, button, _ = action
                code.append(f"    # Mouse button release at position ({x}, {y})")
                code.append(f"    safe_x, safe_y = adjust_coordinates({x}, {y}, current_width, current_height)")
                code.append(f"    pyautogui.mouseUp(safe_x, safe_y, button='{button}', _pause=False)")
            elif action[0] == 'scroll':
                _, x, y, _, delta, _ = action
                code.append(f"    # Mouse scroll at position ({x}, {y})")
                code.append(f"    safe_x, safe_y = adjust_coordinates({x}, {y}, current_width, current_height)")
                code.append(f"    pyautogui.scroll({delta}, x=safe_x, y=safe_y)")
            elif action[0] == 'keydown':
                _, key, _ = action
                code.append(f"    # Key press {key}")
                if len(key) == 1:
                    code.append(f"    pyautogui.press('{key}', _pause=False)")
                else:
                    code.append(f"    pyautogui.keyDown('{key}', _pause=False)")
            elif action[0] == 'keyup':
                _, key, _ = action
                if len(key) > 1:
                    code.append(f"    # Key release {key}")
                    code.append(f"    pyautogui.keyUp('{key}', _pause=False)")
            elif action[0] == 'doubleClick':
                _, x, y, timestamp, screenshot_num = action
                if screenshot_num is not None:
                    code.append(f"    # Double click on image {screenshot_num}.png")
                    code.append(f"    image_path = str(screens_dir / '{screenshot_num}.png')")
                    code.append(f"    try:")
                    code.append(f"        target = pyautogui.locateOnScreen(image_path, confidence=0.9)")
                    code.append(f"        if target:")
                    code.append(f"            target_center = pyautogui.center(target)")
                    code.append(f"            safe_x, safe_y = adjust_coordinates(target_center.x, target_center.y, current_width, current_height)")
                    code.append(f"            logging.info(f'Found image {screenshot_num}.png at position ({{safe_x}}, {{safe_y}})')")
                    code.append(f"            pyautogui.doubleClick(safe_x, safe_y, _pause=False)")
                    code.append(f"        else:")
                    code.append(f"            raise pyautogui.ImageNotFoundException")
                    code.append(f"    except pyautogui.ImageNotFoundException:")
                    code.append(f"        logging.warning(f'Image {{image_path}} not found, using relative coordinates')")
                    code.append(f"        new_x, new_y = calculate_new_coordinates({x}, {y}, *ORIGINAL_SCREEN_SIZE)")
                    code.append(f"        pyautogui.doubleClick(new_x, new_y, _pause=False)")
                else:
                    code.append(f"    # Double click at position ({x}, {y})")
                    code.append(f"    new_x, new_y = calculate_new_coordinates({x}, {y}, *ORIGINAL_SCREEN_SIZE)")
                    code.append(f"    pyautogui.doubleClick(new_x, new_y, _pause=False)")
            
            last_time = action[-1]
        
        code.append("")
        code.append("if __name__ == '__main__':")
        code.append("    run_script()")
        
        return "\n".join(code)

if __name__ == '__main__':
    # Test code for MacroGenerator
    generator = MacroGenerator()
    test_actions = [
        ('move', 100, 100, 0.5),
        ('mouseDown', 100, 100, 'left', 0.6, None),
        ('mouseUp', 100, 100, 'left', 0.7),
        ('keydown', 'a', 0.8),
        ('keyup', 'a', 0.9)
    ]
    
    print("Generated code:")
    print(generator.generate_code(test_actions))