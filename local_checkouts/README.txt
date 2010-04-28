If you want to use trunk checkouts of other packages (instead of released
versions), add them as an "svn external" in the ``local_checkouts/`` directory
and add them to the ``develop =`` list in buildout.cfg.

To set svn externals, run ``svn propedit svn:externals .`` (or the
clicky-clicky equivalent in the GUI: TODO document that!).  Every line
contains a checkoutname + url combination::

  myproduct svn://svn.zope.org/repos/main/myproduct/trunk

This will checkout the url as the checkoutname in the current directory.  You
can have multiple checkouts.

Notes:

- An ``svn up`` automatically grabs the latest version of the externals, too.

- An ``svn commit`` in the main directory does *not* commit the changes in the
  externals.

- Watch out with making changes in one of the externals: others also use that
  product, probably, so don't make all sorts of tweaks for your particular
  usecase without making sure it is OK.
