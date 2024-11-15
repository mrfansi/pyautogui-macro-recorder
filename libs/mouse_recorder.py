import time
import pyautogui
import logging
from pynput import mouse
from pathlib import Path

class MouseRecorder:
    def __init__(self, screens_dir, recorder):
        self.screens_dir = screens_dir
        self.screenshot_counter = 0
        self.is_recording = False
        self.is_dragging = False
        self.start_time = None
        self.last_timestamp = 0
        self.last_recorded_pos = (0, 0)
        self.last_mouse_position = (0, 0)
        self.mouse_move_threshold = 2
        self.position_check_interval = 0.016
        self.min_event_interval = 0.016
        self.mouse_listener = None
        
        # Parameters for double-click detection
        self.last_down_sequence = []
        self.last_up_sequence = []
        self.double_click_threshold = 0.2
        
        self.recorder = recorder  # Store reference to main recorder
        logging.info("MouseRecorder initialized")
        
    def start(self, start_time):
        self.start_time = start_time
        self.is_recording = True
        self.last_timestamp = start_time
        
        # Start mouse listener
        self.mouse_listener = mouse.Listener(
            on_move=self.on_mouse_event,
            on_click=self.on_mouse_event,
            on_scroll=self.on_mouse_event
        )
        self.mouse_listener.start()
        logging.debug(f"Mouse recording started at {start_time}")

    def stop(self):
        self.is_recording = False
        if self.mouse_listener:
            self.mouse_listener.stop()
        self.start_time = None
        logging.info("Mouse recording stopped")

    def take_screenshot_around_click(self, x, y):
        """Take screenshot around click position with proper coordinate handling"""
        try:
            # Convert any float coordinates to integers and ensure positive values
            x = max(int(round(float(x))), 0)
            y = max(int(round(float(y))), 0)
            region_size = 100
            
            # Calculate region coordinates
            left = max(x - region_size//2, 0)
            top = max(y - region_size//2, 0)
            
            # Get screen size to prevent out-of-bounds screenshots
            screen_width, screen_height = pyautogui.size()
            
            # Adjust region if it would go beyond screen bounds
            if left + region_size > screen_width:
                left = screen_width - region_size
            if top + region_size > screen_height:
                top = screen_height - region_size
                
            self.screenshot_counter += 1
            screenshot_path = self.screens_dir / f"{self.screenshot_counter}.png"
            
            screenshot = pyautogui.screenshot(region=(left, top, region_size, region_size))
            screenshot.save(screenshot_path)
            logging.debug(f"Screenshot saved: {screenshot_path}")
            return self.screenshot_counter
            
        except Exception as e:
            logging.exception(f"Error taking screenshot at ({x}, {y}): {e}")
            return None

    def on_mouse_event(self, x, y, button=None, pressed=None, delta=0):
        if not self.is_recording or self.start_time is None:
            return
            
        try:
            logging.debug(f"Mouse event detected: x={x}, y={y}, button={button}, pressed={pressed}, delta={delta}")
            current_time = time.time()
            timestamp = current_time - self.start_time
            
            if (current_time - self.last_timestamp) < self.min_event_interval:
                return
                
            event_data = None
            
            # Handle mouse movement
            if button is None and delta == 0:  # Move event
                x_diff = abs(x - self.last_recorded_pos[0])
                y_diff = abs(y - self.last_recorded_pos[1])
                
                if x_diff > self.mouse_move_threshold or y_diff > self.mouse_move_threshold:
                    event_data = {
                        'type': 'move',
                        'x': x,
                        'y': y,
                        'timestamp': timestamp
                    }
                    self.last_recorded_pos = (x, y)
                    self.last_mouse_position = (x, y)
            
            # Handle click events
            elif pressed is not None:  # Click event
                if button == mouse.Button.left:
                    if pressed:
                        screenshot_num = self.take_screenshot_around_click(x, y)
                        event_data = {
                            'type': 'mouseDown',
                            'x': x, 'y': y,
                            'button': button.name,
                            'timestamp': timestamp,
                            'screenshot': screenshot_num
                        }
                        self.last_recorded_pos = (x, y)
                    else:
                        event_data = {
                            'type': 'mouseUp',
                            'x': x, 'y': y,
                            'button': button.name,
                            'timestamp': timestamp
                        }
                else:  # Other mouse buttons
                    event_data = {
                        'type': 'mouseDown' if pressed else 'mouseUp',
                        'x': x, 'y': y,
                        'button': button.name,
                        'timestamp': timestamp,
                        'screenshot': None if pressed else None
                    }
                self.last_timestamp = current_time
                        
            elif delta:  # Scroll event
                event_data = {
                    'type': 'scroll',
                    'x': x, 'y': y,
                    'delta': delta,
                    'timestamp': timestamp
                }
                self.last_timestamp = current_time
                
            if event_data:
                logging.debug(f"Prepared event data: {event_data}")
                self.recorder.handle_mouse_event(event_data)
                self.last_timestamp = current_time
                
        except Exception as e:
            logging.exception(f"Error processing mouse event: {e}")
            return None

# Add test functionality
def test_recording(duration=10):
    """Run a test recording for specified duration"""
    import tempfile
    from pathlib import Path
    
    # Create temporary directory for screenshots
    temp_dir = Path(tempfile.mkdtemp())
    
    # Simple recorder mock class
    class SimpleRecorder:
        def handle_mouse_event(self, event_data):
            print(f"Recorded event: {event_data}")
    
    # Create and start recorder
    recorder = MouseRecorder(temp_dir, SimpleRecorder())
    print(f"Starting recording for {duration} seconds...")
    print("Move your mouse, click, or scroll to generate events")
    
    start_time = time.time()
    recorder.start(start_time)
    
    try:
        time.sleep(duration)
    except KeyboardInterrupt:
        print("\nRecording interrupted by user")
    finally:
        recorder.stop()
        print(f"Recording stopped. Screenshots saved in: {temp_dir}")

if __name__ == "__main__":
    # Run test recording when script is executed directly
    test_recording()