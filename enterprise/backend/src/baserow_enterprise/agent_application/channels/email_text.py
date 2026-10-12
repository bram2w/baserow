import html
import re

# What mail clients put above the quoted earlier message. Everything from
# the first match on is the quote, not the person's new words.
_QUOTE_HEADER_PATTERNS = [
    # Gmail, Apple Mail and most others: "On <date>, <name> wrote:", possibly
    # wrapped over two lines.
    re.compile(r"^On .{3,200}?wrote:\s*$", re.IGNORECASE | re.DOTALL | re.MULTILINE),
    re.compile(r"^-{2,}\s*Original Message\s*-{2,}\s*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^-{2,}\s*Forwarded message\s*-{2,}\s*$", re.IGNORECASE | re.MULTILINE),
    # Outlook's header block.
    re.compile(
        r"^(?:From|Van|Von|De):\s.*\n(?:(?:Sent|Verzonden|Gesendet|Envoyé|Date|To|Aan|An|À|Cc|Subject|Onderwerp|Betreff|Objet):\s.*\n)+",
        re.IGNORECASE | re.MULTILINE,
    ),
    # French, German, Dutch, Spanish variants of "wrote:".
    re.compile(
        r"^Le .{3,200}?a écrit\s?:\s*$", re.IGNORECASE | re.DOTALL | re.MULTILINE
    ),
    re.compile(
        r"^Am .{3,200}?schrieb .{0,100}?:\s*$", re.IGNORECASE | re.DOTALL | re.MULTILINE
    ),
    re.compile(
        r"^Op .{3,200}?schreef .{0,100}?:\s*$", re.IGNORECASE | re.DOTALL | re.MULTILINE
    ),
    re.compile(r"^El .{3,200}?escribió:\s*$", re.IGNORECASE | re.DOTALL | re.MULTILINE),
]
_SIGNATURE_SEPARATOR = re.compile(r"^--\s*$", re.MULTILINE)


def strip_quoted_reply(text: str) -> str:
    """
    The new words of a reply: whatever comes before the quoted earlier
    message, the quoted lines themselves and a `-- ` signature. Clients
    differ in how they mark the quote, so this is a best effort; an email
    that matches nothing is returned whole.
    """

    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    cut = len(text)
    for pattern in _QUOTE_HEADER_PATTERNS:
        match = pattern.search(text)
        if match and match.start() < cut:
            cut = match.start()
    text = text[:cut]

    # A run of `>` quoted lines at the end is a quote without a header.
    lines = text.split("\n")
    while lines and (not lines[-1].strip() or lines[-1].lstrip().startswith(">")):
        lines.pop()
    text = "\n".join(lines)

    signature = _SIGNATURE_SEPARATOR.search(text)
    if signature:
        text = text[: signature.start()]
    return text.strip()


# A tag never spans a `<`; without that, every unclosed `<` would scan to the
# end of the body, which is quadratic on hostile mail.
_BLOCK_TAGS = re.compile(
    r"</?(?:p|div|br|tr|li|h[1-6]|blockquote|table|ul|ol|section|article)[^<>]*>",
    re.IGNORECASE,
)
_HIDDEN_OPEN = re.compile(r"<(script|style|head)[^<>]*>", re.IGNORECASE)
_HIDDEN_CLOSE = {
    tag: re.compile(f"</{tag}>", re.IGNORECASE) for tag in ("script", "style", "head")
}
_TAGS = re.compile(r"<[^<>]+>")
_BLANK_LINES = re.compile(r"\n{3,}")


def _strip_hidden_blocks(markup: str) -> str:
    # A lazy `<style>.*?</style>` regex rescans the rest of the body for every
    # unclosed opening tag. A tag found without a closing one can't have one
    # further on either, so it is only searched for once.
    parts, position, unclosed = [], 0, set()
    while True:
        opening = _HIDDEN_OPEN.search(markup, position)
        if opening is None:
            break
        tag = opening.group(1).lower()
        closing = None
        if tag not in unclosed:
            closing = _HIDDEN_CLOSE[tag].search(markup, opening.end())
        if closing is None:
            unclosed.add(tag)
            parts.append(markup[position : opening.end()])
        else:
            parts.append(markup[position : opening.start()])
        position = opening.end() if closing is None else closing.end()
    parts.append(markup[position:])
    return "".join(parts)


def html_to_text(markup: str) -> str:
    """A readable plain text rendering of an HTML body, for mail without one."""

    text = _strip_hidden_blocks(markup or "")
    text = _BLOCK_TAGS.sub("\n", text)
    text = _TAGS.sub("", text)
    text = html.unescape(text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    return _BLANK_LINES.sub("\n\n", text).strip()


_REPLY_PREFIXES = re.compile(
    r"^\s*(?:(?:re|aw|sv|vs|fwd?|tr|wg|antw|antwoord)\s*:\s*)+", re.IGNORECASE
)


def normalize_subject(subject: str) -> str:
    """The subject without reply and forward prefixes, for matching threads."""

    return _REPLY_PREFIXES.sub("", subject or "").strip().lower()


def reply_subject(subject: str) -> str:
    subject = (subject or "").strip()
    if not subject:
        return "Re: your message"
    return subject if subject.lower().startswith("re:") else f"Re: {subject}"
