import logging
from lizard_ui import configchecker
from django.conf import settings

logger = logging.getLogger(__name__)


@configchecker.register
def checker():  # Pragma: nocover
    """Verify lizard_map's demands on settings.py."""
    if ('lizard_map.context_processors.processor.processor'
        in settings.TEMPLATE_CONTEXT_PROCESSORS):
        logger.warn(
            "You can remove "
            "'lizard_map.context_processors.processor.processor' "
            "from TEMPLATE_CONTEXT_PROCESSORS. Sometimes this makes "
            "the TEMPLATE_CONTEXT_PROCESSORS default. In that case you can "
            "remove TEMPLATE_CONTEXT_PROCESSORS as well.")
    if not settings.USE_TZ == True:
        logger.warn("Set USE_TZ to True in your settings. "
                    "We need timezone aware datetimes.")
