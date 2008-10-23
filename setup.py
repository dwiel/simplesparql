#!/usr/bin/env python

from distutils.core import setup

setup(name = 'SimpleSPARQL',
      version = '0.1',
      description = """SimpleSPARQL allows queries to SPARQL endpoints in a very simple language similar to MQL. The query language is designed specifically for python and uses python dictionaries in the same way as MQL.""",
      url = 'http://code.google.com/p/simplesparql/',
      author = 'Zach Dwiel',
      author_email = 'zdwiel@gmail.com',
      packages = ['SimpleSPARQL'],
      )

