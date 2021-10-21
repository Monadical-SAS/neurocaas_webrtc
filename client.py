import argparse
import asyncio
import logging
import signal
from datetime import datetime

from aiortc.contrib.signaling import (add_signaling_arguments,
                                      create_signaling)

from streamclient import StreamClient
from utils import deserialize_numpy_array

logger = logging.getLogger("pc")


async def main():
    parser = argparse.ArgumentParser(description="Data channels ping/pong")

    parser.add_argument(
        "--url", type=str, nargs="?", default="http://127.0.0.1:8080/offer"
    )

    parser.add_argument(
        "--show",
        help="Show the video window. True or False",
        type=eval,
        choices=[True, False],
        default="True",
    )
    parser.add_argument(
        "--record",
        help="Record the video. True or False",
        type=eval,
        choices=[True, False],
        default="False",
    )

    parser.add_argument(
        "--ping-pong",
        help="Benchmark data channel with ping pong",
        type=eval,
        choices=[True, False],
        default="False",
    )

    parser.add_argument(
        "--filename",
        type=str,
        help="Video Record filename",
        nargs="?",
        default=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}.mp4",
    )

    parser.add_argument(
        "--play-from",
        type=str,
        default="",
    )

    parser.add_argument(
        "--poses",
        help="Return poses in datachannel",
        type=eval,
        choices=[True, False],
        default="False",
    )

    parser.add_argument(
        "--transform",'-tf',
        help="Video transform option",
        type=str,
        default="",
    )

    parser.add_argument("--verbose", "-v", action="count")
    add_signaling_arguments(parser)

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    signaling = create_signaling(args)

    async def shutdown(signal, loop):
        """Cleanup tasks tied to the service's shutdown."""
        logging.info(f"Received exit signal {signal.name}...")
        logging.info("Closing database connections")
        logging.info("Nacking outstanding messages")
        tasks = [t for t in asyncio.all_tasks() if t is not
                asyncio.current_task()]

        [task.cancel() for task in tasks]

        logging.info(f"Cancelling {len(tasks)} outstanding tasks")
        await asyncio.gather(*tasks, return_exceptions=True)
        logging.info(f"Flushing metrics")
        loop.stop()

    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    loop = asyncio.get_event_loop()
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(shutdown(s, loop)))

    # Init client
    sc = StreamClient(
        signaling=signaling,
        url=args.url,
        record_video=args.record,
        show_video=args.show,
        record_filename=args.filename,
        play_from=args.play_from,
        ping_pong=args.ping_pong,
        return_poses=args.poses,
        transform=args.transform
    )
    await sc.start()

    async for msg in sc.get_reader():
        if sc.transform == 'dlclive':
            try:
                print(deserialize_numpy_array(msg))
            except:
                print(msg)
        else:
            print(msg)


if __name__ == "__main__":
    asyncio.run(main())
