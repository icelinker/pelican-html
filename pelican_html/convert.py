from .case_insensitive_dict import CaseInsensitiveDefaultDict 
from html.parser import HTMLParser
from time import gmtime, mktime
from datetime import datetime
from io import StringIO
from os import listdir
from os.path import isfile, join
import os
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
        
def convert_html_files(dir=None):
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
        parser = PelicanParser(f)
        parser.read_html()
        parser.to_md()

class PelicanParser(HTMLParser):
    ''' Parses through a single HTML document and makes it Pelican ready '''
    
    ignore = set(['html', 'head', 'body'])
    
    def __init__(self, file, strip=set(['meta', 'h1'])):
        '''
        Args:
            file:   str or os.path
                    HTML file to be processed
            strip:  set
                    Set of tags to not include in final output
        '''
    
        super(PelicanParser, self).__init__()
        self.file = file
        
        self.strip_tags = strip
        self.final_html = StringIO()
        
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
        
        # Flags
        self._parse_title = False
        self._parse_ignore = False
        
    def handle_starttag(self, tag, attrs):
        '''
        Example of what attrs looks like:
        
        ('src', 'python-logo.png')
        ('alt', 'The Python logo')
        '''
    
        if tag == 'title':
            self._parse_title = True
        elif tag in self.strip_tags:
            self._parse_ignore = True
        elif tag not in self.ignore:
            attr_str = ' '.join('{attr}="{val}"'.format(
                attr=i[0], val=i[1]) for i in attrs)
            
            if attr_str:
                html_str = '<{0} {1}>'.format(tag, attr_str)
            else:
                html_str = '<{}>'.format(tag)
            
            self.final_html.write(html_str)
        
    def handle_endtag(self, tag):
        if tag == 'title':
            self._parse_title = False
        elif self._parse_ignore:
            self._parse_ignore = False
        elif tag not in self.ignore:
            self.final_html.write('</{}>'.format(tag))
        
    def handle_data(self, data):
        if self._parse_title:
            self.md_head['title'] += data
        elif not self._parse_ignore:
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
        with open(self.file, mode='r') as html_file:
            for line in html_file:
                self.feed(line)
            
    def to_md(self):
        ''' Create a Pelican-ready Markdown file '''
        
        self.final_html.seek(0)
        filename = self.file.replace('.html', '.md')
        filename_no_ext = self.file.replace('.html', '')
        
        with open(os.path.join(self.output_dir, filename),
            mode='w') as output:
            for key in ['Title', 'Date', 'Modified', 'Authors',
                'Template', 'Summary']:
                if self.md_head[key]:
                    output.write('{}: {}'.format(key, self.md_head[key]))
                    output.write('\n')
            
            output.write('Slug: {}'.format(filename_no_ext))
            output.write('\n')

            # Write HTML contents
            output.write(self.final_html.read())