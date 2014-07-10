#!/usr/bin/python
from kivy.uix.filechooser import FileSystemAbstract
import urllib2
from urllib import urlencode # I'm surprised urllib2 doesn't have an equivalent to this.
from HTMLParser import HTMLParser
from datetime import datetime
from time import time, sleep

# Extended FileSystemLocal
from kivy.uix.filechooser import FileSystemLocal
import os
class FileSystemLocal(FileSystemLocal):
    # Helpers
    def join(self, *path):
        return os.path.join(*path)
    def normpath(self, path):
        return os.path.normpath(path)

    # Query Functions
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

    # Modify Functions
    def mkdir(self, fn):
        return os.mkdir(fn)

class HTMLDirParse(HTMLParser):
    # This is written for mini-httpd's indexing HTML, it will probably completely fail with anything else.
    def reset_files(self, *args):
        self.files = []
        self.in_pre = False
        self.in_a = False
    def handle_starttag(self, tag, attrs):
        if tag == 'pre':
            self.in_pre = True
        if self.in_pre and tag == 'a':
            self.in_a = True
            for attr in attrs:
                if attr[0] == 'href':
                    if attr[1] not in ('.', '..'):
                        self.files.append({'filename': urllib2.unquote(attr[1])})
    def handle_endtag(self, tag):
        if tag == 'pre':
            self.in_pre = False
        if self.in_pre and self.in_a and tag == 'a':
            self.in_a = False
    def handle_data(self, data):
        if self.in_pre and not self.in_a:
            if data != '\n' and len(self.files) != 0 and not (self.files[-1].has_key('mtime') or self.files[-1].has_key('size')):
                split_data = data.strip().split(' ')
                mtime = ' '.join(split_data[0:2])
                size = split_data[-1]
                self.files[-1]['mtime'] = datetime.strptime(mtime, '%d%b%Y %H:%M')
                self.files[-1]['size'] = int(size)

class FileSystemURL(FileSystemAbstract):
    last_url = ''
    last_get = 0
    parser = HTMLDirParse()
    def _get_url(self, url):
        if url.startswith('/'):
            url = url[1:]
        if not url.startswith('https://') and not url.startswith('http://'): url = url.replace('/', '//', 1)
        self.last_url = url
        response = urllib2.urlopen(url)
        html = response.read()
        response.close()
        if not html[:6].lower() == '<html>': return html # Not HTML, can't do anything with it.

        self.parser.reset_files()
        self.parser.feed(html)
        self._files = self.parser.files
        self.parser.close()

        self.last_get = time()

        return html
    # Helpers
    sep = '/'
    def join(self, *path):
        url = path[0]
        for i in xrange(1, len(path)):
            if not path[i-1].endswith(self.sep) and not path[i].startswith(self.sep):
                url += self.sep
            url += path[i]
        return url
    def normpath(self, url):
        split_url = urllib2.urlparse.urlsplit(url)
        quoted_url = urllib2.urlparse.urlunsplit((split_url.scheme, split_url.netloc, urllib2.quote(split_url.path), split_url.query, split_url.fragment))
        return quoted_url

    # Query Functions
    def listdir(self, url):
        print 'listing', url
        if self.last_url != url or self.last_get < time()-10:
            self._get_url(url)
        dirlist = []
        for f in self._files:
            dirlist.append(f['filename'])
        return sorted(dirlist)
    def getsize(self, url):
        for f in self._files:
            if f['filename'] == url:
                return f['size']
    def is_hidden(self, url):
        # I don't care to support hidden files
        return False
    def is_file(self, url):
        # This is a bad way to implement this, I'm just checking whether it has a '.' in the filename. So it completely fails to check whether the filea actually exists in the first place
        return '.' in url
    def is_dir(self, url):
        # This is a bad way to implement this, I'm just checking whether it has a '.' in the filename. So it completely fails to check whether the filea actually exists in the first place
        return '.' not in url
    def getmtime(self, url):
        for i in self._files:
            if os.path.basename(url) == i['filename']:
                return int(i['mtime'].strftime('%s'))
        return 0

    # Modify Functions
    def mkdir(self, url):
        # The cgi script on the HTTP server automatically creates directories as necessary so this mkdir is unnecessary
        pass
    def savefile(self, dn, ext, fname):
        url = urllib2.urlparse.urlparse(dn)
        cgi_url = url.scheme + '://' + url.netloc + '/cgi-bin/newfile.py'
        with open(fname, 'r') as f:
            data = urlencode({'dirname': url.path, 'extension': ext, 'contents': f.read()})
        response = urllib2.urlopen(url=cgi_url, data=data)
        if response.read().startswith('File saved: '):
            return True
        else:
            return False
