from django import template

register = template.Library()


@register.inclusion_tag('lizard_map/tag_background_map.html')
def background_map(background_map):
    """Render a div tag for a background layer

    The div tag is picked up by lizard-wms.js
    """
    return {'background_map': background_map}


@register.inclusion_tag('lizard_map/tag_animation_control_panel.html')
def animation_control_panel(workspace):
    """
    """
    return {'workspace': workspace}
