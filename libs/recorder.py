import time
import threading
import keyboard
import pyautogui
from pathlib import Path
import shutil
import logging
from pynput import mouse
from .macro_generator import MacroGenerator

class Recorder:
    def __init__(self):
        self.actions = []
        self.preserved_actions = None  # Add new variable to preserve actions
        self.start_time = None
        self.running = False
        self.last_mouse_position = (0, 0)
        self.position_check_interval = 0.016  # Changed to ~60fps (1/60 second)
        self.is_dragging = False
        self.screenshot_counter = 0
        self.screens_dir = Path("screens")
        self.clear_screens_directory()
        self.macro_generator = MacroGenerator()
        
        # Add key replacement dictionary
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
        
        # Parameters for double-click detection
        self.last_down_sequence = []  # sequence of down events
        self.last_up_sequence = []    # sequence of up events
        self.double_click_threshold = 0.2  # time between clicks in seconds
        
        # Parameters for filtering repeated events
        self.last_event_type = None
        self.last_action_time = 0
        self.min_event_interval = 0.016  # Match the check interval
        self.mouse_move_threshold = 2  # Minimum pixel distance for move events
        self.last_recorded_pos = (0, 0)
        
        # Logging setup
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.mouse_listener = None
        self.keyboard_listener = None
        self.cleanup_logging()
        self._last_generated_code = None  # Add this line
        self.is_recording = False
        self.current_actions = []  # Temporary storage for current recording
        self.base_actions = []  # Store all previous recordings
        self.last_timestamp = 0  # Add this line
    
    def cleanup_logging(self):
        """Clean up logging handlers and reinitialize"""
        # Remove all handlers
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            
        # Reinitialize logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            force=True
        )
    
    def clear_screens_directory(self):
        """Clears the screenshots directory"""
        if self.screens_dir.exists():
            shutil.rmtree(self.screens_dir)
        self.screens_dir.mkdir(exist_ok=True)
        
    def take_screenshot_around_click(self, x, y):
        # Define the area around the click (e.g., 100x100 pixels)
        region_size = 100
        left = max(x - region_size//2, 0)
        top = max(y - region_size//2, 0)
        
        # Take a screenshot of the area
        self.screenshot_counter += 1
        screenshot_path = self.screens_dir / f"{self.screenshot_counter}.png"
        
        try:
            screenshot = pyautogui.screenshot(region=(left, top, region_size, region_size))
            screenshot.save(screenshot_path)
            return self.screenshot_counter
        except Exception as e:
            print(f"Error taking screenshot: {e}")
            return None
    
    def is_double_click(self, x, y, timestamp, event_type='down'):
        """Checks if the current click is part of a double click"""
        # Select the appropriate sequence based on the event type
        sequence = self.last_down_sequence if event_type == 'down' else self.last_up_sequence
        
        # Add the current time to the sequence
        sequence.append(timestamp)
        
        # Keep only the last two events
        if len(sequence) > 2:
            sequence.pop(0)
        
        # If this is the first event in the sequence
        if len(sequence) < 2:
            logging.debug(f"First {event_type} in sequence at ({x}, {y})")
            return False
        
        # Calculate the time between events
        time_diff = sequence[1] - sequence[0]
        
        logging.debug(f"Time between {event_type}s: {time_diff:.3f}s (threshold: {self.double_click_threshold}s)")
        
        # Check the time between events
        is_double = time_diff <= self.double_click_threshold
        
        if is_double:
            logging.info(f"Double click detected by {event_type} events!")
            sequence.clear()  # Clear the sequence
            # Also clear the other sequence
            if event_type == 'down':
                self.last_up_sequence.clear()
            else:
                self.last_down_sequence.clear()
        
        return is_double
    
    def start(self):
        """Starts recording a new macro"""
        if self.running:
            self.stop()
        
        # Reset state for new recording
        self.current_actions = []
        self.running = True
        self.is_recording = True
        self.start_time = time.time()  # Set start_time first
        self.last_timestamp = self.start_time
        
        # Store previous actions if any exist
        if self.actions:
            self.base_actions = self.actions.copy()
            
        # Start listeners
        self.start_listening()
        logging.info(f"Started new recording session at {self.start_time:.3f} (existing actions: {len(self.base_actions)})")

    def stop(self):
        """Stops recording and generates macro code"""
        if not self.running:
            return self._last_generated_code or self.macro_generator.generate_code(self.actions)
        
        logging.info("Stopping recording...")
        self.running = False
        self.is_recording = False
        
        # Stop listeners first
        keyboard.unhook_all()
        if self.mouse_listener:
            self.mouse_listener.stop()
            
        # Wait for mouse thread
        if hasattr(self, 'mouse_thread') and self.mouse_thread.is_alive():
            self.mouse_thread.join(timeout=1.0)
        
        # Clear timing variables last
        self.start_time = None
        self.last_timestamp = 0
        
        # Combine base actions with current recording
        if self.current_actions:  # Only combine if there are new actions
            self.actions = self.base_actions + self.current_actions
            logging.info(f"Combined {len(self.base_actions)} previous actions with {len(self.current_actions)} new actions")
            
            # Generate code
            self._last_generated_code = self.macro_generator.generate_code(self.actions)
            return self._last_generated_code
        elif self.base_actions:  # Return existing code if no new actions
            self._last_generated_code = self.macro_generator.generate_code(self.base_actions)
            return self._last_generated_code
        else:
            logging.warning("No actions recorded")
            return ""

    def generate_code(self):
        """Optimize generated code for smoother playback"""
        if not self.actions:
            return None
            
        # Optimize mouse movements by reducing redundant points
        optimized_actions = []
        last_move = None
        
        for action in self.actions:
            if action[0] == 'move':
                if not last_move or (time.time() - last_move[-1]) > 0.05:
                    optimized_actions.append(action)
                    last_move = action
            else:
                optimized_actions.append(action)
        
        self._last_generated_code = self.macro_generator.generate_code(optimized_actions)
        return self._last_generated_code

    def track_mouse_movement(self):
        """Track mouse movements with optimized sampling"""
        while self.running:
            if self.is_recording and not self.is_dragging:
                try:
                    current_pos = pyautogui.position()
                    x_diff = abs(current_pos[0] - self.last_recorded_pos[0])
                    y_diff = abs(current_pos[1] - self.last_recorded_pos[1])
                    
                    # Only record if mouse moved beyond threshold
                    if x_diff > self.mouse_move_threshold or y_diff > self.mouse_move_threshold:
                        timestamp = time.time() - self.start_time
                        self.current_actions.append(('move', current_pos[0], current_pos[1], timestamp))
                        self.last_recorded_pos = current_pos
                        self.last_mouse_position = current_pos
                except Exception as e:
                    logging.error(f"Error tracking mouse: {e}")
            time.sleep(self.position_check_interval)
    
    def on_keyboard_event(self, event):
        """Handle keyboard events with additional safety checks"""
        if not self.is_recording:
            return
            
        try:
            # Verify recording state and timing
            if self.start_time is None:
                logging.warning("Keyboard event received but start_time is None")
                return
                
            current_time = time.time()
            if current_time < self.start_time:
                logging.warning("Invalid timestamp detected")
                return
                
            # Skip events with None key name
            if event.name is None:
                return
                
            # Normalize the key name
            normalized_key = self._normalize_key(event.name)
            if not normalized_key:  # Skip empty keys
                return
                
            timestamp = current_time - self.start_time
            
            if event.event_type == 'down':
                self.current_actions.append(('keydown', normalized_key, timestamp))
                logging.debug(f"Recorded keydown: {normalized_key} at {timestamp:.3f}s")
            elif event.event_type == 'up':
                self.current_actions.append(('keyup', normalized_key, timestamp))
                logging.debug(f"Recorded keyup: {normalized_key} at {timestamp:.3f}s")
                
        except Exception as e:
            logging.error(f"Error processing keyboard event: {e}", exc_info=True)

    def filter_repeated_event(self, timestamp, event_type, x, y):
        """Filters out too frequent repeated events"""
        current_event = (event_type, x, y)
        time_diff = timestamp - self.last_action_time
        
        if (current_event == self.last_event_type and 
            time_diff < self.min_event_interval):
            return True
            
        self.last_event_type = current_event
        self.last_action_time = timestamp
        return False
    
    def on_mouse_event(self, x, y, button=None, pressed=None, delta=0):
        """Optimized mouse event handler"""
        if not self.is_recording or self.start_time is None:
            return
            
        try:
            current_time = time.time()
            timestamp = current_time - self.start_time
            
            # Filter high-frequency events
            if (current_time - self.last_timestamp) < self.min_event_interval:
                return
                
            if pressed is not None:  # Click event
                if button == mouse.Button.left:
                    if pressed:
                        screenshot_num = self.take_screenshot_around_click(x, y)
                        self.current_actions.append(('mouseDown', x, y, button.name, timestamp, screenshot_num))
                        self.last_recorded_pos = (x, y)
                    else:
                        self.current_actions.append(('mouseUp', x, y, button.name, timestamp))
                else:  # Other mouse buttons
                    if pressed:
                        self.current_actions.append(('mouseDown', x, y, button.name, timestamp, None))
                    else:
                        self.current_actions.append(('mouseUp', x, y, button.name, timestamp))
                self.last_timestamp = current_time
                        
            elif delta:  # Scroll event
                # Consolidate scroll events
                if self.current_actions and self.current_actions[-1][0] == 'scroll':
                    if timestamp - self.current_actions[-1][-1] < 0.1:  # Combine scrolls within 100ms
                        self.current_actions[-1] = ('scroll', x, y, 0, self.current_actions[-1][4] + delta, timestamp)
                        return
                self.current_actions.append(('scroll', x, y, 0, delta, timestamp))
                self.last_timestamp = current_time
                
        except Exception as e:
            logging.error(f"Error processing mouse event: {e}")

    def start_listening(self):
        """Starts listening to keyboard and mouse events"""
        # Stop existing listeners if any
        if self.mouse_listener:
            self.mouse_listener.stop()
        if hasattr(self, 'mouse_thread') and self.mouse_thread.is_alive():
            self.mouse_thread.join(timeout=1.0)
            
        keyboard.unhook_all()
        
        # Start tracking mouse movements in a separate thread
        self.mouse_thread = threading.Thread(target=self.track_mouse_movement)
        self.mouse_thread.daemon = True
        self.mouse_thread.start()
        
        # Set up event handlers
        keyboard.hook(self.on_keyboard_event)
        self.mouse_listener = mouse.Listener(
            on_move=self.on_mouse_event,
            on_click=self.on_mouse_event,
            on_scroll=self.on_mouse_event
        )
        self.mouse_listener.start()

    def _normalize_key(self, key):
        """Normalizes the key name to the correct format for PyAutoGUI"""
        if key is None:
            return ''  # Return empty string for None keys
        return self.key_replacements.get(key.lower(), key)

    def clear_recording(self):
        """Clear all recorded actions"""
        self.actions = []
        self.base_actions = []
        self.current_actions = []
        self.screenshot_counter = 0
        self._last_generated_code = None
        self.clear_screens_directory()
        logging.info("Cleared all recorded actions")