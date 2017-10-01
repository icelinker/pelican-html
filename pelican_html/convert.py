from .case_insensitive_dict import CaseInsensitiveDefaultDict 
from html.parser import HTMLParser
from time import gmtime, mktime
from datetime import datetime
from io import StringIO
from os import listdir
from os.path import isfile, join
import importlib
import os
import sys
import re
import json

def load_settings(dir):
    ''' Try to find and load JSON settings '''
    try:
        with open(os.path.join(dir, 'pelican.json')) as settings_file:
            settings = json.loads(settings_file.read())
        return settings
    except FileNotFoundError:
        return {}
        
def convert_html_files(dir=None, **kwargs):
    ''' Parse all relevant HTML files in a directory '''
    if not dir:
        dir = os.getcwd()
    
    try:
        # Get a list of files to include
        files = load_settings(dir)['global']['include']
    except:
        files = [f for f in listdir(dir) if isfile(join(dir, f))]
        files = [f for f in files if re.search('\.html', f)]
    
    for f in files:
        parser = PelicanParser(f, **kwargs)
        parser.read_html()
        parser.to_md()

class PelicanParser(HTMLParser):
    ''' Parses through a single HTML document and makes it Pelican ready '''
    
    ignore = set(['html', 'body'])
    
    def __init__(self, file,
        pelican_dir=None,
    
        # Tag Removal
        strip=set(['meta', 'h1']),
        strip_by_attr={},
        
        # Attribute Removal
        strip_attr={'td': 'align'}):
        '''
        Args:
            file:           str or os.path
                            HTML file to be processed
            pelican_dir:    str or os.path
                            Path of the Pelican website directory
            strip:          set
                            Set of tags to not include in final output
            strip_by_attr:  dict (Attribute to regex pattern)
                            Set of attributes, that if a tag has, will cause
                            it to be excluded
        '''
    
        super(PelicanParser, self).__init__()
        self.file = file
        self.strip_by_attr = strip_by_attr
        self.strip_attr = strip_attr
        
        self.strip_tags = strip
        self.final_head = StringIO()
        self.final_html = StringIO()
        
        # Try to find location to place HTML templates
        if pelican_dir:
            parent_dir = os.path.split(pelican_dir)[:-1][0]
            pelican_dirname = os.path.split(pelican_dir)[-1]
            sys.path.append(parent_dir)
            
            # Import Pelican settings file
            import importlib.util
            spec = importlib.util.spec_from_file_location("pelican_conf",
                os.path.join(pelican_dir, 'pelicanconf.py'))
            pelican_conf = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(pelican_conf)
            
            self.templates_dir = os.path.join(pelican_dir, pelican_conf.THEME, 'templates')
        
        # Settings
        self.settings = settings = load_settings(os.getcwd())
        
        try:
            self.output_dir = settings['global']['output_dir']
        except KeyError:
            self.output_dir = os.getcwd()
        
        # Parse metadata
        try:
            metadata = CaseInsensitiveDefaultDict(str,
                self.settings['global']['metadata'])
        except KeyError:
            metadata = CaseInsensitiveDefaultDict(str)
            
        try:
            file_metadata = CaseInsensitiveDefaultDict(str,
                self.settings[file]['metadata'])
                
            for k, v in file_metadata.items():
                metadata[k] = v
        except KeyError:
            pass
            
        self.md_head = metadata
        
        # State
        self.current_path = []
        self.del_index = None
        self._parse_ignore = None   # Ignore data in between stripped tags
        
        # Flags
        self._head = False
        self._parse_title = False
        
    def handle_starttag(self, tag, attrs):
        '''
        Example of what attrs looks like:
        
        ('src', 'python-logo.png')
        ('alt', 'The Python logo')
        '''
        
        self.current_path.append(tag)
    
        if tag == 'title':
            self._parse_title = True
        elif tag == 'head':
            self._head = True
        elif tag in self.strip_tags:
            self._parse_ignore = tag
        elif tag not in self.ignore:
            # Check against attributes
            for attr, val in [j for j in attrs if j[0] in self.strip_by_attr]:
                if re.search(self.strip_by_attr[attr], val):
                    self.del_index = len(self.current_path) - 1
                    return
            
            # Clean up attributes
            if (tag in self.strip_attr):
                attrs = [i for i in attrs if i[0] not in self.strip_attr[tag]]
            
            attr_str = ' '.join('{attr}="{val}"'.format(
                attr=i[0], val=i[1]) for i in attrs)
            
            if attr_str:
                html_str = '<{0} {1}>'.format(tag, attr_str)
            else:
                html_str = '<{}>'.format(tag)
            
            if self._head:
                self.final_head.write(html_str)
            else:
                self.final_html.write(html_str)
        
    def handle_endtag(self, tag):
        if (self.del_index) and \
            ((len(self.current_path) - 1) == self.del_index):
            self.del_index = None
            return
    
        del self.current_path[-1]
    
        if tag == 'title':
            self._parse_title = False
        elif tag == 'head':
            self._head = False
        elif tag == self._parse_ignore:
            self._parse_ignore = None
        elif tag not in self.ignore:
            if self._head:
                self.final_head.write('</{}>'.format(tag))
            else:
                self.final_html.write('</{}>'.format(tag))
        
    def handle_data(self, data):
        if self._parse_title:
            self.md_head['title'] += data
        elif not self._parse_ignore:
            if self._head:
                self.final_head.write(data)
            else:
                self.final_html.write(data)
            
    def read_html(self):
        '''
        Get file metadata from system
         - Note: getctime() gets last modified time on Unix systems
           - See: https://docs.python.org/3/library/os.path.html#os.path.getctime
        '''
        
        # 1. Get time in seconds since last epoch
        # 2. Convert to time_struct with readable date and time
        # 3. Convert to datetime object
        self.md_head['date'] = datetime.fromtimestamp(
            mktime(gmtime(os.path.getctime(self.file))))
        self.md_head['modified'] = datetime.fromtimestamp(
            mktime(gmtime(os.path.getmtime(self.file))))
        
        # Try to import output.py settings if there is one
        
        # Parse HTML
        with open(self.file, mode='r', encoding='utf-8') as html_file:
            for line in html_file:
                self.feed(line)
            
    def to_md(self):
        '''
        Create a Pelican-ready Markdown file with UTF-8 encoding
        (as Pelican expects)
            
        Rules:
         - Place templates in '.../templates/<category>/<page>.html' '''
        
        self.final_head.seek(0)
        self.final_html.seek(0)
        filename = self.file.replace('.html', '.md')
        filename_no_ext = self.file.replace('.html', '')
        
        head = self.final_head.read()
        if head:
            # Write <head> contents
            with open(os.path.join(
                self.templates_dir, filename_no_ext + '.html'),
                encoding='utf-8', mode='w') as output:
                output.write('{% extends "article.html" %}\n{% block pelican_html_head %}\n')
                output.write(head)
                output.write('\n{% endblock %}')
            
        with open(os.path.join(self.output_dir, filename),
            encoding='utf-8', mode='w') as output:
            for key in ['Title', 'Date', 'Modified', 'Authors',
                'Template', 'Summary']:
                if self.md_head[key]:
                    output.write('{}: {}'.format(key, self.md_head[key]))
                    output.write('\n')
            
            output.write('Slug: {}'.format(filename_no_ext))
            output.write('\n')
            
            output.write('Template: {}'.format(filename_no_ext))
            output.write('\n')
            
            # Write HTML contents
            output.write(self.final_html.read())