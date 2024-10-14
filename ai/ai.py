import logging

from langdetect import detect, LangDetectException
from openai import OpenAI, RateLimitError

from bot.messages import create_message
from bot.utils import utf16len

MAX_HYPE_TEXT_LENGTH = 200


def should_skip_text(text: str, max_length=MAX_HYPE_TEXT_LENGTH):
    if utf16len(text) > max_length:
        return False
    try:
        client = OpenAI()
        language = detect(text)
        prompt = create_message("prompt.detect.comments.request", language)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You can answer only 'YES' or 'NO'. Answer 'NO' if you are not sure."},
                {
                    "role": "user",
                    "content": f"""
                    {prompt}
                    <Start of text>
                    {text}
                    <End of text>
                    """
                }
            ]
        )
        answer = completion.choices[0].message.content
        return answer == "YES"
    except RateLimitError:
        logging.info("Rate limit exceeded")
    except LangDetectException:
        logging.info(f"Failed to detect language in text: {text}")
    except Exception as e:
        logging.exception(e)
    return False
