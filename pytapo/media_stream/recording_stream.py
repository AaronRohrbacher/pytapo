# SPDX-License-Identifier: GPL-2.0-only

import asyncio
import json

from ._utils import StreamType


class RecordingStream:
    """Stream one SD-card recording through Tapo's playback media session.

    The caller owns media conversion and the final duration cut because some
    camera firmware ignores ``end_time`` and continues into later events.
    Closing this object closes the camera socket immediately.
    """

    def __init__(
        self,
        tapo,
        startTime: int,
        endTime: int,
        event_type=(2,),
        channels=(0, 1),
        window_size=200,
        no_data_timeout=10,
    ):
        self.tapo = tapo
        self.startTime = int(startTime)
        self.endTime = int(endTime)
        self.event_type = list(event_type)
        self.channels = list(channels)
        self.window_size = int(window_size)
        self.no_data_timeout = no_data_timeout
        self.mediaSession = None
        self.userID = None

    def _build_payload(self):
        return {
            "type": "request",
            "seq": 1,
            "params": {
                "playback": {
                    "client_id": self.userID,
                    "channels": self.channels,
                    "scale": "1/1",
                    "start_time": str(self.startTime),
                    "end_time": str(self.endTime),
                    "event_type": self.event_type,
                },
                "method": "get",
            },
        }

    async def start(self):
        if self.endTime <= self.startTime:
            raise ValueError("endTime must be greater than startTime")
        if self.mediaSession is not None:
            return

        loop = asyncio.get_running_loop()
        self.userID = await loop.run_in_executor(None, self.tapo.getUserID)
        self.mediaSession = await loop.run_in_executor(
            None, self.tapo.getMediaSession, StreamType.Download
        )
        self.mediaSession.set_window_size(self.window_size)
        await self.mediaSession.start()

    async def responses(self):
        if self.mediaSession is None:
            raise RuntimeError("Recording stream has not been started")

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
                            "Camera rejected recording playback request "
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
