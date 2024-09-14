def word_stats(text):
    if not text or text.isspace():
        return {'word_count': 0, 'char_count': 0, 'avg_word_length': 0.0}

    words = text.split()
    word_count = len(words)
    char_count = sum(len(word) for word in words)
    avg_word_length = round(char_count / word_count, 2) if word_count > 0 else 0.0

    return {
        'word_count': word_count,
        'char_count': char_count,
        'avg_word_length': avg_word_length
    }
