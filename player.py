import threading
import time
from pathlib import Path
import pyautogui
from PIL import Image
import re
import traceback
import sys
import cv2
import numpy as np
import logging

# Настраиваем логирование с правильной кодировкой
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(levelname)s - %(message)s',
                   handlers=[
                       logging.FileHandler('player_debug.log', encoding='utf-8'),
                       logging.StreamHandler(sys.stdout)
                   ])

class ActionPlayer:
    def __init__(self):
        self.running = False
        self.log_handler = None
    
    def play(self, code):
        self.running = True
        try:
            # Создаем локальное пространство имен для выполнения кода
            namespace = {}
            
            # Перехватываем вывод logging для отправки в GUI
            class LogHandler(logging.Handler):
                def emit(self, record):
                    msg = f"{record.asctime} - {record.levelname} - {record.getMessage()}"
                    if hasattr(self, 'callback'):
                        self.callback(msg, record.levelname)
            
            # Очищаем предыдущие обработчики
            logger = logging.getLogger()
            if self.log_handler:
                logger.removeHandler(self.log_handler)
            
            # Настраиваем новый обработчик
            self.log_handler = LogHandler()
            self.log_handler.callback = self.log_callback
            logger.addHandler(self.log_handler)
            logger.setLevel(logging.INFO)
            
            # Логируем начало выполнения
            logging.info("Executing run_script()")
            
            # Выполняем код
            exec(code, namespace)
            
            # Вызываем функцию run_script из пространства имен
            if 'run_script' in namespace:
                namespace['run_script']()
            else:
                logging.error("Function run_script() not found in the code")
            
        except Exception as e:
            logging.error(f"Error during playback: {str(e)}")
            traceback.print_exc()
        finally:
            self.running = False
            logging.info("Macro playback finished")
            # Удаляем обработчик после завершения
            if self.log_handler:
                logger = logging.getLogger()
                logger.removeHandler(self.log_handler)
                self.log_handler = None
            
    def stop(self):
        self.running = False