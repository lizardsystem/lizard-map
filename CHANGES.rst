Changelog of lizard-map
=======================


1.51 (2011-02-16)
-----------------

- Fixed bug in date range handling: the default start/end dates would
  be calculated JUST ONCE at system startup.  So the "2 weeks before
  today" would really be "2 weeks before the date apache restarted".
  Fixed it by adding two methods that do the proper thing.


1.50 (2011-02-15)
-----------------

- Added support for ApplicationScreens.

- Added fool proof checking on Color object.


1.44 (2011-02-08)
-----------------

- Added **experimental** django-piston REST api.


1.43 (2011-02-03)
-----------------

- Fixed breadcrumbs bug.


1.42 (2011-02-01)
-----------------

- Fixed bug with breadcrumbs on homepage.

- Fixed bug with daterange template.

- Added default view for apps homepage, including example homepage.

- Added function html to color object.

- Added option ncol to Graph legend.

- Added extra logging for missing TEMPLATE_CONTEXT_PROCESSORS.

- Started sphinx documentation setup.


1.41 (2011-01-20)
-----------------

- Added option "data-popup-login" to "lizard-map-link", which pops up
  a login screen before following the link.


1.40 (2011-01-13)
-----------------

- Improved css for workspace acceptable. Minor change, but it looks
  good.


1.39 (2011-01-13)
-----------------

- Improved css for workspace items.

- Added add_datasource_point to compensate for Mapnik bug #402.

- Added add-to-workspace button next to workspace acceptables.

- Added pan-to function to workspace items.

- Added panning when selecting a workspace-acceptable.

- Changed default workspace name from "Workspace" to "My Workspace".

- Added workspace.extent function and corresponding url.


1.38 (2011-01-11)
-----------------

- Google Maps API key in wms.html is now a variable.


1.37 (2011-01-11)
-----------------

- Added debugging info in custom templatetag map.

- Changed 'load map location' to 'load default map location'.

- Removed 'save map location'.

- The map automatically saves its position when leaving the page.


1.36 (2011-01-06)
-----------------

- Added function detect_prj in coordinates.


1.35 (2011-01-06)
-----------------

- Bugfix ZeroDivisionError in statistics.


1.34 (2011-01-05)
-----------------

- Bugfix http_user_agent in test client.


1.33 (2011-01-05)
-----------------

- Make clicking less sensitive for iPad.

- Introduced analyze_http_user_agent in utility.py.


1.32 (2011-01-04)
-----------------

- Bugfix touch.js: now we can pan again.


1.31 (2011-01-04)
-----------------

- Improved touch.js: now we pan instantly. If we pan very little, it
  will now click.


1.30 (2011-01-04)
-----------------

- Added browser detection as custom template tag.

- Added location awareness.

- Added touch gestures for map (iPad, iPhone, android support).

- Added initial South migration.


1.29 (2010-12-13)
-----------------

- Fixed load/save map location after altering map-actions.

- Added 'Empty workspace' button.

- Added translations.


1.28 (2010-12-09)
-----------------

- Finetuning hover popup.

- Added point icons.


1.27 (2010-12-08)
-----------------

- Added list operations coming from fewsjdbc.


1.26 (2010-12-01)
-----------------

- Moved tooltip css to lizard_ui.


1.25 (2010-11-25)
-----------------

- Add global to js file to satisfy jslint.


1.24 (2010-11-24)
-----------------

Attention: You need to add 'django.core.context_processors.request' to
your TEMPLATE_CONTEXT_PROCESSORS in order to make map-locations work
correctly. For more information see the README.

- Moved some functions to mapnik_helper.

- Add tests for Color, bugfix Color.

- Add South for database migrations.

- Add option for Google Maps background layer.

- Model LegendPoint now has parent Legend.

- Add default_color to Legend and LegendPoint models.

- Bugfix float_to_string.

- Moved adapter layers.py to lizard-shape.

- Removed extent coordinates from model Workspace.

- Add actions map-location-save and map-location-load.

- Bugfix when name is None.

- Bugfix int in id_field would result in an error.


1.23 (2010-11-11)
-----------------

- Remove necessity of google_coords in popup_json and popup_collage_json.

- Show snippet name when adding shapefile layer to collage.


1.22 (2010-11-11)
-----------------

- Pinned newest lizard-ui version.


1.21 (2010-11-11)
-----------------

- Moved js setUpLegendTooltips() to lizard_ui: setUpTooltips().

- Refactor Colors: removed model, add ColorField.

- Reimplemented search function using shapely. Before it was
  implemented using Mapnik and it worked only with polygons.


1.20 (2010-11-01)
-----------------

- Make adapter_shapefile more generic, removed default settings.

- Added mapnik_helper.py for mapnik helper functions.

- Added mapnik_linestyle to Legend object.


1.19 (2010-10-27)
-----------------

- Bugfix in statistics: the average over the rows doesn't crash anymore if
  there are empty values.


1.18 (2010-10-15)
-----------------

- Fixed bug in statistics export when there wasn't a percentile value set.

- Small values in the statistics display don't end up as ``0.00`` anymore, but
  as, for instance, ``1.02e-03``.

- Using custom template tag 'map_variables' to get map settings in
  your client. The settings are set in settings.py.

- Added option to set DEFAULT_START_DAYS and DEFAULT_END_DAYS in settings.


1.17 (2010-10-01)
-----------------

- Fixed bug where graph edit form would fail always unless you switched on
  summaries per *month*.


1.16 (2010-09-28)
-----------------

- Added option: allow_custom_legend in adapter.

- Added optional transparency slider.

- Fixed bug in graph edit and graph line edit popup forms.


1.15 (2010-09-27)
-----------------

- Fixed IE bug that most workspace-related icons floated one line down.


1.14 (2010-09-27)
-----------------

- Fixed bug in filter-on-month handling.

- Using newer lizard-ui with better print icon handling.

- Using color widget for legend customization.


1.13 (2010-09-22)
-----------------

- Bugfix data attributes lizard-map-wms. Moved divs from above-content
  to content.


1.12 (2010-09-22)
-----------------

- Make 'now' line orange.


1.11 (2010-09-20)
-----------------

- Added more tests (test coverage now at 62%).

- Various UI and javascript fixes.

- Showing aggregation period data in the statistics table.

- Moved javascript out of map template into a separate javascript file: this
  way the javascript can be tested automatically (and it is!).

- "Sleep items hierheen" and "Nog geen grafieken" are not draggable anymore.

- Add restrict-to-month option.

- Percentile in collage screen is now user adjustable.

- Move legend code to template tag. Add custom legend modification possibility.


1.10 (2010-09-08)
-----------------

- Add never_cache to several server requests, to prevent caching in IE.

- Fixed graph popup rendering problem for IE7 (empty <a> tags get hidden
  there, even if there's an icon background).


1.9 (2010-09-03)
----------------

- Use updated krw shapefiile.

- Use different open street map.


1.8 (2010-08-30)
----------------

- Bugfix for when no statistics are available.


1.7 (2010-08-27)
----------------

- Graph and collage popups now use the "regular" jquerytools popup instead of
  the OpenLayers in-the-map popup.  Visually cleaner, clearer and prettier.
  And easier to maintain and to get right.

- Various visual fixes.

- Deleting a workspace item also deletes the corresponding snippets.

- Added color pulldown for collage view settings (instead of requiring you to
  know the internal matplotlib color code names :-) )


1.6 (2010-08-26)
----------------

- Animation slider and name-hover are now also working in the default
  workspace view.

- Name hover is now placed just to the lower right of the cursor.  This way
  you can still click on the item you hovered above instead of your click
  being blocked sometimes by the hovering name.

- Added slightly more whitespace to the right of legend-less graphs: this
  prevents (most) labels from being cut off.


1.5 (2010-08-26)
----------------

- Added tooltips with name when hovering over clickable map items.

- Layout improvements for popups and tables.

- Added dateperiods: calculate periods for use in graphs.

- Added styling for popups.


1.4 (2010-08-23)
----------------

- WorkspaceCollageSnippetGroup's name was a TextField (=multiline) instead of
  a simple CharField.  Oracle stores a TextField as a "NCLOB" and has some
  restrictions on them (no index, no .distinct()).  Anyway, this blew up on
  an oracle-using installation.  Fixed now.

- Removed double value_aggregate() method from base adapter: the extra one
  raised a NotImplemented error and overshadowed the real method.


1.3 (2010-08-18)
----------------

- Requiring our dependencies that must be installed with system eggs.  We use
  the osc.recipe.sysegg in our own buildout to grab them from the system.  A
  sample config is included in the readme.

- Implemented export csv for snippet_group.

- Added optional legends.

- Add option to show tables in collage view.

- Importing the simplejson module in a different way to please windows in
  combination with python 2.6.


1.2 (2010-08-16)
----------------

- Added a bit of test setup to make xml test reports possible (for integration
  with Hudson).  Similarly for coverage reports, also for Hudson.  Automatic
  code quality monitoring!

- Implemented snippet groups. Snippet groups group similar snippets in
  a collage.

- Removed site-specific breadcrumbs.

- Refactored collage view. One can now edit graphs in the collage
  view. The graph-only editor has been removed.

- Added an animation slider for showing map layers at specific points in
  time.  Only shown when there are workspace items that support it.

- Removed graph-properties that were stored in the session.

- Passing extra 'request' keyword argument to all adapter layer() methods.
  **Warning**:  This needs refactoring in all adapters.  Advance warning:
  we'll probably refactor the adapters to get the request in their
  ``__init__()`` method later on.


1.1 (2010-07-16)
----------------

- Changed json decode behaviour: keys are now strings, not unicode.


1.0 (2010-07-15)
----------------

- Automatically empties temp workspace when adding item to workspace.
- Add custom graph edit screen.
- Add layout option to adapter.location for use with custom graphs.
- Make generic adapter html rendering, for i.e. popups and collage
  views. Refactored popup_json.
- Add collage view.
- Put date_popup in template tag.
- Update wms.html for custom map-javascript code, for use with
  lizard-sticky.
- Add symbol function to adapter.
- Add wgs84 support in coordinates.
- Add GraphProps manager for keeping track of customized graphs.


0.16 (2010-07-06)
-----------------

- Compensating for lizard-ui's "use-my-size" instead of "use-my-width/height"
  class for image replacement.


0.15 (2010-07-02)
-----------------

- Better empty height/width handling for images.

- Slightly bigger search radius when clicking on a map.


0.14 (2010-07-01)
-----------------

- Using lizard-ui's generic graph resizing and reloading now.


0.13 (2010-06-28)
-----------------

- Popup graph size fixes.

- Updated documentation.

- We're now released on pypi!


0.12 (2010-06-23)
-----------------

- Fancier "nothing found" popup.


0.11 (2010-06-23)
-----------------

- UI interaction fixes.

- Temp workspace popups don't show add-to-collage.

- Added empty-the-workspace button.

- Fixed graph display: no more overlap.

- Added global graph settings.


0.10 (2010-06-22)
-----------------

- Popup (upon map click) shows popup when nothing's found.

- More feedback (hourglass pointer and so).


0.9 (2010-06-18)
----------------

- Fixed wms.html's javascript code: long live jslint!

- Not emptying the temp workspace anymore: it was happening too often.  Now it
  isn't happening often enough, though.  Will be fixed later.


0.8 (2010-06-18)
----------------

- Using lizard-ui's new css/javascript blocks.

- Copied charts from krw here.


0.7 (2010-06-16)
----------------

- "Add to collage" is now hardcoded NL.

- Collage popup is bigger and doesn't contain "add to collage" links anymore.


0.6 (2010-06-15)
----------------

- Added the date range popup widget from krw-waternet here.  (Still
  session-based.  It also doesn't work with multiple workspaces yet.

- Changed layer_method and other setuptools registered functions to an
  adapter class.

- Added fully functioning collages/snippets support.

0.5 (2010-06-08)
----------------

- Added early support for collages/snippets.

- Switched the custom attributes over to "data-xxxxx" attributes (those are
  valid html5).

- Added generic draggability of .workspace-acceptable items.


0.4 (2010-05-18)
----------------

- Collected the rijksdriehoek and google mercator proj4 strings in one
  location (coordinates.py).  Including handy conversion methods.

- Added views for showing and managing workspaces.

- Added workspaces and workspaceitems for showing map layers and de-coupling
  them with behind-the-scenes data.

- Added generic WMS view.

- Added shapefile layer rendering function.

- Added generic layer rendering and layer searching hook-ups through
  so-called setuptools entrypoints.

- Added template tags for rendering workspaces.


0.3 (2010-04-14)
----------------

- Reordered templates a bit between lizard-ui and us.


0.2 (2010-03-29)
----------------

- Really added analysis.html


0.1 (2010-03-29)
----------------

- Moved analysis.html from krw-waternet to lizard-map
- Initial library skeleton created by nensskel.  Jack Ha
