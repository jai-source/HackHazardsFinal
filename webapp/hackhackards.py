from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from aitranslator import Textify
import os
import tempfile
import shutil
import speech_recognition as sr
from gtts import gTTS
import base64
import io
from pydub import AudioSegment
from langcodes import Language  

import shutil

# Dynamically detect FFmpeg and FFprobe paths
ffmpeg_path = shutil.which("ffmpeg")
ffprobe_path = shutil.which("ffprobe")

if not ffmpeg_path or not ffprobe_path:
    raise FileNotFoundError("FFmpeg or FFprobe not found. Please ensure they are installed and accessible in the system PATH.")
else:
    print(f"Using FFmpeg: {ffmpeg_path}")
    print(f"Using FFprobe: {ffprobe_path}")

# Explicitly set the paths for pydub
AudioSegment.converter = ffmpeg_path
AudioSegment.ffprobe = ffprobe_path

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins

# Increase file upload size limit
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/textify")
def textify():
    return render_template("textify.html")

@app.route("/audiomac_real")
def audiomac_real():
    return render_template("audiomac_real.html")

@app.route("/audiomac")
def audiomac():
    return render_template("audiomac.html")

@app.route("/translate", methods=["POST"])
def translate():
    try:
        data = request.get_json()
        text = data['text']
        srcLangCode = getLanguageCode(data['srcLang'])
        destLangCode = getLanguageCode(data['destLang'])
        translator = Textify()
        translatedText = translator.translate_text(text, destLangCode, srcLangCode)
        return jsonify({"translatedText": translatedText}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/translate-audio", methods=["POST"])
def translate_audio():
    try:
        print("Incoming request:", request.form, request.files)  # Log request data

        # Get audio file from request
        if "audio" not in request.files:
            print("No audio file provided")
            return jsonify({"error": "No audio file provided"}), 400

        audio_file = request.files["audio"]
        source_lang = request.form.get("source_lang", "auto")
        target_lang = request.form.get("target_lang", "en")

        # Log source and target languages
        print(f"Source language: {source_lang}, Target language: {target_lang}")

        # Use a temporary directory for audio processing
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_file_path = os.path.join(temp_dir, "uploaded_audio.wav")
            audio_file.save(audio_file_path)
            print(f"Audio file saved at: {audio_file_path}")

            # Convert the audio file to PCM WAV format if necessary
            pcm_wav_path = os.path.join(temp_dir, "converted_audio.wav")
            audio = AudioSegment.from_file(audio_file_path)
            audio.export(pcm_wav_path, format="wav", codec="pcm_s16le")
            print(f"PCM WAV file created at: {pcm_wav_path}")

            # Explicitly delete the AudioSegment object to release the file lock
            del audio

            # Initialize recognizer
            recognizer = sr.Recognizer()

            # Convert speech to text
            with sr.AudioFile(pcm_wav_path) as source:
                recognizer.adjust_for_ambient_noise(source)
                audio_data = recognizer.record(source)

                try:
                    text = recognizer.recognize_google(audio_data, language=source_lang)
                    print(f"Recognized text: {text}")
                except sr.UnknownValueError:
                    print("Could not understand the audio")
                    return jsonify({"error": "Could not understand the audio"}), 400
                except sr.RequestError as e:
                    print(f"Speech recognition error: {str(e)}")
                    return jsonify({"error": f"Speech recognition error: {str(e)}"}), 500

            # Translate the text
            translator = Textify()
            basic_translation = translator.translate_text(text, target_lang, source_lang)
            print(f"Translated text: {basic_translation}")

            # Convert translated text to speech
            tts = gTTS(text=basic_translation, lang=target_lang)
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)
            print("Translated audio generated successfully")

            # Return the audio as base64
            audio_b64 = base64.b64encode(audio_fp.read()).decode("utf-8")
            print("Audio successfully encoded to base64")

            return jsonify({
                "recognized_text": text,
                "basic_translation": basic_translation,
                "audio_base64": audio_b64
            })

    except Exception as e:
        print("Error in translate_audio:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/delete-audio-files", methods=["POST"])
def delete_audio_files():
    try:
        # Define the directory containing audio files
        audio_dir = os.path.join(os.path.dirname(__file__), "../audio_files")
        
        if not os.path.exists(audio_dir):
            return jsonify({"message": "Audio directory does not exist."}), 200

        # Delete all files in the audio_files directory
        for file_name in os.listdir(audio_dir):
            file_path = os.path.join(audio_dir, file_name)
            if os.path.isfile(file_path):
                try:
                    os.unlink(file_path)
                    print(f"Deleted file: {file_path}")
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")

        return jsonify({"message": "All audio files deleted successfully."}), 200

    except Exception as e:
        print("Error in delete_audio_files:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/clean-audio-files", methods=["POST"])
def clean_audio_files():
    try:
        audio_dir = os.path.join(os.path.dirname(__file__), "../audio_files")

        if not os.path.exists(audio_dir):
            return jsonify({"message": "Audio directory does not exist."}), 200

        for file_name in os.listdir(audio_dir):
            file_path = os.path.join(audio_dir, file_name)
            if os.path.isfile(file_path):
                try:
                    os.unlink(file_path)
                    print(f"Deleted file: {file_path}")
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")

        return jsonify({"message": "All audio files cleaned up successfully."}), 200

    except Exception as e:
        print("Error in clean_audio_files:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/check-ffmpeg", methods=["GET"])
def check_ffmpeg():
    try:
        import subprocess
        result = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return jsonify({"ffmpeg_version": result.stdout.decode("utf-8")}), 200
    except FileNotFoundError:
        return jsonify({"error": "FFmpeg is not installed or not found in PATH"}), 500

@app.route("/test-audio-conversion", methods=["POST"])
def test_audio_conversion():
    try:
        audio_file = request.files["audio"]
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, "input_audio.wav")
            output_path = os.path.join(temp_dir, "output_audio.wav")
            audio_file.save(input_path)
            audio = AudioSegment.from_file(input_path)
            audio.export(output_path, format="wav", codec="pcm_s16le")
            return jsonify({"message": "Audio conversion successful"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def getLanguageCode(language):
    try:
        # Use langcodes to validate and fetch the language code
        lang = Language.find(language)
        return lang.language
    except Exception as e:
        print(f"Error finding language code for '{language}': {e}")
        return "en"  # Default to English if language is not found

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000, debug=True)
