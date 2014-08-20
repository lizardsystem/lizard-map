import logging

from django.middleware.locale import LocaleMiddleware
from django.utils import translation

from lizard_map.models import Setting


logger = logging.getLogger(__name__)


class LocaleFromSettingMiddleware(LocaleMiddleware):
    """Set language from lizard_map Setting model."""

    def process_request(self, request):

        language = None

        try:
            language = Setting.objects.get(key__iexact='language_code').value
        except Setting.DoesNotExist as err:
            logger.debug(err)
            
        if language is None:
            return

        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
