import logging

from langdetect import detect
from openai import OpenAI, RateLimitError

from bot.messages import create_message


def should_skip_text(text: str):
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
        return False
    except Exception as e:
        logging.exception(e)
        return False
