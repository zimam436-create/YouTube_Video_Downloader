# YTD — YouTube Downloader

**YTD** is a Windows-focused command-line YouTube downloader built to make `yt-dlp` easier to use for everyday users.

Instead of requiring users to understand format IDs, FFmpeg commands, playlist expressions, or complicated `yt-dlp` syntax, YTD provides a guided interface for video, audio, playlist ranges, quality selection, parallel downloads, automatic retries, and download reports.

> **A Zamify product — built by Zimam.**

---

## ✨ Features

- Simple interactive interface
- Video + audio downloads merged into MP4
- Audio-only downloads
- Playlist downloads
- Download a complete playlist or an exact range such as `2-6`
- Playlist-wide quality selection
- Automatic quality fallback:
  - requested quality when available
  - nearest lower quality when necessary
  - nearest higher quality when no lower/equal quality exists
- Clear `downgraded` / `upgraded` labels
- Sequential or parallel playlist downloading
- Automatic retry and troubleshooting for failed video downloads
- Multiple fallback format strategies when a normal download fails
- Protection against treating incomplete/partial files as successful downloads
- Playlist download reports
- Failed-download summary at the end
- Uses the official `yt-dlp` executable, FFmpeg, and Deno as supporting tools
- User-level installation — no administrator privileges required

## 🖥️ Requirements

- Windows 10 or newer
- Python 3.11 or newer
- Internet connection

The repository includes the same Windows yt-dlp, FFmpeg, Deno executable, and FFmpeg DLL set used by the tested YTD setup. No separate dependency download is required for the bundled Windows release.

## 🚀 Installation

### Easiest method

1. Download or clone this repository.
2. Make sure Python 3.11+ is installed.
3. Double-click `install.bat` once.
4. Close and reopen PowerShell.
5. Run:

```powershell
ytd "https://www.youtube.com/watch?v=VIDEO_ID"
```

You can also run YTD directly from the repository without installing the command launcher:

```powershell
.\ytd.cmd "https://www.youtube.com/watch?v=VIDEO_ID"
```

The bundled executables and FFmpeg DLLs stay with the project, so the same tested toolset is used by every installation of this release.

### Updating

Run:

```powershell
.\update.ps1
```

This refreshes the third-party tools used by YTD.

### Uninstalling

Run:

```powershell
.\uninstall.ps1
```

Your downloaded videos in the normal Windows `Downloads` folder are not removed.

---

## 📥 Basic Usage

```powershell
ytd "https://www.youtube.com/watch?v=VIDEO_ID"
```

For YouTube URLs containing `&`, quote the URL in PowerShell:

```powershell
ytd "https://www.youtube.com/watch?v=VIDEO_ID&list=PLAYLIST_ID"
```

YTD automatically detects whether the URL points to an individual video or a playlist.

---

## 📚 Playlist Downloads

When a playlist is detected, YTD lets you choose:

1. Entire playlist
2. A specific range
3. Video + Audio or Audio only
4. Video quality
5. Sequential or parallel downloads

For example, selecting:

```text
2-6
```

means exactly:

```text
#02
#03
#04
#05
#06
```

The playlist index is preserved in the filename:

```text
#02 - Video Title.mp4
#03 - Video Title.mp4
#04 - Video Title.mp4
```

---

## 🛠️ Automatic Troubleshooting

YTD does not immediately give up when a video fails.

After the normal playlist download finishes, failed videos are identified and YTD attempts alternative download strategies automatically. A failed attempt is not considered successful merely because one stream was downloaded.

YTD verifies the final output before marking a download as successful. Temporary files are cleaned up between fallback attempts.

This is especially useful when a video stream can be downloaded but its audio stream or final merge fails.

---

## 📄 Download Reports

Playlist downloads generate a `download_report.txt` file inside the playlist folder.

The report contains:

- Selected videos
- Duration
- Requested/actual quality
- Estimated size
- Total duration
- Total size
- Successful downloads
- Failed downloads
- Unavailable videos
- Error information

Example:

```text
#02  08:41      1080p       ~17.6 MB     What is Virtualization? | Hypervisor Types | Virtual Machines [HINDI] [FAILED]
```

---

## 🏗️ How YTD Works

YTD is a user-friendly wrapper around established command-line tools rather than a replacement downloader engine.

```text
YTD Python application
        │
        ├── yt-dlp → YouTube extraction and downloading
        │
        ├── FFmpeg → audio/video merging
        │
        └── Deno → JavaScript runtime support for yt-dlp
```

The Python application handles the interface, playlist logic, quality selection, retry strategies, reporting, and user experience.

---

## 📁 Project Structure

```text
ytd/
├── ytd.py
├── ytd.ps1
├── ytd.cmd
├── setup.ps1
├── update.ps1
├── uninstall.ps1
├── install.bat
├── update.bat
├── uninstall.bat
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
├── THIRD_PARTY_NOTICES.md
├── .gitignore
├── .gitattributes
├── docs/
│   └── DEVELOPMENT.md
├── tests/
│   └── test_syntax.py
└── tools/
    └── .gitkeep
```

Third-party executables are intentionally **not committed to Git**. `setup.ps1` downloads them when the user installs YTD.

---

## 👨‍💻 Creator

**Made by Zimam**

For bug reports, suggestions, feedback, or collaboration:

- Instagram: https://www.instagram.com/zimam_114/

Please use Instagram to report reproducible bugs with the URL type, selected quality, error message, and relevant `download_report.txt` details. Never share private cookies, authentication tokens, or personal information.

---

## 🏢 Zamify

YTD is presented as a **product of Zamify**, the technology agency I work with.

- Website: https://www.zamify.online/
- Instagram: https://www.instagram.com/zamify.online/

Zamify works on software, websites, technology projects, and digital products.

---

## ⚖️ Third-Party Software

YTD relies on third-party software. Their licenses remain with their respective authors/projects.

- **yt-dlp** — used for media extraction and downloading
- **FFmpeg** — used for media processing and merging
- **Deno** — used as a JavaScript runtime for yt-dlp where required

See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for project links and distribution notes.

---

## 📜 License

YTD's own source code is released under the MIT License. See [`LICENSE`](LICENSE).

The MIT License applies to the YTD project code, not to the third-party software downloaded by `setup.ps1`.

---

## ⚠️ Responsible Use

Use YTD only for content you are authorized to download and in accordance with the terms and laws applicable to your use. YTD does not bypass DRM or provide access to private content.

---

## ⭐ Support the Project

If YTD is useful to you, consider starring the repository, reporting bugs, and suggesting improvements. Contributions and constructive feedback are welcome.
