# SPDX-License-Identifier: GPL-2.0-only

import asyncio
import json

from ._utils import StreamType


class PreviewStream:
    """Yield MPEG-TS parts from a camera's live preview media session."""

    def __init__(
        self,
        tapo,
        quality="HD",
        channels=(0,),
        audio=("default",),
        window_size=50,
        no_data_timeout=10,
    ):
        self.tapo = tapo
        self.quality = quality
        self.channels = list(channels)
        self.audio = list(audio)
        self.window_size = int(window_size)
        self.no_data_timeout = no_data_timeout
        self.mediaSession = None

    def _build_payload(self):
        return {
            "type": "request",
            "seq": 1,
            "params": {
                "preview": {
                    "audio": self.audio,
                    "channels": self.channels,
                    "resolutions": [self.quality],
                },
                "method": "get",
            },
        }

    async def start(self):
        if self.mediaSession is not None:
            return
        loop = asyncio.get_running_loop()
        self.mediaSession = await loop.run_in_executor(
            None, self.tapo.getMediaSession, StreamType.Stream
        )
        self.mediaSession.set_window_size(self.window_size)
        await self.mediaSession.start()

    async def responses(self):
        if self.mediaSession is None:
            raise RuntimeError("Preview stream has not been started")
        responses = self.mediaSession.transceive(
            json.dumps(self._build_payload()),
            "application/json",
            no_data_timeout=self.no_data_timeout,
        )
        async for response in responses:
            if response.mimetype == "application/json":
                data = response.json_data
                if isinstance(data, dict):
                    error_code = data.get("error_code")
                    if error_code not in (None, 0):
                        raise RuntimeError(
                            "Camera rejected preview request "
                            f"with error code {error_code}"
                        )
                    params = data.get("params", {})
                    if (
                        params.get("event_type") == "stream_status"
                        and params.get("status") == "finished"
                    ):
                        break
                continue
            if response.mimetype == "video/mp2t":
                yield response

    async def close(self):
        mediaSession = self.mediaSession
        self.mediaSession = None
        if mediaSession is not None:
            await mediaSession.close()

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
