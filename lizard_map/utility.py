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


def float_to_string(value):
    """Converts float to nice string representing the float. The
    resulting string should always be 10 chars or smaller."""
    try:
        float(value)
    except (TypeError, ValueError):
        # It is not a number so we just pass it on.
        return value
    if (0 < abs(value) < 0.01) or (abs(value) >= 1000000000):
        return '%.2e' % value
    if abs(value) >= 10000000:
        return '%.0f' % value
    return '%.2f' % value
