import datetime
import pkg_resources

from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore
from django.test import TestCase
from django.test.client import Client


from lizard_map.models import ExtentMixin
from lizard_map.models import PeriodMixin
from lizard_map.models import UserSessionMixin

from lizard_map.models import WorkspaceEdit
from lizard_map.models import WorkspaceStorage
from lizard_map.models import WorkspaceEditItem
from lizard_map.models import WorkspaceStorageItem

import lizard_map


class Period(PeriodMixin):
    """Test class to instantiate PeriodMixin"""
    pass


class PeriodMixinTest(TestCase):
    def setUp(self):
        pass

    def test_smoke(self):
        p = Period()
        p.save()

    def test_period_absolute(self):
        """
        Using absolute period.
        """
        now = datetime.datetime(2011, 8, 15)
        p = Period(
            dt_start=datetime.datetime(2011, 8, 5),
            dt_end=datetime.datetime(2011, 8, 15),
            absolute=True)

        # Testing period.
        dt_start, dt_end = p.period(now=now)
        self.assertEquals(dt_start, datetime.datetime(2011, 8, 5))
        self.assertEquals(dt_end, datetime.datetime(2011, 8, 15))

        # By default, the time is dt, unless otherwise specified.
        dt = p.time(now=now)
        self.assertEquals(dt, datetime.datetime(2011, 8, 15))

    def test_period_absolute2(self):
        """
        Using absolute period with custom time.
        """
        now = datetime.datetime(2011, 8, 15)
        p = Period(
            dt_start=datetime.datetime(2011, 8, 5),
            dt_end=datetime.datetime(2011, 8, 15),
            dt=datetime.datetime(2011, 8, 16),
            absolute=True,
            custom_time=True)

        # By default, the time is dt, unless otherwise specified.
        dt = p.time(now=now)
        self.assertEquals(dt, datetime.datetime(2011, 8, 16))

    def test_period_relative(self):
        """
        Using relative period.
        """
        now = datetime.datetime(2011, 8, 15)
        p = Period(
            td_start=-10.0,
            td_end=0.0)

        # Testing period.
        dt_start, dt_end = p.period(now=now)
        self.assertEquals(dt_start, datetime.datetime(2011, 8, 5))
        self.assertEquals(dt_end, datetime.datetime(2011, 8, 15))

        # By default, the time is dt, unless otherwise specified.
        dt = p.time(now=now)
        self.assertEquals(dt, datetime.datetime(2011, 8, 15))

    def test_period_relative_custom(self):
        """
        Using relative period, custom time.
        """
        now = datetime.datetime(2011, 8, 15)
        p = Period(
            td_start=-10.0,
            td_end=0.0,
            td=1.0,
            custom_time=True)

        # By default, the time is dt, unless otherwise specified.
        dt = p.time(now=now)
        self.assertEquals(dt, datetime.datetime(2011, 8, 16))

    def test_period_not_specified(self):
        """
        If period is not fully specified, return None(s).

        Depending on fields absolute and custom_time, some of the
        fields dt_start.. td must be specified.
        """
        now = datetime.datetime(2011, 8, 15)
        p = Period()

        dt_start, dt_end = p.period(now=now)
        self.assertEquals(dt_start, None)
        self.assertEquals(dt_end, None)

        dt = p.time(now=now)
        self.assertEquals(dt, None)

    def test_period_not_specified_fallback(self):
        """
        Return fallback values.
        """
        now = datetime.datetime(2011, 8, 15)
        expected_dt_start = datetime.datetime(2011, 8, 5)
        expected_dt_end = datetime.datetime(2011, 8, 16)
        p = Period()

        dt_start, dt_end = p.period(now=now, fallback=True)
        self.assertEquals(dt_start, expected_dt_start)
        self.assertEquals(dt_end, expected_dt_end)

        dt = p.time(now=now, fallback=True)
        self.assertEquals(dt, now)


class Extent(ExtentMixin):
    pass


class ExtentMixinTest(TestCase):
    def setUp(self):
        pass

    def test_smoke(self):
        e = Extent(x_min=1, y_min=1.5, x_max=2, y_max=3)
        e.save()

    def test_extent(self):
        e = Extent(x_min=1, y_min=1.5, x_max=2, y_max=3)
        e.save()
        result = e.extent()
        expected = (1.0, 1.5, 2.0, 3.0)
        self.assertEquals(result, expected)


class UserSession(UserSessionMixin):
    """Test class to instantiate UserSessionMixin"""
    pass


class UserSessionMixinTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.session_key = 'session_key'
        self.other_session_key = 'other_session_key'

    def test_get_or_create(self):
        """User session object get_or_create with session and
        anonymous user"""
        user = AnonymousUser()
        user_session_object = UserSession.get_or_create(
            self.session_key, user)
        self.assertTrue(user_session_object.id)

    def test_get_or_create2(self):
        """User session object get_or_create with user and session"""
        user = User(username='pony', password='pink')
        user.save()
        user_session_object = UserSession.get_or_create(
            self.session_key, user=user)
        self.assertTrue(user_session_object.id)

    def test_get_or_create5(self):
        """User session object get_or_create gets same workspace based
        on session"""
        user = AnonymousUser()
        user_session_object = UserSession.get_or_create(
            self.session_key, user)
        self.assertTrue(user_session_object.id)
        user_session_object2 = UserSession.get_or_create(
            self.session_key, user)
        self.assertEquals(user_session_object.id, user_session_object2.id)

    def test_get_or_create6(self):
        """User session object get_or_create based on session or user"""
        user = User(username='pony', password='pink')
        user.save()

        user_session_object = UserSession.get_or_create(
            self.session_key, user)
        self.assertTrue(user_session_object.id)

        user_session_object_user = UserSession.get_or_create(
            self.session_key, user)
        self.assertEquals(
            user_session_object.id, user_session_object_user.id)

        user_session_object_session = UserSession.get_or_create(
            self.session_key, user)
        self.assertEquals(
            user_session_object.id, user_session_object_session.id)

    def test_get_or_create7(self):
        """User session object get_or_create workspace cornercase.

        Defined user has preference over defined session."""
        user = User(username='pony', password='pink')
        user.save()
        user2 = User(username='reinout', password='annie')
        user2.save()
        session_store = SessionStore(session_key='other_session')
        session_store.save()

        user_session_object = UserSession.get_or_create(
            self.other_session_key, user=user)
        self.assertTrue(user_session_object.id)

        user_session_object_user = UserSession.get_or_create(
            self.session_key, user=user)
        self.assertEquals(
            user_session_object.id, user_session_object_user.id)

        # Don't find anything: create new workspace
        user_session_object_other = UserSession.get_or_create(
            self.other_session_key, user=user2)
        self.assertNotEquals(
            user_session_object.id, user_session_object_other.id)

    def test_get_or_create_anonymous(self):
        """User session object get_or_create with anonymous user and
        session"""
        user = AnonymousUser()
        user_session_object = UserSession.get_or_create(
            self.session_key, user=user)
        self.assertTrue(user_session_object.id)


class WorkspaceLoadSaveTest(TestCase):
    """Loading and saving from WorkspaceEdit to WorkspaceStorage.

    """

    def setUp(self):
        self.user = User(username='mindstorms')
        self.user.save()

        self.workspace_edit = WorkspaceEdit()
        self.workspace_edit.save()

        self.workspace_storage = WorkspaceStorage(
            name='storage', owner=self.user)
        self.workspace_storage.save()

        class Mock(dict):
            pass

        self.request = Mock()
        self.request.session = Mock()
        self.request.session.session_key = 'mock-session-key'
        self.request.user = AnonymousUser()
        self.request.META = {}

    def test_item_edit_as_storage(self):
        """WorkspaceEditItem to WorkspaceStorageItem conversion."""
        workspace_item_edit = WorkspaceEditItem(
            workspace=self.workspace_edit)
        workspace_item_edit.save()

        workspace_storage_item = workspace_item_edit.as_storage(
            workspace=self.workspace_storage)
        workspace_storage_item.save()  # Do not crash.

        # This dict does not have _state, _workspace_cache, workspace_id
        edit_dict = workspace_item_edit.__dict__

        storage_dict = workspace_storage_item.__dict__

        # _workspace_cache does not appear in other code... strange?
        del storage_dict['id']
        del storage_dict['_state']
        del storage_dict['_workspace_cache']
        del storage_dict['workspace_id']

        self.assertEquals(edit_dict, storage_dict)

    def test_item_storage_as_edit(self):
        """WorkspaceStorageItem to WorkspaceEditItem conversion."""
        workspace_storage_item = WorkspaceStorageItem(
            workspace=self.workspace_storage)
        workspace_storage_item.save()

        workspace_item_edit = workspace_storage_item.as_edit(
            workspace=self.workspace_edit)
        workspace_item_edit.save()  # Do not crash.

        # This dict does not have _state, _workspace_cache, workspace_id
        storage_dict = workspace_storage_item.__dict__

        edit_dict = workspace_item_edit.__dict__

        # _workspace_cache does not appear in other code... strange?
        del edit_dict['id']
        del edit_dict['_state']
        del edit_dict['_workspace_cache']
        del edit_dict['workspace_id']

        self.assertEquals(edit_dict, storage_dict)

    def test_load(self):
        """Load: copy from storage to edit."""
        # Add some random workspace_items in edit workspace.
        self.workspace_edit.workspace_items.create(name="mock")

        # Add some random workspace_items in storage workspace.
        self.workspace_storage.workspace_items.create(name="saved")

        self.workspace_edit.load_from_storage(self.workspace_storage)

        self.assertEquals(len(self.workspace_edit.workspace_items.all()), 1)
        self.assertEquals(
            self.workspace_edit.workspace_items.all()[0].name, 'saved')

    def test_save(self):
        """Load: copy from storage to edit."""
        # Add some random workspace_items in edit workspace.
        self.workspace_edit.workspace_items.create(name="edit")

        # Add some random workspace_items in storage workspace.
        self.workspace_storage.workspace_items.create(name="saved")

        # The name and owner must correspond.
        self.workspace_edit.save_to_storage(name='storage', owner=self.user)

        self.assertEquals(len(self.workspace_edit.workspace_items.all()), 1)

        # Just copied 'edit' from edit to storage.
        self.assertEquals(
            self.workspace_storage.workspace_items.all()[0].name, 'edit')

        # Item "saved" is deleted.
        self.assertEquals(
            len(WorkspaceStorageItem.objects.filter(name="saved")), 0)

    def test_save2(self):
        """Load: copy from storage to edit in different workspaces."""
        user2 = User(username="pinkpony")
        user2.save()
        # Add some random workspace_items in edit workspace.
        self.workspace_edit.workspace_items.create(name="edit")

        # Find existing workspace = 1.
        self.workspace_edit.save_to_storage(name='storage', owner=self.user)
        # Create new workspace = 2.
        self.workspace_edit.save_to_storage(name='new', owner=self.user)
        # Create new workspace = 3.
        self.workspace_edit.save_to_storage(name='storage', owner=user2)
        # Overwrite workspace = 3.
        self.workspace_edit.save_to_storage(name='storage', owner=user2)

        # 3 workspaces, 3 workspace items should exist.
        self.assertEquals(WorkspaceStorage.objects.count(), 3)
        self.assertEquals(WorkspaceStorageItem.objects.count(), 3)

    def test_save_not_authenticated(self):
        data = {'name': 'test workspace'}
        form = lizard_map.forms.WorkspaceSaveForm(data)
        form.is_valid()  # it must succeed

        # Count workspaces
        no_of_workspaces = WorkspaceStorage.objects.count()

        view = lizard_map.views.WorkspaceSaveView()
        view.request = self.request  # Manually put request in view.
        response = view.form_valid_action(form)  # Perform save action.

        self.assertTrue(response.status_code, 403)

        # Nothing is changed.
        self.assertEquals(WorkspaceStorage.objects.count(), no_of_workspaces)


class WorkspaceModelMixinTest(TestCase):
    def setUp(self):
        pass

    def test_is_animatable(self):
        user = User(username='lespaul')
        workspace = WorkspaceEdit.get_or_create('fake session key', user)
        self.assertFalse(workspace.is_animatable)

    def test_is_animatable2(self):
        user = User(username='lespaul')
        workspace = WorkspaceEdit.get_or_create('fake session key', user)
        workspace.workspace_items.create(
            name='fake',
            adapter_class='adapter_class',
            adapter_layer_json='adapter_layer_json')
        workspace.workspace_items.create(
            name='fake2',
            adapter_class='adapter_class',
            adapter_layer_json='adapter_layer_json')
        self.assertFalse(workspace.is_animatable)

    def test_check_workspace_item_adapters(self):
        user = User(username='lespaul')
        workspace = WorkspaceEdit.get_or_create('fake session key', user)
        workspace.workspace_items.create(
            name='fake',
            adapter_class='adapter_class',
            adapter_layer_json='adapter_layer_json')
        workspace.check_workspace_item_adapters()


class WorkspaceEditTest(TestCase):

    class MockRequest(object):
        class MockSession(object):
            session_key = 'mock'

        def __init__(self, user):
            self.session = self.MockSession()
            self.user = user
            self.POST = {}
            self.GET = {}

    def setUp(self):
        self.client = Client()
        self.user = User(username='jack')
        self.request = self.MockRequest(self.user)

    def test_workspace_item_add(self):
        workspace = WorkspaceEdit()
        workspace.save()
        params = {'name': 'test workspace_item',
                  'adapter_class': 'test adapter_class',
                  'adapter_layer_json': '{"json"}'}
        self.request.POST.update(params)
        lizard_map.views.workspace_item_toggle(
            self.request, workspace_edit=workspace)
        self.assertTrue(workspace.workspace_items.filter())

    def test_workspace_item_reorder(self):
        """Test workspace items reorder

        TODO: this is not a very good test, because indices are given
        in the test. How to fake getlist in your view?
        """
        workspace = WorkspaceEdit()
        workspace.save()
        workspace_item1 = workspace.workspace_items.create()
        workspace_item2 = workspace.workspace_items.create()
        order = {str(workspace_item2.id): 10,
                 str(workspace_item1.id): 20}
        lizard_map.views.workspace_item_reorder(
            self.request, workspace_edit=workspace,
            workspace_items_order=order)

        self.assertEqual(workspace.workspace_items.all()[0], workspace_item2)
        self.assertEqual(workspace.workspace_items.all()[1], workspace_item1)

    def test_workspace_edit_item(self):
        workspace = WorkspaceEdit(
            session_key=self.request.session.session_key,
            user=self.request.user)
        workspace.save()
        workspace_item1 = workspace.workspace_items.create(
            name='test workspaceitem')

        lizard_map.views.workspace_edit_item(
            self.request, workspace_edit=workspace,
            workspace_item_id=str(workspace_item1.id),
            visible='false')
        self.assertEqual(
            WorkspaceEditItem.objects.get(name='test workspaceitem').visible,
            False)
        lizard_map.views.workspace_edit_item(
            self.request, workspace_edit=workspace,
            workspace_item_id=str(workspace_item1.id),
            visible='true')
        self.assertEqual(
            WorkspaceEditItem.objects.get(name='test workspaceitem').visible,
            True)

    def test_workspace_item_delete(self):
        workspace = WorkspaceEdit()
        workspace.save()
        workspace_item1 = workspace.workspace_items.create(
            name='test workspaceitem')

        self.request.POST['object_id'] = str(workspace_item1.id)
        lizard_map.views.workspace_item_delete(
            self.request, workspace_edit=workspace)
        self.assertFalse(workspace.workspace_items.all())

    def test_workspace_edit(self):
        user = User(username='lespaul')
        workspace = WorkspaceEdit.get_or_create('fake session key', user)
        workspace.__unicode__()
        workspace.wms_url()

    # def test_workspace_extent_temp(self):
    #     """
    #     Tests if the workspace extent does not crash (although the
    #     content will be meaningless).
    #     """
    #     url = reverse('lizard_map_session_workspace_extent_temp')
    #     result = self.client.get(url, {})
    #     self.assertEqual(result.status_code, 200)

    # Not testable without adapter
    # def test_workspace_extent(self):
    #     """
    #     Tests if the workspace extent does not crash (although the
    #     content will be meaningless).
    #     """
    #     workspace = Workspace()
    #     workspace.save()
    #     workspace_item1 = workspace.workspace_items.create(
    #         name='test workspaceitem')
    #     url = reverse('lizard_map_workspace_item_extent')
    #     result = self.client.get(url, {
    #             'workspace_item_id': workspace_item1.id})
    #     self.assertEqual(result.status_code, 200)
    #     self.assertTrue('north' in result.content)


    # Not testable without adapter
    # def test_workspace_item_image(self):
    #     workspace = Workspace()
    #     workspace.save()
    #     workspace_item1 = workspace.workspace_items.create(
    #         name='test workspaceitem')

    #     url = reverse('lizard_map_workspace_item_image')
    #     url += '?identifier={test_identifier}'
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, 200)


class WorkspaceItemTest(TestCase):

    # def test_has_adapter(self):
    #     """A workspace item can point to a method that returns a layer."""
    #     workspace_item = WorkspaceEditItem()
    #     self.assertFalse(workspace_item.has_adapter())
    #     workspace_item.adapter_class = 'todo'
    #     self.assertTrue(workspace_item.has_adapter())

    def test_entry_points_exist(self):
        """There's at least one adapter entry point registered."""
        self.assertTrue(list(pkg_resources.iter_entry_points(
                    group='lizard_map.adapter_class')))

    def test_entry_point_lookup(self):
        """The string that identifies a method is looked up as a so-called
        entry point."""
        workspace_item = WorkspaceEditItem()
        workspace_item.adapter_class = 'adapter_dummy'
        workspace_item.adapter_layer_json = ("{}")
        self.assertTrue(isinstance(
                workspace_item.adapter,
                lizard_map.layers.AdapterDummy))

    def test_adapter_arguments(self):
        """The layer method probably needs arguments. You can store them as a
        json string."""
        workspace_item = WorkspaceEditItem()
        self.assertTrue(isinstance(workspace_item._adapter_layer_arguments,
                                   dict))
        self.assertFalse(len(workspace_item._adapter_layer_arguments))
        workspace_item.adapter_layer_json = '{"bla": "yes"}'
        self.assertEquals(workspace_item._adapter_layer_arguments['bla'],
                          'yes')

    def test_name(self):
        """A workspace item always has a name.  It is blank by default,
        though."""
        workspace_item = WorkspaceEditItem()
        self.assertEquals(workspace_item.name, '')
        workspace_item2 = WorkspaceEditItem(name='bla')
        self.assertEquals(workspace_item2.name, 'bla')

    def test_representation(self):
        workspace = WorkspaceEdit()
        workspace.save()
        workspace_item = workspace.workspace_items.create(
            name="workspace_item")
        # No errors: fine.  As long as we return something.
        self.assertTrue(unicode(workspace_item))

    def test_delete_invalid_ws_item_1(self):
        workspace = WorkspaceEdit()
        workspace.save()
        workspace_item = workspace.workspace_items.create(
            adapter_class='adapter_dummy', name='reinout')
        workspace_item.save()
        self.assertTrue(isinstance(workspace_item.adapter,
                                   lizard_map.layers.AdapterDummy))
        workspace_item.adapter_layer_json = ''
        workspace_item.save()
        workspace_item.adapter_layer_json = '[{"invalid": "non existing"}a]'
        # The workspace item should be deleted after .adapter() got an error.
        self.assertTrue(workspace_item.adapter is None)
        # Don't know why this doesn't work
        # self.assertEquals(workspace_item.adapter, None)
        # Make sure the code doesn't hang in the __unicode__ after a deletion.
        self.assertTrue(unicode(workspace_item))

    def test_delete_invalid_ws_item_2(self):
        workspace = WorkspaceEdit()
        workspace.save()
        workspace_item = workspace.workspace_items.create(
            adapter_class='adapter_does_not_exist', name='workspace-item')
        workspace_item.save()
        # The workspace item should be deleted after .adapter() got an error.
        self.assertEquals(workspace_item.adapter, None)
        # Make sure the code doesn't hang in the __unicode__ after a deletion.
        self.assertTrue(unicode(workspace_item))
