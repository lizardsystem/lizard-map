import datetime
from django import forms
from django.conf import settings

from datewidget import SelectDateWidget
from django.forms.widgets import RadioSelect

from daterange import PERIOD_CHOICES
from daterange import PERIOD_OTHER


class WorkspaceSaveForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)


class WorkspaceLoadForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)


class HorizontalRadioRenderer(forms.RadioSelect.renderer):
    """ this overrides widget method to put radio buttons horizontally
        instead of vertically.
    """

    def render(self):
        """Outputs radios"""
        return (u'\n'.join([u'%s\n' % widget for widget in self]))


class DateRangeForm(forms.Form):
    """
    Date range form.
    """
    # Settings
    start_year = getattr(settings,
                         'START_YEAR',
                          datetime.date.today().year - 7)
    end_year = getattr(settings,
                       'END_YEAR',
                        datetime.date.today().year + 3)
    years_choices = range(start_year, end_year + 1)

    # Form fields
    period = forms.ChoiceField(
        required=True,
        widget=RadioSelect(renderer=HorizontalRadioRenderer),
        choices=PERIOD_CHOICES,
        label='',)
    # TODO: NL date format.  Also hardcoded in the js.
    dt_start = forms.DateTimeField(
        label='van',
        widget=SelectDateWidget(years=years_choices),
        required=False)
    dt_end = forms.DateTimeField(
        label='t/m',
        widget=SelectDateWidget(years=years_choices),
        required=False)

    def __init__(self, *args, **kwargs):
        # # Add argument period, if not available.
        # if 'period' not in args[0]:
        #     args[0]['period'] = PERIOD_DAY
        super(DateRangeForm, self).__init__(*args, **kwargs)

        # Set initial dt_start/end on disabled when not selected.
        if args and 'period' in args[0] and args[0]['period'] != PERIOD_OTHER:
            self.fields['dt_start'].widget.attrs['disabled'] = True
            self.fields['dt_end'].widget.attrs['disabled'] = True


