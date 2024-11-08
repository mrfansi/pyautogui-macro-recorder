# PyAutoGUI Macro Recorder

PyAutoGUI Macro Recorder is a GUI application for recording and playing back user actions (macros) based on PyAutoGUI library. Unlike most similar solutions, PyAutoGUI Macro Recorder uses image recognition instead of absolute coordinates, making macros more reliable and resolution-independent.

## Key Features

- 🎥 Record mouse and keyboard actions:
  - Single and double clicks
  - Mouse movement and dragging
  - Scroll wheel actions
  - Keyboard input
  - Modifier keys support (Ctrl, Alt, Shift)
- 🖼️ Create screenshots of click areas for precise playback
- 🔍 Find screen elements by image recognition
- 📝 Generate Python script for playback
- 💾 Save projects with ability to run later
- 🎨 Built-in code editor with syntax highlighting
- 🖼️ Screenshot gallery with preview and editing
- 📋 Debug window with real-time action logging

## What Makes It Special

The main difference between PyAutoGUI Macro Recorder and alternatives is the use of computer vision to find elements on the screen. Instead of saving absolute click coordinates, the application creates screenshots of areas around click points and uses them to find the required elements during playback. This makes macros:

- Resolution independent
- Working with changed interface scaling
- Resistant to minor interface changes
- Portable between computers

## System Requirements

- Windows 10/11 (tested only on Windows)
- Python 3.8+
- Required libraries: pyautogui, pillow, opencv-python, keyboard, mouse

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/pyautogui-macro-recorder.git
cd pyautogui-macro-recorder

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Usage

1. Launch the application
2. Click "●" button to start recording
3. Perform the actions you want to record
4. Click "■" to stop recording
5. Review and edit the generated code if needed
6. Click "▶" to play back the macro
7. Use "💾" to save the project

### Project Structure

When you save a project, it creates the following structure:

```
your_project_name/
├── __init__.py
├── main.py          # Generated macro code
├── run.py          # Runner script
└── screens/        # Click area screenshots
    ├── 1.png
    ├── 2.png
    └── ...
```

### Generated Project

The saved project is a standalone Python package that can be run on any computer with Python and required dependencies installed. Each project contains:

- **main.py**: The main script with recorded actions
- **run.py**: A launcher that handles imports and runs the macro
- **screens/**: Directory with screenshots used for image recognition
- **__init__.py**: Makes the project a proper Python package

To run a saved project:
```bash
cd your_project_name
python run.py
```

## Limitations

- Application was developed and tested only on Windows
- Elements must be visible on screen for recognition to work
- It's recommended to make small pauses between actions while recording
- Some applications may block input simulation
- High DPI screens might require additional configuration

## Security

⚠️ Be careful when running macros from unknown sources - they may contain malicious code. Always review the macro code before running.

## Development

The project is open for contributions. Main areas for improvement:

- Adding Linux and macOS support
- Improving element recognition algorithms
- Adding screenshot editing capabilities
- Creating a marketplace for macro sharing

## Technical Details

- Written in Python using Tkinter for GUI
- Uses PyAutoGUI for input simulation
- Implements computer vision with OpenCV
- Supports high DPI displays
- Modular architecture for easy extension

## License

MIT License. See [LICENSE](LICENSE) file for details.

## Author

[Riocool] - [https://t.me/riocool]

## Acknowledgments

- [PyAutoGUI](https://github.com/asweigart/pyautogui)
- [TkCode](https://github.com/username/tkcode)
- All project contributors
