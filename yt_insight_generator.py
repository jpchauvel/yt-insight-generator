#!/usr/bin/env python3
import argparse
import datetime
import os
from urllib.parse import urlparse, parse_qs

from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
from jinja2 import Environment, PackageLoader, select_autoescape

CONF_FILE = "~/.config/openai.token"
AI_TAG = "ai-generated"


class KnownError(Exception):
    pass


def get_conf_file_contents():
    filepath = os.path.expanduser(CONF_FILE)
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r") as fd:
        return fd.read().strip()


def get_api_key():
    api_key = get_conf_file_contents()
    if api_key is None:
        # try to get it from the the environment variable `OPENAI_API_KEY`
        api_key = os.environ.get('OPENAI_API_KEY')
    if api_key is None:
        raise KnownError("Missing OpenAI key.")
    return api_key


def get_video_id(video_url):
    video_ids = parse_qs(urlparse(video_url).query).get('v')
    if video_ids is None:
        raise KnownError(
            "Missing `v` querystring variable in YouTube video URL."
        )
    return video_ids[0]


def get_args():
    parser = argparse.ArgumentParser(
        description="An Sphinx article generator that creates YouTube video's"
        " insights using OpenAI's API.",
    )
    parser.add_argument(
        "-s",
        "--source",
        dest="source",
        type=str,
        required=True,
        help="The Youtube video URL.",
    )
    parser.add_argument(
        "-d",
        "--destination",
        dest="destination",
        type=str,
        required=True,
        help="The Markdown (.md extension) output file of the article.",
    )
    parser.add_argument(
        "-l",
        "--language",
        dest="language",
        type=str,
        default="English",
        help="The language of the resulting article."
    )
    parser.add_argument(
        "-a",
        "--author",
        dest="author",
        type=str,
        required=True,
        help="The name of the author of the article.",
    )
    parser.add_argument(
        "-c",
        "--category",
        dest="category",
        type=str,
        help="The category of the article."
    )
    parser.add_argument(
        "-t",
        dest="tags",
        nargs="+",
        type=str,
        required=True,
        help="The tags of the article.",
    )
    args = parser.parse_args()
    return args


def get_message_template():
    env = Environment(
        loader=PackageLoader("yt_insight_generator", "templates"),
        autoescape=select_autoescape(),
    )
    template = env.get_template("ai-message.txt")
    return template


def main():
    args = get_args()
    video_id = get_video_id(args.source)
    transcript = "\n".join(
        [
            t["text"]
            for t in YouTubeTranscriptApi.get_transcript(video_id)
        ]
    )
    client = OpenAI(api_key=get_api_key())
    template = get_message_template()
    stream = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {
                "role": "user",
                "content": template.render(
                    date=datetime.date.today().strftime("%d %b, %Y"),
                    author=args.author,
                    category=args.category,
                    tags=", ".join(args.tags + [AI_TAG]),
                    language=args.language,
                    video_id=video_id,
                    transcript=transcript,
                )
            },
        ],
        stream=True,
    )
    with open(os.path.expanduser(args.destination), "w") as fd:
        for chunk in stream:
            data = chunk.choices[0].delta.content or ""
            print(data, end="")
            fd.write(data)
        print("")


if __name__ == "__main__":
    main()
