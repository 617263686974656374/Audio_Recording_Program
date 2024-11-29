import sounddevice as sd
import numpy as np
from pydub import AudioSegment
import threading
import os
import sys
import webrtcvad
from datetime import datetime

# Globálna premenná na zastavenie nahrávania
stop_recording = False


def normalize_audio(data):
    """Normalizuje audio dáta na rozsah -1 až 1."""
    max_val = np.max(np.abs(data))
    return data / max_val if max_val > 0 else data


def get_ffmpeg_path():
    """Získa cestu k FFmpeg."""
    if getattr(sys, 'frozen', False):  # Ak je spustený ako .exe
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)

    return os.path.join(base_path, "ffmpeg", "bin", "ffmpeg.exe")

# Nastavte cestu k FFmpeg
AudioSegment.converter = get_ffmpeg_path()
print(f"Používam FFmpeg z: {get_ffmpeg_path()}")

def save_audio_to_aac(audio_data, sample_rate, folder="output_audio"):
    """Uloží zaznamenaný zvuk do M4A formátu do určeného priečinka."""
    # Vytvorte priečinok, ak neexistuje
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"Priečinok '{folder}' bol vytvorený.")

    # Vygenerujte názov súboru podľa aktuálneho dátumu a času
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(folder, f"{timestamp}.m4a")

    print(f"Ukladám zvuk do {filename}...")
    audio_array = (audio_data * 32767).astype(np.int16)  # Konverzia na PCM int16
    audio_segment = AudioSegment(audio_array.tobytes(), frame_rate=sample_rate, sample_width=2, channels=1)

    # Export do MP4/M4A s AAC kodekom
    audio_segment.export(
        filename,
        format="mp4",
        codec="aac",
        parameters=["-b:a", "192k"]  # Nastavenie bitrate na 192 kbps
    )
    print(f"Zvuk uložený do {filename}.")

def user_input_listener():
    """Sleduje vstup používateľa a zastaví nahrávanie pri stlačení Enter."""
    global stop_recording
    input("Stlačte Enter na ukončenie nahrávania.\n")
    stop_recording = True
    print("Zastavujem nahrávanie...")

def record_audio_continuously(sample_rate=44100):
    """Nepretržité nahrávanie zvuku s možnosťou ukončiť stlačením Enter."""
    global stop_recording
    recording = []
    print("Nahrávanie spustené. Stlačte Enter na ukončenie.")
    while not stop_recording:
        chunk = sd.rec(int(1 * sample_rate), samplerate=sample_rate, channels=1, dtype="float32")
        sd.wait()
        recording.append(chunk)
    print("Nahrávanie ukončené.")
    return np.concatenate(recording, axis=0)

def detect_human_voice_vad(chunk, sample_rate=16000):
    """Použitie VAD na detekciu hlasu."""
    vad = webrtcvad.Vad()
    vad.set_mode(1)  # Stredná citlivosť

    # Konverzia do PCM formátu (16-bit int)
    pcm_data = (chunk.flatten() * 32767).astype(np.int16).tobytes()

    # Veľkosť rámca
    frame_duration_ms = 30  # Dĺžka rámca (10, 20 alebo 30 ms)
    frame_size = int(sample_rate * frame_duration_ms / 1000)  # Počet vzoriek

    # Doplníme PCM dáta na správnu veľkosť
    if len(pcm_data) < frame_size * 2:
        pcm_data += b'\x00' * (frame_size * 2 - len(pcm_data))

    try:
        # Vyhodnotenie viacerých rámcov pre presnosť
        frame_results = []
        for i in range(5):  # Spracujte 5 rámcov za sebou
            result = vad.is_speech(pcm_data[:frame_size * 2], sample_rate)
            frame_results.append(result)

        # Väčšina rámcov musí byť detegovaná ako hlas
        return sum(frame_results) > len(frame_results) // 2
    except Exception as e:
        print(f"Chyba pri detekcii: {e}")
        return False



def record_audio_on_detection(sample_rate=16000, min_record_time=600):
    """
    Nahráva len pri detekcii zvuku.
    """
    global stop_recording
    recording = []
    silence_duration = 0
    chunk_duration = 30  # Trvanie úseku (ms)

    print("Nahrávanie spustené. Stlačte Enter na ukončenie.")

    while not stop_recording and silence_duration < min_record_time:
        # Zachytávanie zvuku
        frame_size = int(sample_rate * chunk_duration / 1000)
        chunk = sd.rec(frame_size, samplerate=sample_rate, channels=1, dtype="float32")
        sd.wait()

        try:
            if detect_human_voice_vad(chunk, sample_rate=sample_rate):
                silence_duration = 0
                print("Zvuk detekovaný. Pokračujem v nahrávaní...")
                recording.append(chunk)
            else:
                silence_duration += chunk_duration / 1000
                print(f"Ticho detekované {silence_duration}/{min_record_time} sekúnd...")
        except ValueError as e:
            print(f"Chyba: {e}. Preskakujem tento úsek.")

    print("Nahrávanie ukončené.")
    return np.concatenate(recording, axis=0)


def monitor_audio_in_real_time(sample_rate=44100):
    """Počúvanie mikrofónu v reálnom čase bez ukladania."""
    global stop_recording
    print("Počúvanie mikrofónu v reálnom čase. Stlačte Enter na ukončenie.")

    def audio_callback(indata, outdata, frames, time, status):
        if status:
            print(f"Status: {status}")
        outdata[:] = indata  # Posielanie mikrofónového zvuku priamo na výstup (reproduktory)

    with sd.Stream(samplerate=sample_rate, channels=1, dtype="float32", callback=audio_callback):
        while not stop_recording:
            sd.sleep(100)  # Čaká na vstup používateľa
    print("Počúvanie ukončené.")

def main():
    global stop_recording
    print("Vyberte možnosť:")
    print("1. Nepretržité nahrávanie")
    print("2. Nahrávanie pri detekcii zvuku")
    print("3. Počúvanie mikrofónu v reálnom čase")
    choice = input("Zadajte číslo (1, 2 alebo 3): ")

    sample_rate = 16000  # WebRTC VAD vyžaduje podporované vzorkovacie frekvencie

    # Spustenie vlákna na sledovanie vstupu používateľa
    input_thread = threading.Thread(target=user_input_listener)
    input_thread.daemon = True
    input_thread.start()

    try:
        if choice == "1":
            audio_data = record_audio_continuously(sample_rate=sample_rate)
            save_audio_to_aac(audio_data, sample_rate)
        elif choice == "2":
            audio_data = record_audio_on_detection(sample_rate=sample_rate)
            save_audio_to_aac(audio_data, sample_rate)
        elif choice == "3":
            monitor_audio_in_real_time(sample_rate=sample_rate)
        else:
            print("Neplatná možnosť!")
    finally:
        stop_recording = True
        input_thread.join()



if __name__ == "__main__":
    main()
