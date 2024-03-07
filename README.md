# HITSZ Course Replay Downloader

## Feature List

- [x] Login
- [x] Select Course
- [x] Select Terms
- [x] Download Video

- [ ] Get courses list when separated by pages
- [ ] Set Video file name
- [ ] Select Video
- [ ] Release .exe file

## Walk Through

The replay website strictly holds on to browser session. After login, a jsessionid cookie is returned. Maintaining this cookie with the same session is the key to pass verification.

The replays are stored in a hls video format. This script uses ffmpeg to download hls video.
