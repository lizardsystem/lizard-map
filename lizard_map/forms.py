from django import forms

from lizard_map.dateperiods import MONTH
from lizard_map.models import StatisticsMixin
from lizard_map.models import WorkspaceStorage

import logging
logger = logging.getLogger(__name__)


class WorkspaceSaveForm(forms.Form):
    """
    Save workspace from edit to storage
    """
    name = forms.CharField(max_length=100, required=True, label='Naam')


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
    title = forms.CharField(max_length=100, required=False, label='Titel')
    y_min = forms.FloatField(required=False, label='Minimale y waarde')
    y_max = forms.FloatField(required=False, label='Maximale y waarde')
    x_label = forms.CharField(max_length=100, required=False, label='X label')
    y_label = forms.CharField(max_length=100, required=False, label='Y label')
    aggregation_period = forms.ChoiceField(label='Aggregatie periode')
    restrict_to_month = forms.ChoiceField(required=False, label='Maand')

    # Single item fields
    boundary_value = forms.FloatField(required=False, label='Grenswaarde')
    percentile_value = forms.FloatField(required=False,
                                        label='Percentielgrens')
    line_min = forms.BooleanField(required=False, label='Toon minimum')
    line_max = forms.BooleanField(required=False, label='Toon maximum')
    line_avg = forms.BooleanField(required=False, label='Toon gemiddelde')

    def __init__(self, *args, **kwargs):
        """
        """
        super(CollageItemEditorForm, self).__init__(*args, **kwargs)

        # Leave out week and day [:4].
        self.fields['aggregation_period'].choices = (
            StatisticsMixin.AGGREGATION_PERIOD_CHOICES[:4])
        self.fields['restrict_to_month'].choices = (
            (0, 'alle'),
            (1, 'alleen januari'),
            (2, 'alleen februari'),
            (3, 'alleen maart'),
            (4, 'alleen april'),
            (5, 'alleen mei'),
            (6, 'alleen juni'),
            (7, 'alleen juli'),
            (8, 'alleen augustus'),
            (9, 'alleen september'),
            (10, 'alleen oktober'),
            (11, 'alleen november'),
            (12, 'alleen december'),
            )

        # Initial status
        # Sometimes this has no 'aggregation_period', for some reason
        if int(kwargs.get('initial', dict()).
               get('aggregation_period', '-1')) != MONTH:
            self.fields['restrict_to_month'].widget.attrs['disabled'] = True
