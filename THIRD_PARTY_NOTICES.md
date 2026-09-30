# Third-Party Notices

YTD is a Python application that invokes third-party tools. YTD does not claim ownership of those projects.

## yt-dlp

Project: https://github.com/yt-dlp/yt-dlp

YTD uses the official Windows `yt-dlp.exe` release. The upstream project publishes its own licensing and third-party notices with its releases. See the upstream repository and release package for the applicable notices.

## FFmpeg

Project: https://ffmpeg.org/

Windows binaries used by the setup script are obtained from the Gyan.dev Windows builds referenced by FFmpeg's official download page:

https://www.gyan.dev/ffmpeg/builds/

YTD uses the essentials build for media merging. The applicable FFmpeg/build licenses belong to FFmpeg and the respective build distributor.

## Deno

Project: https://github.com/denoland/deno

YTD installs the official Windows x64 Deno release as a JavaScript runtime for yt-dlp.

## Important

Third-party tools are downloaded during setup rather than committed to this repository. Their licenses, trademarks, and copyrights remain with their respective projects and contributors.
