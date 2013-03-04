import unittest


class Test_Directory(unittest.TestCase):
    """
    tests for node.ext.directory:directory.py:Directory
    """
    def test_it(self):
        #from node.ext.directory import Directory
        pass


class Test_File(unittest.TestCase):
    """
    tests for node.ext.directory:directory.py:File
    """
    def test_textfile(self):
        """
        test operations on a file in text mode
        """
        from node.ext.directory import File
        import os
        import tempfile
        tempdir = tempfile.mkdtemp()
        filepath = os.path.join(tempdir, 'file.txt')
        file = File(filepath)
        self.assertEqual(file.data, '')

        # ensure the file does not exists yet
        self.assertFalse(os.path.exists(filepath))
        # write out the file by calling it
        file()
        # check that the file now exists
        self.assertTrue(os.path.exists(filepath))

        with open(filepath) as f:
            out = f.read()
        self.assertEqual(out, '')

        file.data = "abc\ndef"
        file()
        with open(filepath) as f:
            out = f.read()
        self.assertEqual(out, 'abc\ndef')

        self.assertEqual(file.data, 'abc\ndef')
        self.assertEqual(file.lines, ['abc', 'def'])
        self.assertEqual(file.mode, 0)  # file is in text mode

        file.mode = 1  # set mode to binary
        # reading data in 'binary' mode must yield None
        #self.assertIsNone(binary_stuff)
        self.assertEqual(file.mode, 1)  # file is in binary mode

        file.mode = 0  # setting text mode again
        self.assertEqual(file.mode, 0)  # file is in text mode

        # check that we can set lines
        file._set_lines(['foo', 'bar'])
        file()
        with open(filepath) as f:
            out = f.readlines()
        self.assertEqual(out, ['foo\n', 'bar'])

    def test_binaryfile(self):
        """
        test operations on a file in binary mode
        """
        from node.ext.directory import File
        import os
        import tempfile
        tempdir = tempfile.mkdtemp()
        filepath = os.path.join(tempdir, 'file.txt')
        file = File(filepath)
        file.mode = 1  # binary
        self.assertEqual(file.data, None)

        # ensure the file does not exists yet
        self.assertFalse(os.path.exists(filepath))
        file.data = "foo"
        # write out the file by calling it
        file()
        # check that the file now exists
        self.assertTrue(os.path.exists(filepath))

        with open(filepath) as f:
            out = f.read()
        self.assertEqual(out, 'foo')

        file.data = "abc\ndef"
        file()

        # why the heck is this not working?
        #self.assertRaises(RuntimeError, file.lines, None)

        with self.assertRaises(RuntimeError) as re:
            file.lines
        #        print(dir(re))
        # print('------------------------------')
        # print('re.exception: ')
        # print re.exception
        # print type(re.exception)
        # print('expected: ')
        # print(re.expected)
        # print type(re.expected)
        # print('expected_regexp: ')
        # print(re.expected_regexp)
        # print type(re.expected_regexp)
        # #print('failureException: ')
        # #print(re.failure_exception)
        # print('------------------------------')
        # self.assertEqual(
        #     re.exception,
        #     RuntimeError(u'Cannot read lines from binary file.')
        # )

        # check: may not set lines on binary file
        with self.assertRaises(RuntimeError) as re:
            file._set_lines(['foo', 'bar'])
            print re


class Test_FileFactories(unittest.TestCase):
    """
    tests for node.ext.directory:directory.py:file_factories
    """
    def test_file_factory(self):
        from node.ext.directory import file_factories
        self.assertEqual(file_factories, {})


class Test_DirectoryStorage(unittest.TestCase):
    """
    tests for node.ext.directory:directory.py:DirectoryStorage
    """
    def test_child_directory_factory(self):
        """
        test child_directory_factory
        """
        from node.ext.directory import DirectoryStorage
        import tempfile
        tempdir = tempfile.mkdtemp()

        #print(help(DirectoryStorage))
        #ds = DirectoryStorage(tempdir)
        #print ('ds.child_directory_factory:')
        #print ds.child_directory_factory

        #self.assertTrue(0)
        pass  # I have no idea how to make this work

    def test_factory_for_ending(self):
        """
        test 
        """
        from node.ext.directory import Directory
        import tempfile
        tempdir = tempfile.mkdtemp()
        dire = Directory(tempdir)
        self.assertEqual(dire.factories, {})

        dire._factory_for_ending('bar')

#        print dir(dire)
#        self.assertTrue(0)



class Test_Factories(unittest.TestCase):
    """
    another approach at testing stuff in directory.py
    """
    def test_it(self):
        """
        test some stuff
        covers DirectoryStorage.__init__ :-)
        """
        from node.ext.directory import Directory
        import tempfile
        tempdir = tempfile.mkdtemp()
        dire = Directory(tempdir)
        self.assertEqual(dire.factories, {})

        print dir(dire)
        self.assertTrue(0)



