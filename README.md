# Audio Recording Program

This program is designed for recording audio with human voice detection and saving it in AAC (M4A) format. It offers continuous recording, recording triggered by voice detection, and real-time audio monitoring without saving. The audio files are saved in a designated folder with unique names based on the current date and time.

---

## Requirements

- **Operating System:** Windows (packaged as an executable .exe).
- **Libraries:**
  - `sounddevice`
  - `numpy`
  - `pydub`
  - `webrtcvad`
  - `threading`
  - `os`
  - `sys`
  - `datetime`
- **FFmpeg:** FFmpeg is included in the package and does not need to be installed separately.

---

## Features

### 1. Continuous Recording
The program continuously records audio until the user presses `Enter`. The recorded audio is saved in the designated folder in M4A format.

### 2. Recording on Voice Detection
The program uses VAD (Voice Activity Detection) to detect human voices. Audio is recorded only when human speech is detected, minimizing background noise using filters and detection algorithms.

### 3. Real-Time Audio Monitoring
Audio is streamed directly from the microphone to the speakers without being saved. The program terminates when `Enter` is pressed.

---

## Usage

1. Run the program by double-clicking the `.exe` file or using a terminal command.
2. Choose one of the available options:
   - `1` - Continuous Recording
   - `2` - Recording on Voice Detection
   - `3` - Real-Time Audio Monitoring
3. Press `Enter` to stop the program.
4. Recorded audio files are saved in the `output_audio` folder, named as `YYYY-MM-DD_HH-MM-SS.m4a`.

---

## Creating an Executable .exe

1. Install **PyInstaller:**
   ```bash
   pip install pyinstaller
   ```

2. Ensure `ffmpeg` is included in the project folder structure:
   ```
   audio_program/
   ├── audio.py
   ├── ffmpeg/
       └── bin/
           └── ffmpeg.exe
   ```

3. Use the following command to create the .exe:
   ```bash
   pyinstaller --onefile --add-data "ffmpeg/bin/ffmpeg.exe;ffmpeg/bin" audio.py
   ```

4. The resulting `.exe` file will be located in the `dist/` folder.

---




