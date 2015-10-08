Changelog of lizard-map
=======================

5.4 (unreleased)
----------------

- Nothing changed yet.


5.3 (2015-10-08)
----------------

- Added (still empty) arabic translation files.


5.2 (2015-01-15)
----------------

- Remove defaults from JSONFields in old migrations. The default
  default (dict) is fine, and incorrect defaults caused some
  migrations to fail.


5.1 (2014-12-15)
----------------

- Upped lizard-ui requirement.


5.0 (2014-12-15)
----------------

- You can now save the dashboard just like you could already save the
  workspace. They're not shown on the homepage, though. If needed you
  can add an app icon for that.

- You can add a ``disclaimer_text`` setting in the admin now. This is copied
  verbatim to the first window of the on-screen tour. So don't put html tags
  in here.

- Removed pan-to-click-location, it is simply to obtrusive.

- The display-name-while-hovering-over-the-map functionality now only searches
  in the first layer (=workspace item), not in all of them. This way, it is
  more predictable which results you get.

- Removed 'week' from the period selection. 'Week+1' is now called 'week', but
  retained the week+1 functionality. Added 'halfyear' option.

- Using 'orangered'instead of yellow in the graphs as HHNK wants that.

- Added lizard-security to WorkspaceStorage: this allows you to effectively
  filter the start page.

- Set workspace on default as private.

- Fix grammatical mistakes in info-tour.

- Move to Lizard 5.

- Add `private` flag to WorkspaceStorage model. If a WorkspaceStorage
  instance is labelled private, it is not shown to anonymous users.

- Migrated to mapnik 2.2.0.

- Added action for elevationprofile

- Update translations.

- Removed console.log statements. IE hangs with them.

- Make two untranslated strings translatable.

- Update source language (english) django.po

- Add Box awesome.

- Add support for correct getFeatureInfo for lizard wms.

- Reintroduced workspace save icon (admin only).

- Remove animatable.

- Add WMS filter on the page.

- Fix bug where IE9 couldn't use the search bar; we should use JSONP
  for cross-site requests.

- Re-added collage screen (called "Dashboard" now), mostly by re-enabling old
  functionality. Bigger change is the layout of the actual main collage page:
  the labels and so are now next to the graphs as there's no separate sidebar
  anymore.

- Fix timezones once more.

- Fix text, layout and z-iondex positions of info tour wizard.

- Hiding rainapp's period summary on the collage screen.

- Opening dashboard/collage in new tab.

- UI updates for the dashboard page.

- Remove coordinates.DEFAULT_MAP_SETTINGS (unused since 2011), move default
  map code from views.py and coordinates.py into models.BackgroundMap.

- Move settings and their defaults to conf.py (using django-appconf).

- The Setting model's .get() and .extent() functions now don't take a
  default anymore, rather if a Setting isn't found they get their
  defaults from normal Django settings -- a setting called "mysetting"
  uses the LIZARD_MAP_DEFAULT_MYSETTING_SETTING setting. Setting
  setting setting.

- Several defaults were updated to what lizard5-site sets in its
  base.py, so the settings can be removed there. No other settings
  were actually set in lizard5-site, so how configurable do these
  things need to be?

- Added reloading of graphs upon flot pan/zoom. The
  according-to-the-manual-zoom start/end date is passed in the normal way to
  the backend: no changes necesseary. This is expensive, though, so the
  backend *must* add an extra ``.dynamic-graph-zoomable`` class in addition to
  the current ``.dynamic-graph`` class.

- Made the interaction with graphs that fail to load nicer.

- View state persists also on the dashboard page now.

- Added 'please log in' hint when there are no visible workspace storages.

- The 'default_range_type' Setting can now be set to override the
  default date range. Possible values are 'today', '2_day', 'week',
  'week_plus_one' (default), 'month' and 'year'.

- Use the function values_multiple_timeseries() to export timeseries from
  lizard-fancylayers adapter.

- Add LanguageView to setup a different language per site.

- Create LocaleFromSettingMiddleware to use language_code from Setting models.

4.28 (2013-05-06)
-----------------

- Added a completely transparant icon, ghost.png, for layers that
  shouldn't be shown but for which the popup should still work.

- Some changes to be iPad friendly were made.

  - The small layerswitcher is moved to the upper bar for easier use.

  - The left hand zoom in and out buttons are not shown on iPad.

  - 'Zoom to start location' is now just an icon.


4.27 (2013-04-03)
-----------------

- Fixed tab_titles being undefined when a popup of collage items is
  opened.

- Merged functionality from the deltaportaal lizard-map branch:

  - Showing metadata at the bottom of the regular description popup. The popup
    is now an 'i' you should click instead of an on-hover dialog. Works better
    with an ipad. Note that there's now a ``lizard_map.css`` again.

  - CQL filtering is possible on featureinfo items on wms layers.

  - Popups opened from the sidebar now disappear when the sidebar scrolls. No
    more zombie popups.


4.26 (2013-03-20)
-----------------

- Tabs in the popup now, by default, get the name of the first workspace item
  whose result is shown. This is waaaaay nicer than "tab 1, tab 2, tab 3".


4.25.6 (2013-03-13)
-------------------

- Fixed IE7 error caused by extraneous comma in animations.js.


4.25.5 (2013-02-27)
-------------------

- Haastige spoed...


4.25.4 (2013-02-27)
-------------------

- Default number of frames in animation set to 720.


4.25.3 (2013-02-27)
-------------------

- Changed animation speed from 500ms to 1000ms per frame.


4.25.2 (2013-02-27)
-------------------

- Moved animations.js import again.


4.25.1 (2013-02-27)
-------------------

- Changed animations.js import order (caused error).


4.25 (2013-02-26)
-----------------

- The change described in 4.24 didn't really work well, because the
  session object wasn't created yet when the default workspace was
  copied. This is fixed.

- Removed hour / day clamping (rounding) in the daterangepicker. Values for
  dt_start and dt_end are now simply a relative period based on the current
  time.


4.24 (2013-02-25)
-----------------

- It is now possible to use some stored workspace as a "default
  workspace" for users who get a newly created workspace.

  If the Setting 'default_workspace_anonymous_user' exists and is the
  secret slug of some existing stored workspace, then the items in it
  will be copied to any anonymous user's workspace when it is first
  created.

  The same holds for 'default_workspace_user' and logged in users,
  although it is probably less useful for them since their workspace
  is only initially created once, after that they keep using their
  existing one.


4.23 (2013-02-19)
-----------------

- Add vietnamese translations for month names via google translate.

- Remove zc.buildout >= 2.0.1 from setup.py since it is not a dependency.


4.22 (2013-02-19)
-----------------

- Added animation support for wms urls that have 'time' in them. Includes
  backbone 0.9.10, underscore 1.4.4.


4.21 (2013-02-19)
-----------------

- Manage translation strings with Transifex. Update en (source) and nl
  translations. Use nens/translations package for this.

- Add vietnamese django.po file from Transifex.

- Upgrade to zc.buildout 2.0.1.


4.20 (2013-01-22)
-----------------

- Fix context instance instantiation in html_default method.


4.19 (2013-01-21)
-----------------

- Add RequestContext instance when rendering a template in html_default
  method. This way request-related tags and context variables can be
  used when rendering the template.


4.18 (2013-01-17)
-----------------

- Adjust FlotGraphAxes to enable threshold lines.
- PEP8 fixes.

4.17 (2013-01-10)
-----------------

- Fix timezone handling for Flot graphs.

  The leading principle is that Javascript should do no timezone
  manipulation on time data from the past, because that would mean
  that the timezone of events recorded in the past depends on things
  like the _current_ summer / winter time setting. A graph of the same
  data should show the same information regardless of when it is
  viewed.

  In Lizard we internally work with UTC datetimes as much as possible,
  and convert these times to the site's timezone (usually
  Europe/Amsterdam) right before handing them to Javascript.

4.16 (2012-12-19)
-----------------

- Fixed urls.py, so it won't recusively include other lizard-* URLs when
  running as part of a site.


4.15 (2012-12-20)
-----------------

- Removed animationsettings for now. They're used in a tiny number of older
  projects and probably have to be re-instated later on. But the daterange
  implementation used by animationsettings has changed anyway. Perhaps
  implement it in the projects that need it?

- We're depending on the 2.x version of Django REST framework now. This means
  updating other projects that use Django REST framework. For a starting
  point, see
  http://reinout.vanrees.org/weblog/2012/12/04/django-rest-framework-2.html.

- Removed all daterange tests as none of them work. ``daterange.py`` itself
  has not been removed as it is used in quite a lot of views.

- Added configchecker test (``bin/django check_config``) whether ``USE_TZ =
  True`` is set in your setttings file.

- Added an "add_percentiles" function to FlotGraph, that allows
  plotting filled-in "percentile areas" around graphs. Will be
  implemented for Matplotlib too, but that's not done yet.

- Added a workaround in ViewStateService, because Forms seem no longer
  supported by rest_framework.


4.14 (2012-12-04)
-----------------

- Changed some text and changed location_list to always load initial results
  on opening.


4.13 (2012-12-03)
-----------------

- Fixing automatic migration step ``0009`` by deleting/adding the
  ``identifier`` column on ``CollageEditItem`` instead of altering it. The old
  ``JSONField``'s implementation is incomplete and wreaks the migration.

- Store current extent when saving a workspace, and load it back again
  when loading a workspace which has an extent set.


4.12 (2012-11-27)
-----------------

- Nothing big.


4.11 (2012-11-29)
-----------------

- Slightly refactored the 'workspace_item_toggle' view so that its
  main functionality is now in the WorkspaceEdit model, so that it can
  be called from other functions as well.
  As a result, WorkspaceEdit now has methods 'toggle_workspace_item'
  and 'add_workspace_item'.


4.10 (2012-11-22)
-----------------

- Support mixed flot/matplotlib (IE8) graphs.

- Fixed some IE8 issues.

- Added some more zoomLevels for WMS background layers.

- Graphs now reload on a date change.

- Removed some obsolete code regarding animation.

- Changed hover popup to one built with jQuery, as the previously used
  OpenLayers one causes an unnecessary redraw on IE8.

- Moved all graph code to lizard-map, which should be a more suitable place
  for it.

- Fixed usage of naive datetime objects.

- Added zoom/pan linked graphs.

- Added support for a singleTile WMS background layer.

- Location list now shows some initial results.

- Fixed various small bugs.

4.9 (2012-10-18)
----------------

- Fixed some styling issues.

- Fix test build config, travis & pep8.


4.8 (2012-10-05)
----------------

- Fix a missing css and made some javascript code optional.


4.7 (2012-10-04)
----------------

- Relicensed from GPL to LGPL.

- Added MAP_SHOW_MULTISELECT, MAP_SHOW_DATE_RANGE and MAP_SHOW_DEFAULT_ZOOM
  optional settings to make it possible to hide the three default lizard-map
  content actions. They're True by default.

- Added popup with subtabs.

- Merged and cleaned various JavaScript files.

- Link to Pillow instead of PIL.

- Move most CSS styling to lizard-ui.

- Fix some styling issues, typo's.

- Revived the collage page.

- Switch to a Twitter Bootstrap based date-range selector.

- Fix legend order.

- Disable obsolete OpenLayers reprojection.

- Changed default graph colours.

- Popup is shown directly after click on map.

- Add some iPad exceptions and add graph navigation.

- Add support for location search.

- Add more resolutions for Rijksdriehoek.

- Started a simple JavaScript view state holder on the client.
  In the future this will hold map extent, map layers etc. as well.

- Tables now have borders, as requested.


4.6 (2012-08-23)
----------------

- Fix graphs and popups: switch from jquery-tools tabs to superior jquery-ui tabs.

- Properly resize graphs instead of reloading them.


4.5 (2012-08-14)
----------------

- Fix OpenStreetMap pink tiles at Firefox.


4.4 (2012-08-14)
----------------

- Flot graphs: fallback to .axes label if one is available, because flot only supports a single ylabel.

- Flot graphs: pass x and y limits so we can determine tick size.

- Multiple select: don't show animation when nothing is found.

- Mapnik WMS rendering: reduce memory usage because of buffers being copied multiple times.

- Changed lots of core stuff: no longer combine workspace layers into a single WMS layer.

- Added multi-url legend support.

- Fix some bad hover_popup code.

- OpenLayers: fix iPad.

4.3 (2012-07-10)
----------------

- If a legend_image url is empty, we don't show the legend anymore.


4.2 (2012-07-10)
----------------

- In a map view, you can now provide ``.extra_wms_layers()`` to add extra
  WMS to the map. Handy for layers that are really part of a specific content
  item. The list of dictionaries that this method has to return is really an
  unfriendly API: this needs refactoring later on.

- Internal refactoring. Renamed ``.maps()`` to ``.backgrounds()`` in the
  views. This (hopefully) isn't used externally.


4.1.1 (2012-06-29)
------------------

- Importing JSONField in fields.py as otherwise the migrations fail.


4.1 (2012-06-28)
----------------

- Requiring newer django-jsonfield version (which works with django's multi-db
  functionality). Removed our custom JSONField in favour of
  django-jsonfield's one.


4.0 (2012-06-19)
----------------

- Added flot graph axis label support.

- Some table styling.

- Fix date range popup.

- Readded the option to save a workspace.

- Readded the nothingFoundPopup.

- Support EPSG:3857 alias for google coordinates.

- Added feature to load stored workspace in editable workspace.

- Add moving box on collage-add and multiple select.

- Fix my-collage popups.

- Reinstated multi-select functionality.


4.0b6 (2012-06-01)
------------------

- Add support for bar graphs (Flot).

- Remove an obsolete console.log call.


4.0b5 (2012-05-31)
------------------

- Removed OpenLayers.ImgPath of theme 'Dark'.

- Minor styling fix for workspaces.

- Add the new FlotGraph.

4.0b4 (2012-05-29)
------------------

- Fixed Javascript not finding href attributes during click events.


4.0b3 (2012-05-29)
------------------

- Collage and workspace are now styled using tables.


4.0b1 (2012-05-29)
------------------

- Added missing dependency lizard_security.

- Fixed popup and popup contents styling.

- Collage and workspace UI working again.


4.0a1 (2012-05-18)
------------------

- Requiring lizard-ui 4.0 alpha: the new twitter bootstrap layout.

- Using compiled css instead of less.

- Removed old HomepageView and renamed the MapIconView.

- Using new twitter-bootstrap layout. Using the MapView class based view is
  now really mandatory to get everything to work.

- Renamed /media to /static. That's django-staticfile's new standard.

- Timeseries can now be localized in Graph object.

- Fixed syntax error in jquery.workspace.js.

- Adds STATIC_URL to application icons.

- Making the normal AppView the main cbv instead of the temporary MapView name.


3.31 (2012-05-15)
-----------------

- Changed map click popup to jQuery ui dialog: it is now movable and
  resizable.

- The maximum number of tabs in popups has been made configurable.

- If an item is removed from the workspace while rendering (for instance because an Exception
  was raised), the page loads without giving an internal server error caused by trying to
  create a Legend.


3.30 (2012-04-26)
-----------------

- Added one icon.


3.29 (2012-04-25)
-----------------

- Added two icons.


3.28 (2012-04-13)
-----------------

- Re-enabling hover functionality on saved workspaces.


3.27.1 (2012-04-13)
-------------------

- Also removed references to touch.js and lizard_touch.js from the templates...


3.27 (2012-04-13)
-----------------

- Required lizard-ui 3.14 (new Openlayers).

- Removed touch.js, necessary with the new Openlayers version.

- Uncommented extent() in WorkspaceItemAdapter. It should be there
  because it is one of the methods that can be overridden by
  implementing adapters.

3.26 (2012-04-06)
-----------------

- Changed collage detail template so that apps can configure it a bit more.
  Collage items (that are put in groups on the collage page) have properties
  that control the header shown over the group (data_description), which edit
  dialog to show for a collage item edit button (collage_detail_edit_action),
  whether to show the whole Edit block at all (collage_detail_show_edit_block),
  and whether to show the statistics block (collage_detail_show_statistics_block).

  These functions in turn call functions in their adapters, with an identifier
  as argument (because one adapter can have items in different groups, with different
  settings. This way it gets the identifier of the first item in each group)::

    def collage_detail_data_description(self, identifier, *args, **kwargs):
      default 'Grafiek'
    def collage_detail_edit_action(self, identifier, *args, **kwargs):
      default 'graph'
    def collage_detail_show_edit_block(self, identifier, *args, **kwargs):
      default True
    def collage_detail_show_statistics_block(self, identifier, *args, **kwargs):
      default True

  ``*args`` and ``**kwargs`` are meaningless but present in case the
  functions' signatures change in the future. These functions can be
  overridden in your adapter.


3.25 (2012-04-04)
-----------------

- Improved docstrings at a few places (mainly location() in
  WorkspaceItemAdapter)

- Added method 'adapter_layer_json' to WorkspaceItemAdapter, helpful
  to generate this bit of json when it's needed.

- Added 'adapter': self to html_default's template context variables.
  This gives templates access to adapter's methods and attributes,
  like adapter.adapter_class and adapter.adapter_layer_json.

3.24 (2012-03-05)
-----------------

- It's now possible to not use a popup_click_handler.


3.23 (2012-02-16)
-----------------

- Added grouping_hint option to the result of adapter.search(), to make it
  possible for a single workspace layer to open a popup with multiple tabs.


3.22 (2012-01-27)
-----------------

- Translation fixes, added breadcrumb to the workspace storage
  page. Last fixes before "Lizard 3.0" release?


3.21 (2012-01-26)
-----------------

- Make sure graphs never zoom in so far that they show Y-axis values
  with more than 2 decimals.


3.20 (2012-01-26)
-----------------

- Changed waterstand icon from triangle pointing up to triangle
  pointing down.

- Changed workspace save/load functionality. Now workspaces can only
  be saved, which gives them a "secret slug" (a string with random
  characters), and the workspace detail page is opened in a new page.
  The URL to this page includes the secret slug and can be shared with
  others. The workspace shown on the page can't be changed. The
  "workspace load" button is gone until we have a nice user interface
  that can show many saved workspaces, and a way to deal with user
  privileges.

  This is minimal functionality that will be improved in later
  versions.

3.19 (2012-01-23)
-----------------

- Removed Download button because we don't have working background maps

- Added a nice calendar to the period selection dialog

- Fixed bug with opacity slider and WMS layers

- Added some functions for the collage detail page, so that different apps
  can show different titles and/or hide the Edit button.

3.18 (2012-01-17)
-----------------

- Breadcrumbs for application screens, first
  page of applications

- Possibility for apps to add their own breadcrumbs


3.17 (2012-01-13)
-----------------

- Fixed bug where items on the collage page didn't have access to the
  request (and therefore not to start- and end dates).


3.16 (2012-01-10)
-----------------

- Fix bug with editing collages.


3.15 (2012-01-05)
-----------------

- Fix bug where X-label of graph wasn't visible.


3.14.1 (2012-01-05)
-------------------

- Nothing changed yet.


3.14 (2012-01-05)
-----------------

- Hack to prevent error when a dictionary key doesn't exist.


3.13 (2012-01-04)
-----------------

- Skip map layers without params in downloaded image. (internal server
  error fix)


3.12.1 (2012-01-02)
-------------------

- Fix bug: not every adapter has an extent


3.12 (2012-01-02)
-----------------

- The workspace item zoom button is back and works.

- Changed "jouw" in some tooltip strings to "uw".

3.11 (2011-12-21)
-----------------

- Added functions in collage_edit and workspace_edit to check whether
  certain items already exist in them.

- Fixed bug where items could be added to a collage several times.

3.10 (2011-12-21)
-----------------

- New template tag 'if_in_workspace_edit' that can return a string
  if a given item's name is present in the workspace.

3.9 (2011-12-21)
----------------

- Removed some max_lengths in forms.py, because it caused valid forms
  to fail. There is no reason JSON fields should have a hard limit,
  and other fields should have the same limit as in the model.

3.8 (2011-12-20)
----------------

- Added 'transform_point' utility function that can use the site's
  projection Setting to transform points to a desired projection.


3.7 (2011-12-20)
----------------

- Made it possible to scale y-axis of graphs manually (it used to be
  possible, except then the y-axis would be recalculated afterwards)


3.6 (2011-12-19)
----------------

- WorkspaceItemAdapter's html_default() can use the
  extra_render_kwargs kwarg again. Subclasses can use it to send
  variables to the template and still use the html_default method for
  most of the work.

- Added a block popup_title to html_default.html so that the title
  can be changed in extending templates.


3.5.2 (2011-11-29)
------------------

- Removed object-actions block with the non-existing 'help-workspace' url that
  broke the interface.


3.5.1 (2011-11-28)
------------------

- Restored a small feature that RainApp depends on.

- Fixed test test_mixins.


3.5 (2011-11-14)
----------------

- Added wms_layers function to base Workspace model so that lizard-wms
  can work.


3.4.3 (2011-11-11)
------------------

- Deleted collage help button because it didn't work.

- Textual changes to satisfy pyflakes/pep8.


3.4.2 (2011-11-07)
------------------

- Nothing changed yet.


3.4.1 (2011-11-07)
------------------

- Minor layout.


3.4 (2011-11-07)
----------------

- Added layout_extra_from_request to AdapterMixin.

- Updated adapter views for image and values: you can now provide start and
  end dates in the url parameters.

- Added new adapter function identifiers.

- Fixed bug where tipsy tooltips didn't close correctly
  https://office.nelen-schuurmans.nl/trac/ticket/3378
  https://github.com/jaz303/tipsy/issues/19

- Added tooltip to the remove icon within the workspace

3.3 (2011-10-31)
----------------

- Cleaned up admin.py.

- Added experimental rest.js to handle rest apis.

- Improved i18n and tipsy tooltips.


3.2 (2011-10-06)
----------------

- Nothing changed yet.


3.1.5 (2011-10-05)
------------------

- Replaced dialogReplaceTitles with the more generic dialogReplaceIds
  and replaceItems. After submitting a dialog box you can now change
  the items you like. Some gui elements will be re-initialized.

- Fixed updating animation slider after changing period.

- Fixed animation slider bug.

- Updated MANIFEST.in to use graft.


3.1.4 (2011-10-05)
------------------

- Added option for restrict_to_month with javascript
  enabling/disabling field.

- Added view for statistics, javascript loading statistics in collage
  screen because that could take a while.

- Added reload page + message when period is changed in collage screen.

- Fixed collage item add when name is too long.

- Fixed javascript_hover_handler.

- Updated CollageItemEditorView to work correctly with adapter.image.

- Collage item editor: No week and day.

- Collage item editor: group fields are now filled in for every
  collage item in the group.

- Cleaned up unused code.

- Moved export csv button to table "Bewerken".

- Statistics in collage screen are now below edit options.

- Changed geoserver url to ip address, see #3283.

- And yet another (last) bug in ``**identifier`` in
  html_default. Apparently keys from identifiers are transformed to
  unicode on the server, while the development environment works just fine.


3.1.3 (2011-10-03)
------------------

- Convert keys of adapter.identifier to str before using it in
  html_default.


3.1.2 (2011-10-03)
------------------

- Fixed error in MANIFEST.in. 3.1.1 didn't include any lizard-map/* data.


3.1.1 (2011-10-03)
------------------

- Fixed CollageEditItem.csv_url function.

- Fixed bug with collage items. The popup crashed as well as the
  collage screen.

- Moved from company-internal svn to github:
  https://github.com/lizardsystem/lizard-map .


3.1 (2011-09-30)
----------------

- Fixed Color/Mapnik Color related bug.

- Added non-blockable spaces to html_default.html to prevent
  disappearing icons.

- Improved float layout in collage detail: statistics.

- Reload page after changing collage in collage detail screen.

- Fixed problem when adding collage items by coordinates (name too long).

- Fixed (re-) sorting of collage items.

- Fixed dialog box items first time popup in collage screen.

- Removed setUpGraphEditPopup, it was used in the popup code.

- Changed lizard-map client-side error.

- Fixed google maps in wms.

- Added date popup to collage detail view.

- Added download-map button.

- Added y-min and y-max option for collage detail screen.

- Added csv statistics output for collage.

- Added table view to collage edit detail screen.

- Improved layout collage-item editor popup.

- Improved layout collage edit detail screen.

- Improved export csv link in popup: now for every location.

- Moved Grouping_hint check from adapter.location to
  adapter.location['identifier']. Apparently this was the location of
  the grouping hint.

- Pylint.

- Added option "add to selection" in map popup.

- Removed console.log and alert from js.

- Fixed popup dialog size, it will now always be the default size.

- Fixed "pan & zoom to default location". After changes in workspace
  the button didn't work anymore.

- WMS background maps can now be used as overlays.


3.0 (2011-09-28)
----------------

Lizard 3: Make sure you read the readme before upgrading to this version.

- Rebuilt collage screen with grouping.

- Added configchecker.

- Added migration for new models; South introspection rules.

- Integrated search_name in search_coordinates.

- Various functions work on WorkspaceEdits and WorkspaceStorages.

- Added generic dialog javascript code.

- Added generic POST action javascript code.

- Made app_screen class-based, with helper class WorkspaceView.

- Added new workspaces, collages.

- Added PeriodMixin with tests.

- Added all kinds of mixins for workspaces, collages, etc:
  GoogleTrackingMixin, WorkspaceMixin, WorkspaceEditMixin, MapMixin,
  CollageMixin, DateRangeMixin.

- Added class based views: AppView,
  WorkspaceStorageView, HomepageView, CollageDetailView.

- Added class based views for dialogs: ActionDialogView, WorkspaceSaveView,
  WorkspaceLoadView, DateRangeView, CollageItemEditorView,
  WorkspaceStorageListView, CollageView, CollageEmptyView,
  CollageItemEditView, CollagePopupView, WorkspaceEmptyView.

- Adapter stuff: AdapterMixin, ImageMixin, AdapterImageView, AdapterCsvView.


2.5 (2011-09-23)
----------------

- Not mentioning pyproj as a dependency anymore, even though we *do* need
  it. Somehow the osc.recipe.sysegg buildout recipe doesn't really want to
  play nice with it.

- When there's an non-existing adapter (=invalid/non-existing entry point
  name), we now also delete the workspace item instead of raising an
  error. There just might be an old workspace item laying around in a
  customer's session and we shouldn't keep the customer stuck in an
  error 500.


2.4 (2011-09-22)
----------------

- The context processor now first weeds out faulty workspace items before
  attempting anything else. This prevents an "error 500": normally the
  workspace item gets deleted, but the .is_animatable call still breaks on the
  just-deleted workspaceitem. Now we first remove the faulty ones beforehand.


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
