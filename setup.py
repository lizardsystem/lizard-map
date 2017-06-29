from setuptools import setup

version = '5.5'

long_description = '\n\n'.join([
    open('README.rst').read(),
    # open(os.path.join('lizard_map', 'USAGE.rst')).read(),
    open('CREDITS.rst').read(),
    open('CHANGES.rst').read(),
    ])

install_requires = [
    'Django >= 1.6, < 1.7',
    'Pillow',
    'django-extensions',
    'django-jsonfield',
    'django-nose',
    'django-piston',
    'djangorestframework >= 2.0',
    'iso8601',
    'lizard-help',
    'lizard-security',
    'lizard-ui >= 5.0',
    'lizard-wms',
    'pkginfo',
    'python-dateutil',
    'pytz',
    'south',
    'requests',
    'django-appconf',
    # 'pyproj', Including that as a dependency
    # doesn't work right at the moment.
    # mapnik: sorry, there's no real package for that.  We do need it however.
    'translations',
    ],

tests_require = [
    'mock',
    'coverage',
    ]

setup(name='lizard-map',
      version=version,
      description="Basic map setup for lizard web sites",
      long_description=long_description,
      # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=['Programming Language :: Python',
                   'Framework :: Django',
                   ],
      keywords=[],
      author='Reinout van Rees',
      author_email='reinout.vanrees@nelen-schuurmans.nl',
      url='http://www.nelen-schuurmans.nl/lizard/',
      license='LGPL',
      packages=['lizard_map'],
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=tests_require,
      extras_require={'test': tests_require},
      entry_points={
          'console_scripts': [
            ],
          'lizard_map.adapter_class': [
            'adapter_dummy = lizard_map.layers:AdapterDummy',
            ],
          },
      )
