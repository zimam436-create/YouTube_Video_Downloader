"""YTD - YouTube Downloader

A user-friendly Windows frontend around yt-dlp and FFmpeg.
Made by Zimam. Presented as a product of Zamify.
Instagram: https://www.instagram.com/zimam_114/
Zamify: https://www.zamify.online/
"""

import subprocess
import sys
import json
import re
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


# ============================================================
# CONFIGURATION
# ============================================================

# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

APP_VERSION = "1.0.0"
AUTHOR = "Zimam"
ZAMIFY_URL = "https://www.zamify.online/"

BASE_DIR = Path(__file__).resolve().parent
TOOLS_DIR = BASE_DIR
YTDLP = str(TOOLS_DIR / "yt-dlp.exe")
FFMPEG = str(TOOLS_DIR / "ffmpeg.exe")
DOWNLOAD_FOLDER = str(Path.home() / "Downloads")

# Keep the bundled yt-dlp, FFmpeg and Deno discoverable.
TOOL_ENV = os.environ.copy()
TOOL_ENV["PATH"] = str(TOOLS_DIR) + os.pathsep + TOOL_ENV.get("PATH", "")


# ============================================================
# GENERAL HELPERS
# ============================================================

def run_command(command):
    """Run command and return exit code + output."""

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=TOOL_ENV
    )

    return result.returncode, result.stdout


def format_size(size_bytes):
    """Convert bytes to decimal MB / GB."""

    if size_bytes is None:
        return "Unknown"

    if size_bytes >= 1_000_000_000:
        return f"{size_bytes / 1_000_000_000:.2f} GB"

    return f"{size_bytes / 1_000_000:.1f} MB"

def format_duration(seconds):
    """Convert seconds to HH:MM:SS or MM:SS."""

    if seconds is None:
        return "Unknown"

    seconds = int(seconds)

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    return f"{minutes:02d}:{secs:02d}"


def get_duration(info):
    """Get video duration in seconds."""

    return info.get("duration")


def get_total_duration(items):
    """Calculate total duration of selected videos."""

    total = 0

    for item in items:

        duration = get_duration(
            item.get("info", {})
        )

        if duration is not None:
            total += duration

    return total



def get_size(fmt):
    """Return exact or approximate filesize."""

    if fmt.get("filesize"):
        return fmt["filesize"]

    if fmt.get("filesize_approx"):
        return fmt["filesize_approx"]

    return None


def clean_filename(name):
    """Remove Windows-invalid filename characters."""

    if not name:
        return "Unknown Playlist"

    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = name.strip().rstrip(".")

    return name[:200]


# ============================================================
# YOUTUBE INFORMATION
# ============================================================

def get_info(url, flat=False):
    """Get yt-dlp JSON information."""

    command = [
        YTDLP,
        "--dump-single-json",
        "--no-warnings"
    ]

    if flat:
        command.append("--flat-playlist")

    command.append(url)

    code, output = run_command(command)

    if code != 0:
        print()
        print("ERROR: Could not retrieve YouTube information.")
        print(output)
        return None

    try:
        return json.loads(output)

    except json.JSONDecodeError:
        print()
        print("ERROR: yt-dlp returned invalid JSON.")
        return None


def is_playlist(info):
    """Determine whether metadata represents a playlist."""

    return (
        info.get("_type") == "playlist"
        or "entries" in info
    )


# ============================================================
# FORMAT SELECTION
# ============================================================

def get_video_formats(info):
    """
    Return the best video format for each resolution.
    """

    formats = info.get("formats", [])

    resolutions = {}

    for fmt in formats:

        vcodec = fmt.get("vcodec")

        if not vcodec or vcodec == "none":
            continue

        height = fmt.get("height")

        if not height or height < 144:
            continue

        fps = fmt.get("fps") or 0

        # Prefer AV1, then VP9, then AVC.
        codec_score = 0

        if vcodec.startswith("av01"):
            codec_score = 3
        elif vcodec.startswith("vp9"):
            codec_score = 2
        elif vcodec.startswith("avc1"):
            codec_score = 1

        score = (
            codec_score,
            fps,
            get_size(fmt) or 0
        )

        if (
            height not in resolutions
            or score > resolutions[height]["score"]
        ):
            resolutions[height] = {
                "format": fmt,
                "score": score
            }

    return resolutions


def get_best_audio(info):
    """Return best audio-only format."""

    formats = info.get("formats", [])

    audio_formats = []

    for fmt in formats:

        if fmt.get("vcodec") not in (None, "none"):
            continue

        if fmt.get("acodec") in (None, "none"):
            continue

        abr = fmt.get("abr") or 0

        audio_formats.append(
            (
                abr,
                get_size(fmt) or 0,
                fmt
            )
        )

    if not audio_formats:
        return None

    audio_formats.sort(
        key=lambda x: (x[0], x[1]),
        reverse=True
    )

    return audio_formats[0][2]


def get_playlist_resolutions(video_infos):
    """
    Return every resolution available anywhere
    in the selected playlist videos.
    """

    resolutions = set()

    for info in video_infos:

        formats = get_video_formats(info)

        resolutions.update(
            formats.keys()
        )

    return sorted(
        resolutions,
        reverse=True
    )


# ============================================================
# SIZE CALCULATIONS
# ============================================================

def calculate_video_size(video_format, audio_format):

    video_size = get_size(video_format)
    audio_size = get_size(audio_format)

    if video_size is None or audio_size is None:
        return None

    return video_size + audio_size


# ============================================================
# USER INPUT
# ============================================================

def choose_download_type():

    print()
    print("=" * 70)
    print("DOWNLOAD TYPE")
    print("=" * 70)

    print("1. Video + Audio")
    print("2. Audio only")
    print("0. Cancel")

    while True:

        choice = input("\nChoose: ").strip().lower()

        if choice == "1":
            return "video"

        if choice == "2":
            return "audio"

        if choice == "0":
            return None

        print("Invalid choice.")


def choose_video_quality(resolutions):

    print()
    print("=" * 70)
    print("AVAILABLE VIDEO QUALITIES")
    print("=" * 70)

    for index, height in enumerate(resolutions, start=1):
        print(f"{index}. {height}p")

    print("0. Cancel")

    while True:

        choice = input(
            "\nChoose video quality: "
        ).strip()

        if choice == "0":
            return None

        try:
            number = int(choice)

            if 1 <= number <= len(resolutions):
                return resolutions[number - 1]

        except ValueError:
            pass

        print("Invalid choice.")


def choose_playlist_range(total):

    print()
    print("=" * 70)
    print("PLAYLIST RANGE")
    print("=" * 70)

    print(f"Playlist contains {total} videos.")
    print()
    print("1. Download entire playlist")
    print("2. Download a range")
    print("0. Cancel")

    while True:

        choice = input("\nChoose: ").strip()

        if choice == "1":
            return 1, total

        if choice == "2":

            while True:

                value = input(
                    "Enter range (example: 1-10 or 6-12): "
                ).strip()

                match = re.fullmatch(
                    r"(\d+)\s*-\s*(\d+)",
                    value
                )

                if not match:
                    print(
                        "Invalid range. Example: 1-10"
                    )
                    continue

                start = int(match.group(1))
                end = int(match.group(2))

                if (
                    start < 1
                    or end > total
                    or start > end
                ):
                    print("Range is outside playlist.")
                    continue

                return start, end

        if choice == "0":
            return None

        print("Invalid choice.")


def choose_parallel_count():

    print()
    print("=" * 70)
    print("DOWNLOAD MODE")
    print("=" * 70)

    print(
        "Enter the number of parallel downloads."
    )
    print(
        "Enter N for sequential downloading."
    )

    while True:

        value = input(
            "\nParallel downloads [N]: "
        ).strip().lower()

        if value in ("", "n", "no"):
            return 1

        try:

            number = int(value)

            if number >= 1:
                return number

        except ValueError:
            pass

        print(
            "Enter a number such as 1, 2, 3 or N."
        )


# ============================================================
# VIDEO DOWNLOAD
# ============================================================

def run_download(command, display_name=""):
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env=TOOL_ENV
    )

    units = {"iB": 1, "KiB": 1024, "MiB": 1024**2, "GiB": 1024**3, "TiB": 1024**4}
    speed_units = {"iB/s": 1, "KiB/s": 1024, "MiB/s": 1024**2, "GiB/s": 1024**3, "TiB/s": 1024**4}
    diagnostics = []

    for line in process.stdout:
        stripped = line.rstrip()

        if stripped and not stripped.startswith("[download]"):
            diagnostics.append(stripped)
            diagnostics = diagnostics[-12:]

        match = re.search(
            r"\[download\]\s+([\d.]+)%\s+of\s+"
            r"([\d.]+)([KMGT]?iB)\s+at\s+([\d.]+)([KMGT]?iB/s)"
            r"\s+ETA\s+(\S+)",
            line
        )

        if match:
            percent = float(match.group(1))
            total_bytes = float(match.group(2)) * units[match.group(3)]
            speed_bytes = float(match.group(4)) * speed_units[match.group(5)]
            downloaded_bytes = total_bytes * percent / 100
            remaining_bytes = total_bytes - downloaded_bytes
            prefix = f"{display_name} " if display_name else ""

            print(
                f"\r{prefix}{percent:5.1f}% | "
                f"{format_size(downloaded_bytes)} / {format_size(total_bytes)} | "
                f"{speed_bytes / 1_000_000:.2f} MB/s | "
                f"{format_size(remaining_bytes)} remaining | ETA {match.group(6)}",
                end="", flush=True
            )
        elif stripped and any(tag in stripped for tag in (
            "ERROR:", "[Merger]", "[ffmpeg]", "WARNING:"
        )):
            print("\n" + stripped)

    process.wait()
    print()

    if process.returncode != 0 and diagnostics:
        print("Download error:")
        for line in diagnostics[-6:]:
            print(f"  {line}")

    return process.returncode


def cleanup_partial_output(output_prefix):
    folder = os.path.dirname(output_prefix)
    prefix = os.path.basename(output_prefix)
    if not os.path.isdir(folder):
        return

    for name in os.listdir(folder):
        if name == prefix or name.startswith(prefix + "."):
            path = os.path.join(folder, name)
            try:
                if os.path.isfile(path):
                    os.remove(path)
            except OSError:
                pass


def make_video_command(url, video_format, audio_format, output_path, temp_folder, force=False):
    command = [
        YTDLP,
        "--newline", "--progress",
        "--retries", "10",
        "--fragment-retries", "10",
        "--extractor-retries", "3",
        "--file-access-retries", "3",
        "--retry-sleep", "http:exp=1:10",
        "--retry-sleep", "fragment:exp=1:10",
        "-f", f"{video_format['format_id']}+{audio_format['format_id']}",
        "--merge-output-format", "mp4",
        "--ffmpeg-location", FFMPEG,
        "--paths", f"temp:{temp_folder}",
        "-o", output_path,
    ]
    if force:
        command.append("--force-overwrites")
    command.append(url)
    return command


def make_fallback_video_commands(url, selected_height, output_path, temp_folder):
    limit = selected_height or 2160
    strategies = [
        (
            f"bestvideo[height<={limit}][ext=mp4]+bestaudio[ext=m4a]/"
            f"best[height<={limit}][ext=mp4]",
            "MP4 video + M4A audio"
        ),
        (
            f"bestvideo[height<={limit}]+bestaudio[ext=m4a]/"
            f"best[height<={limit}]",
            "best video + M4A audio"
        ),
        (
            f"best[height<={limit}]",
            "single progressive format"
        ),
    ]

    result = []
    for selector, label in strategies:
        command = [
            YTDLP,
            "--newline", "--progress",
            "--retries", "10",
            "--fragment-retries", "10",
            "--extractor-retries", "3",
            "--file-access-retries", "3",
            "--retry-sleep", "http:exp=1:10",
            "--retry-sleep", "fragment:exp=1:10",
            "-f", selector,
            "--merge-output-format", "mp4",
            "--ffmpeg-location", FFMPEG,
            "--paths", f"temp:{temp_folder}",
            "--force-overwrites",
            "-o", output_path,
            url,
        ]
        result.append((label, command))
    return result


def download_video_with_retries(
    url, video, audio, output_path, temp_folder, selected_height, display_name=""
):
    os.makedirs(temp_folder, exist_ok=True)

    attempts = [
        ("selected formats",
         make_video_command(
             url, video, audio, output_path, temp_folder, force=False
         ))
    ]
    attempts.extend(
        make_fallback_video_commands(
            url, selected_height, output_path, temp_folder
        )
    )

    for number, (label, command) in enumerate(attempts, start=1):
        print(
            f"\n{'Download attempt 1' if number == 1 else f'Retry {number - 1}'}: {label}"
        )

        cleanup_partial_output(os.path.splitext(output_path)[0])
        code = run_download(command, display_name=display_name)

        if code == 0 and os.path.exists(output_path):
            print("Download verified successfully.")
            return 0

        cleanup_partial_output(os.path.splitext(output_path)[0])

    print("All automatic download methods failed.")
    return 1


# ============================================================
# SINGLE VIDEO DOWNLOAD
# ============================================================

def download_single_video(
    url,
    info,
    mode,
    selected_height=None
):

    title = info.get("title", "Unknown")

    duration = info.get("duration")

    resolutions = get_video_formats(info)

    audio = get_best_audio(info)

    if not audio:

        print("No audio format available.")
        return 1

    if mode == "audio":

        audio_size = get_size(audio)

        print()
        print("=" * 70)
        print("DOWNLOAD SUMMARY")
        print("=" * 70)

        print(f"Title:    {title}")
        print(
            f"Duration:  {format_duration(duration)}"
        )
        print(
            f"Quality:  {audio.get('abr', 'Unknown')} kbps"
        )
        print(
            f"Audio:    {format_size(audio_size)}"
        )
        print(
            f"Final:    ~{format_size(audio_size)}"
        )
        print(
            f"Location: {DOWNLOAD_FOLDER}"
        )

        print("=" * 70)

        confirm = input(
            "\nStart download? [Y/n]: "
        ).strip().lower()

        if confirm not in ("", "y", "yes"):
            print("Cancelled.")
            return 0

        command = [
            YTDLP,
            "--newline",
            "--progress",
            "-f",
            audio["format_id"],
            "-P",
            DOWNLOAD_FOLDER,
            url
        ]

        return run_download(command)

    if selected_height is None:

        selected_height = choose_video_quality(
            sorted(resolutions.keys(), reverse=True)
        )

        if selected_height is None:
            return 0

    video = resolutions.get(selected_height)

    if not video:
        print(
            f"{selected_height}p is not available."
        )
        return 1

    video = video["format"]

    final_size = calculate_video_size(
        video,
        audio
    )

    print()
    print("=" * 70)
    print("DOWNLOAD SUMMARY")
    print("=" * 70)

    print(f"Title:    {title}")
    print(
        f"Duration:  {format_duration(duration)}"
    )
    print(
        f"Quality:  {selected_height}p"
    )
    print(
        f"Video:    {format_size(get_size(video))}"
    )
    print(
        f"Audio:    {format_size(get_size(audio))}"
    )
    print(
        f"Final:    ~{format_size(final_size)}"
    )
    print(
        f"Location: {DOWNLOAD_FOLDER}"
    )

    print("=" * 70)

    confirm = input(
        "\nStart download? [Y/n]: "
    ).strip().lower()

    if confirm not in ("", "y", "yes"):
        print("Cancelled.")
        return 0

    safe_title = clean_filename(title)
    output_path = os.path.join(DOWNLOAD_FOLDER, f"{safe_title}.mp4")
    temp_folder = os.path.join(DOWNLOAD_FOLDER, ".ytd-temp")

    return download_video_with_retries(
        url,
        video,
        audio,
        output_path,
        temp_folder,
        selected_height,
        display_name=""
    )


# ============================================================
# PLAYLIST DOWNLOAD
# ============================================================

def prepare_playlist_items(
    playlist_info,
    start,
    end
):

    entries = playlist_info.get("entries", [])

    selected = []

    for index, entry in enumerate(entries, start=1):

        if index < start or index > end:
            continue

        if not entry:
            continue

        video_id = entry.get("id")

        if not video_id:
            continue

        webpage_url = entry.get("webpage_url")

        if not webpage_url:
            webpage_url = (
                f"https://www.youtube.com/watch?v={video_id}"
            )

        selected.append(
            {
                "playlist_index": index,
                "id": video_id,
                "title": entry.get(
                    "title",
                    f"Video {index}"
                ),
                "url": webpage_url
            }
        )

    return selected


def get_playlist_video_infos(items):

    print()
    print(f"Checking {len(items)} selected videos...", end="", flush=True)

    for number, item in enumerate(items, start=1):
        print(f"\rChecking {number}/{len(items)}...", end="", flush=True)

        info = get_info(item["url"], flat=False)

        if info:
            item["info"] = info
            item["status"] = "ready"
            item["error"] = None
        else:
            item["info"] = None
            item["status"] = "unavailable"
            item["error"] = "Could not retrieve video information"

    print(f"\rChecking {len(items)}/{len(items)}... done")
    return items


def build_playlist_download_data(
    items,
    mode,
    selected_height
):

    download_data = []
    unavailable_items = []

    for item in items:
        info = item.get("info")

        if not info:
            unavailable_items.append(item)
            continue

        audio = get_best_audio(info)

        if not audio:
            item["status"] = "unavailable"
            item["error"] = "No audio format available"
            unavailable_items.append(item)
            continue

        duration = get_duration(info)

        if mode == "audio":
            download_data.append({
                "item": item,
                "audio": audio,
                "video": None,
                "size": get_size(audio),
                "duration": duration,
                "requested_height": None,
                "actual_height": None,
                "adjustment": ""
            })
            item["status"] = "ready"
            continue

        resolutions = get_video_formats(info)
        available_heights = sorted(resolutions.keys())

        if not available_heights:
            item["status"] = "unavailable"
            item["error"] = "No video formats available"
            unavailable_items.append(item)
            continue

        lower_or_equal = [h for h in available_heights if h <= selected_height]

        if lower_or_equal:
            actual_height = max(lower_or_equal)
            adjustment = "" if actual_height == selected_height else "downgraded"
        else:
            actual_height = min(available_heights)
            adjustment = "upgraded"

        video = resolutions[actual_height]["format"]
        final_size = calculate_video_size(video, audio)

        download_data.append({
            "item": item,
            "audio": audio,
            "video": video,
            "size": final_size,
            "duration": duration,
            "requested_height": selected_height,
            "actual_height": actual_height,
            "adjustment": adjustment
        })
        item["status"] = "ready"

    return download_data, unavailable_items


def playlist_summary(
    playlist_name,
    download_data,
    mode,
    selected_height,
    unavailable_items=None
):

    unavailable_items = unavailable_items or []
    total_size = 0
    total_duration = 0

    print()
    print("=" * 78)
    print("PLAYLIST DOWNLOAD SUMMARY")
    print("=" * 78)
    print(f"Playlist:  {playlist_name}")
    print(f"Selected:  {len(download_data) + len(unavailable_items)}")
    print(f"Ready:     {len(download_data)}")
    print(f"Unavailable: {len(unavailable_items)}")

    if mode == "video":
        print(f"Requested: {selected_height}p")
    else:
        print("Type:      Audio only")

    print("-")
    print(f"{'#':<5}{'Duration':<10}{'Quality':<12}{'Size':<12}Title")
    print("-" * 78)

    rows = {data["item"]["playlist_index"]: data for data in download_data}
    unavailable = {item["playlist_index"]: item for item in unavailable_items}
    indexes = sorted(set(rows) | set(unavailable))

    for index in indexes:
        if index in unavailable:
            item = unavailable[index]
            print(f"#{index:02d}  {'--':<8}{'--':<12}{'--':<12}[UNAVAILABLE] {item['title']}")
            continue

        data = rows[index]
        item = data["item"]
        duration = data.get("duration")
        size = data.get("size")

        if duration is None:
            duration_text = "Unknown"
        else:
            duration_text = format_duration(duration)
            total_duration += duration

        if size is None:
            size_text = "Unknown"
        else:
            size_text = f"~{format_size(size)}"
            total_size += size

        if mode == "video":
            quality_text = f"{data['actual_height']}p"
            adjustment = data.get("adjustment", "")
            if adjustment:
                quality_text += f" {adjustment}"
        else:
            quality_text = f"{data['audio'].get('abr', '?')}k"

        print(
            f"#{index:02d}  "
            f"{duration_text:<10}"
            f"{quality_text:<12}"
            f"{size_text:<12}"
            f"{item['title']}"
        )

    print("-" * 78)
    print(f"TOTAL DURATION: {format_duration(total_duration)}")
    print(f"TOTAL SIZE:     ~{format_size(total_size)}")

    if mode == "video":
        print("Adjusted qualities are marked as 'downgraded' or 'upgraded'.")

    print("=" * 78)


def download_playlist_item(data, playlist_folder, mode):
    item = data["item"]
    index = item["playlist_index"]
    title = item["title"]
    safe_title = clean_filename(title)
    temp_folder = os.path.join(playlist_folder, ".ytd-temp")
    os.makedirs(temp_folder, exist_ok=True)

    print(f"\nStarting #{index:02d}: {title}")

    if mode == "audio":
        output_path = os.path.join(
            playlist_folder, f"#{index:02d} - {safe_title}.%(ext)s"
        )
        command = [
            YTDLP, "--newline", "--progress",
            "--retries", "10", "--fragment-retries", "10",
            "--extractor-retries", "3", "--file-access-retries", "3",
            "--paths", f"temp:{temp_folder}",
            "-f", data["audio"]["format_id"],
            "-o", output_path,
            item["url"]
        ]
        code = run_download(command, display_name=f"#{index:02d}")
        return index, code

    output_path = os.path.join(
        playlist_folder, f"#{index:02d} - {safe_title}.mp4"
    )

    code = download_video_with_retries(
        item["url"],
        data["video"],
        data["audio"],
        output_path,
        temp_folder,
        data.get("requested_height"),
        display_name=f"#{index:02d}"
    )
    return index, code


def download_playlist_parallel(
    download_data,
    playlist_folder,
    mode,
    workers
):

    print()
    print(
        f"Starting {workers} parallel "
        f"download worker(s)..."
    )

    results = []

    with ThreadPoolExecutor(
        max_workers=workers
    ) as executor:

        futures = []

        for data in download_data:

            future = executor.submit(
                download_playlist_item,
                data,
                playlist_folder,
                mode
            )

            futures.append(future)

        for future in as_completed(futures):

            index, code = future.result()

            results.append(
                (index, code)
            )

            status = (
                "OK"
                if code == 0
                else "FAILED"
            )

            print(
                f"\n#{index:02d}: {status}"
            )

    return results


def download_playlist_sequential(
    download_data,
    playlist_folder,
    mode
):

    results = []

    for data in download_data:

        index, code = download_playlist_item(
            data,
            playlist_folder,
            mode
        )

        results.append(
            (index, code)
        )

        if code != 0:

            print(
                f"#{index:02d} failed."
            )

    return results

def handle_higher_quality_items(
    higher_quality_items,
    download_data
):

    skipped_items = []

    if not higher_quality_items:
        return skipped_items

    print()
    print("=" * 70)
    print("HIGHER QUALITY AVAILABLE")
    print("=" * 70)

    for data in higher_quality_items:

        item = data["item"]

        print()
        print(
            f"#{item['playlist_index']:02d} - "
            f"{item['title']}"
        )

        print(
            f"Requested maximum: "
            f"{data['requested_height']}p"
        )

        print()
        print("Available higher qualities:")

        qualities = data["available_heights"]

        for index, height in enumerate(
            qualities,
            start=1
        ):

            print(
                f"    {index}. {height}p"
            )

        print(
            f"    {len(qualities) + 1}. "
            "Skip this video"
        )

        print()

        while True:

            choice = input(
                "Choose quality: "
            ).strip()

            if not choice.isdigit():
                print(
                    "Please enter a number."
                )
                continue

            choice = int(choice)

            # Skip
            if choice == len(qualities) + 1:

                skipped_items.append(
                    {
                        "item": item,
                        "reason": (
                            f"No quality at or below "
                            f"{data['requested_height']}p"
                        ),
                        "available_heights": qualities,
                        "duration": data["duration"]
                    }
                )

                print(
                    f"Skipped #{item['playlist_index']:02d}."
                )

                break

            # Valid quality
            if 1 <= choice <= len(qualities):

                selected_height = qualities[
                    choice - 1
                ]

                video = data["resolutions"][
                    selected_height
                ]["format"]

                final_size = calculate_video_size(
                    video,
                    data["audio"]
                )

                download_data.append(
                    {
                        "item": item,
                        "audio": data["audio"],
                        "video": video,
                        "size": final_size,
                        "duration": data["duration"],
                        "requested_height": (
                            data["requested_height"]
                        ),
                        "actual_height": selected_height,
                        "quality_override": True
                    }
                )

                print(
                    f"Selected {selected_height}p "
                    f"for #{item['playlist_index']:02d}."
                )

                break

            print(
                "Invalid choice. "
                "Please select one of the numbers above."
            )

    return skipped_items

def write_playlist_report(
    playlist_folder,
    playlist_name,
    download_data,
    unavailable_items,
    mode,
    selected_height,
    completed_items=None,
    failed_items=None
):

    report_path = os.path.join(playlist_folder, "download_report.txt")
    completed_items = completed_items or []
    failed_items = failed_items or []
    unavailable_items = unavailable_items or []

    total_duration = sum(
        data["duration"] for data in download_data
        if data.get("duration") is not None
    )
    total_size = sum(
        data["size"] for data in download_data
        if data.get("size") is not None
    )

    lines = [
        "=" * 78,
        "PLAYLIST DOWNLOAD REPORT",
        "=" * 78,
        "",
        f"Playlist:     {playlist_name}",
        f"Selected:     {len(download_data) + len(unavailable_items)}",
        f"Downloaded:   {len(completed_items)}",
        f"Failed:       {len(failed_items)}",
        f"Unavailable:  {len(unavailable_items)}",
        f"Location:     {playlist_folder}",
        "",
        "-" * 78,
    ]

    if mode == "video":
        lines.append(f"Requested quality: {selected_height}p")
    else:
        lines.append("Type: Audio only")

    lines += ["", "SELECTED VIDEOS", "-" * 78]

    all_items = {}
    for data in download_data:
        all_items[data["item"]["playlist_index"]] = ("ready", data)
    for item in unavailable_items:
        all_items[item["playlist_index"]] = ("unavailable", item)

    for index in sorted(all_items):
        status, value = all_items[index]
        if status == "unavailable":
            item = value
            lines.append(
                f"#{index:02d} [UNAVAILABLE] {item['title']}"
            )
            lines.append(
                f"Error: {item.get('error', 'Unknown error')}"
            )
            continue

        data = value
        item = data["item"]
        duration = data.get("duration")
        size = data.get("size")
        duration_text = (
            format_duration(duration) if duration is not None else "Unknown"
        )
        size_text = (
            f"~{format_size(size)}" if size is not None else "Unknown"
        )

        if mode == "video":
            quality = f"{data['actual_height']}p"
            if data.get("adjustment"):
                quality += f" {data['adjustment']}"
        else:
            quality = f"{data['audio'].get('abr', '?')}k"

        final_failed = any(
            failed_item["playlist_index"] == index
            for failed_item in failed_items
        )
        status_text = " [FAILED]" if final_failed else ""

        lines.append(
            f"#{index:02d}  {duration_text:<10} {quality:<20} "
            f"{size_text:<12} {item['title']}{status_text}"
        )

    lines += [
        "",
        "-" * 78,
        f"TOTAL DURATION: {format_duration(total_duration)}",
        f"TOTAL SIZE:     ~{format_size(total_size)}",
    ]

    if failed_items:
        lines += ["", "FAILED DOWNLOADS", "-" * 78]
        for item in failed_items:
            data = item.get("download_data")
            if data:
                duration = data.get("duration")
                size = data.get("size")
                duration_text = (
                    format_duration(duration) if duration is not None else "Unknown"
                )
                size_text = (
                    f"~{format_size(size)}" if size is not None else "Unknown"
                )
                quality = (
                    f"{data.get('actual_height', '?')}p"
                    if mode == "video"
                    else f"{data['audio'].get('abr', '?')}k"
                )
                lines.append(
                    f"#{item['playlist_index']:02d}  {duration_text:<10} "
                    f"{quality:<10} {size_text:<12} "
                    f"{item['title']} [FAILED]"
                )
            else:
                lines.append(
                    f"#{item['playlist_index']:02d} - {item['title']} [FAILED]"
                )
            lines.append(f"Error: {item.get('error', 'Download failed')}")

    lines += ["", "=" * 78, "END OF REPORT", "=" * 78]

    with open(report_path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    return report_path


def run_playlist(url, playlist_info):

    playlist_name = clean_filename(
        playlist_info.get("title", "YouTube Playlist")
    )

    entries = playlist_info.get("entries", [])
    total = len(entries)

    if total == 0:
        print("Playlist contains no videos.")
        return 1

    print()
    print("=" * 70)
    print("PLAYLIST")
    print("=" * 70)
    print(f"Playlist: {playlist_name}")
    print(f"Videos:   {total}")

    selected_range = choose_playlist_range(total)
    if not selected_range:
        print("Cancelled.")
        return 0

    start, end = selected_range
    items = prepare_playlist_items(playlist_info, start, end)

    if len(items) != end - start + 1:
        print(
            f"Warning: selected range contains {end - start + 1} videos, "
            f"but only {len(items)} playlist entries could be prepared."
        )

    if not items:
        print("No valid videos found.")
        return 1

    print(f"\nSelected videos: #{start} through #{end}")

    mode = choose_download_type()
    if mode is None:
        return 0

    items = get_playlist_video_infos(items)

    selected_infos = [item["info"] for item in items if item.get("info")]

    selected_height = None
    if mode == "video":
        playlist_resolutions = get_playlist_resolutions(selected_infos)

        if not playlist_resolutions:
            print("\nNo video qualities could be found for the selected videos.")
            playlist_summary(playlist_name, [], mode, None, items)
            return 1

        selected_height = choose_video_quality(playlist_resolutions)
        if selected_height is None:
            return 0

    download_data, unavailable_items = build_playlist_download_data(
        items, mode, selected_height
    )

    print()
    playlist_summary(
        playlist_name,
        download_data,
        mode,
        selected_height,
        unavailable_items
    )

    if not download_data:
        print("No downloadable videos found.")
        return 1

    playlist_folder = os.path.join(DOWNLOAD_FOLDER, playlist_name)
    os.makedirs(playlist_folder, exist_ok=True)

    workers = choose_parallel_count()

    if workers == 1:
        print("\nDownload mode: Sequential")
    else:
        print(f"\nDownload mode: {workers} parallel downloads")

    confirm = input("\nStart playlist download? [Y/n]: ").strip().lower()
    if confirm not in ("", "y", "yes"):
        print("Cancelled.")
        return 0

    if workers == 1:
        results = download_playlist_sequential(
            download_data, playlist_folder, mode
        )
    else:
        results = download_playlist_parallel(
            download_data, playlist_folder, mode, workers
        )

    result_map = {index: code for index, code in results}
    failed_data = [
        data for data in download_data
        if result_map.get(data["item"]["playlist_index"], 1) != 0
    ]

    if failed_data:
        print()
        print("=" * 70)
        print("TROUBLESHOOTING FAILED DOWNLOADS")
        print("=" * 70)
        print(f"{len(failed_data)} video(s) failed. Trying alternate methods...")

        for data in failed_data:
            index = data["item"]["playlist_index"]
            item = data["item"]
            safe_title = clean_filename(item["title"])
            output_path = os.path.join(
                playlist_folder, f"#{index:02d} - {safe_title}.mp4"
            )
            temp_folder = os.path.join(playlist_folder, ".ytd-temp")

            code = download_video_with_retries(
                item["url"],
                data["video"],
                data["audio"],
                output_path,
                temp_folder,
                data.get("requested_height"),
                display_name=f"#{index:02d}"
            )
            result_map[index] = code

    successful = sum(
        1 for data in download_data
        if result_map.get(data["item"]["playlist_index"], 1) == 0
    )
    failed = len(download_data) - successful

    completed_items = [
        data["item"] for data in download_data
        if result_map.get(data["item"]["playlist_index"], 1) == 0
    ]

    failed_items = []
    for data in download_data:
        if result_map.get(data["item"]["playlist_index"], 1) != 0:
            failed_item = dict(data["item"])
            failed_item["error"] = "All automatic download methods failed"
            failed_item["download_data"] = data
            failed_items.append(failed_item)

    report_path = write_playlist_report(
        playlist_folder, playlist_name, download_data, unavailable_items,
        mode, selected_height,
        completed_items=completed_items,
        failed_items=failed_items
    )

    print()
    print("=" * 70)
    print("PLAYLIST COMPLETE")
    print("=" * 70)
    print(f"Successful:   {successful}")
    print(f"Failed:       {failed}")
    print(f"Unavailable:  {len(unavailable_items)}")

    if failed_items:
        print()
        print("FAILED DOWNLOADS:")
        for item in sorted(failed_items, key=lambda x: x["playlist_index"]):
            print(f"#{item['playlist_index']:02d}  {item['title']}")

    if unavailable_items:
        print()
        print("UNAVAILABLE VIDEOS:")
        for item in sorted(unavailable_items, key=lambda x: x["playlist_index"]):
            print(f"#{item['playlist_index']:02d}  {item['title']}")

    print()
    print(f"Location:     {playlist_folder}")
    print(f"Report:       {report_path}")
    print("=" * 70)

    return 0 if failed == 0 and not unavailable_items else 1


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) < 2:

        print(
            "Usage:"
        )

        print(
            '  ytd "YouTube URL"'
        )

        sys.exit(1)

    url = sys.argv[1]

    if not os.path.exists(YTDLP):
        print("ERROR: yt-dlp.exe was not found.")
        print(f"Expected: {YTDLP}")
        print("Run setup.ps1 first to install the required tools.")
        sys.exit(1)

    if not os.path.exists(FFMPEG):
        print("ERROR: ffmpeg.exe was not found.")
        print(f"Expected: {FFMPEG}")
        print("Run setup.ps1 first to install the required tools.")
        sys.exit(1)

    os.makedirs(
        DOWNLOAD_FOLDER,
        exist_ok=True
    )

    print()
    print("=" * 70)
    print(f"Zamify YouTube Downloader v{APP_VERSION} Made By Zimam")
    print("=" * 70)

    print()
    print("Checking YouTube URL...")
    print("Please wait...")

    # First attempt to retrieve playlist metadata.
    # --flat-playlist makes this cheap.
    info = get_info(
        url,
        flat=True
    )

    if not info:

        sys.exit(1)

    if is_playlist(info):

        code = run_playlist(
            url,
            info
        )

        sys.exit(code)

    # --------------------------------------------------------
    # INDIVIDUAL VIDEO
    # --------------------------------------------------------

    # Get complete metadata.
    full_info = get_info(
        url,
        flat=False
    )

    if not full_info:

        sys.exit(1)

    title = full_info.get(
        "title",
        "Unknown"
    )

    print()
    print(f"Title: {title}")

    mode = choose_download_type()

    if mode is None:

        print("Cancelled.")
        return

    selected_height = None

    if mode == "video":

        resolutions = get_video_formats(
            full_info
        )

        available = sorted(
            resolutions.keys(),
            reverse=True
        )

        selected_height = choose_video_quality(
            available
        )

        if selected_height is None:
            return

    code = download_single_video(
        url,
        full_info,
        mode,
        selected_height
    )

    sys.exit(code)


if __name__ == "__main__":
    main()
