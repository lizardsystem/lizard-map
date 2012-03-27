How to make a Lizard 3 app
==========================

Introduction
------------

Currently, a wide range of Lizard apps exists. Some of them are
ancient (like over four months old), others are "converted to Lizard
3". What does that even mean? Is this documented anywhere? What is a
Lizard app anyway?

The answer is obvious: no, it is not documented anywhere, but it will
be, or at least somewhat. Once I've finished typing this.

What is Lizard 3?
-----------------

Lizard is a water information platform, originally developed and
popularized by Nelen & Schuurmans. See http://www.lizard.net .

Its core component is probably "lizard-map". If you are reading this,
you have probably found that package.

What does Lizard do?

It has a fullscreen interface, consisting primarily of a large map and
a sidebar. At the bottom of the sidebar, there is a "workspace" and a
"selection". There are also some buttons and a lot of JavaScript, that
helps implement the main functionality of Lizard. Lizard can:

- Show a menu structure using icon buttons in the sidebar
- Show pages belonging to "Apps" in the same area
- Show map layers that have been added to a "workspace"
- Show popups with detailed information about some location
- Show a little bit of information about a location if the mouse hovers
  over it
- Add detailed information to the "selection"
- Show a "selection page" that shows all the information in the selection
  in the area usually used for the map

And various small details relating to this functionality.

"Lizard 3" is loosely defined. Lizard-map had a large backwards
incompatible change when it switched from function-based Django views
to class-based Django views, and the class-based version of lizard-map
could be said to be the core of Lizard 3. When people talk of
"converting an app to Lizard 3", usually that means converting its
views and templates to use the class-based views of the newer
lizard-map.

Another definition is the latest version of the apps as they are used
in the 3.0.x versions of the 'demo.lizard.net' site. At the time of
writing the latest version of demo is 3.0.7, and that uses lizard-ui
3.13 and lizard-map 3.24. When demo.lizard.net 3.1.0 is released, that
will be Lizard 3.1.

So what is an app, and how do I make one?
-----------------------------------------

A "Lizard App" is:

* A Python package implementing a Django app
* that can show its interface in the Lizard sidebar
* and implements map layers that can be added to the workspace, and
  popups.

I will not explain here what a Django app is. In order to get a basic
template that can be used to build a Lizard app on, do ``pip install
nensskel and ``nensskel PROJECTNAME -t nens_djangoapp.

On the other hand, I will now try to explain in detail how to create
views and templates that will show your app in the sidebar, and how to
create fully functional map layers.

Views
=====

A general introduction for Django class based views can be found here:
http://www.slideshare.net/rvanrees/django-class-based-views-dutch-django-meeting-presentation


If you want a view to show inside the Lizard interface, it should be a
class based view inheriting from one of the views in lizard_map.views,
probably AppView. It extends Django's TemplateView and several other
classes defined in lizard_ui and lizard_map.

The most important one of these is a small mixin named
``lizard_ui.view.ViewContextMixin''. That does one important thing: it
adds the current view object to the template's context dictionary. You
don't need to add variables to the dictionary anymore, you can create
methods that can be called from the template (like
``{{ view.method }}'').

A very simple view
------------------

The minimum possible view needs a single thing: a template_name.

So::

    from lizard_map.views import AppView

    class MyView(AppView):
        template_name = 'myapp/template.html'

Is a valid, working class based view (if the template exists).

The template should generally extend "lizard_map/wms.html", which is
the basic Lizard page. The sidebar can then be configured by the
App. Because the workspace and collage are also part of the sidebar,
it is necessary for the App to place them in there too (so it's not
technically necessary for the workspace and collage to be there at all
times, but a page that misses than is very strange).

A minimal template is::

  {% extends "lizard_map/wms.html" %}
  {%a load workspaces %}

  {% block sidebar %}

  <div id="iconbox" class="sidebarbox sidebarbox-stretched iconlist">
    <h2>YOUR HEADER HERE</h2>
    YOUR CONTENT HERE
  </div>

  {% workspace_edit view.workspace_edit %}
  {% collage_edit view.collage_edit %}

  {% endblock %}


Adding variables to the template context
----------------------------------------

The key thing here is that *your view is available in the template as
the 'view' variable*. So instead of adding variables to a dictionary
before going into the template, you add methods to the view and call
them from the template.

Suppose you want to have a list of three URLs in the template; add a function
like::


    class MyView(AppView):
        ...

        def urls(self):
            return (
                ('description1', 'http://www.example.com/'),
                ('description2', 'http://www.example.com/'),
                ('description3', 'http://www.example.com/'),
            )

to the view and in the template::

    <ul>
    {% for description, url in view.urls %}
        <li><a href="{{ url }}">{{ description }}</a></li>
    {% endfor %}
    </ul>

Parameters from the URL
-----------------------

If you want to use variables from the URL pattern or from GET
parameters, override get().

This is an example from lizard_fewsjdbc.views, where the jdbc_source
is part of the urlpattern, and 'filter_id' and 'ignore_cache' can be given
as GET parameters:

urls.py::

    url(r'^fews_jdbc/(?P<jdbc_source_slug>.*)/$',
        JdbcSourceView.as_view(),
        name="lizard_fewsjdbc.jdbc_source",
        ),

views.py::

    def get(self, request, *args, **kwargs):
        """This method is overridden in order to get at the GET parameters."""

        self.jdbc_source_slug = kwargs.get('jdbc_source_slug', )
        self.jdbc_source = get_object_or_404(JdbcSource,
                                             slug=self.jdbc_source_slug)
        self.filter_id = request.GET.get('filter_id', None)
        self.ignore_cache = request.GET.get('ignore_cache', False)

        return super(JdbcSourceView, self).get(request, *args, **kwargs)


Adding something to the workspace
---------------------------------

A template snippet to add an item to the workspace::

    <li class="workspace-acceptable file {% if_in_workspace_edit view.workspace_edit parameter.workspace_name 'selected' %}"
      data-name="{{ parameter.workspace_name }}"
        data-adapter-class="{{ view.adapter_class }}"
        data-adapter-layer-json='{"slug":"{{ view.jdbc_source_slug }}","filter":"{{ parameter.filter_id }}","parameter":"{{ parameter.id }}"}'
        data-filter-id="{{ parameter.filter_id }}">
      {{ parameter.name }} ({{ parameter.filter_name }})
    </li>

The above bit of HTML is taken from lizard-fewsjdbc. It is a <li>
element that, when clicked, adds the current combination of fewsjdbc
source, filter and parameter to the Lizard workspace.

Notes:

* The css class "workspace-acceptable" is what makes the <li>
  clickable. The function setUpWorkspaceAcceptable in lizard_map.js
  adds some Javascript to elements with this class that gives them an
  onclick handler that toggles their workspace status.
* An item with the css class "selected" looks different (blue
  background). It is given that when added to the workspace, but the
  if_in_workspace_edit bit also sets the class when the page is first
  loaded.
* data-name is the name that will be given to this workspace item.
* data-adapter-class is the name of the adapter that will be used for
  this workspace item (see below)
* data-adapter-layer-json is data that will be used in constructing an
  instance of the adapter (see below). This should be a dictionary,
  but there are no rules on what the contents have to be.
* data-filter-id: I don't know, perhaps this is leftover from an old version?
  Unfortunately this happens more often than it should.
* The content of the <li> is simply the description of this item as it
  should look in the sidebar.

Adapters
========

Each app that shows map layers from its workspace needs an
*adapter*. Adapters inherit from
lizard_map.workspace.WorkspaceItemAdapter or a subclass thereof.

The "adapter-layer-json" that was used to add a workspace item to the
workspace is turned into a Python dictionary and passed to the
constructor of the adapter. It should have all the information the
adapter needs to recognize which layer to draw. For instance, if you
have an app that draws water wells, and you have one map layer for
each company that owns water wells, then the dict should hold the name
or primary key of the company. A FEWS app would record which fews
server, filter and parameter is associated with this layer. If an app
draws only a single layer then the dictionary might as well be empty.

Right now the adapter is called like this::

    adapter = adapter_class(workspace_item, layer_arguments=layer_arguments,
                            adapter_class=adapter_class)

Workspace_item is an instance of
lizard_map.models.WorkspaceItem. Layer_arguments is the dictionary
constructed from adapter-layer-json. Adapter_class is a string like
'adapter_fewsjdbc' that is listed in lizard-fewsjdbc's setup.py's
entry points, which is the link between the frontend (<li> element and
Javascript) and the specific class implementing the adapter in
lizard_fewsjdbc/layers.py.

The default __init__ sets self.layer_arguments to layer_arguments,
both self.workspace_item and self.workspace_mixin_item to
workspace_item, and self.adapter_class to adapter_class.

Although it would work to have an __init__ that has parameters exactly
like the ones listed, it is more future proof (but not more readable,
I'm afraid) to write __init__ like this::

    class MyAdapter(WorkspaceItemAdapter)
        def __init__(self, *args, **kwargs):
            super(MyAdapter, self).__init__(*args, **kwargs)

	    # Now use self.layer_arguments to do your own setup

The rest of the adapter implements Lizard's functionality. We'll
repeat the list here and then treat the different methods and what
they need to implement.

Apps can:

- Show map layers that have been added to a "workspace"
- Show popups with detailed information about some location
- Show a little bit of information about a location if the mouse hovers
  over it
- Add detailed information to the "selection"
- Show a "selection page" that shows all the information in the selection
  in the area usually used for the map


Show a map layer
----------------
