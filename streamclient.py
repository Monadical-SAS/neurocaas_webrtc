import asyncio
import logging
import platform
import time
import uuid

import requests
from aiortc import (RTCPeerConnection, RTCSessionDescription)
from aiortc.contrib.media import (MediaPlayer, MediaRecorder, MediaRelay)


import media
from utils import ConfigDLC

logger = logging.getLogger("pc")


class StreamClient:
    def __init__(
        self,
        signaling,
        url="http://127.0.0.1:8080",
        record_video=False,
        show_video=True,
        record_filename="test.mp4",
        play_from=None,
        ping_pong=False,
        return_poses=False,
        transform=''
    ):
        self.signaling = signaling
        self.server_url = url
        self.show_video = show_video
        self.record_video = record_video
        self.record_filename = record_filename
        self.play_from = play_from
        self.ping_pong = ping_pong
        self.return_poses = return_poses
        self.transform = transform

        self.pc = RTCPeerConnection()

        self.loop = asyncio.get_event_loop()
        # self.loop = asyncio.new_event_loop()
        self.relay = None
        self.webcam = None
        self.pcs = set()
        self.time_start = None
        self.queue = asyncio.Queue()

        self.cfg = ConfigDLC('dlc_config').get_config()

        if self.record_video:
            self.recorder = MediaRecorder(self.record_filename)
        if self.show_video:
            self.shower = media.MyMediaShower()

    def stop(self):
        self.loop.run_until_complete(self.signaling.close())
        if self.record_video:
            self.loop.run_until_complete(self.recorder.stop())
        if self.show_video:
            self.loop.run_until_complete(self.shower.stop())
        self.loop.run_until_complete(self.pc.close())
        # self.loop.close()
        print("ended")

    def create_local_tracks(self, play_from):
        if play_from:
            player = MediaPlayer(play_from)
            return player.audio, player.video
        else:
            fps = self.cfg['cameras']['params']['fps']
            width = self.cfg['cameras']['params']['resolution'][0]
            height = self.cfg['cameras']['params']['resolution'][1]
            device = self.cfg['cameras']['params']['device']

            options = {
                "framerate": f"{fps}",
                "video_size": f"{width}x{height}"
            }

            if self.relay is None:
                if platform.system() == "Darwin":
                    self.webcam = MediaPlayer(
                        "default:none", format="avfoundation", options=options
                    )
                elif platform.system() == "Windows":
                    self.webcam = MediaPlayer(
                        "video=Integrated Camera", format="dshow", options=options
                    )
                else:
                    self.webcam = MediaPlayer(
                        device, format="v4l2", options=options
                    )
                self.relay = MediaRelay()
            return None, self.relay.subscribe(self.webcam.video)

    def channel_log(self, channel, t, message):
        print("channel(%s) %s %s" % (channel.label, t, message))

    def channel_send(self, channel, message):
        self.channel_log(channel, ">", message)
        channel.send(message)

    def current_stamp(self):

        if self.time_start is None:
            self.time_start = time.time()
            return 0
        else:
            return int((time.time() - self.time_start) * 1000000)

    async def run_offer(self, pc, signaling):
        # webcam
        audio, video = self.create_local_tracks(self.play_from)
        pc_id = "PeerConnection(%s)" % uuid.uuid4()
        self.pcs.add(pc)

        def log_info(msg, *args):
            logger.info(pc_id + " " + msg, *args)

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            print("Connection state is %s" % pc.connectionState)
            if pc.connectionState == "failed":
                await pc.close()
                pc.discard(pc)

        @pc.on("track")
        def on_track(track):
            print("Receiving %s" % track.kind)
            if self.record_video:
                self.recorder.addTrack(self.relay.subscribe(track))
            if self.show_video:
                self.shower.addTrack(self.relay.subscribe(track))

            @track.on("ended")
            async def on_ended():
                log_info("Track %s ended", track.kind)
                if self.record_video:
                    await self.recorder.stop()
                if self.show_video:
                    await self.shower.stop()

        if self.webcam and self.webcam.video:
            pc.addTrack(self.webcam.video)

        # DataChannel
        channel = pc.createDataChannel("data-channel")
        self.channel_log(channel, "-", "created by local party")


        async def send_pings():
            while True:
                self.channel_send(channel, "ping %d" % self.current_stamp())
                await asyncio.sleep(1)

        @channel.on("open")
        def on_open():
            if self.ping_pong:
                asyncio.ensure_future(send_pings())

        @channel.on("message")
        def on_message(message):
            self.queue.put_nowait(message)
            if self.ping_pong:
                self.channel_log(channel, "<", message)

                if isinstance(message, str) and message.startswith("pong"):
                    elapsed_ms = (self.current_stamp() - int(message[5:])) / 1000
                    print(" RTT %.2f ms" % elapsed_ms)


        await pc.setLocalDescription(await pc.createOffer())

        sdp = {
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type,
            "video_transform": self.transform,
            "return_poses": self.return_poses
        }

        try:
            request = requests.post(self.server_url, json=sdp, timeout=10)
        except:
            SystemExit("Could not reach signaling server")

        params = request.json()
        answer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
        await pc.setRemoteDescription(answer)
        if self.record_video:
            await self.recorder.start()
        if self.show_video:
            await self.shower.start()

        self.reader = self.worker(f"worker", self.queue)

    def get_reader(self):
        return self.reader

    async def worker(self, name, queue):
        while True:
            # Get a "work item" out of the queue.
            msg = await self.queue.get()

            # Notify the queue that the "work item" has been processed.
            yield msg
            self.queue.task_done()

    async def start(self):
        coro = self.run_offer(self.pc, self.signaling)
        task = asyncio.create_task(coro)
        await task
