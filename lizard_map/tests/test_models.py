from django.test import TestCase

from lizard_map import models


class TestBackgroundMap(TestCase):
    def test_default_maps_always_returns_at_least_one(self):
        """Don't do setup and see if we get at least one map."""
        maps = models.BackgroundMap.default_maps()

        self.assertTrue(len(list(maps)) >= 1)


class TestSetting(TestCase):
    def test_get_returns_default_from_setting(self):
        with self.settings(LIZARD_MAP_DEFAULT_RANDOM_SETTING="Testing"):
            self.assertEquals(models.Setting.get('random'), "Testing")

    def test_get_returns_setting_if_in_database(self):
        models.Setting.objects.create(
            key='random', value='1')

        with self.settings(LIZARD_MAP_DEFAULT_RANDOM_SETTING="2"):
            self.assertEquals(models.Setting.get('random'), '1')
