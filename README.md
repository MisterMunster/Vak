# Vak - Audio Batch Processor

Vak is a Python-based desktop application designed to streamline the processing of audio files stored in Google Drive. It automatically downloads audio files, transcribes them to text, generates their International Phonetic Alphabet (IPA) representation, logs the results to a Google Sheet, and organizes the processed files into a destination folder.

## Features

- **Google Drive Integration**: Fetches audio files from a specified input folder and moves them to a "Done" folder after processing.
- **Google Sheets Integration**: Logs file metadata, transcription, and phonetic spelling to a specified Google Sheet.
- **Audio Transcoding**: Automatically converts various audio formats (MP3, M4A) to WAV for compatibility with transcription engines using `pydub` and `ffmpeg`.
- **Speech Recognition**: Uses the Google Web Speech API (via `speech_recognition`) to transcribe audio to text.
- **Phonetic Conversion**: Converts transcribed text into IPA phonetics using `eng_to_ipa`.
- **Sanskrit Transliteration**: Converts IPA phonetics to Sanskrit (Devanagari) script.
- **IAST Conversion**: Converts Sanskrit Devanagari to International Alphabet of Sanskrit Transliteration (IAST).
- **User Friendly GUI**: Built with `tkinter`, providing a simple interface to manage configuration and view processing logs.

## Prerequisites

Before running the application, ensure you have the following installed:

1.  **Python 3.x**: [Download Python](https://www.python.org/downloads/)
2.  **FFmpeg**: Required for audio conversion.
    *   **Windows**: [Download FFmpeg](https://ffmpeg.org/download.html), extract it, and add the `bin` folder to your system PATH.
    *   **Mac/Linux**: Install via homebrew (`brew install ffmpeg`) or your package manager.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/MisterMunster/Vak.git
    cd Vak
    ```

2.  Install the required Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

To use Vak, you need a **Google Service Account** with permissions to access your Drive folders and Google Sheet.

1.  **Create a Service Account**: Go to the [Google Cloud Console](https://console.cloud.google.com/), create a project, and enable the **Google Drive API** and **Google Sheets API**.
2.  **Download JSON Key**: Create a key for the service account and download the JSON file.
3.  **Share Resources**:
    *   Share your **Input Drive Folder** with the service account email (Editor access).
    *   Share your **Done Drive Folder** with the service account email (Editor access).
    *   Share your **Google Sheet** with the service account email (Editor access).

## Usage

1.  Run the application:
    ```bash
    python main.py
    ```

2.  In the GUI, provide the following details:
    *   **Service Account JSON**: Path to the JSON key file you downloaded.
    *   **Input Drive Folder ID**: The ID from the URL of your input folder (e.g., `1A2b3C...`).
    *   **Done Drive Folder ID**: The ID from the URL of your destination folder.
    *   **Google Sheet ID**: The ID from the URL of your Google Sheet.

3.  Click **Batch Process**. The application will:
    *   Scan the input folder for audio files.
    *   Process each file one by one.
    *   Update the log window with progress.

## Component Overview

### `main.py`
The entry point of the application. It initializes the `tkinter` GUI, handles user inputs, and spawns a separate thread for the processing logic to keep the UI responsive.
*   **AudioApp Class**: Manages the UI layout, input validation, and log updates.

### `processor.py`
Contains the core business logic in the `BatchProcessor` class.
*   **`authenticate()`**: Connects to Google Drive and Sheets API.
*   **`process_folder()`**: The main loop that iterates through files in the input folder.
*   **`download_file()`**: Downloads files to a local temporary path.
*   **`convert_to_wav()`**: Converts MP3/M4A files to WAV format using `pydub`.
*   **`transcribe_and_phonetic()`**: Performs Speech-to-Text and IPA conversion.
*   **`update_sheet()`**: Appends the results to the Google Sheet.
*   **`move_file()`**: Moves the processed file to the "Done" folder using the Drive API.

## Logic Flow

1.  **Auth**: App uses the Service Account JSON to authenticate with Google APIs.
2.  **Fetch**: Queries Google Drive for files in the `Input Folder ID`.
3.  **Filter**: Filters files by extension (`.wav`, `.mp3`, `.m4a`).
4.  **Loop**: For each valid audio file:
    *   **Download**: Saves the file temporarily locally.
    *   **Convert**: If not already WAV, converts it to WAV.
    *   **Transcribe**: Sends audio to Google Web Speech API for text result.
    *   **IPA**: Converts text result to IPA symbols.
    *   **Sanskrit**: Converts IPA to Devanagari.
    *   **IAST**: Converts Devanagari to IAST.
    *   **Log**: Appends `[Filename, Timestamp, Text, Phonetic, Sanskrit, IAST]` to the Google Sheet.
    *   **Move**: Moves the original file on Drive to the `Done Folder ID`.
    *   **Cleanup**: Deletes local temporary files.
