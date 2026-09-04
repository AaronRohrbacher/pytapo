# pytapo fork for Tapo Enhance

Forked from [`JurajNyiri/pytapo`](https://github.com/JurajNyiri/pytapo) at
commit `8c97d90d26c8129d9b8c051cd8d82c4f7cb424d1` (version 3.4.18). Juraj
Nyíri and the upstream contributors deserve full credit for the protocol work
and library on which these additions are built.

All inherited upstream code remains under the MIT license in `LICENSE`.
Tapo Enhance-specific additions are licensed under GPL-2.0-only, whose complete
text is in `LICENSE-GPL-2.0`.

Local changes are kept in the library rather than duplicated by the app:

- `RecordingThumbnail` implements the camera's native event-JPEG request.
- `RecordingStream` owns the recording playback request and ensures callers
  can promptly close firmware that streams beyond the requested event.
- `PreviewStream` owns live-preview request construction and error handling.
- `HttpMediaSession` parses MPEG-TS audio only for MPEG-TS responses.

Fork releases use a PEP 440 post-release suffix. `3.4.18.post1` therefore means
the first Tapo Enhance fork release based on upstream `3.4.18`; it does not
claim to be a newer upstream release.
