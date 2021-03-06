from collections import namedtuple
from mock import Mock, patch, mock_open
import sys
import unittest

import os
import md5
from gladius import GladiusHandler, project_dir


class TestGladius(unittest.TestCase):
    def setUp(self):
        self.handler = GladiusHandler()

    def test_gladius_handler_cache(self):
        self.assertEquals([], self.handler.cache)

    def test_gladius_handler_outpath(self):
        shouldbe = os.path.join(project_dir, 'gladiushandler_out')
        self.assertEquals(self.handler.outpath, shouldbe)

    def test_gladius_handler_junk(self):
        shouldbe = os.path.join(project_dir, 'junk')
        self.assertEquals(self.handler.junkpath, shouldbe)

    @patch('gladius.os')
    def test_gladius_handler_path_creation_on_not_exist(self, mock_os):
        mock_os.path = Mock()
        mock_os.path.exists.return_value = False
        self.handler = GladiusHandler()
        mock_os.makedirs.assert_called_with(self.handler.outpath)
        mock_os.makedirs.assert_called_with(self.handler.junkpath)

    @patch('gladius.os')
    def test_gladius_handler_path_creation_on_exist(self, mock_os):
        mock_os.path = Mock()
        mock_os.path.exists.return_value = True
        self.handler = GladiusHandler()
        mock_os.makedirs.assert_not_called()

    @patch('gladius.tempfile')
    def test_gladius_handler_get_outfile_no_suffix(self, mock_tempfile):
        self.handler.get_outfile()
        mock_tempfile.NamedTemporaryFile.assert_called_with(delete=False, dir=self.handler.outpath, suffix='')

    @patch('gladius.tempfile')
    def test_gladius_handler_get_junkfile_no_suffix(self, mock_tempfile):
        self.handler.get_junkfile()
        mock_tempfile.NamedTemporaryFile.assert_called_with(delete=False, dir=self.handler.junkpath, suffix='')

    @patch('gladius.os')
    def test_gladius_handler_on_created_directory(self, mock_os):
        Directory = namedtuple("Directory", ['src_path'])
        src_path = 'test_src_path'
        my_dir = Directory(src_path)
        self.handler.on_created(my_dir)
        mock_os.path.isdir.assert_called_with(src_path)

    @patch('gladius.os')
    def test_gladius_handler_on_created_directory_true(self, mock_os):
        mock_os.path.isdir.return_value = True

        Directory = namedtuple("Directory", ['src_path'])
        src_path = 'test_src_path'
        my_dir = Directory(src_path)
        result = self.handler.on_created(my_dir)
        self.assertEquals(result, None)

    @patch('gladius.md5')
    @patch('gladius.open')
    @patch('gladius.os')
    def test_gladius_handler_on_created_directory_true(self, mock_os, mock_open, mock_md5):
        mock_os.path.isdir.return_value = False

        Directory = namedtuple("Directory", ['src_path'])
        src_path = 'test_src_path'
        my_dir = Directory(src_path)
        self.handler.on_created(my_dir)
        mock_open.assert_called_with(src_path, 'r')

    @patch('gladius.md5')
    @patch('gladius.open')
    @patch('gladius.os')
    def test_gladius_handler_on_created_in_cache_true(self, mock_os, mock_open, mock_md5):
        '''Test when file is modified, if the file has been seen, do not add it to the cache'''
        mock_os.path.isdir.return_value = False
        
        mock_file = Mock()
        mock_file.read.return_value = 'abcd'

        mock_hash = Mock()
        mock_md5.new.return_value = mock_hash
        mock_hash.hexdigest.return_value = 'fakehash'
        self.handler.cache = ['fakehash']

        Directory = namedtuple("Directory", ['src_path'])
        src_path = 'test_src_path'
        my_dir = Directory(src_path)
        result = self.handler.on_created(my_dir)

        mock_open.return_value = mock_file
        self.assertEqual(result, None)

    @patch('gladius.md5')
    @patch('gladius.open')
    @patch('gladius.os')
    def test_gladius_handler_on_created_in_cache_false(self, mock_os, mock_open, mock_md5):
        '''Test when file is modified, if the file has not been seen, do add it to the cache'''
        mock_os.path.isdir.return_value = False

        mock_file = Mock()
        mock_file.read.return_value = 'abcd'

        mock_hash = Mock()
        mock_md5.new.return_value = mock_hash
        mock_hash.hexdigest.return_value = 'fakehash'

        Directory = namedtuple("Directory", ['src_path'])
        src_path = 'test_src_path'
        my_dir = Directory(src_path)
        self.handler.on_created(my_dir)

        mock_open.return_value = mock_file
        self.assertEqual(self.handler.cache, ['fakehash'])

    def test_gladius_handler_on_modified_calls_created(self):
        self.handler.on_created = Mock()

        event = 'testevent'
        self.handler.on_modified(event)
        self.handler.on_created.assert_called_once_with(event)

    @patch('gladius.open')
    def test_gladius_get_lines(self, mock_open):
        Event = namedtuple("Event", ['src_path'])
        src_path = 'test_src_path'
        event = Event(src_path)

        self.handler.get_lines(event)

        mock_open.assert_called_with(event.src_path, 'r')

    def test_gladius_get_lines_correct_return(self):
        Event = namedtuple("Event", ['src_path'])
        src_path = 'test_src_path'
        event = Event(src_path)

        file_contents = '\n'.join(['a', 'b', 'c'])
        
        m = mock_open(read_data=file_contents)
        with patch('gladius.open', m, create=True):
            result = self.handler.get_lines(event)

        self.assertEqual(result, ['a', 'b', 'c'])

if __name__ == '__main__':
    unittest.main()
