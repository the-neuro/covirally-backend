from collections import Counter

from app.db.models.hashtags.utils import extract_hashtags_from_text


def test_extract_tags_from_text():
    tag_with_20_symbols = 'alfkbnfdlknasdasdasd'
    tag_with_more_than_20_symbols = 'asdsadasaldjgnaljdgna'

    text = f"""
    #asd sdlkvjaf  lakDFNA 0-A232 VAER an95cmd
    #ASD #DD
    ####D-as
    #_____das
    #vmsd__
    #000as
    ##
    #{tag_with_more_than_20_symbols}
    #{tag_with_20_symbols}
    """

    extracted_hashtags = extract_hashtags_from_text(text)

    expected = ['asd', 'dd', 'd-as', '_____das', 'vmsd__', '000as', tag_with_20_symbols]
    assert Counter(extracted_hashtags) == Counter(expected)
