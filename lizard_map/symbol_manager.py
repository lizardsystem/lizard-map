# -*- coding: utf-8 -*-
"""Purpose: Manage image files that are scaled, colorized and rotated.
"""

import logging
import os.path
import fnmatch
from PIL import Image
from PIL import ImageFilter
import pkg_resources

logger = logging.getLogger(__name__)


def list_image_file_names():
    """
    Collect names of available images of icons directory.
    """

    file_extentions = ('png', 'svg')
    icon_names = []
    file_names = None
    path = pkg_resources.resource_filename('lizard_map', 'icons/')
    try:
        file_names = os.listdir(path)
        file_names.sort()
    except:
        logger.critical('icon/mask path %s does not exist', path)
        raise Exception()

    for file_name in file_names:
        for file_extention in file_extentions:
            if fnmatch.fnmatch(file_name, '*.' + file_extention):
                icon_names.append((file_name, file_name))

    return icon_names


class SymbolManager:

    def __init__(self, symbol_path_original, symbol_path_generated):
        # logger.debug('Initializing SymbolManager')
        self.symbol_path_original = symbol_path_original
        self.symbol_path_generated = symbol_path_generated
        if not(os.path.exists(self.symbol_path_original)):
            logger.critical('original path %s does not exist',
                         self.symbol_path_original)
            raise Exception(
                'SymbolManager failed: original path %s does not exist' % (
                    self.symbol_path_original))
        if not(os.path.exists(self.symbol_path_generated)):
            os.makedirs(self.symbol_path_generated)
            logger.info('Created map %s' % self.symbol_path_generated)

    def get_symbol_transformed(self, filename_nopath, **kwargs):
        """Returns relative filename,

        if the transformed symbol does not yet exist, it is
        created. Transformation as follows:

        1) color, if given
        2) scale, if given
        3) rotate, if given
        4) shadow, if given

        input: filename_nopath is <symbol_path_original>\<filename_nopath>
        kwargs:
        * size: (x, y)
        * color: (r, g, b, a) (alpha is unaltered)
        * rotate: in degrees, counterclockwise, around center
        * shadow_height: in pixels
        """
        # logger.debug('Entering get_symbol_transformed')

        SHADOW_FACTOR_Y = 1
        SHADOW_FACTOR_X = 0.5

        #get kwargs
        color = kwargs.get('color', (1.0, 1.0, 1.0, 1.0))
        fn_mask, = kwargs.get('mask', (filename_nopath,))
        sizex, sizey = kwargs.get('size', (0, 0))
        rotate, = kwargs.get('rotate', (0,))
        rotate %= 360
        shadow_height, = kwargs.get('shadow_height', (0,))
        force = kwargs.get('force', False)

        # logger.debug('color: %s' % str(color))
        # logger.debug('mask: %s' % fn_mask)
        # logger.debug('size: %dx%d' % (sizex, sizey))
        # logger.debug('rotate: %d' % (rotate))
        # logger.debug('shadow_height: %d' % (shadow_height))
        # logger.debug('force no cache: %s' % (force))

        filename_mask_abs = os.path.join(self.symbol_path_original, fn_mask)

        #result filename is :
        #<orig filename>_<mask>_<hex r><hex g><hex b>_<sx>x<sy>_r<r>.\
        # <orig extension>
        fn_orig_base, fn_orig_extension = os.path.splitext(filename_nopath)
        result_filename_nopath = '%s_%s_%02x%02x%02x_%dx%d_r%03d_s%d%s' % (
            fn_orig_base, os.path.splitext(fn_mask)[0],
            min(255, color[0] * 256), min(255, color[1] * 256),
            min(255, color[2] * 256),
            sizex, sizey, rotate, shadow_height, fn_orig_extension)

        result_filename = os.path.join(self.symbol_path_generated,
                                       result_filename_nopath)
        if os.path.isfile(result_filename) and force == False:
            pass
            # logger.debug('image already exists, returning filename')
        else:
            # logger.debug('generating image...')
            filename_orig_abs = os.path.join(self.symbol_path_original,
                                       filename_nopath)
            # logger.debug('orig filename: %s' % filename_orig_abs)
            if not(os.path.isfile(filename_orig_abs)):
                raise Exception('File not found (%s)' % filename_orig_abs)

            im = Image.open(filename_orig_abs)
            if im.mode != 'RGBA':
                im = im.convert('RGBA')

            #color
            im_mask = Image.open(filename_mask_abs)
            if im_mask.mode != 'RGBA':
                im_mask = im_mask.convert('RGBA')

            # Create objects where you can read and write pixel values.
            pix = im.load()
            pix_mask = im_mask.load()
            for x in range(im.size[0]):
                for y in range(im.size[1]):
                    mask = pix_mask[x, y][3]
                    r, g, b, a = pix[x, y]
                    r = (int(color[0] * r * mask / 256) +
                         r * (255 - mask) / 256)
                    g = (int(color[1] * g * mask / 256) +
                         g * (255 - mask) / 256)
                    b = (int(color[2] * b * mask / 256) +
                         b * (255 - mask) / 256)
                    pix[x, y] = (r, g, b, a)

            if sizex > 0 and sizey > 0:
                if sizex != im.size[0] or sizey != im.size[1]:
                    im = im.resize((sizex, sizey), Image.ANTIALIAS)

            #expand=True werkt niet goed: wordt niet meer deels doorzichtig
            if rotate > 0:
                im = im.rotate(rotate, Image.BICUBIC)

            #drop shadow
            #see also: http://en.wikipedia.org/wiki/Alpha_compositing, A over B
            if shadow_height > 0:
                im_shadow = Image.new('RGBA', im.size)
                im_shadow.paste((192, 192, 192, 255),
                                (int(shadow_height * SHADOW_FACTOR_X),
                                 int(shadow_height * SHADOW_FACTOR_Y)),
                                im)
                #now blur the im_shadow a little bit
                im_shadow = im_shadow.filter(ImageFilter.BLUR)

                #im_shadow.paste(im, (0,0))
                #paste original image on top, using the alpha channel
                pix = im.load()
                pix_shadow = im_shadow.load()
                # logger.debug('shadow x: %d' % im_shadow.size[0])
                for x in range(im_shadow.size[0]):
                    for y in range(im_shadow.size[1]):
                        r, g, b, a = pix_shadow[x, y]
                        r2, g2, b2, a2 = pix[x, y]
                        r_res = r2 * a2 / 256 + r * a * (255 - a2) / 256 / 256
                        g_res = g2 * a2 / 256 + g * a * (255 - a2) / 256 / 256
                        b_res = b2 * a2 / 256 + b * a * (255 - a2) / 256 / 256
                        a_res = a2 + (255 - a2) * a / 256
                        pix_shadow[x, y] = (r_res, g_res, b_res, a_res)

                im = im_shadow

            if os.path.isfile(result_filename):
                # logger.debug('deleting existing result file')
                os.remove(result_filename)

            # logger.debug('saving image (%s)' % result_filename)
            im.save(result_filename)

        return result_filename_nopath  # result_filename
