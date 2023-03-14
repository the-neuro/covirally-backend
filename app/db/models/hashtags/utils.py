import re

from app.db.models.hashtags.handlers import add_hashtags


def extract_hashtags_from_text(text: str) -> list[str]:
    hashtag_reg = r"\B\#([-_0-9a-zA-Z]{1,20}\b)\s?(?![;=@!±§<>\.\?#$%^&*\(\)])"
    extracted = re.findall(hashtag_reg, text)
    return list({tag.lower() for tag in extracted})


async def extract_and_insert_hashtags(text: str, task_id: str) -> None:
    hashtags = extract_hashtags_from_text(text)
    await add_hashtags(tags=hashtags, task_id=task_id)
