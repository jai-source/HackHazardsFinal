from flask import Flask, request, jsonify
from flask_cors import CORS
import speech_recognition as sr
from gtts import gTTS
import io
import base64
from pydub import AudioSegment
from text import Textify
import tempfile
import os

app = Flask(__name__)
CORS(app)

recognizer = sr.Recognizer()
translator = Textify()

def get_language_code(lang_name):
    LANGUAGE_CODES = {
        'english': 'en', 'spanish': 'es', 'french': 'fr',
        'german': 'de', 'japanese': 'ja', 'hindi': 'hi',
        'en': 'en', 'es': 'es', 'fr': 'fr', 'de': 'de',
        'ja': 'ja', 'hi': 'hi'
    }
    return LANGUAGE_CODES.get(lang_name.lower(), 'en')

@app.route("/translate-audio", methods=["POST"])
def translate_audio():
    try:
        # Get the audio file from request
        file = request.files['audio']
        if not file:
            return jsonify({"error": "No audio file provided"}), 400

        print(f"Received audio file: {file.filename}, Content-Type: {file.content_type}")

        # Get language preferences
        source_lang = request.form.get("source_lang", "auto")
        target_lang = request.form.get("target_lang", "en")
        print(f"Source lang: {source_lang}, Target lang: {target_lang}")

        # Create a temporary file to save the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            # Convert WebM to WAV using pydub
            audio = AudioSegment.from_file(file, format="webm")
            audio.export(temp_file.name, format="wav")
            
            # Use speech recognition
            with sr.AudioFile(temp_file.name) as source:
                # Adjust for ambient noise and record
                recognizer.adjust_for_ambient_noise(source)
                audio_data = recognizer.record(source)
                
                try:
                    # Attempt speech recognition
                    text = recognizer.recognize_google(audio_data, language=get_language_code(source_lang))
                    print(f"Recognized text: {text}")
                except sr.UnknownValueError:
                    return jsonify({"error": "Could not understand the audio"}), 400
                except sr.RequestError as e:
                    return jsonify({"error": f"Speech recognition error: {str(e)}"}), 500

        # Clean up temporary file
        os.unlink(temp_file.name)

        try:
            # Translate the text
            basic = translator.translate_text(text, target_lang, source_lang)
            enhanced = translator.enhance_translation_with_ai(text, basic)
            print(f"Translation: {enhanced}")
        except Exception as e:
            print("Translation error:", e)
            return jsonify({"error": f"Translation error: {str(e)}"}), 500

        try:
            # Generate audio from translated text
            tts = gTTS(text=enhanced, lang=get_language_code(target_lang))
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)
            audio_b64 = base64.b64encode(audio_fp.read()).decode("utf-8")
        except Exception as e:
            print("Text-to-speech error:", e)
            return jsonify({"error": f"Text-to-speech error: {str(e)}"}), 500

        return jsonify({
            "recognized_text": text,
            "basic_translation": basic,
            "ai_translation": enhanced,
            "audio_base64": audio_b64
        })

    except Exception as e:
        print("Unhandled error:", e)
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
