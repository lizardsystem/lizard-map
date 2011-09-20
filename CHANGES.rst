Changelog of lizard-map
=======================

2.3 (2011-09-20)
----------------

- Made the automatic invalid-workspaceitem-deletion more robust.

- Removed the youtube popup. Unused at the moment. And the implementation was
  terribly hardcoded.

- Commented out all the debugging in the symbolmanager


2.2 (2011-09-02)
----------------

- 2.1.13 stated "please clear your session info when you upgrade to this
  version as the fix to #3181 stores different information." This release
  fixes that. No session data deletion is needed anymore.


2.1.13 (2011-09-01)
-------------------

- Fixed a problem in the date range selector, namely that the day of the end
  date with move to the next day when the user selected another month of the
  end date (#3181).

- Added request to templatetag snippet_group to be able to use request in
  adapters' html function.


2.1.12 (2011-08-30)
-------------------

- Added try/except around hotshot in profile middleware, because it
  requires python-profiler.

- Added request to layout_options in popup_collage_json. The request
  is needed in some adapter.html functions in order to get user
  datetime/periods.


2.1.11 (2011-08-30)
-------------------

- Fixed progress cursor in popup_click_handler().

- Zoom to closest extent is no longer used for workspace items.


2.1.10 (2011-08-24)
-------------------

- Requiring lizard-ui 3.0 now, which also means Django 1.3. Updated the
  buildout and the testsettings for that. We're also using the KGS (known good
  set) now to limit the amount of version pinning.


2.1.9 (2011-08-16)
------------------

- Edited mouse progress on click in map.


2.1.8 (2011-08-05)
------------------

- Added function to list icons names.


2.1.7 (2011-08-04)
------------------

- Fixed background-map wms. Updated template and js.

- Changed font-size for long legend texts in adapter.py. #3095.

- Added pdf.png icon. Use pdf.png as mask as well with color ffffff.

- Changed breadcrumbs according to #2499. The behaviour is as follows:
  home for home screen and home -> screen for other screens.

- Fixed clicking bug in FF5: set pixelTolerance to null instead if 0
  is a workaround for the OpenLayers bug. #3108.


2.1.6 (2011-07-29)
------------------

- Added function to convert WGS84 coordinates to RD.

- Updated point_3.png: the upper left corner contained an error.

- Added truncation of workspace-item-names to 80 characters (the
  server would otherwise crash on longer names).

- Now using QuerySet.count instead of len(QuerySet.all()) in workspace
  manager.

- Added some rel=tipsy html parameters.

- Pinned lizard_ui to 2.1.4


2.1.5 (2011-07-25)
------------------

- Settings are now cached. After deleting and saving the cache will be
  invalidated.

- Added setting option javascript_hover_handler. Setting this option
  to 'popup_hover_handler' will enable mouse overs. Note: run a
  migrate after upgrading, the Setting.key field can now be 40
  characters.

- #3096: fixed blue info button in workspace-acceptables (they appear
   in lizard-shape).


2.1.4 (2011-07-14)
------------------

- iPad update: the (+) works again as well as some trees on the
  sidebar. #3003, #3004.


2.1.3 (2011-07-12)
------------------

- Removed draggability of workspace-acceptables.

- Made the adapter.extent function optional. In
  WorkspaceItem.has_extent we now just detect if the function is at
  all present.  #3041, #3036.

- Added wms layers to transparency function. #3039.

- Updated googlemaps_api_keys in fixture: the new key is for
  lizardsystem.nl and all its subdomains.

- Updated workspace_item_empty: When emptying workspace, the
  snippet-groups will also be deleted. #3031.

- Added try/except around search_coordinates and search_name for
  #3033.


2.1.2 (2011-06-30)
------------------

- Adapter.legend: removed "force_legend_below" behaviour when width <
  500. TODO: fix force_legend_below or remove.

- Changed adapter.legend: self.axes.legend instead of
  self.figure.legend. Everything seems ok.


2.1.1 (2011-06-30)
------------------

- Added google_tracking_code from settings to context_processor, if
  available.

- Added try/except in WorkspaceCollageSnippetGroup.values_table (used
  in "show tables" of collage view), because some adapters don't
  implement the adapter.values function.


2.1 (2011-06-29)
----------------

- Temporary disable sorting in workspace when a new workspace-item is
  being added. Solves #2961.


2.0.1 (2011-06-22)
------------------

- Really fixed the non-closed span element.


2.0 (2011-06-22)
----------------

- Fixed a non-closed 'span' element that broke the layout in IE.


1.90 (2011-06-22)
-----------------

- Changed empty workspace text.


1.89 (2011-06-21)
-----------------

- Raising workspaceitemerror when the json we get isn't decodable. More
  robust code this way.


1.88 (2011-06-21)
-----------------

- Made popups more consistent (shadow color and size).

- Added 'continue to site' link in introductory video popup.

- Showing reload link in the statistics part that is shown when the date range
  has been changed.

- Adding extra safety measure so lizard-map doesn't crash on faulty
  shapefiles.

- Fixed collage graph editing: made a check more robust for missing parameters.


1.87 (2011-06-17)
-----------------

- Re-enabled custom y tick locator amount selection.

- Showing the table now looks at the table belonging to the button by means of
  a wrapper div, which is more reliable.

- Fixed the problem that a hidden popup would remain populated and re-evaluated
  (ticket 2892).


1.86 (2011-06-16)
-----------------

- Added bare try/except around wms workspace layer looping to prevent
  the function to crash.

- Added transparency_slider to context variables. From now on the
  transparency_slider is enabled by default.

- Added optional popup_video_url parameter to the ``homepage()`` view.  This
  video url, when used, should point to the embed urls of YouTube videos.
  Currently the sizes are hardcoded, so this is work-in-progress.
  The video is shown once per day, max.

- Modified graph: less yticks, bigger ylabel, dutch monthnames,
  yearlabel is now at first tick of year.


1.85 (2011-06-10)
-----------------

- Fixed tab setup in graph popup: no more unneeded reloading of the html. Also
  the graphs aren't reloaded more often than necessary.

- Added force_legend_below parameter to ``legend()`` to force the legend to be
  placed below the graph.

- Added function to create a image from reguest and response to save
  it as .png on client side (views.py, urls.py, lizard_wms.js)

- Added declaration to OpenLayers' ImgPath to use our own dark theme location.

- Implemented tipsy in some places.

- Worked on appearance of graph-popup.


1.84 (2011-06-07)
-----------------

- Fixed javascript bug that prevented IE from displaying background maps.

- Changed start_extent in background_maps fixture to match 1.83 changes.


1.83 (2011-06-07)
-----------------

- Solved intermittent problem with the zooming level. See #2656, #2762, and
  #2794.


1.82 (2011-06-03)
-----------------

- Added spinner ("waiting") icon for clicking on a workspace item, clicking on
  the plus sign, deleting a workspace item or deleting a collage item.


1.81 (2011-06-03)
-----------------

- Workspace items and snippets take up a fixed one-line height now. The
  overflow is hidden. This makes the interface more predictable.


1.80 (2011-06-01)
-----------------

- Added default "javascript_click_handler" (namely ``popup_click_handler``) to
  the context via the lizard_map context processor.

- By default, a hover_click_handler isn't added anymore unless you specify one
  yourself in the context. Most sites don't need/want it.

- Fixed overly-aggressive reloading of map layers. This improves the performance.

- Added checkboxes and functionality to collage-items (snippets).


1.79 (2011-05-30)
-----------------

- Use gray background color for map: loading of tiles is less noticable

- Added possibility for profiling middleware according to
  http://www.no-ack.org/2010/12/yet-another-profiling-middleware-for.html

- Added debug toolbar.

- Upped django to 1.2.3.


1.78 (2011-05-18)
-----------------

- Various UI fixes and IE7 glitches.

- Fixed 'add to collage' option in workspace view when viewing others'
  workspaces. You are not allowed to add snippets in that workspace. #2707.

- Fixed layout problem of animation sliders in block above -r20937 #2503 .


1.77 (2011-05-06)
-----------------

- Fixed timezone bug when comparing dates.


1.76 (2011-05-06)
-----------------

- Fixed pylint errors.

- Fixed layout of date_popup form for IE7.

- Added css to only show workspace items when you hover it.

- Added 'remove workspace-item' and 'remove snippet' buttons.

- Removed trashcan on bottom of screen. Before the buttons we dragged
  items into this trashcan.

- Added titles to various workspace items.

- Added empty-collage.

- NOTE: controls for add and remove workspace items not working on iPad .


1.75 (2011-05-03)
-----------------

- Fixed jslint error.

- Added base_layer to map_location_save. It now remembers not only the
  extent of the view, but also which base layer was selected.

- Removed default controls from OpenLayers map.

- Added slider zoom control to OpenLayers map.

- Made javascript jslint-approved again.

- Disabled auto zoom in lizard_map.js setUpWorkspaceAcceptable().


1.74 (2011-04-28)
-----------------

- Changed set_ylim_method so that it doesn't crash on axhlims.

- Changed set_ylim_method so that it doesn't crash on no data.

- Changed set_ylim_method so that it autoscales to visible data only.


1.73 (2011-04-27)
-----------------

- Fixed "Export" and "Voeg toe" in popup with tabs.

- Changed x-axes label formatting. At periods > 10 year, not every
  year gets a label anymore.

- Fixed default period. It now takes the period depending on
  DEFAULT_PERIOD.


1.72 (2011-04-27)
-----------------

- Added tag_date_trigger.


1.71 (2011-04-27)
-----------------

- Added templatetag for date_trigger.

- Replaced action-icon 'calendar' and date_popup block to block
  above-content in lizardgis.html and wms.html.

- Changed function updateDateSelectOrInput() in lizard_map.js to
  update title of action-icon 'calendar'

- Deleted action-icon 'calendar' and date_popup block from
  tag_workspace.html

- Fixed bug with updating snippet-list when pressing trashcan.

- Implemented new date popup (day, 2 days, week, ...). It now stores
  relative datetimes in the session. It submits and updates on
  changes. Added tests for daterange.

- Modified adapter.py so that graphs always have a top margin

- Fixed timeout on nothingFoundPopup (#2585).

- Fixed nothingFoundPopup on collage class (#2557).

- Removed map parameter from show_popup function.


1.70 (2011-04-20)
-----------------

- Rewritten loop to remove all openlayers layers to prevent error in
  newest openlayers.

- Fixed OpenLayers location to /static_media/openlayers/.


1.69 (2011-04-20)
-----------------

- Fixed #2582: fixed load default map location.


1.68 (2011-04-20)
-----------------

- Fixed jslint warning.


1.67 (2011-04-20)
-----------------

- Added custom OpenLayers._getScriptLocation.

- Changed x-axis layout for graphs to have more ticks with no overlapping

- Added method to set_ylim_margin() to adapter.Graph.

- Jslint jquery.workspace.js.

- Fixed blank nothingFoundPopup.

- Added WorkspaceItemError class.


1.66 (2011-04-14)
-----------------

- Fixed collage popup.


1.65 (2011-04-14)
-----------------

- Removed header from standard popup (looks better).

- Added feature to click on workspaces of other users than yourself.

- Improved zoom to layer (it was zoomed in too much).

- Added default settings to MapSettings, improved code a bit.

- Renamed fixture lizard_map to background_maps.

- Added progress animation (zandloper) on delete workspece item(s) by
  click on the trash icon and by dragging/draopping the item into
  trash.


1.64 (2011-04-12)
-----------------

- Added migration for BackgroundMap and Setting models.

- Changed "zoom to box" instead of "pan to center" when clicking
  workspace-acceptable or workspace-item magnifying glass.

- Added BackgroundMap and Setting models. Model BackgroundMap used to
  store the configuration of single background maps and if the map is
  the default one. Setting is to store global, end-user changeable
  settings, such as startlocation_x, startlocation_y, etc. This change
  also removes dependencies of settings.MAP_SETTINGS.

- Added twitter icon.


1.63 (2011-04-05)
-----------------

- Added support for a second vertical axis in Graph.


1.62 (2011-03-28)
-----------------

- Turning offset off in adapter using ticker.ScalarFormater.


1.61 (2011-03-24)
-----------------

- Extended adapter.html_default options with template and
  extra_render_kwargs.

- Fixed bug with animation slider. Previously it would not jump to the
  correct date/time when start_date is changed.

- Added waterbalance icon.


1.60 (2011-03-16)
-----------------

- Added workspaces and date_range_form to context processor. In your
  view you do not need to add these variables anymore. You can still
  provide your own workspaces or date_range_form by adding them in
  your view.

- Added context_processors.processor. This replaces the custom
  templatetags.map. See README for usage (TEMPLATE_CONTEXT_PROCESSORS).

- Added var html in lizard_map.js (Jslint).


1.59 (2011-03-10)
-----------------

- (+) shows up when hovering above a workspace-acceptable. Previous it
  appeared only when clicking on a workspace-acceptable.


1.58 (2011-03-10)
-----------------

- Moved WSGIImportScript outside VirtualHost in apache config template.

- Removed add-workspace-item button by default. It appears after
  clicking an item.

- Changed arrow to magnifier. Only shows magnifier if
  WorkspaceItem.has_extent is True.

- Added tests for google_to_srs and srs_to_google.

- Added WorkspaceItem.has_extent.

- Added transformation of projection on extent function.


1.57 (2011-03-03)
-----------------

- Added tests for MapSettings.

- Added srid property to MapSettings.


1.56 (2011-02-28)
-----------------

- Fixed update workspace bug.


1.55 (2011-02-28)
-----------------

- Added coordinates.MapSettings. It makes life easier when reading
  from your django setting MAP_SETTINGS.

- Added support for client-side wms adapter. This will add, remove,
  reload wms layers client-side without reloading the page.


1.54 (2011-02-21)
-----------------

- Removed example_homepage.html, updated app_screen.html and
  views.homepage.


1.53 (2011-02-17)
-----------------

- Added app_screen template for pages with apps, workspace and map.


1.52 (2011-02-17)
-----------------

- Switched off mandatory authentication for the experimental API.


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
