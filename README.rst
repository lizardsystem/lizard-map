lizard-map
==========

Lizard-map provides basic map interaction for `Django
<http://www.djangoproject.com>`_ applications that use a `lizard-ui
<http://pypi.python.org/pypi/lizard-ui>`_ user interface.  We designed it at
`Nelen & Schuurmans <http://www.nelen-schuurmans.nl>`_ for our geographical
information websites (with water management information).

It provides:

- Openlayers (map javascript libary) map display and server-side map
  generation (mapnik's WMS functionality). Background maps are configurable.

- A "workspace" interaction model: drag mappable items into a workspace and
  they'll get displayed.  The workspace is stored in the Django database.

- A "collage" attached to every workspace for storing selected info on map
  items (like graphs).

- An extention mechanism to plug more or less arbitrary map sources into the
  workspace so that they can be displayed, searched, etc.

.. image:: https://secure.travis-ci.org/lizardsystem/lizard-map.png?branch=master
   :target: http://travis-ci.org/#!/lizardsystem/lizard-map

Translation status:

.. image:: https://translations.lizard.net/projects/p/lizardsystem/resource/lizard-map/chart/image_png
   :target: https://translations.lizard.net/projects/p/lizardsystem/resource/lizard-map/


Core concept: workspaces
------------------------

A *workspace item* is something that can be displayed on a map.  A *workspace*
is a collection of workspace items that is actually displayed.

There are two types of workspaces:

- Edit Workspace: Every session/user gets its own workspace. This
  workspace can be edited.

- Storage Workspace. TODO: extra info.


A workspace item needs to know how to display itself, how to search for items
when you click on the map and more.  To get that to work for arbitrary map
sources, you need to configure an adapter.  The adapter has a ``layer()``
method for returning a mapnik layer, a ``search()`` method for searching and
so on.

- You register an adapter as a so-called "setuptools entrypoint" under a
  specfic name.

- When you add a workspace item, you pass in the adapter name and an optional
  snippet of json to configure the adapter.

The workspace item keeps track of this adapter and its configuragion and uses
it to generate maps, for searching, etc.


Collages
--------

A workspace item often results in multiple areas or points.  If you click on
such a point, you normally get a popup with extra information.  If you want to
compare a couple of those information "snippets", you can place them in your
*collage*. In the GUI this is called "Selectie".

Clicking the collage gives a popup with all the collected information popups
in that single popup.


Interaction
-----------

Included is quite some javascript for workspace interaction.  Potential
workspace items can be drag/dropped into a workspace to add them.  Workspace
items can be reordered.  You can drag them to the trash.


Dependencies
------------

Almost all dependencies are listed in our ``setup.py``, so they get pulled in
automatically.  Not all of them install as good as eggs, though.  You might be
better off installing them system-wide with your OS's own packaging system.

You can force buildout to use system-wide installed packages with the
`osc.recipe.sysegg <http://pypi.python.org/pypi/osc.recipe.sysegg>`_ recipe.
An example config::

  [buildout]
  ...
  parts =
      sysegg
      ...

  [sysegg]
  recipe = osc.recipe.sysegg
  force-sysegg = true
  eggs =
      PIL
      matplotlib
      simplejson
      pyproj


Development installation
------------------------

The first time, you'll have to run the "bootstrap" script to set up setuptools
and buildout::

    $> python bootstrap.py

And then run buildout to set everything up::

    $> bin/buildout

(On windows it is called ``bin\buildout.exe``).

You'll have to re-run buildout when you or someone else made a change in
``setup.py`` or ``buildout.cfg``.

The current package is installed as a "development package", so
changes in .py files are automatically available (just like with ``python
setup.py develop``).

If you want to use trunk checkouts of other packages (instead of released
versions), add them as an "svn external" in the ``local_checkouts/`` directory
and add them to the ``develop =`` list in buildout.cfg.

Tests can always be run with ``bin/test`` or ``bin\test.exe``.


External dependencies
---------------------

The dependencies for a full website that uses lizard-map are best expressed as
ubuntu/debian package dependencies: build-essential, python2.6-dev, apache2,
libjpeg-dev, python-imaging, python-matplotlib, python-mapnik, python-scipy,
libapache2-mod-wsgi, python-gdal, spatialite-bin, python-pysqlite2,
python-pyproj.


Upgrading to Lizard 3
---------------------

Short summary to convert your app to Lizard 3.

- Replace old template tags workspace with workspace_edit and
  collage_edit (see below).

- Review urls.py for old lizard_map views. Replace with new ones or
  remove.

- Migrate

- Upgrade to class-based views, using one of the View classes
  (i.e. AppView). An excellent description can be found when googling
  "class based views reinout". You can take lizard-map views as
  examples as well.


Site integration
----------------

The following steps has to be done in order to use the
lizard_map/workspace concepts.

- Install lizard-map somewhere. (Add 'lizard-map' in your setup.py:
  install_requires)

- Add 'lizard_map' to your settings.py: INSTALLED_APPS.

- Add an entry in your urls.py::

    import lizard_map.urls

    (r'^map/', include(lizard_map.urls)),

- Use one of the views, i.e. AppView.


Example view::

    from lizard_map.views import AppView

    class MyAppView(AppView):
        template_name = 'my_app/template.html'


Example template::

    {% extends "lizard_map/wms.html" %}
    {% load workspaces %}

    {% block subtitle %} (page name) {% endblock %}

    {% block sidebar %}

    <div id="iconbox" class="sidebarbox sidebarbox-stretched iconlist">
      <h2>Apps</h2>
      <ul>
          <li>
            <a href="/address/" class="lizard-map-link">
              <img src="{{ STATIC_URL }}lizard_ui/app_icons/meetgegevens.png" />
              <div>App</div>
            </a>
          </li>
      </ul>
    </div>

    {% workspace_edit view.workspace_edit %}
    {% collage_edit view.collage_edit %}

    {% endblock %}

- Add this view to your url.py:

    import my_app.views

    (r'^$', my_app.views.MyAppView.as_view()),


- Start testing by running syncdb / migrate.

- Add and configure background maps by loading "background_maps" fixture.

- Start dev server.


Settings
--------

Some default date range settings can be set in settings.py. All
settings are optional::

    START_YEAR = 2000  # Defaults to today - 7 years
    END_YEAR = 2010  # Defaults to today + 3 years.

    # Define default period 1..5
    # From daterange.py:
    # PERIOD_DAY = 1
    # PERIOD_TWO_DAYS = 2
    # PERIOD_WEEK = 3
    # PERIOD_MONTH = 4
    # PERIOD_YEAR = 5
    # PERIOD_OTHER = 6

    DEFAULT_PERIOD = 5  # Defaults to 1

    # If DEFAULT_PERIOD = 6, define these
    DEFAULT_START_DAYS = -20  # Defaults to -1000
    DEFAULT_END_DAYS = 1  # Defaults to 10

You can add google analytics to your site by adding the tracking
code::

    GOOGLE_TRACKING_CODE = 'AA-12345678-0'
