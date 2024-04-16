#!/usr/bin/env python3
import argparse
import datetime
import os
from urllib.parse import urlparse, parse_qs

from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
from jinja2 import BaseLoader, Environment

CONF_FILE = "~/.config/openai.token"
AI_TAG = "ai-generated"
TEMPLATE = """
The following text is a transcript from a YouTube video. Write a post in
Markdown giving an insight about the content of the video:
```
{{ transcript }}
```
Notes:
- Avoid generating text about any sponsorships.
- The generated Markdown should be in 80 columns.
- Prepend the generated Markdown with the following directive (include the
  three dashes):
---
blogpost: true
date: {{ date }}
author: {{ author }}
{% if category %}
category: {{ category }}
{% endif %}
tags: {{ tags }}
---
- Insert somewhere in the generated Markdown text the video ID `{{ video_id }}`
  with the following format (Include the three backticks before and after the
  youtube directive):
```{youtube} the_video_id
```
- Generate the content in {{ language }}.
- Include several sections.
{%if words %}
- Use at least {{ words }} words.
{% endif %}
"""


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
        description="A Sphinx post generator that creates YouTube video's"
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
        help="The Markdown (.md extension) output file of the post.",
    )
    parser.add_argument(
        "-l",
        "--language",
        dest="language",
        type=str,
        default="English",
        help="The language of the resulting post."
    )
    parser.add_argument(
        "-a",
        "--author",
        dest="author",
        type=str,
        required=True,
        help="The name of the author of the post.",
    )
    parser.add_argument(
        "-c",
        "--category",
        dest="category",
        type=str,
        help="The category of the post.",
    )
    parser.add_argument(
        "-w",
        "--words",
        dest="words",
        type=str,
        help="The number of words for the post.",
    )
    parser.add_argument(
        "-t",
        dest="tags",
        nargs="+",
        type=str,
        help="The tags of the post.",
    )
    args = parser.parse_args()
    return args


def get_message_template():
    template = Environment(
        loader=BaseLoader, trim_blocks=True, lstrip_blocks=True
    ).from_string(TEMPLATE)
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
                    words=args.words,
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
