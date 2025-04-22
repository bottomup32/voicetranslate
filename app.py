import os
import tkinter as tk
from tkinter import font
import openai
from openai import OpenAI
import pyaudio
import wave
import threading
import tempfile
import time
import numpy as np
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI API key setup
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

class TranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bilingual Voice Translator (Korean-English)")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")
        
        # Translation status
        self.is_translating = False
        self.frames = []
        
        # Audio settings
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000  # Reduced sample rate for better compatibility with Whisper
        self.chunk = 1024
        self.audio = pyaudio.PyAudio()
        
        # Voice activity detection
        self.silence_threshold = 300  # Adjust based on your microphone
        self.silence_frames_limit = 15  # How many silent frames before stopping
        self.currently_speaking = False
        self.silence_frames = 0
        
        # Create UI elements
        self.setup_ui()
    
    def setup_ui(self):
        # Title label
        title_font = font.Font(family="Arial", size=28, weight="bold")
        title = tk.Label(self.root, text="Bilingual Voice Translator (Korean-English)", font=title_font, bg="#f0f0f0")
        title.pack(pady=30)
        
        # Status label
        self.status_font = font.Font(family="Arial", size=14)
        self.status_label = tk.Label(self.root, text="Ready for translation", font=self.status_font, bg="#f0f0f0")
        self.status_label.pack(pady=15)
        
        # Translation result text area with scrollbar
        result_font = font.Font(family="Arial", size=18)
        
        # 텍스트 영역과 스크롤바를 포함할 프레임
        text_frame = tk.Frame(self.root, bg="#f0f0f0")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)
        
        # 스크롤바 추가
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 텍스트 영역 생성 및 스크롤바 연결
        self.result_text = tk.Text(text_frame, height=20, width=80, font=result_font, 
                                  yscrollcommand=scrollbar.set, 
                                  bg="white", fg="#333333",
                                  padx=10, pady=10,
                                  wrap=tk.WORD)  # 단어 단위로 줄바꿈
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.result_text.yview)
        
        # Button frame
        button_frame = tk.Frame(self.root, bg="#f0f0f0")
        button_frame.pack(pady=20)
        
        # 버튼 스타일 개선
        button_style = {
            "font": self.status_font,
            "borderwidth": 2, 
            "relief": tk.RAISED,
            "height": 2
        }
        
        # Clear button
        self.clear_button = tk.Button(button_frame, text="Clear Text", 
                                     command=self.clear_text,
                                     bg="#FF9800", fg="white", 
                                     width=15, **button_style)
        self.clear_button.grid(row=0, column=0, padx=15)
        
        # Start translation button
        self.start_button = tk.Button(button_frame, text="Start Translation", 
                                     command=self.start_translation,
                                     bg="#4CAF50", fg="white", 
                                     width=18, **button_style)
        self.start_button.grid(row=0, column=1, padx=15)
        
        # Stop translation button
        self.stop_button = tk.Button(button_frame, text="Stop Translation", 
                                    command=self.stop_translation,
                                    bg="#F44336", fg="white", 
                                    width=18, state=tk.DISABLED,
                                    **button_style)
        self.stop_button.grid(row=0, column=2, padx=15)
        
        # Exit button
        self.quit_button = tk.Button(button_frame, text="Exit", 
                                    command=self.quit_app,
                                    bg="#2196F3", fg="white", 
                                    width=15, **button_style)
        self.quit_button.grid(row=0, column=3, padx=15)
    
    def clear_text(self):
        self.result_text.delete(1.0, tk.END)
    
    def start_translation(self):
        self.is_translating = True
        self.status_label.config(text="Translating... (Waiting for speech)")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Start continuous translation thread
        self.translate_thread = threading.Thread(target=self.continuous_translation)
        self.translate_thread.daemon = True
        self.translate_thread.start()
    
    def get_rms(self, data):
        """Calculate the RMS (Root Mean Square) volume of audio data"""
        # Convert bytes to numpy array
        data_np = np.frombuffer(data, dtype=np.int16)
        # Avoid division by zero or negative values
        squared = np.square(data_np.astype(np.float64))
        mean_squared = np.mean(squared) if len(data_np) > 0 else 0
        return np.sqrt(mean_squared) if mean_squared > 0 else 0
    
    def continuous_translation(self):
        try:
            stream = self.audio.open(format=self.format, channels=self.channels,
                                    rate=self.rate, input=True,
                                    frames_per_buffer=self.chunk)
            
            self.frames = []
            self.currently_speaking = False
            self.silence_frames = 0
            
            # Continuously monitor for speech
            while self.is_translating:
                try:
                    data = stream.read(self.chunk, exception_on_overflow=False)
                    
                    # Calculate audio level for voice activity detection
                    rms = self.get_rms(data)
                    
                    # Detect if speaking
                    if rms > self.silence_threshold:
                        if not self.currently_speaking:
                            # Speech just started
                            self.currently_speaking = True
                            self.root.after(0, lambda: self.status_label.config(text="Translating... (Speech detected)"))
                        
                        # Reset silence counter
                        self.silence_frames = 0
                        
                        # Add frame to buffer
                        self.frames.append(data)
                    else:
                        # No speech detected
                        if self.currently_speaking:
                            # Count silent frames
                            self.silence_frames += 1
                            
                            # Add frame to buffer (to capture trailing speech)
                            self.frames.append(data)
                            
                            # If enough silence, process the speech
                            if self.silence_frames >= self.silence_frames_limit:
                                self.currently_speaking = False
                                self.root.after(0, lambda: self.status_label.config(text="Translating... (Processing speech)"))
                                
                                # Process collected audio if we have enough frames
                                if len(self.frames) > 10:  # Minimum frames to process
                                    frames_to_process = self.frames.copy()
                                    self.frames = []
                                    
                                    process_thread = threading.Thread(
                                        target=self.process_audio, 
                                        args=(frames_to_process,)
                                    )
                                    process_thread.daemon = True
                                    process_thread.start()
                                else:
                                    # Too short, discard
                                    self.frames = []
                                    self.root.after(0, lambda: self.status_label.config(text="Translating... (Waiting for speech)"))
                except Exception as e:
                    print(f"Error reading audio: {e}")
                    # Brief pause to prevent CPU hogging in case of persistent errors
                    time.sleep(0.1)
                
            # Close stream when translation stops
            stream.stop_stream()
            stream.close()
        except Exception as e:
            print(f"Error in audio stream setup: {e}")
            self.root.after(0, lambda: self.status_label.config(text=f"Error: {e}"))
            self.is_translating = False
            self.root.after(0, self.stop_translation)
    
    def process_audio(self, frames):
        # Create temporary WAV file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav:
            temp_filename = temp_wav.name
        
        # Save WAV file
        wf = wave.open(temp_filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        try:
            # First, transcribe with auto language detection
            with open(temp_filename, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            
            transcribed_text = transcript.text
            
            # Translate if we have valid text
            if transcribed_text and transcribed_text.strip() and len(transcribed_text.strip()) > 1:
                # Detect language and translate
                # Use GPT to detect language and translate accordingly
                chat_completion = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a professional translator. First, identify if the text is primarily Korean or English. Then translate it to the other language. Output format should be JSON with 'source_language', 'source_text', and 'translated_text' fields."},
                        {"role": "user", "content": transcribed_text}
                    ],
                    response_format={"type": "json_object"}
                )
                
                response = chat_completion.choices[0].message.content
                # Simple parsing of JSON-like response
                import json
                try:
                    translation_data = json.loads(response)
                    source_language = translation_data.get("source_language", "Unknown")
                    source_text = translation_data.get("source_text", transcribed_text)
                    translated_text = translation_data.get("translated_text", "Translation failed")
                    
                    # Update UI based on detected language
                    if source_language.lower() in ["korean", "ko", "kr"]:
                        self.update_ui(source_text, translated_text, is_korean_source=True)
                    else:
                        self.update_ui(translated_text, source_text, is_korean_source=False)
                except json.JSONDecodeError:
                    # Fallback for non-JSON responses
                    self.update_ui(transcribed_text, response, is_korean_source=True)
                    
            else:
                # No valid speech detected
                self.root.after(0, lambda: self.status_label.config(text="Translating... (No valid speech detected)"))
        
        except Exception as e:
            print(f"Error during processing: {e}")
            self.root.after(0, lambda: self.status_label.config(text=f"Error: {e}"))
        
        finally:
            # Remove temporary file
            try:
                os.unlink(temp_filename)
            except:
                pass
            
            # Reset to waiting state
            if self.is_translating:
                self.root.after(0, lambda: self.status_label.config(text="Translating... (Waiting for speech)"))
    
    def update_ui(self, source_text, translated_text, is_korean_source=True):
        # Use after method to execute in UI thread
        self.root.after(0, self._update_ui, source_text, translated_text, is_korean_source)
    
    def _update_ui(self, source_text, translated_text, is_korean_source):
        if is_korean_source:
            self.result_text.insert(tk.END, f"한국어: {source_text}\n")
            self.result_text.insert(tk.END, f"English: {translated_text}\n\n")
        else:
            self.result_text.insert(tk.END, f"English: {source_text}\n")
            self.result_text.insert(tk.END, f"한국어: {translated_text}\n\n")
        self.result_text.see(tk.END)  # Scroll to bottom
    
    def stop_translation(self):
        self.is_translating = False
        self.status_label.config(text="Translation stopped")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
    
    def quit_app(self):
        # Stop translation
        self.is_translating = False
        
        # Terminate PyAudio
        self.audio.terminate()
        
        # Exit application
        self.root.destroy()

# Run main application
if __name__ == "__main__":
    root = tk.Tk()
    app = TranslatorApp(root)
    root.mainloop()