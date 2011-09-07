from django import forms


class WorkspaceSaveForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)


class WorkspaceLoadForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)
