"""
These regexes must be kept in sync with web-frontend/modules/database/search/regexes.js
"""

import re

RE_ONE_OR_MORE_WHITESPACE = re.compile(r"\s+", re.UNICODE)
RE_TO_REMOVE_EMAIL_URL_AND_POSITIVE_INT_PUNCTUATION = r"[@:/+.]"
RE_DASH_NOT_FOLLOWED_BY_DIGIT = r"-(?!\d)"
RE_DASH_PRECEDED_BY_NON_WHITESPACE_AND_FOLLOWED_BY_DIGIT = r"(?<=\S)-(?=\d)"
RE_STANDALONE_DASH = r"\b-\b"
RE_MATCH_ALL_DASH_OTHER_THAN_NEGATIVE_NUMBERS_AND_DECIMAL_NUMBERS = "|".join(
    [
        RE_DASH_NOT_FOLLOWED_BY_DIGIT,
        RE_DASH_PRECEDED_BY_NON_WHITESPACE_AND_FOLLOWED_BY_DIGIT,
        RE_STANDALONE_DASH,
    ]
)

"""
This regex pattern is used to simplify input strings
passed to postgresql's to_tsvector to prevent it from doing smart tokenization of
say emails. This smart tokenization prevents us from doing a simple frontend search
to match the backend, so we prevent it by just excluding certain characters.

Also due to the fact that we can't create custom postgres full text search
dictionaries on behalf of our
users (which would really super-user privileges) we need to do this.
"""
RE_REMOVE_NON_SEARCHABLE_PUNCTUATION_FROM_TSVECTOR_DATA = re.compile(
    "|".join(
        [
            RE_TO_REMOVE_EMAIL_URL_AND_POSITIVE_INT_PUNCTUATION,
            RE_MATCH_ALL_DASH_OTHER_THAN_NEGATIVE_NUMBERS_AND_DECIMAL_NUMBERS,
        ]
    ),
    re.UNICODE,
)

RE_ALL_NON_WHITESPACE_OR_WORD_CHARACTERS_EXCLUDING_DASH = r"[^\w\s\-]"

"""
This regex is used on search terms provided by users before we construct a value
to pass to to_tsquery.

We remove any characters that could cause
to_tsquery to crash (it supports say text:* to match tokens starting with text, but :*
on its own is invalid and will crash to_tsquery). To do this we can just strip out
all punctuation other than some specific situations.

Also by stripping out all punctuation we emulate what to_tsvector does. By doing this
when we split the users query into individual terms, we make sure we split these terms
into tokens that will match what to_tsvector did.

For example to_tsvector('simple', "Base&^%row") will store two tokens in the tsvector:
"Base" followed by "row". So then if a user searches for "Base&^%row" we want to
produce the ts query input "Base <-> row:*", to do this we must strip out all the
punctuation, replace it with spaces and split on space to get the same tokens we can
then join with <->!
"""
RE_REMOVE_ALL_PUNCTUATION_ALREADY_REMOVED_FROM_TSVS_FOR_QUERY = re.compile(
    "|".join(
        [
            RE_ALL_NON_WHITESPACE_OR_WORD_CHARACTERS_EXCLUDING_DASH,
            "_",
            RE_MATCH_ALL_DASH_OTHER_THAN_NEGATIVE_NUMBERS_AND_DECIMAL_NUMBERS,
        ]
    ),
    re.UNICODE,
)
