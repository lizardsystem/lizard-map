import logging

from lizard_map.animation import AnimationSettings
from lizard_map.coordinates import MapSettings
from lizard_map.utility import analyze_http_user_agent
from lizard_map.views import MAP_LOCATION

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
    session = request.session
    add_to_context = MapSettings().map_settings
    add_to_context['animation_slider'] = None  # default

    # Map variables.
    # By default it takes coordinates from the django settings. If a
    # user has custom coordinates in his session, it will take those
    # coordinates and zoomlevel.

    if MAP_LOCATION in session:
        map_location = session[MAP_LOCATION]
        add_to_context['startlocation_x'] = str(map_location['x'])
        add_to_context['startlocation_y'] = str(map_location['y'])
        add_to_context['startlocation_zoom'] = str(map_location['zoom'])
        logger.debug('Fetched map coordinates from session: '
                     '%s, %s, %s' % (
                str(map_location['x']),
                str(map_location['y']),
                str(map_location['zoom'])))

    # Add animation slider? Default: no.
    animation_slider = AnimationSettings(request).info()
    add_to_context['animation_slider'] = animation_slider

    # Add detected browser
    add_to_context.update(detect_browser(request))

    return add_to_context
