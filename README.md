# AdultEmpire Movie Dumper

**AdultEmpire Movie Dumper** is a Python-based GUI tool designed to automate the downloading and organization of video content from AdultEmpire. It streamlines the process by handling login sessions, extracting `.m3u8` links, scraping metadata, and renaming files automatically.

## ✨ Features

*   **Persistent Login**: Logs in once and maintains the session.
*   **Auto-Metadata**: Scrapes Title, Studio, Cast, and Release Date.
*   **Smart Renaming**: Automatically renames files (e.g., `YYYY-MM-DD - Cast - Title [Studio].mp4`).
*   **Batch Downloading**: Queue multiple URLs and download them sequentially without re-logging.
*   **Quality Selection**: Choose your preferred resolution (4K, 1080p, etc.) or let the tool pick the best.
*   **Headless Mode**: Runs the browser in the background.
*   **Settings Tab**: Customize filename templates, thread count, and tool flags.

## 🛠️ Requirements

*   **Python 3.8+**
*   **Google Chrome** (required by Playwright)
*   **N_m3u8DL-RE**: This external tool is **REQUIRED** for downloading.

## 📦 Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/AE_Dumper.git
    cd AE_Dumper
    ```

2.  **Create and Activate Virtual Environment**:
    *   **Windows**:
        ```bash
        python -m venv .venv
        .venv\Scripts\activate
        ```
    *   **Linux/Mac**:
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```

3.  **Install Python Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Playwright Browsers**:
    ```bash
    playwright install
    ```

4.  **Setup External Tools**:
    *   Download `N_m3u8DL-RE` (Binary) from [GitHub](https://github.com/nilaoda/N_m3u8DL-RE/releases).
    *   Create a folder named `tools` in the script directory.
    *   Place `N_m3u8DL-RE.exe` inside the `tools` folder.
    *   **Structure**:
        ```text
        AE_Dumper/
        ├── tools/
        │   └── N_m3u8DL-RE.exe
        ├── ae_dumper.pyw
        ├── requirements.txt
        └── ...
        ```

## 🚀 Usage

Run the script using Python:

```bash
python ae_dumper.pyw
```

### Single Download
1.  Paste the video URL.
2.  The tool will auto-detect metadata.
3.  Click **DOWNLOAD**.

### Batch Download
1.  Go to the "Batch Download" tab.
2.  Paste a list of URLs (one per line).
3.  Click **AVVIA BATCH**.

## ⚙️ Settings

In the **Impostazioni** tab you can:
*   **Customize Filename**: Use placeholders like `{date}`, `{cast}`, `{title}`, `{studio}`.
*   **Threads**: Set the number of download threads.
*   **Flags**: Enable/Disable logs (`--no-log`) or date info (`--no-date-info`).

## ⚠️ Disclaimer
This tool is for educational purposes or personal archiving only. Respect the terms of service of the target website.
