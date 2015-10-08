import logging

from django.middleware.locale import LocaleMiddleware
from django.utils import translation
from django.utils.translation import get_language_from_request

from lizard_map.models import Setting


logger = logging.getLogger(__name__)


class LocaleFromSettingMiddleware(LocaleMiddleware):
    """Set language from lizard_map Setting model."""

    def process_request(self, request):
        language = None
        if Setting.get('show_language_picker'):
            # We don't want the regular lizard5 per-site configured language,
            # we want the user's preferred language instead.
            language = get_language_from_request(request)

        if language is None:
            # Look for the per-site Setting object.
            language = Setting.get('language_code')

        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
