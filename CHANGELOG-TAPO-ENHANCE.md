# Tapo Enhance fork changes

Tapo Enhance-specific additions are licensed under GPL-2.0-only. Inherited
upstream code remains under MIT.

## 3.4.18.post1

Based on upstream `pytapo` 3.4.18 (`8c97d90d26c8129d9b8c051cd8d82c4f7cb424d1`).

- Add `RecordingThumbnail` for the camera's native event JPEG response.
- Add bounded, promptly closable `RecordingStream` playback.
- Add `PreviewStream` live-preview response iteration.
- Parse private RTP audio only from MPEG-TS multipart responses, allowing JSON
  and JPEG parts to pass through safely.
- Export the three additions from `pytapo.media_stream`.

The upstream project, history, authorship, and MIT license are preserved.
