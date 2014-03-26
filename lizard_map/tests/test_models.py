from django.test import TestCase

from lizard_map import models


class TestBackgroundMap(TestCase):
    def test_default_maps_always_returns_at_least_one(self):
        """Don't do setup and see if we get at least one map."""
        maps = models.BackgroundMap.default_maps()

        self.assertTrue(len(list(maps)) >= 1)
