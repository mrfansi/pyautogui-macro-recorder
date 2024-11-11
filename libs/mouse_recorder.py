import time
import threading
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
        self.mouse_thread = None
        
        # Parameters for double-click detection
        self.last_down_sequence = []
        self.last_up_sequence = []
        self.double_click_threshold = 0.2
        
        self.recorder = recorder  # Store reference to main recorder
        
    def start(self, start_time):
        self.start_time = start_time
        self.is_recording = True
        self.last_timestamp = start_time
        
        # Start mouse tracking thread
        self.mouse_thread = threading.Thread(target=self.track_mouse_movement)
        self.mouse_thread.daemon = True
        self.mouse_thread.start()
        
        # Start mouse listener
        self.mouse_listener = mouse.Listener(
            on_move=self.on_mouse_event,
            on_click=self.on_mouse_event,
            on_scroll=self.on_mouse_event
        )
        self.mouse_listener.start()

    def stop(self):
        self.is_recording = False
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.mouse_thread and self.mouse_thread.is_alive():
            self.mouse_thread.join(timeout=1.0)
        self.start_time = None

    def track_mouse_movement(self):
        while self.is_recording:
            if not self.is_dragging:
                try:
                    current_pos = pyautogui.position()
                    x_diff = abs(current_pos[0] - self.last_recorded_pos[0])
                    y_diff = abs(current_pos[1] - self.last_recorded_pos[1])
                    
                    if x_diff > self.mouse_move_threshold or y_diff > self.mouse_move_threshold:
                        timestamp = time.time() - self.start_time
                        event_data = {
                            'type': 'move',
                            'x': current_pos[0],
                            'y': current_pos[1],
                            'timestamp': timestamp
                        }
                        self.last_recorded_pos = current_pos
                        self.last_mouse_position = current_pos
                        self.recorder.handle_mouse_event(event_data)  # Send to main recorder
                except Exception as e:
                    logging.error(f"Error tracking mouse: {e}")
            time.sleep(self.position_check_interval)

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
            return self.screenshot_counter
            
        except Exception as e:
            logging.error(f"Error taking screenshot at ({x}, {y}): {e}", exc_info=True)
            return None

    def on_mouse_event(self, x, y, button=None, pressed=None, delta=0):
        if not self.is_recording or self.start_time is None:
            return
            
        try:
            current_time = time.time()
            timestamp = current_time - self.start_time
            
            if (current_time - self.last_timestamp) < self.min_event_interval:
                return
                
            event_data = None
            
            if pressed is not None:  # Click event
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
                self.recorder.handle_mouse_event(event_data)  # Send to main recorder
                
        except Exception as e:
            logging.error(f"Error processing mouse event: {e}")
            return None