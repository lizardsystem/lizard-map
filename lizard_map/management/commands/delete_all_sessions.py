from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

import logging

from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session

from lizard_map.models import WorkspaceEdit

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    args = ''
    help = """Deletes all Django sessions and lizard-map WorkspaceEdits."""

    def handle(self, *args, **options):
        Session.objects.all().delete()
        WorkspaceEdit.objects.all().delete()
        print('Done')
