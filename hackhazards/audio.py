import speech_recognition as sr
import threading
from gtts import gTTS
import os
import time
from pygame import mixer
import queue
from text import Textify
import io

# Language mapping dictionary
LANGUAGE_CODES = {
    # Common full names to ISO 639-1 codes
    'konkani': 'kok',
    'hindi': 'hi',
    'english': 'en',
    'spanish': 'es',
    'french': 'fr',
    'german': 'de',
    'chinese': 'zh',
    'japanese': 'ja',
    'korean': 'ko',
    'russian': 'ru',
    'arabic': 'ar',
    'bengali': 'bn',
    'urdu': 'ur',
    'tamil': 'ta',
    'telugu': 'te',
    'marathi': 'mr',
    'gujarati': 'gu',
    'kannada': 'kn',
    'malayalam': 'ml',
    # Also accept ISO codes directly
    'kok': 'kok',
    'hi': 'hi',
    'en': 'en',
    'es': 'es',
    'fr': 'fr',
    'de': 'de',
    'zh': 'zh',
    'ja': 'ja',
    'ko': 'ko',
    'ru': 'ru',
    'ar': 'ar',
    'bn': 'bn',
    'ur': 'ur',
    'ta': 'ta',
    'te': 'te',
    'mr': 'mr',
    'gu': 'gu',
    'kn': 'kn',
    'ml': 'ml',
}

class RealTimeTranslator:
    def __init__(self, target_lang='hi', source_lang='auto'):
        self.recognizer = sr.Recognizer()
        self.audio_queue = queue.Queue()
        self.is_running = False
        mixer.init(frequency=44100)
        self.translator = Textify()
        # Convert language input to proper code
        self.target_lang = self.get_language_code(target_lang)
        self.source_lang = 'auto' if source_lang == 'auto' else self.get_language_code(source_lang)

    @staticmethod
    def get_language_code(language):
        """Convert language name or code to proper ISO 639-1 code"""
        lang_input = language.lower().strip()
        if lang_input in LANGUAGE_CODES:
            return LANGUAGE_CODES[lang_input]
        print(f"Warning: Unknown language '{language}'. Using English (en) instead.")
        return 'en'

    @staticmethod
    def list_available_languages():
        """Return a formatted string of available languages"""
        full_names = sorted(set(key for key in LANGUAGE_CODES.keys() 
                              if len(key) > 2))  # Only show full names
        return ", ".join(full_names)

    def listen_audio(self):
        with sr.Microphone() as source:
            print("Adjusting for ambient noise... Please wait...")
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print("Ready! Start speaking...")
            
            while self.is_running:
                try:
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=3)
                    self.audio_queue.put(audio)
                except sr.WaitTimeoutError:
                    continue
                except Exception as e:
                    print(f"Error listening: {str(e)}")

    def process_audio(self):
        while self.is_running:
            if not self.audio_queue.empty():
                audio = self.audio_queue.get()
                try:
                    # Convert speech to text
                    text = self.recognizer.recognize_google(audio)
                    print(f"Original text: {text}")

                    # Use the instance target language
                    translated_text = self.translate_text(text, self.target_lang, self.source_lang)
                    print(f"Translated text: {translated_text}")

                    # Pass the target language to text_to_speech
                    self.text_to_speech(translated_text, self.target_lang)

                except sr.UnknownValueError:
                    print("Could not understand the audio")
                except sr.RequestError as e:
                    print(f"Could not request results; {str(e)}")
                except Exception as e:
                    print(f"Error processing audio: {str(e)}")

    def translate_text(self, text, target_language='hi', source_language='auto'):
        # Convert language codes if full names are provided
        target_code = self.get_language_code(target_language)
        source_code = 'auto' if source_language == 'auto' else self.get_language_code(source_language)
        
        translated_text = self.translator.translate_text(
            text=text,
            target_lang=target_code,
            source_lang=source_code
        )
        return translated_text

    def text_to_speech(self, text, language='hi'):
        try:
            # Convert language code if full name is provided
            language_code = self.get_language_code(language)
            
            # Create an in-memory bytes buffer
            mp3_fp = io.BytesIO()
            
            # Generate the audio and save it to the in-memory buffer
            tts = gTTS(text=text, lang=language_code)
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            
            # Reinitialize mixer before each playback
            mixer.quit()
            mixer.init(frequency=44100)
            
            # Load and play the audio from memory
            mixer.music.load(mp3_fp)
            mixer.music.play()
            
            # Wait for playback to finish
            while mixer.music.get_busy():
                time.sleep(0.1)
            
        except Exception as e:
            print(f"Error in text to speech: {str(e)}")

    def start(self):
        self.is_running = True
        listen_thread = threading.Thread(target=self.listen_audio)
        process_thread = threading.Thread(target=self.process_audio)
        
        listen_thread.start()
        process_thread.start()

    def stop(self):
        self.is_running = False

# Example usage
if __name__ == "__main__":
    print("Real-Time Voice Translator")
    print("\nAvailable languages:")
    print(RealTimeTranslator.list_available_languages())
    print("\nYou can use either the full language name (e.g., 'Hindi') or its code (e.g., 'hi')")
    
    target_lang = input("\nEnter target language (default: Hindi): ").strip() or 'hindi'
    source_lang = input("Enter source language (or 'auto' for automatic detection): ").strip() or 'auto'
    
    translator = RealTimeTranslator(target_lang=target_lang, source_lang=source_lang)
    try:
        translator.start()
        print(f"\nTranslating from {source_lang} to {target_lang}")
        print("Press Enter to stop...")
        input()
    finally:
        translator.stop()