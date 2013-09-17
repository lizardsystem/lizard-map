from django.test import TestCase

from lizard_map import adapter

class TestMakePercentileLabel(TestCase):
    def test_make_percentile_label(self):
        with self.settings(LANGUAGE_CODE='nl'):
            orig_label = u"label"
            percentiles = (0.1, 0.2, 0.8, 0.9)

            label = adapter._make_percentile_label(orig_label, percentiles)

            self.assertEquals(
                label,
                u"label (met 10% - 90% percentiel, 20% - 80% percentiel)")
