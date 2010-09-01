"""Small utility functions"""

def short_string(value, length):
    """
    Shorten string to given length. Length must be >= 5

    TODO: wordwrap
    """

    if value == value[:length]:
        return value
    else:
        length_pre = min(int(length * 0.75), length - 3)
        length_post = max(length - length_pre - 3, 0)
        result = value[:length_pre] + '...'
        if length_post > 0:
            result += value[-length_post:]
        return result

