import doctest


def suite():
    """Return test suite

    This method is automatically called by django's test mechanism.

    """
    return doctest.DocFileSuite(
        'USAGE.txt',
        #'TODO_several_more_tests.txt',
        module_relative=True,
        optionflags=(doctest.NORMALIZE_WHITESPACE|
                     doctest.ELLIPSIS|
                     doctest.REPORT_NDIFF))
