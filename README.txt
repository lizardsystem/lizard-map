lizard-map
==========

Lizard-map provides basic map interaction for `Django
<http://www.djangoproject.com>`_ applications that use a `lizard-ui
<http://pypi.python.org/pypi/lizard-ui>`_ user interface.  We designed it at
`Nelen & Schuurmans <http://www.nelen-schuurmans.nl>`_ for our geographical
information websites (with water management information).

It provides:

- Openlayers (map javascript libary) map display and server-side map
  generation (mapnik's WMS functionality).

- A "workspace" interaction model: drag mappable items into a workspace and
  they'll get displayed.  The workspace is stored in the Django database.

- A "collage" attached to every workspace for storing selected info on map
  items (like graphs).

- An extention mechanism to plug more or less arbitrary map sources into the
  workspace so that they can be displayed, searched, etc.


Core concept: workspaces
------------------------

A *workspace item* is something that can be displayed on a map.  A *workspace*
is a collection of workspace items that is actually displayed.

Every session gets its own workspace.  (There is a possiblity of adding extra
workspaces, but that isn't used yet in one of our sites, so it isn't fully
thought-out yet).

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
workspace's *collage*.

Clicking the collage gives a popup with all the collected information popups
in that single popup.


Interaction
-----------

Included is quite some javascript for workspace interaction.  Potential
workspace items can be drag/dropped into a workspace to add them.  Workspace
items can be reordered.  You can drag them to the trash.


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

