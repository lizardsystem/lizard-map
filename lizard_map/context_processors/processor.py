from django.conf import settings
import logging

from lizard_map.animation import AnimationSettings
from lizard_map.coordinates import MapSettings
from lizard_map.daterange import current_period
from lizard_map.daterange import current_start_end_dates
from lizard_map.daterange import DateRangeForm
from lizard_map.models import Setting
from lizard_map.utility import analyze_http_user_agent
from lizard_map.views import MAP_BASE_LAYER
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
    add_to_context = {}
    add_to_context.update(MapSettings().map_settings)

    # By default it takes coordinates from the django settings. If a
    # user has custom coordinates in his session, it will take those
    # coordinates and zoomlevel.

    if MAP_LOCATION in session:
        map_location = session[MAP_LOCATION]
        add_to_context['start_extent'] = map_location
        logger.debug('Fetched map coordinates from session: '
                     '%s' % (map_location))
    if MAP_BASE_LAYER in session:
        add_to_context['base_layer_name'] = session[MAP_BASE_LAYER]
    else:
        add_to_context['base_layer_name'] = ""

    return add_to_context


def workspace_variables(request):
    """Add workspace variables.

    workspaces
    date_range_form
    animation_slider
    use_workspaces: used in template to view certain parts
    """
    add_to_context = {}

    workspace_manager = WorkspaceManager(request)
    workspaces = workspace_manager.load_or_create()
    add_to_context['workspaces'] = workspaces

    current_date_range = current_start_end_dates(request, for_form=True)
    current_date_range.update({'period': current_period(request)})

    add_to_context['date_start_period'] = current_date_range["dt_start"]
    add_to_context['date_end_period'] = current_date_range["dt_end"]

    date_range_form = DateRangeForm(current_date_range)
    add_to_context['date_range_form'] = date_range_form

    # Add animation slider? Default: no.
    animation_slider = None  # default
    for k, ws_list in workspaces.items():
        for ws in ws_list:
            if ws.is_animatable:
                animation_slider = AnimationSettings(request).info()
                break
    add_to_context['animation_slider'] = animation_slider

    # Click/hover handlers.
    # This used to be 'popup_hover_handler'.
    add_to_context['javascript_hover_handler'] = Setting.get(
        'javascript_hover_handler', None)

    add_to_context['javascript_click_handler'] = 'popup_click_handler'

    add_to_context['use_workspaces'] = True

    add_to_context['transparency_slider'] = True

    return add_to_context


def processor(request):
    """
    A context processor to add the lizard_map variables to the current
    context.
    """
    add_to_context = {}

    # Add map variables.
    add_to_context.update(map_variables(request))

    # Add workspaces.
    add_to_context.update(workspace_variables(request))

    # Add detected browser.
    add_to_context.update(detect_browser(request))

    # Add google_tracking_code, if available.
    try:
        add_to_context.update(
            {'google_tracking_code': settings.GOOGLE_TRACKING_CODE})
    except AttributeError:
        pass

    return add_to_context
