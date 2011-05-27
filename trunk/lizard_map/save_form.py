"""Saves the passed workspace or collage.
"""
import datetime
import logging

from django import forms
from django.conf import settings
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response

logger = logging.getLogger(__name__)


class SaveForm(forms.Form):
    """
    Form to save workspace or collage..
    """

    # Form fields
    name = forms.CharField(
        required=False,
        max_length=100,
        help_text='Type een unieke naam.',
        label='Workspace naam',)

#    def __init__(self, *args, **kwargs):
        # # Add argument period, if not available.
        # if 'period' not in args[0]:
        #     args[0]['period'] = PERIOD_DAY
        #super(DateRangeForm, self).__init__(*args, **kwargs)

        # Set initial dt_start/end on disabled when not selected.
        #if args and 'period' in args[0] and args[0]['period'] != PERIOD_OTHER:
        #     self.fields['dt_start'].widget.attrs['disabled'] = True
        #     self.fields['dt_end'].widget.attrs['disabled'] = True


#def store_timedelta_range(request, period, timedelta_start, timedelta_end):
#    """Store relative start/end dates in session."""
#    request.session[SESSION_DT_PERIOD] = period
#    request.session[SESSION_DT_START] = timedelta_start
#    request.session[SESSION_DT_END] = timedelta_end


def save_workspace(request, template='lizard_map/tag_save_popup.html',
                   now=None):
    """Save the current workspace including workspace_items

    POST must contain a workspace name to save
    """
    from lizard_map.models import Workspace
    from django.db.models import Max
    if request.method == 'POST':
        submit = request.POST.get('cancel', None)
        if submit != None:
            return HttpResponseRedirect("/")

        form = SaveForm(request.POST)
        if form.is_valid():
            came_from = request.META.get('HTTP_REFERER', '/')
            max_id = Workspace.objects.all().order_by('-id')[0].id
            next_id = int(max_id) + 1
            new_workspace = Workspace(id=next_id, name=form.cleaned_data['name'])
            new_workspace.save()
    else:
        form = SaveForm()

    # Form rendering just for debugging errors.
    return HttpResponseRedirect("/")


def current_period(request):
    """
    Return the current period, either default or from session.

    TODO: mix together with current_start_end_dates (but is has a lot
    of impact)
    """
    default_period = getattr(settings, 'DEFAULT_PERIOD', PERIOD_DAY)

    return request.session.get(SESSION_DT_PERIOD, default_period)
