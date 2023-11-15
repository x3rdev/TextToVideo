import asyncio
import time
from random import random

import edge_tts
import ffmpeg
import ffprobe
import pysubs2

TEXT = '''

Am i the asshole for referring to a binder as “dummy thicc”?

I work in a role where I have a lot of say about the office furniture and decor. Think office operations, trying not to be too specific here. The other day my coworker handed me a binder of new furniture options since we are upgrading some items in the office. I expected a small stapled packet of paper but it was a binder that was at least 3” thick. So I laughed and said “damn this binder is DUMMY thicc”

Anyway I thought nothing of it until a week later when my coworker reported me to HR for using hostile language that made her feel uncomfortable because I had commented on women’s bodies. I told HR I was commenting on the binder, not a woman, and made what was probably a bad Mitt Romney joke but I have this problem where I just can’t resist. Anyway I apologized to my coworker if it offended her but I feel weird “owning up to” being creepy about women’s bodies when I would never actually say that about a real woman. am i the asshole?

'''

VOICE = "en-US-ChristopherNeural"
OUTPUT_FILE = "./temp/test.mp3"
WEBVTT_FILE = "./temp/test.vtt"


async def audio() -> None:
    communicate = edge_tts.Communicate(TEXT, VOICE)
    communicate.rate = 1.3

    submaker = edge_tts.SubMaker()
    with open(OUTPUT_FILE, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.create_sub((chunk["offset"], chunk["duration"]), chunk["text"])

    with open(WEBVTT_FILE, "w", encoding="utf-8") as file:
        file.write(submaker.generate_subs())


async def combine() -> None:
    audio_length = ffprobe.FFProbe("./temp/test.mp3").streams[0].duration_seconds() + 2
    video_start = random() * (ffprobe.FFProbe("./source/source.mp4").streams[0].duration_seconds() - audio_length - 4)
    input_video = ffmpeg.input("./source/source.mp4", ss=video_start, t=audio_length)
    input_audio = ffmpeg.input("./temp/test.mp3", t=audio_length)
    subs = pysubs2.load("./temp/test.vtt")
    subs.save("./temp/subtitles.ass")

    (ffmpeg
     .concat(input_video, input_audio, v=1, a=1)
     .filter("crop", 608, 1080)
     .filter("subtitles", "./temp/subtitles.ass")
     .output("./output/finished_video.mp4")
     .run(overwrite_output=True))


def time_stamp(seconds):
    return time.strftime('%H:%M:%S', time.gmtime(seconds))


if __name__ == "__main__":
    print("Starting TextToVideo")
    loop = asyncio.get_event_loop_policy().get_event_loop()
    try:
        loop.run_until_complete(audio())
        loop.run_until_complete(combine())
    finally:
        loop.close()