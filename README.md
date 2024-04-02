Youtube Insight Generator
=========================

Note: This script uses the OpenAI API. To configure the script's OpenAI
functionality, you should configure OpenAI API key of two of the possible
ways:

## Creating a configuration file

```sh
# save api key to `~/.config/openai.token` file
echo "YOUR_OPENAI_API_KEY" > ~/.config/openai.token
```

## Running the script with the OPENAI_API_KEY environment variable

```sh
OPENAI_API_KEY="YOUR_OPENAI_API_KEY" poetry run ./yt_insight_generator.py --source="https://www.youtube.com/watch?v=JpviQnH3Hdw" --destination=article.md --author="Jean-Pierre Chauvel" -t cat siamese
```

## Installation and Execution

1. Install poetry

```sh
pip install poetry
```

2. Install the project dependencies

```sh
poetry install
```

3. Run the script's help
```sh
poetry run ./yt_insight_generator.py --help
```
