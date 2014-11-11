from django import forms
from django.utils.translation import ugettext_lazy as _

from lizard_map.dateperiods import MONTH
from lizard_map.models import StatisticsMixin
from lizard_map.models import WorkspaceStorage

import logging
logger = logging.getLogger(__name__)


class WorkspaceSaveForm(forms.Form):
    """
    Save workspace from edit to storage
    """
    name = forms.CharField(max_length=100, required=True, label=_('Name'))


class CollageSaveForm(forms.Form):
    """
    Save collage from edit to storage
    """
    name = forms.CharField(max_length=100, required=True, label=_('Name'))


class WorkspaceLoadForm(forms.Form):
    """
    Load workspace from storage to edit.
    """
    id = forms.ChoiceField(required=True, label='')

    def __init__(self, *args, **kwargs):
        """
        The choices are dynamic, they depend on the user/session.
        """
        super(WorkspaceLoadForm, self).__init__(*args, **kwargs)
        # TODO: use request to filter WorkspaceStorage.
        workspaces = WorkspaceStorage.objects.all()
        workspace_choices = [
            (workspace.id, workspace.name) for workspace in workspaces]
        self.fields['id'].choices = workspace_choices


class HorizontalRadioRenderer(forms.RadioSelect.renderer):
    """ this overrides widget method to put radio buttons horizontally
        instead of vertically.
    """

    def render(self):
        """Outputs radios"""
        return (u'\n'.join([u'%s\n' % widget for widget in self]))


class CollageForm(forms.Form):
    """
    Collage form. Never actually displayed.
    """
    workspace_id = forms.IntegerField(required=True)

    # Values should be "workspace_storage" or "workspace_edit", but this
    # is not enforced. If no value is given, assume "workspace_edit".
    workspace_type = forms.CharField(max_length=20, required=False)
    x = forms.FloatField(required=True)
    y = forms.FloatField(required=True)
    radius = forms.FloatField(required=True)
    srs = forms.CharField(max_length=100, required=True)


class CollageAddForm(forms.Form):
    """
    Collage form. Never actually displayed.
    """

    # Name in the database is max 80 characters, but I still removed
    # the max_length because the view takes care of it already, and
    # clicks shouldn't silently fail.
    name = forms.CharField(required=True)

    # The others don't need a max_length either.
    adapter_class = forms.CharField(required=True)
    adapter_layer_json = forms.CharField(required=True)
    identifier = forms.CharField(required=True)


class EmptyForm(forms.Form):
    """
    Empty form. Used by views.
    """
    pass


class SingleObjectForm(forms.Form):
    """
    Form with one object_id (can be anything).
    """
    object_id = forms.IntegerField(required=True)


class EditForm(forms.Form):
    """
    Form with one object_id (can be anything) and fixed properties.
    """

    action = forms.CharField(max_length=100, required=True)
    object_id = forms.IntegerField(required=True)
    visible = forms.BooleanField(required=False)  # Only when "update".


class CollageItemEditorForm(forms.Form):
    """
    Form to edit collage item edits.

    TODO: split group fields and single item fields. The class-based
    view must be updated too.
    """

    # Group fields
    title = forms.CharField(max_length=100, required=False, label=_('Title'))
    y_min = forms.FloatField(required=False, label=_('Minimum y value'))
    y_max = forms.FloatField(required=False, label=_('Maximum y value'))
    x_label = forms.CharField(max_length=100, required=False, label=_('X label'))
    y_label = forms.CharField(max_length=100, required=False, label=_('Y label'))
    aggregation_period = forms.ChoiceField(label=_('Aggregation period'))
    restrict_to_month = forms.ChoiceField(required=False, label=_('Month'))

    # Single item fields
    boundary_value = forms.FloatField(required=False, label=_('Limit'))
    percentile_value = forms.FloatField(required=False,
                                        label=_('Percentile limit'))
    line_min = forms.BooleanField(required=False, label=_('Show minimum'))
    line_max = forms.BooleanField(required=False, label=_('Show maximum'))
    line_avg = forms.BooleanField(required=False, label=_('Show average'))

    def __init__(self, *args, **kwargs):
        """
        """
        super(CollageItemEditorForm, self).__init__(*args, **kwargs)

        # Leave out week and day [:4].
        self.fields['aggregation_period'].choices = (
            StatisticsMixin.AGGREGATION_PERIOD_CHOICES[:4])
        self.fields['restrict_to_month'].choices = (
            (0, _('all')),
            (1, _('only january')),
            (2, _('only february')),
            (3, _('only march')),
            (4, _('only april')),
            (5, _('only may')),
            (6, _('only june')),
            (7, _('only july')),
            (8, _('only august')),
            (9, _('only september')),
            (10, _('only oktober')),
            (11, _('only november')),
            (12, _('only december')),
            )

        # Initial status
        # Sometimes this has no 'aggregation_period', for some reason
        if int(kwargs.get('initial', dict()).
               get('aggregation_period', '-1')) != MONTH:
            self.fields['restrict_to_month'].widget.attrs['disabled'] = True
