class WorkspaceItemError(Exception):
    """To be raised when a WorkspaceItem is out of date.

    A WorkspaceItem can represent something that does no longer exist.
    For example, it may refer to a shape that has been deleted from
    the database. This error may trigger deletion of such orphans.
    """
    pass
