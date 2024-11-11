import time
from pathlib import Path
import shutil
import logging

# Handle both package and direct script usage
try:
    from .macro_generator import MacroGenerator
    from .keyboard_recorder import KeyboardRecorder
    from .mouse_recorder import MouseRecorder
except ImportError:
    # When running directly as a script
    from macro_generator import MacroGenerator
    from keyboard_recorder import KeyboardRecorder
    from mouse_recorder import MouseRecorder

class Recorder:
    def __init__(self):
        self.actions = []
        self.preserved_actions = None  # Add new variable to preserve actions
        self.start_time = None
        self.running = False
        self.screens_dir = Path("screens")
        self.clear_screens_directory()
        self.macro_generator = MacroGenerator()
        self.keyboard_recorder = KeyboardRecorder(self)  # Pass self reference
        self.mouse_recorder = MouseRecorder(self.screens_dir, self)  # Pass self reference
        
        # Logging setup
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
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
        self.mouse_recorder.start(self.start_time)
        # self.keyboard_recorder.start(self.start_time)
        logging.info(f"Started new recording session at {self.start_time:.3f} (existing actions: {len(self.base_actions)})")

    def stop(self):
        """Stops recording and generates macro code"""
        if not self.running:
            return self._last_generated_code or self.macro_generator.generate_code(self.actions)
        
        logging.info("Stopping recording...")
        self.running = False
        self.is_recording = False
        
        # Stop listeners first
        self.keyboard_recorder.stop()
        self.mouse_recorder.stop()
        
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

    def clear_recording(self):
        """Clear all recorded actions"""
        self.actions = []
        self.base_actions = []
        self.current_actions = []
        self.screenshot_counter = 0
        self._last_generated_code = None
        self.clear_screens_directory()
        logging.info("Cleared all recorded actions")

    def handle_keyboard_event(self, event_data):
        """Handle keyboard events from KeyboardRecorder"""
        if event_data and self.is_recording:
            event_type = event_data['type']
            key = event_data['key']
            timestamp = event_data['timestamp']
            self.current_actions.append((event_type, key, timestamp))

    def handle_mouse_event(self, event_data):
        """Handle mouse events from MouseRecorder"""
        if event_data and self.is_recording:
            event_type = event_data['type']
            if event_type == 'move':
                self.current_actions.append((
                    'move',
                    event_data['x'],
                    event_data['y'],
                    event_data['timestamp']
                ))
            elif event_type in ['mouseDown', 'mouseUp']:
                self.current_actions.append((
                    event_type,
                    event_data['x'],
                    event_data['y'],
                    event_data['button'],
                    event_data['timestamp'],
                    event_data.get('screenshot')
                ))
            elif event_type == 'scroll':
                self.current_actions.append((
                    'scroll',
                    event_data['x'],
                    event_data['y'],
                    0,  # Horizontal scroll (legacy parameter)
                    event_data['delta'],
                    event_data['timestamp']
                ))

def test_recorder():
    """Simple test function to demonstrate recorder functionality"""
    recorder = Recorder()
    print("Starting recorder in 3 seconds...")
    time.sleep(3)
    
    recorder.start()
    print("Recording started - move your mouse and press some keys")
    print("Recording will stop in 10 seconds...")
    time.sleep(10)
    
    generated_code = recorder.stop()
    print("\nGenerated Python code:")
    print(generated_code)

if __name__ == "__main__":
    test_recorder()