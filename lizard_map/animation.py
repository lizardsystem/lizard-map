"""Animation scrollbar handling."""

ANIMATION_SETTINGS = 'animation_settings'


class AnimationSettings(object):
    """Handle animation settings in the session."""

    def __init__(self, request):
        self.request = request
        self.session = self.request.session
        if ANIMATION_SETTINGS not in self.session:
            self.session[ANIMATION_SETTINGS] = {}

    def info(self):
        """Return info for creating the slider."""
        return {}

    def _set_slider_position(self, value):
        """Store value in the session."""
        self.session[ANIMATION_SETTINGS]['slider_position'] = value

    def _get_slider_position(self):
        """Return value stored in the session."""
        return self.session[ANIMATION_SETTINGS].get('slider_position')

    slider_position = property(_get_slider_position, _set_slider_position)
