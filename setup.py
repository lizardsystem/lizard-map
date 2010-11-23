from setuptools import setup

version = '1.24dev'

long_description = '\n\n'.join([
    open('README.txt').read(),
    # open(os.path.join('lizard_map', 'USAGE.txt')).read(),
    open('TODO.txt').read(),
    open('CREDITS.txt').read(),
    open('CHANGES.txt').read(),
    ])

install_requires = [
    'Django',
    'PIL',
    'django-nose',
    'django-staticfiles',
    'lizard-ui >= 1.18',
    'matplotlib',
    'pyproj',
    'south',
    # mapnik: sorry, there's no real package for that.  We do need it however.
    ],

tests_require = [
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
      license='GPL',
      packages=['lizard_map'],
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=tests_require,
      extras_require = {'test': tests_require},
      entry_points={
          'console_scripts': [
            ],
          'lizard_map.adapter_class': [
            'adapter_dummy = lizard_map.layers:AdapterDummy',
            ],
          },
      )
