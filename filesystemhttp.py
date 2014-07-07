#!/usr/bin/python
from kivy.uix.filechooser import FileSystemAbstract, FileSystemLocal
import os

class FileSystemLocal(FileSystemLocal):

    # Helpers
    def join(self, *path):
        return os.path.join(*path)

    # Query FS
    ## listdir(self, fn): """Return the list of files in the directory 'fn'"""
    ## getsize(self, fn): """Return the size in bytes of a file"""
    ## is_hidden(self, fn): """Return True if the file is hidden"""
    ## is_dir(self, fn): """Return True if the argument passed to this method is a directory"""
    def is_file(self, fn):
        return os.path.isfile(fn)
    def is_dir(self, fn):
        return os.path.isdir(fn)
    def getmtime(self, fn):
        return os.path.getmtime(fn)

    # Modify FS
    def mkdir(self, fn):
        return os.mkdir(fn)
