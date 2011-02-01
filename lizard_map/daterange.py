"""Handle the date range setting and remembering"""
import datetime

from django import forms
from django.conf import settings
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response

default_start_days = getattr(settings, 'DEFAULT_START_DAYS', -1000)
default_end_days = getattr(settings, 'DEFAULT_END_DAYS', 10)

DEFAULT_START = datetime.date.today() + datetime.timedelta(
    days=default_start_days)
DEFAULT_END = datetime.date.today() + datetime.timedelta(
    days=default_end_days)

DUTCH_DATE_FORMAT = '%d/%m/%Y'
# ^^^ This is what jquery ui with the Dutch locale does for Reinout.


class DateRangeForm(forms.Form):
    # TODO: NL date format.  Also hardcoded in the js.
    date_start = forms.DateField(input_formats=(DUTCH_DATE_FORMAT,),
                                 label='Begindatum')
    date_end = forms.DateField(input_formats=(DUTCH_DATE_FORMAT,),
                               label='Einddatum')


def set_date_range(request, template='lizard_map/daterange.html'):
    """View: store the date range in the session and redirect."""
    if request.method == 'POST':
        form = DateRangeForm(request.POST)
        if form.is_valid():
            came_from = request.META.get('HTTP_REFERER', '/')
            request.session['date_start'] = form.cleaned_data['date_start']
            request.session['date_end'] = form.cleaned_data['date_end']
            return HttpResponseRedirect(came_from)
    else:
        form = DateRangeForm()
    # Form rendering just for debugging errors.
    return render_to_response(
        template,
        {'date_range_form': form},
        context_instance=RequestContext(request))


def current_start_end_dates(request, for_form=False):
    """Return the current start/end date strings, either default or from session.

    If for_form is True, return it as a dict so that we can pass it directly
    into a form class.  Otherwise return it as a tuple.

    """
    date_start = request.session.get('date_start', DEFAULT_START)
    date_end = request.session.get('date_end', DEFAULT_END)
    if for_form:
        date_start = date_start.strftime(DUTCH_DATE_FORMAT)
        date_end = date_end.strftime(DUTCH_DATE_FORMAT)
        return dict(date_start=date_start,
                    date_end=date_end)
    else:
        return (date_start, date_end)

