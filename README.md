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

### Windows

1. Download the latest release
2. Run the .exe file

### Unix

1. install [ffmpeg](https://ffmpeg.org/)
2. Clone the repo
3. `pip install -r requirements.txt`
4. `python main.py`

## Walk Through

The replay website strictly holds on to browser session. After login, a jsessionid cookie is returned. Maintaining this cookie with the same session is the key to pass verification.

The replays are stored in a hls video format. This script uses ffmpeg to download hls video.
