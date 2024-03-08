# HITSZ Course Replay Downloader

## Feature List

- [x] Login
- [x] Select Course
- [x] Select Terms
- [x] Download Video
- [x] Get courses list when separated by pages
- [x] Set Video file name
- [x] Select Video
- [x] Release .exe file

## How to use

### Run the .exe file

1. Disable Windows Defender real-time protection
2. Download the [latest release](https://github.com/lng205/HITSZ_replay_downloader/releases/download/v1.0/HITSZ_replay_downloader.exe)
3. Run the .exe file

### Run the script manually

If you don't trust the .exe file, you can run the script manually.

1. install [ffmpeg](https://ffmpeg.org/)
2. Clone the repo
3. `pip install -r requirements.txt`
4. `python main.py`

## Walk Through

The replay website strictly holds on to browser session. After login, a jsessionid cookie is returned. Maintaining this cookie with the same session is the key to pass verification.

The replays are stored in a hls video format. This script uses ffmpeg to download hls video.
