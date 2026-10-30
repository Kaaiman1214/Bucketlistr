import unicodedata


def fold(text):
    """Lower-case a string and strip accents, so 'Curacao' and 'Curaçao' sort and match alike."""
    decomposed = unicodedata.normalize('NFKD', text or '')
    return ''.join(c for c in decomposed if not unicodedata.combining(c)).casefold()
