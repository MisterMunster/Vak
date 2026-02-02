import os
import time
import speech_recognition as sr
import eng_to_ipa as ipa
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import shutil
from pydub import AudioSegment

class BatchProcessor:
    def __init__(self, service_account_path):
        self.service_account_path = service_account_path
        self.scopes = [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets'
        ]
        self.creds = None
        self.drive_service = None
        self.sheets_client = None

    def authenticate(self):
        """Authenticates with Google Services."""
        try:
            self.creds = Credentials.from_service_account_file(
                self.service_account_path, scopes=self.scopes)
            self.drive_service = build('drive', 'v3', credentials=self.creds)
            self.sheets_client = gspread.authorize(self.creds)
            return True, "Authentication successful."
        except Exception as e:
            return False, f"Authentication failed: {str(e)}"

    def download_file(self, file_id, file_name):
        """Downloads a file from Google Drive."""
        request = self.drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        # Save to local temp file
        local_path = file_name
        with open(local_path, "wb") as f:
            f.write(fh.getbuffer())
        return local_path

    def convert_to_wav(self, file_path):
        """Converts audio file to WAV format for transcription."""
        if file_path.lower().endswith('.wav'):
             return file_path, False
        
        # New temp path
        wav_path = file_path + ".converted.wav"
        try:
            # pydub requires ffmpeg to be installed and in path for mp3/m4a
            audio = AudioSegment.from_file(file_path)
            audio.export(wav_path, format="wav")
            return wav_path, True
        except Exception as e:
            print(f"Conversion Error: {e}")
            return None, False

    def transcribe_and_phonetic(self, file_path):
        """Transcribes audio and generates phonetic spelling."""
        r = sr.Recognizer()
        
        wav_path, is_converted = self.convert_to_wav(file_path)
        
        if not wav_path:
            return "[Conversion Failed - Install FFMPEG?]", "[Error]"

        try:
            with sr.AudioFile(wav_path) as source:
                audio_data = r.record(source)
                text = r.recognize_google(audio_data)
                phonetic = ipa.convert(text)
        except sr.UnknownValueError:
            text = "[Unintelligible]"
            phonetic = "[N/A]"
        except Exception as e:
            text = f"[Error: {str(e)}]"
            phonetic = "[Error]"
        finally:
            if is_converted and os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except:
                    pass
        
        return text, phonetic

    def update_sheet(self, sheet_id, data_row):
        """Appends a row to the Google Sheet."""
        try:
            sheet = self.sheets_client.open_by_key(sheet_id).sheet1
            sheet.append_row(data_row)
            return True
        except Exception as e:
            print(f"Sheet Error: {e}")
            return False

    def move_file(self, file_id, destination_folder_id):
        """Moves a file to a new folder in Google Drive."""
        try:
            # Retrieve the existing parents to remove
            file = self.drive_service.files().get(fileId=file_id,
                                                  fields='parents').execute()
            previous_parents = ",".join(file.get('parents'))
            
            # Move the file by adding the new parent and removing the old ones
            self.drive_service.files().update(fileId=file_id,
                                              addParents=destination_folder_id,
                                              removeParents=previous_parents,
                                              fields='id, parents').execute()
            return True
        except Exception as e:
            print(f"Move Error: {e}")
            return False

    def process_folder(self, input_folder_id, done_folder_id, sheet_id, log_callback):
        """Main processing loop."""
        log_callback(f"Starting batch process for folder ID: {input_folder_id}")
        
        try:
            # List files in input folder
            # We sort of blindly accept anything that looks like audio or video, then filter by extension
            query = f"'{input_folder_id}' in parents and trashed = false"
            results = self.drive_service.files().list(
                q=query, fields="nextPageToken, files(id, name, mimeType)").execute()
            items = results.get('files', [])

            if not items:
                log_callback("No files found in input folder.")
                return
            
            # Filter for extensions locally
            valid_extensions = ('.wav', '.mp3', '.m4a')
            audio_files = [f for f in items if f['name'].lower().endswith(valid_extensions)]

            if not audio_files:
                log_callback("No supported audio files (.wav, .mp3, .m4a) found.")
                return

            log_callback(f"Found {len(audio_files)} audio files to process.")

            for item in audio_files:
                file_id = item['id']
                file_name = item['name']
                log_callback(f"Processing: {file_name}...")

                # 1. Download
                local_path = self.download_file(file_id, file_name)
                
                # 2. Transcribe & Phonetic
                name, phonetic = self.transcribe_and_phonetic(local_path)
                log_callback(f"  - Detected Name: {name}")
                log_callback(f"  - Phonetic: {phonetic}")
                
                # 3. Update Sheet
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                row = [file_name, timestamp, name, phonetic]
                self.update_sheet(sheet_id, row)
                log_callback("  - Sheet updated.")

                # 4. Move File
                self.move_file(file_id, done_folder_id)
                log_callback("  - File moved to Done folder.")

                # Cleanup local file
                try:
                    os.remove(local_path)
                except:
                    pass
            
            log_callback("Batch processing complete.")

        except Exception as e:
            log_callback(f"Critical Error: {str(e)}")
