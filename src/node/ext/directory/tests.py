from interlude import interact
from pprint import pprint
from zope.configuration.xmlconfig import XMLConfig
import doctest
import unittest


optionflags = doctest.NORMALIZE_WHITESPACE | \
              doctest.ELLIPSIS | \
              doctest.REPORT_ONLY_FIRST_FAILURE


TESTFILES = [
    'directory.rst',
]


def test_suite():
    return unittest.TestSuite([
        doctest.DocFileSuite(
            file,
            optionflags=optionflags,
            globs={'interact': interact,
                   'pprint': pprint},
        ) for file in TESTFILES
    ])


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')                 #pragma NO COVER
