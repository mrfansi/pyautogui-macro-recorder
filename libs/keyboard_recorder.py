import logging
import time
import platform
from pynput import keyboard
import json

class KeyboardRecorder:
    def __init__(self, recorder):
        # Base key mappings for all platforms
        self.key_replacements = {
            'Key.enter': 'return',
            'Key.esc': 'escape',
            'Key.space': 'space',
            'Key.page_up': 'pageup',
            'Key.page_down': 'pagedown',
            'Key.caps_lock': 'capslock',
            'Key.num_lock': 'numlock',
            'Key.scroll_lock': 'scrolllock',
            'Key.print_screen': 'printscreen',
            'Key.tab': 'tab',
            'Key.delete': 'delete',
            'Key.backspace': 'backspace',
            'Key.home': 'home',
            'Key.end': 'end',
            'Key.insert': 'insert',
        }
        
        # Platform-specific key mappings
        self.system = platform.system().lower()
        if self.system == 'darwin':  # macOS
            self.key_replacements.update({
                'Key.cmd': 'command',
                'Key.cmd_r': 'command',
                'Key.ctrl_l': 'ctrlleft',
                'Key.ctrl_r': 'ctrlright',
                'Key.alt_l': 'optionleft',
                'Key.alt_r': 'optionright',
                'Key.shift_l': 'shiftleft',
                'Key.shift_r': 'shiftright',
            })
        else:  # Windows and Linux
            self.key_replacements.update({
                'Key.cmd': 'winleft',
                'Key.cmd_r': 'winright',
                'Key.ctrl_l': 'ctrlleft',
                'Key.ctrl_r': 'ctrlright',
                'Key.alt_l': 'altleft',
                'Key.alt_r': 'altright',
                'Key.shift_l': 'shiftleft',
                'Key.shift_r': 'shiftright',
            })

        self.start_time = None
        self.is_recording = False
        self.recorder = recorder
        self.listener = None

    def start(self, start_time):
        self.start_time = start_time
        self.is_recording = True
        self.listener = keyboard.Listener(
            on_press=lambda key: self.on_keyboard_event(key, True),
            on_release=lambda key: self.on_keyboard_event(key, False)
        )
        self.listener.start()

    def stop(self):
        self.is_recording = False
        if self.listener:
            self.listener.stop()
        self.start_time = None

    def on_keyboard_event(self, key, is_press):
        """Handle keyboard events with pynput compatibility"""
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
                
            normalized_key = self._normalize_key(key)
            if not normalized_key:
                return
                
            timestamp = current_time - self.start_time
            
            event_data = {
                'type': 'keydown' if is_press else 'keyup',
                'key': normalized_key,
                'timestamp': timestamp
            }
            
            self.recorder.handle_keyboard_event(event_data)
                
        except Exception as e:
            logging.error(f"Error processing keyboard event: {e}", exc_info=True)

    def _normalize_key(self, key):
        """Normalizes the key name to the correct format for PyAutoGUI with platform support"""
        try:
            if isinstance(key, keyboard.KeyCode):
                # Handle normal character keys
                if hasattr(key, 'char') and key.char:
                    if key.char.isprintable():
                        return key.char.lower()
                    return ''
                return ''

            # Special key handling
            key_str = str(key)
            
            # Remove 'Key.' prefix if present
            if key_str.startswith('Key.'):
                key_str = key_str

            # Get the normalized key or return the original
            return self.key_replacements.get(key_str, key_str)
        except:
            logging.error(f"Error normalizing key: {key}", exc_info=True)
            return ''

class TestRecorder:
    """Simple recorder class for testing"""
    def __init__(self):
        self.events = []
        
    def handle_keyboard_event(self, event_data):
        print(f"Recorded event: {json.dumps(event_data)}")
        self.events.append(event_data)

if __name__ == "__main__":
    print("Starting keyboard recorder test...")
    print("Press keys to test recording (Ctrl+C to exit)")
    
    try:
        test_recorder = TestRecorder()
        recorder = KeyboardRecorder(test_recorder)
        recorder.start(time.time())
        
        # Keep the main thread alive
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nStopping recorder...")
        recorder.stop()
        
        print("\nRecorded events:")
        for event in test_recorder.events:
            print(f"- {event['type']}: {event['key']} at {event['timestamp']:.2f}s")