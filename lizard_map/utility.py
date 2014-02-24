"""Small utility functions"""
from tls import request


def short_string(value, length):
    """
    Shorten string to given length. Length must be >= 5

    TODO: wordwrap
    """

    if len(value) <= length:
        return value  # Already short enough
        
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
        float_value = float(value)
    except (TypeError, ValueError):
        # It is not a number so we just pass it on.
        return value
    abs_float_value = abs(float_value)
    if (0 < abs_float_value < 0.01) or (abs_float_value >= 1000000000):
        return '%.2e' % float_value
    if abs_float_value >= 10000000:
        return '%.0f' % float_value
    return '%.2f' % float_value


def analyze_http_user_agent(http_user_agent):
    """Analyzes http_user_agent and return dictionary of properties."""
    device = 'other'

    if 'iPad' in http_user_agent:
        device = 'iPad'

    return {'device': device}


def get_host():
    """Get the current host.

    Needed in the multitancy Lizard 5 site for cache keys.
    """
    host = ''
    if hasattr(request, 'get_host'):
        host = request.get_host()
    return host
