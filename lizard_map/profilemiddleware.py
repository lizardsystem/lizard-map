from cStringIO import StringIO
from time import time
import functools
import logging
import os
import re
import tempfile

from django.conf import settings

# On some systems, hotshot is now available.
try:
    import hotshot
    import hotshot.stats
    hotshot = hotshot  # pyflakes...
except ImportError:
    hotshot = None

COMMENT_SYNTAX = ((re.compile(r'^application/(.*\+)?xml|text/html$', re.I),
                   '<!--', '-->'),
                  (re.compile(r'^application/j(avascript|son)$',     re.I),
                   '/*',   '*/'))


logger = logging.getLogger(__name__)

# Decorator from
# http://www.heikkitoivonen.net/blog/2011/02/02/decorator-to-log-slow-calls/


def time_slow(f=None, threshold=0.01):
    def decorated(f):
        @functools.wraps(f)
        def wrapper(*args, **kw):
            start = time()
            try:
                ret = f(*args, **kw)
            finally:
                duration = time() - start
                if duration > threshold:
                    logger.info('slow: %s %.9f seconds', f.__name__, duration)
            return ret
        return wrapper
    if f is not None:
        return decorated(f)
    return decorated


# Copied from somewhere by Reinout.
class ProfileMiddleware(object):
    def process_view(self, request, callback, args, kwargs):
        # For safety, if hotshot cannot be imported
        if hotshot is None:
            return

        # Create a profile, writing into a temporary file.
        filename = tempfile.mktemp()
        profile = hotshot.Profile(filename)

        try:
            try:
                # Profile the call of the view function.
                response = profile.runcall(callback, request, *args, **kwargs)

                # If we have got a 3xx status code, further
                # action needs to be taken by the user agent
                # in order to fulfill the request. So don't
                # attach any stats to the content, because of
                # the content is supposed to be empty and is
                # ignored by the user agent.
                if response.status_code // 100 == 3:
                    return response

                # Detect the appropriate syntax based on the
                # Content-Type header.
                for regex, begin_comment, end_comment in COMMENT_SYNTAX:
                    if regex.match(
                        response['Content-Type'].split(';')[0].strip()):
                        break
                else:
                    # If the given Content-Type is not
                    # supported, don't attach any stats to
                    # the content and return the unchanged
                    # response.
                    return response

                # The response can hold an iterator, that
                # is executed when the content property
                # is accessed. So we also have to profile
                # the call of the content property.
                content = profile.runcall(
                    response.__class__.content.fget, response)
            finally:
                profile.close()

            # Load the stats from the temporary file and
            # write them in a human readable format,
            # respecting some optional settings into a
            # StringIO object.
            stats = hotshot.stats.load(filename)
            if getattr(settings, 'PROFILE_MIDDLEWARE_STRIP_DIRS', False):
                stats.strip_dirs()
            # if getattr(settings, 'PROFILE_MIDDLEWARE_SORT', None):
            #     stats.sort_stats(*settings.PROFILE_MIDDLEWARE_SORT)
            stats.sort_stats('cumulative')
            stats.stream = StringIO()
            stats.print_stats(*getattr(
                    settings, 'PROFILE_MIDDLEWARE_RESTRICTIONS', []))
        finally:
            os.unlink(filename)

        # Construct an HTML/XML or Javascript comment, with
        # the formatted stats, written to the StringIO object
        # and attach it to the content of the response.
        comment = '\n%s\n\n%s\n\n%s\n' % (
            begin_comment, stats.stream.getvalue().strip(), end_comment)
        response.content = content + comment

        # If the Content-Length header is given, add the
        # number of bytes we have added to it. If the
        # Content-Length header is ommited or incorrect,
        # it remains so in order to don't change the
        # behaviour of the web server or user agent.
        if response.has_header('Content-Length'):
            response['Content-Length'] = int(
                response['Content-Length']) + len(comment)

        return response
