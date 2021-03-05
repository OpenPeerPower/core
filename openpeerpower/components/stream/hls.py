"""Provide functionality to stream HLS."""
import io

from aiohttp import web

from openpeerpower.core import callback

from .const import FORMAT_CONTENT_TYPE, MAX_SEGMENTS, NUM_PLAYLIST_SEGMENTS
from .core import PROVIDERS, IdleTimer, OpenPeerPower, StreamOutput, StreamView
from .fmp4utils import get_codec_string, get_init, get_m4s


@callback
def async_setup_hls(opp):
    """Set up api endpoints."""
    opp.http.register_view(HlsPlaylistView())
    opp.http.register_view(HlsSegmentView())
    opp.http.register_view(HlsInitView())
    opp.http.register_view(HlsMasterPlaylistView())
    return "/api/hls/{}/master_playlist.m3u8"


class HlsMasterPlaylistView(StreamView):
    """Stream view used only for Chromecast compatibility."""

    url = r"/api/hls/{token:[a-f0-9]+}/master_playlist.m3u8"
    name = "api:stream:hls:master_playlist"
    cors_allowed = True

    @staticmethod
    def render(track):
        """Render M3U8 file."""
        # Need to calculate max bandwidth as input_container.bit_rate doesn't seem to work
        # Calculate file size / duration and use a small multiplier to account for variation
        # hls spec already allows for 25% variation
        segment = track.get_segment(track.segments[-1])
        bandwidth = round(
            segment.segment.seek(0, io.SEEK_END) * 8 / segment.duration * 1.2
        )
        codecs = get_codec_string(segment.segment)
        lines = [
            "#EXTM3U",
            f'#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},CODECS="{codecs}"',
            "playlist.m3u8",
        ]
        return "\n".join(lines) + "\n"

    async def handle(self, request, stream, sequence):
        """Return m3u8 playlist."""
        track = stream.add_provider("hls")
        stream.start()
        # Wait for a segment to be ready
        if not track.segments:
            if not await track.recv():
                return web.HTTPNotFound()
        headers = {"Content-Type": FORMAT_CONTENT_TYPE["hls"]}
        return web.Response(body=self.render(track).encode("utf-8"), headers=headers)


class HlsPlaylistView(StreamView):
    """Stream view to serve a M3U8 stream."""

    url = r"/api/hls/{token:[a-f0-9]+}/playlist.m3u8"
    name = "api:stream:hls:playlist"
    cors_allowed = True

    @staticmethod
    def render_preamble(track):
        """Render preamble."""
        return [
            "#EXT-X-VERSION:7",
            f"#EXT-X-TARGETDURATION:{track.target_duration}",
            '#EXT-X-MAP:URI="init.mp4"',
        ]

    @staticmethod
    def render_playlist(track):
        """Render playlist."""
        segments = list(track.get_segment())[-NUM_PLAYLIST_SEGMENTS:]

        if not segments:
            return []

        playlist = [
            "#EXT-X-MEDIA-SEQUENCE:{}".format(segments[0].sequence),
            "#EXT-X-DISCONTINUITY-SEQUENCE:{}".format(segments[0].stream_id),
        ]

        last_stream_id = segments[0].stream_id
        for segment in segments:
            if last_stream_id != segment.stream_id:
                playlist.append("#EXT-X-DISCONTINUITY")
            playlist.extend(
                [
                    "#EXTINF:{:.04f},".format(float(segment.duration)),
                    f"./segment/{segment.sequence}.m4s",
                ]
            )
            last_stream_id = segment.stream_id

        return playlist

    def render(self, track):
        """Render M3U8 file."""
        lines = ["#EXTM3U"] + self.render_preamble(track) + self.render_playlist(track)
        return "\n".join(lines) + "\n"

    async def handle(self, request, stream, sequence):
        """Return m3u8 playlist."""
        track = stream.add_provider("hls")
        stream.start()
        # Wait for a segment to be ready
        if not track.segments:
            if not await track.recv():
                return web.HTTPNotFound()
        headers = {"Content-Type": FORMAT_CONTENT_TYPE["hls"]}
        return web.Response(body=self.render(track).encode("utf-8"), headers=headers)


class HlsInitView(StreamView):
    """Stream view to serve HLS init.mp4."""

    url = r"/api/hls/{token:[a-f0-9]+}/init.mp4"
    name = "api:stream:hls:init"
    cors_allowed = True

    async def handle(self, request, stream, sequence):
        """Return init.mp4."""
        track = stream.add_provider("hls")
        segments = track.get_segment()
        if not segments:
            return web.HTTPNotFound()
        headers = {"Content-Type": "video/mp4"}
        return web.Response(body=get_init(segments[0].segment), headers=headers)


class HlsSegmentView(StreamView):
    """Stream view to serve a HLS fmp4 segment."""

    url = r"/api/hls/{token:[a-f0-9]+}/segment/{sequence:\d+}.m4s"
    name = "api:stream:hls:segment"
    cors_allowed = True

    async def handle(self, request, stream, sequence):
        """Return fmp4 segment."""
        track = stream.add_provider("hls")
        segment = track.get_segment(int(sequence))
        if not segment:
            return web.HTTPNotFound()
        headers = {"Content-Type": "video/iso.segment"}
        return web.Response(
            body=get_m4s(segment.segment, int(sequence)),
            headers=headers,
        )


@PROVIDERS.register("hls")
class HlsStreamOutput(StreamOutput):
    """Represents HLS Output formats."""

    def __init__(self, opp: OpenPeerPower, idle_timer: IdleTimer) -> None:
        """Initialize recorder output."""
        super().__init__(opp, idle_timer, deque_maxlen=MAX_SEGMENTS)

    @property
    def name(self) -> str:
        """Return provider name."""
        return "hls"
