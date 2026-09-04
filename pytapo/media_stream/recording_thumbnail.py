# SPDX-License-Identifier: GPL-2.0-only

import asyncio
import json
import os

import aiofiles

from ._utils import StreamType


class RecordingThumbnail:
    """Retrieve the JPEG stored by the camera for one SD-card recording.

    The media-session ``download`` request returns an ``image/jpeg`` part;
    unlike ``playback``, it does not stream or decode the recording.
    """

    MAX_IMAGE_BYTES = 10 * 1024 * 1024

    def __init__(
        self,
        tapo,
        startTime: int,
        endTime: int,
        window_size=50,
        no_data_timeout=10,
    ):
        self.tapo = tapo
        self.startTime = int(startTime)
        self.endTime = int(endTime)
        self.window_size = int(window_size)
        self.no_data_timeout = no_data_timeout

    def _build_payload(self, user_id):
        return {
            "type": "request",
            "seq": 1,
            "params": {
                "download": {
                    "client_id": user_id,
                    "channels": [0],
                    "start_time": str(self.startTime),
                    "end_time": str(self.endTime),
                    "event_type": [2],
                },
                "method": "get",
            },
        }

    async def get(self):
        if self.endTime <= self.startTime:
            raise ValueError("endTime must be greater than startTime")

        loop = asyncio.get_running_loop()
        user_id = await loop.run_in_executor(None, self.tapo.getUserID)
        mediaSession = await loop.run_in_executor(
            None, self.tapo.getMediaSession, StreamType.Download
        )
        mediaSession.set_window_size(self.window_size)
        image = bytearray()

        async with mediaSession:
            responses = mediaSession.transceive(
                json.dumps(self._build_payload(user_id)),
                "application/json",
                no_data_timeout=self.no_data_timeout,
            )
            async for response in responses:
                if response.mimetype == "image/jpeg":
                    image.extend(response.plaintext)
                    if len(image) > self.MAX_IMAGE_BYTES:
                        raise ValueError("Recording thumbnail exceeds maximum size")
                    continue

                if response.mimetype != "application/json":
                    continue

                data = response.json_data
                if not isinstance(data, dict):
                    continue
                error_code = data.get("error_code")
                if error_code not in (None, 0):
                    raise RuntimeError(
                        "Camera rejected recording thumbnail request "
                        f"with error code {error_code}"
                    )
                params = data.get("params", {})
                if (
                    params.get("event_type") == "stream_status"
                    and params.get("status") == "finished"
                ):
                    break

        result = bytes(image)
        jpeg_end = result.rfind(b"\xff\xd9")
        if not result.startswith(b"\xff\xd8") or jpeg_end < 2:
            raise RuntimeError("Camera returned no valid recording thumbnail")
        # Some firmware pads the encrypted multipart body with zero bytes.
        # Publish only the JPEG through its EOI marker.
        return result[: jpeg_end + 2]

    async def download(self, fileName, overwriteFiles=False):
        if os.path.isfile(fileName) and not overwriteFiles:
            return fileName

        image = await self.get()
        async with aiofiles.open(fileName, "wb") as file:
            await file.write(image)
        return fileName
