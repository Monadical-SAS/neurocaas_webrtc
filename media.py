import av
import cv2
import asyncio
from datetime import datetime

from aiortc.contrib.media import (
    MediaPlayer,
    MediaRelay,
    MediaRecorder,
    MediaStreamError,
    MediaRecorderContext,
)


class CountsPerSec:
    """
    Class that tracks the number of occurrences ("counts") of an
    arbitrary event and returns the frequency in occurrences
    (counts) per second. The caller must increment the count.
    """

    def __init__(self):
        self._start_time = None
        self._num_occurrences = 0

    def start(self):
        self._start_time = datetime.now()
        return self

    def increment(self):
        self._num_occurrences += 1

    def countsPerSec(self):
        elapsed_time = (datetime.now() - self._start_time).total_seconds()
        return self._num_occurrences / elapsed_time

class MyMediaShower:

    """
    A media sink that writes audio and/or video to a file.
    Examples:
    .. code-block:: python
        # Write to a video file.
        player = MediaRecorder('/path/to/file.mp4')
        # Write to a set of images.
        player = MediaRecorder('/path/to/file-%3d.png')
    :param file: The path to a file, or a file-like object.
    :param format: The format to use, defaults to autodect.
    :param options: Additional options to pass to FFmpeg.
    """

    def __init__(self, format=None, options={}):
        self.__tracks = {}
        self.stopped = False
        self.cps = CountsPerSec().start()

    def addTrack(self, track):
        """
        Add a track to be recorded.
        :param track: A :class:`aiortc.MediaStreamTrack`.
        """
        self.__tracks[track] = MediaRecorderContext(None)

    async def start(self):
        """
        Start recording.
        """
        for track, context in self.__tracks.items():
            if context.task is None:
                context.task = asyncio.ensure_future(self.__run_track(track, context))

    async def stop(self):
        """
        Stop recording.
        """
        if self.__container:
            for track, context in self.__tracks.items():
                if context.task is not None:
                    context.task.cancel()
                    context.task = None
            self.__tracks = {}

    async def __run_track(self, track, context):
        while True:
            try:
                frame = await track.recv()
                if frame:
                    # self.cps.increment()
                    cv2.imshow("Video", frame.to_ndarray(format="rgb24"))
                    if cv2.waitKey(1) == ord("q"):
                        self.stopped = True

            except MediaStreamError:
                return

