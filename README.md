# ReadTheLips AI 🎙️

Whisprflow AI is a powerful audio and video transcription tool built with **Streamlit** and **OpenAI**. It allows you to upload media files or dictate directly to generate structured, speaker-identified transcripts.

## ✨ Features

-   **Multi-Format Support**: Upload MP3, MP4, WAV, M4A, MOV files.
-   **Audio Extraction**: Automatically extracts audio from video files for transcription.
-   **Smart Transcription**: Uses OpenAI's **Whisper** model for high-accuracy speech-to-text.
-   **Speaker Diarization**: Optionally uses **GPT-4o** to identify speakers and format the transcript into a readable script.
-   **Dictation Mode**: Record your voice directly within the app.
-   **Export**: Download transcripts as text files.

## 🛠️ Prerequisites

-   **Python 3.8+** installed on your system.
-   An **OpenAI API Key** (you will need this to run the transcription).

## 🚀 Installation

1.  **Clone the repository** (or download the files):
    ```bash
    git clone <repository-url>
    cd <repository-folder>
    ```

2.  **Create a Virtual Environment** (Recommended):
    ```bash
    # Windows
    python -m venv .venv
    .venv\Scripts\activate

    # macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## ⚙️ Configuration

You need an OpenAI API Key to use this application. You can provide it in two ways:

1.  **Environment Variable** (Secure):
    Set `OPENAI_API_KEY` in your environment variables. The app will automatically detect it.
    ```bash
    # Windows PowerShell
    $env:OPENAI_API_KEY="sk-..."

    # macOS/Linux
    export OPENAI_API_KEY="sk-..."
    ```

2.  **UI Input**:
    Enter your key directly in the sidebar when the app is running.

## ▶️ Running the App

With your virtual environment activated, run:

```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`.

## 📖 Usage Guide

1.  **Enter API Key**: If not set in the environment, paste your OpenAI API key in the sidebar.
2.  **Choose Mode**:
    *   **Upload File**: Drag and drop an audio or video file.
    *   **Dictate**: Click "Start Recording" to speak directly.
3.  **Settings**: Toggle "Identify Speakers (AI)" in the sidebar if you want GPT-4o to format the output (Note: This may take longer).
4.  **Transcribe**: Click the **Transcribe** button.
5.  **Download**: Once finished, view the transcript on screen or click **Download as Text**.

## 🧩 Troubleshooting

-   **'streamlit' is not recognized**: Ensure you have activated your virtual environment (`.venv\Scripts\activate`) before running the command.
-   **API Error**: Check that your OpenAI API key is valid and has access to GPT-4o and Whisper.
