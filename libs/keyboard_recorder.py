import keyboard
import logging
import time

class KeyboardRecorder:
    def __init__(self, recorder):
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
        self.start_time = None
        self.is_recording = False
        self.recorder = recorder  # Store reference to main recorder

    def start(self, start_time):
        self.start_time = start_time
        self.is_recording = True
        keyboard.hook(self.on_keyboard_event)

    def stop(self):
        self.is_recording = False
        keyboard.unhook_all()
        self.start_time = None

    def on_keyboard_event(self, event):
        """Handle keyboard events with additional safety checks"""
        if not self.is_recording:
            return
            
        try:
            if self.start_time is None:
                logging.warning("Keyboard event received but start_time is None")
                return
                
            current_time = time.time()
            if current_time < self.start_time:
                logging.warning("Invalid timestamp detected")
                return
                
            if event.name is None:
                return
                
            normalized_key = self._normalize_key(event.name)
            if not normalized_key:
                return
                
            timestamp = current_time - self.start_time
            
            event_data = {
                'type': 'keydown' if event.event_type == 'down' else 'keyup',
                'key': normalized_key,
                'timestamp': timestamp
            }
            
            # Send event to main recorder
            self.recorder.handle_keyboard_event(event_data)
                
        except Exception as e:
            logging.error(f"Error processing keyboard event: {e}", exc_info=True)

    def _normalize_key(self, key):
        """Normalizes the key name to the correct format for PyAutoGUI"""
        if key is None:
            return ''
        return self.key_replacements.get(key.lower(), key)