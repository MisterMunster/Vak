"""Google Drive / Sheets batch processing.

Downloads audio files from a Drive folder, runs each through the local
pipeline (pipeline.process_file), logs results to a Google Sheet and moves
processed files to a "Done" folder.
"""
import io
import os
import re
import tempfile
import time

import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

import pipeline


class DriveBatchProcessor:
    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets',
    ]

    def __init__(self, service_account_path):
        self.service_account_path = service_account_path
        self.drive_service = None
        self.sheets_client = None

    def authenticate(self):
        try:
            creds = Credentials.from_service_account_file(
                self.service_account_path, scopes=self.SCOPES)
            self.drive_service = build('drive', 'v3', credentials=creds)
            self.sheets_client = gspread.authorize(creds)
            return True, "Authentication successful."
        except Exception as e:
            return False, f"Authentication failed: {e}"

    def download_file(self, file_id, file_name, dest_dir):
        """Downloads a Drive file into dest_dir with a sanitized name."""
        request = self.drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        safe_name = re.sub(r'[\\/:*?"<>|]', '_', file_name)
        local_path = os.path.join(dest_dir, safe_name)
        with open(local_path, "wb") as f:
            f.write(fh.getbuffer())
        return local_path

    def update_sheet(self, sheet_id, data_row):
        try:
            sheet = self.sheets_client.open_by_key(sheet_id).sheet1
            sheet.append_row(data_row)
            return True, None
        except Exception as e:
            return False, str(e)

    def move_file(self, file_id, destination_folder_id):
        try:
            file = self.drive_service.files().get(
                fileId=file_id, fields='parents').execute()
            previous_parents = ",".join(file.get('parents', []))
            self.drive_service.files().update(
                fileId=file_id,
                addParents=destination_folder_id,
                removeParents=previous_parents,
                fields='id, parents').execute()
            return True, None
        except Exception as e:
            return False, str(e)

    def list_audio_files(self, input_folder_id):
        query = f"'{input_folder_id}' in parents and trashed = false"
        files = []
        page_token = None
        while True:
            results = self.drive_service.files().list(
                q=query, pageToken=page_token,
                fields="nextPageToken, files(id, name, mimeType)").execute()
            files.extend(results.get('files', []))
            page_token = results.get('nextPageToken')
            if not page_token:
                break
        return [f for f in files if pipeline.is_supported(f['name'])]

    def process_folder(self, input_folder_id, done_folder_id, sheet_id, log_callback):
        log_callback(f"Starting batch process for folder ID: {input_folder_id}")

        try:
            audio_files = self.list_audio_files(input_folder_id)
        except Exception as e:
            log_callback(f"Could not list input folder: {e}")
            return

        if not audio_files:
            log_callback("No supported audio files found in input folder.")
            return

        log_callback(f"Found {len(audio_files)} audio files to process.")
        temp_dir = tempfile.mkdtemp(prefix="vak_")

        for item in audio_files:
            file_id, file_name = item['id'], item['name']
            log_callback(f"Processing: {file_name}...")

            local_path = None
            try:
                local_path = self.download_file(file_id, file_name, temp_dir)
                result = pipeline.process_file(local_path)
            except Exception as e:
                log_callback(f"  - Failed: {e}")
                continue
            finally:
                if local_path and os.path.exists(local_path):
                    try:
                        os.remove(local_path)
                    except OSError:
                        pass

            if result.ok:
                log_callback(f"  - Text: {result.text}")
                log_callback(f"  - Phonetic: {result.ipa}")
                log_callback(f"  - Sanskrit: {result.sanskrit}")
                log_callback(f"  - IAST: {result.iast}")
            else:
                log_callback(f"  - {result.error}")

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            # Columns: Filename, Timestamp, Text, Phonetic, Sanskrit, IAST, IAST_Separated
            row = [file_name, timestamp] + result.as_row()
            ok, err = self.update_sheet(sheet_id, row)
            log_callback("  - Sheet updated." if ok else f"  - Sheet update failed: {err}")

            ok, err = self.move_file(file_id, done_folder_id)
            log_callback("  - File moved to Done folder." if ok else f"  - Move failed: {err}")

        try:
            os.rmdir(temp_dir)
        except OSError:
            pass
        log_callback("Batch processing complete.")


# Backwards-compatible alias for the pre-refactor class name.
BatchProcessor = DriveBatchProcessor
