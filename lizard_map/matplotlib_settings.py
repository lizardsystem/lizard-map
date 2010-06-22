# Import this ONCE from a settings.py

import matplotlib

SCREEN_DPI = 72.0
FONT_SIZE = 12


PARAMS = {
    'font.size': FONT_SIZE,
    'legend.fontsize': FONT_SIZE,
    'text.fontsize': FONT_SIZE,
    'xtick.labelsize' : 0.8 * FONT_SIZE,
    'ytick.labelsize' : 0.8 * FONT_SIZE,
    }

matplotlib.rcParams.update(PARAMS)
