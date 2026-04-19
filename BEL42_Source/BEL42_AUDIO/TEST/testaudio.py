import whisper
from gtts import gTTS
from io import BytesIO
import pygame 
import sounddevice as sd 
import numpy as np

from openai import OpenAI
from dotenv import load_dotenv
import os 

load_dotenv()

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY")
)




def speak(text: str):
    tts = gTTS(text, lang='en')
    buffer = BytesIO()
    tts.write_to_fp(buffer)
    buffer.seek(0)

    pygame.mixer.init()
    pygame.mixer.music.load(buffer, 'mp3')
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pass

def listen(dur):
    model = whisper.load_model("base")
    speak("I am ready")

    fs = 16000
    audio = sd.rec(int(dur * fs), samplerate=fs, channels=1, dtype=np.float32)
    sd.wait()
    audio = audio.flatten()

    if np.max(np.abs(audio)) < 0.01:
        print("Warning: Very low audio level detected")

    result = model.transcribe(audio, language="en", fp16=False)
    return result['text']


