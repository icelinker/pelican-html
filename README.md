pelican_html
==============

Pelican is a great static site generator which turns your Markdown into a 
website. However, it is a little limited for generating content
from already existing HTML pages... until now.

`pelican_html` is a package which converts existing HTML pages into 
Pelican-ready Markdown files. This package (ab)uses the fact that Markdown
will render raw HTML as is. However, it does more than just copying 
over your HTML code verbatim, such as stripping out unwanted tags and more.

## Features

* Strip out unwanted and unnecessary tags (e.g. `<head>`, `<body>`, `<h1>`)
* Automatically inspects HTML files for metadata, e.g. time and creation time
* Custom build options, such as automatically placing outputted Markdown in a specified directory