from django.db import models
from django.utils.translation import ugettext as _
from south.modelsinspector import add_introspection_rules
from jsonfield import JSONField

JSONField  # Needed for migrations because there was once a JSONField in here.


def legend_values(min_value, max_value, min_color, max_color, steps):
    """Interpolates colors between min_value and max_value, calc
    corresponding colors and gives boundary values for each band.

    Makes list of dictionaries: {'color': Color, 'low_value':
    low value, 'high_value': high value}"""
    result = []
    value_per_step = (max_value - min_value) / steps
    for step in range(steps):
        try:
            fraction = float(step) / (steps - 1)
        except ZeroDivisionError:
            fraction = 0
        alpha = (min_color.a * (1 - fraction) +
                 max_color.a * fraction)
        red = (min_color.r * (1 - fraction) +
               max_color.r * fraction)
        green = (min_color.g * (1 - fraction) +
                 max_color.g * fraction)
        blue = (min_color.b * (1 - fraction) +
                max_color.b * fraction)
        color = Color('%02x%02x%02x%02x' % (red, green, blue, alpha))

        low_value = min_value + step * value_per_step
        high_value = min_value + (step + 1) * value_per_step
        result.append({
                'color': color,
                'low_value': low_value,
                'high_value': high_value,
                })
    return result


# Add introspection rules for ColorField
add_introspection_rules([], ["lizard_map.fields.ColorField"])


class Color(str):
    """Simple color object: r, g, b, a.

    The object is in fact a string with class variables.
    """

    def __init__(self, s):
        self.r = None
        self.g = None
        self.b = None
        if s is None:
            return
        try:
            self.r = int(s[0:2], 16)
        except ValueError:
            self.r = 128
        try:
            self.g = int(s[2:4], 16)
        except ValueError:
            self.g = 128
        try:
            self.b = int(s[4:6], 16)
        except ValueError:
            self.b = 128
        try:
            # Alpha is optional.
            self.a = int(s[6:8], 16)
        except ValueError:
            self.a = 255

    def to_tuple(self):
        """
        Returns color values in a tuple. Values are 0..1
        """
        result = (self.r / 255.0, self.g / 255.0,
                  self.b / 255.0, self.a / 255.0)
        return result

    @property
    def html(self):
        """
        Returns color in html format.
        """
        if self.r is not None and self.g is not None and self.b is not None:
            return '#%02x%02x%02x' % (self.r, self.g, self.b)
        else:
            return '#ff0000'  # Red as alarm color


class ColorField(models.CharField):
    """Custom ColorField for use in Django models. It's an extension
    of CharField."""

    default_error_messages = {
        'invalid': _(
            u'Enter a valid color code rrggbbaa, '
            'where aa is optional.'),
        }
    description = "Color representation in rgb"

    # Ensures that to_python is always called.
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 8
        super(ColorField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        return str(value)

    def to_python(self, value):
        if isinstance(value, Color):
            return value
        return Color(value)
