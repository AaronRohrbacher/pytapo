# SPDX-License-Identifier: GPL-2.0-only

from types import SimpleNamespace

import pytest

from pytapo.media_stream import PreviewStream, RecordingStream, RecordingThumbnail


class FakeSession:
    def __init__(self, responses):
        self._responses = responses
        self.closed = False
        self.started = False
        self.window_size = None

    def set_window_size(self, value):
        self.window_size = value

    async def start(self):
        self.started = True

    async def close(self):
        self.closed = True

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        await self.close()

    async def transceive(self, *_args, **_kwargs):
        for response in self._responses:
            yield response


class FakeTapo:
    def __init__(self, responses):
        self.session = FakeSession(responses)

    def getUserID(self):
        return "user-id"

    def getMediaSession(self, _stream_type):
        return self.session


def response(mimetype, plaintext=b"", json_data=None):
    return SimpleNamespace(mimetype=mimetype, plaintext=plaintext, json_data=json_data)


@pytest.mark.asyncio
async def test_thumbnail_returns_only_native_jpeg_through_eoi():
    tapo = FakeTapo([
        response("application/json", json_data={"error_code": 0}),
        response("image/jpeg", b"\xff\xd8native-jpeg\xff\xd9\x00\x00"),
    ])
    image = await RecordingThumbnail(tapo, 10, 20).get()
    assert image == b"\xff\xd8native-jpeg\xff\xd9"
    assert tapo.session.closed


@pytest.mark.asyncio
async def test_recording_stream_yields_transport_parts_and_closes():
    transport = response("video/mp2t", b"segment")
    tapo = FakeTapo([response("application/json", json_data={"error_code": 0}), transport])
    async with RecordingStream(tapo, 10, 20) as stream:
        assert [part async for part in stream.responses()] == [transport]
    assert tapo.session.started and tapo.session.closed


@pytest.mark.asyncio
async def test_preview_surfaces_camera_errors_and_still_closes():
    tapo = FakeTapo([response("application/json", json_data={"error_code": -1})])
    with pytest.raises(RuntimeError, match="error code -1"):
        async with PreviewStream(tapo) as stream:
            _ = [part async for part in stream.responses()]
    assert tapo.session.closed


@pytest.mark.parametrize("helper", [RecordingThumbnail, RecordingStream])
def test_recording_helpers_reject_invalid_event_range(helper):
    instance = helper(FakeTapo([]), 20, 20)
    with pytest.raises(ValueError):
        if isinstance(instance, RecordingThumbnail):
            __import__("asyncio").run(instance.get())
        else:
            __import__("asyncio").run(instance.start())
