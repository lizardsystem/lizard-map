import logging

from lizard_map.animation import AnimationSettings
from lizard_map.coordinates import MapSettings
from lizard_map.daterange import DateRangeForm
from lizard_map.daterange import current_start_end_dates
from lizard_map.utility import analyze_http_user_agent
from lizard_map.views import MAP_LOCATION
from lizard_map.workspace import WorkspaceManager

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


def map_variables(request):
    # Map variables.
    session = request.session
    add_to_context = MapSettings().map_settings

    # By default it takes coordinates from the django settings. If a
    # user has custom coordinates in his session, it will take those
    # coordinates and zoomlevel.

    if MAP_LOCATION in session:
        map_location = session[MAP_LOCATION]
        try:
            map_location['x']
            map_location['y']
            map_location['z']
            add_to_context['startlocation_x'] = str(map_location['x'])
            add_to_context['startlocation_y'] = str(map_location['y'])
            add_to_context['startlocation_zoom'] = str(map_location['zoom'])
            logger.debug('Fetched map coordinates from session: '
                         '%s, %s, %s' % (
                    str(map_location['x']),
                    str(map_location['y']),
                    str(map_location['zoom'])))
        except:
            logger.error(
                'Error fetching map coordinates from session: %s'
                % map_location)
    return add_to_context


def workspace_variables(request):
    add_to_context = {}

    workspace_manager = WorkspaceManager(request)
    add_to_context['workspaces'] = workspace_manager.load_or_create()

    add_to_context['date_range_form'] = DateRangeForm(
        current_start_end_dates(request, for_form=True))

    # Add animation slider? Default: no.
    add_to_context['animation_slider'] = None  # default
    #animation_slider = AnimationSettings(request).info()
    #add_to_context['animation_slider'] = animation_slider

    return add_to_context


def processor(request):
    """
    A context processor to add the lizard_map variables to the current
    context.
    """
    session = request.session

    add_to_context = {}

    # Add map variables.
    add_to_context.update(map_variables(request))

    # Add workspaces.
    add_to_context.update(workspace_variables(request))

    # Add detected browser
    add_to_context.update(detect_browser(request))

    return add_to_context
