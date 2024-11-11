import time
from pathlib import Path
import pyautogui
import traceback
import sys
import logging

# Configure logging with the correct encoding
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(levelname)s - %(message)s',
                   handlers=[
                       logging.FileHandler('logs/player_debug.log', encoding='utf-8'),
                       logging.StreamHandler(sys.stdout)
                   ])

class ActionPlayer:
    def __init__(self):
        self.running = False
        self.log_handler = None
        self.log_callback = self._default_log_handler
        
        # Create logs directory if it doesn't exist
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        self.cleanup_logging()  # Initialize clean logging state
        logging.info("ActionPlayer initialized")
    
    def cleanup_logging(self):
        """Clean up logging handlers and reinitialize"""
        # Remove all handlers
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Setup log file path
        log_file = self.logs_dir / "player_debug.log"
        
        # Reinitialize basic logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            force=True,
            handlers=[
                logging.FileHandler(str(log_file), encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _default_log_handler(self, message, level="INFO"):
        """Default handler that prints to console"""
        print(f"{level}: {message}")
        
    def set_log_callback(self, callback):
        """Sets the callback function for log messages"""
        if callback is None:
            self.log_callback = self._default_log_handler
        else:
            self.log_callback = callback

    def _handle_log(self, message, level="INFO"):
        """Internal method to handle log messages"""
        try:
            self.log_callback(message, level)
        except Exception as e:
            print(f"Error in log callback: {e}")
            print(f"{level}: {message}")

    def play(self, code):
        self.cleanup_logging()
        self.running = True
        logging.info("Beginning playback")
        logging.debug(f"Code to execute:\n{code}")
        try:
            # Validate code input
            if not isinstance(code, str):
                logging.error(f"Invalid code type: {type(code)}")
                return
            if not code.strip():
                logging.error("Empty macro code")
                return
            
            logging.info("Starting macro playback")
            logging.debug(f"Code length: {len(code)}")
            
            # Create namespace with required imports
            namespace = {
                'pyautogui': pyautogui,
                'time': time,
                'Path': Path,
                'logging': logging
            }
            
            # Execute the code
            try:
                exec(code, namespace)
                if 'run_script' not in namespace:
                    logging.error("run_script() function not found in the code")
                    return
                    
                logging.info("Executing run_script()")
                logging.info("Executing recorded macro")
                namespace['run_script']()
                
            except SyntaxError as se:
                logging.error(f"Syntax error: {se}")
                return
            except Exception as e:
                logging.exception(f"Exception during macro execution: {e}")
                traceback.print_exc()
                return
                
        finally:
            self.running = False
            logging.info("Playback finished")
            self.cleanup_logging()
            
    def stop(self):
        self.running = False
        logging.info("Stopping playback")
        self.cleanup_logging()  # Clean up when stopping

if __name__ == '__main__':
    # Test code for ActionPlayer
    player = ActionPlayer()
    test_code = """
def run_script():
    print("Test macro running...")
    time.sleep(1)
    print("Moving mouse to (100, 100)")
    pyautogui.moveTo(100, 100)
    """
    print("Starting test playback...")
    player.play(test_code)