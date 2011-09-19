#from django.conf import settings
import logging

from lizard_map.coordinates import MapSettings
from lizard_map.daterange import current_period
from lizard_map.daterange import current_start_end_dates
from lizard_map.forms import DateRangeForm
from lizard_map.utility import analyze_http_user_agent
from lizard_map.views import MAP_BASE_LAYER
from lizard_map.views import MAP_LOCATION
from lizard_map.workspace import WorkspaceManager

# New


logger = logging.getLogger(__name__)


def detect_browser(request):
    result = 'other'  # default answer

    request_meta = request.META
    if 'HTTP_USER_AGENT' in request_meta:
        http_user_agent = request_meta['HTTP_USER_AGENT']

        analyzed = analyze_http_user_agent(http_user_agent)
        if analyzed['device'] == 'iPad':
            result = 'iPad'

    return {'detected_browser': result}


def processor(request):
    """
    A context processor to add the lizard_map variables to the current
    context.
    """
    add_to_context = {}

    # Add detected browser.
    add_to_context.update(detect_browser(request))

    # # Add google_tracking_code, if available.
    # try:
    #     add_to_context.update(
    #         {'google_tracking_code': settings.GOOGLE_TRACKING_CODE})
    # except AttributeError:
    #     pass

    return add_to_context
