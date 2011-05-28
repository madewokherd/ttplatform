# Copyright 2011 Vincent Povirk
#
# This file is part of Imprudence.
#
# Imprudence is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Imprudence is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Imprudence.  If not, see <http://www.gnu.org/licenses/>.

import collections
import os.path
import xml.sax
import xml.sax.handler

class Tileset(object):
    def __init__(self):
        self.tileset_filename = ''
        self.image_filename = ''

        self.tilewidth = 0
        self.tileheight = 0

        self.tileswide = 0
        self.tileshigh = 0

        self.properties = collections.defaultdict(dict)

        self.name = ''

    def load_filename(self, filename):
        assert(self.tileset_filename == '')
        self.tileset_filename = os.path.abspath(filename)

        handler = _TilesetSaxHandler(self)
        xml.sax.parse(filename, handler)

class _TilesetSaxHandler(xml.sax.handler.ContentHandler):
    level = 0

    def __init__(self, tileset):
        self.tileset = tileset

    def startDocument(self):
        assert(self.tileset.tilewidth == 0)

    def endDocument(self):
        assert(self.tileset.tilewidth != 0)
        assert(self.tileset.tileswide != 0)
        assert(self.level == 0)

    def startElement(self, name, attrs):
        if self.level == 0:
            assert(name == 'tileset')

            self.tileset.name = attrs['name']
            self.tileset.tilewidth = int(attrs['tilewidth'])
            self.tileset.tileheight = int(attrs['tileheight'])
        elif self.level == 1:
            if name == 'image':
                self.tileset.image_filename = os.path.normpath(os.path.join(os.path.dirname(self.tileset.tileset_filename), attrs['source']))

                self.tileset.tileswide = int(attrs['width']) // self.tileset.tilewidth
                self.tileset.tileshigh = int(attrs['height']) // self.tileset.tileheight
            elif name == 'tile':
                self.tileid = int(attrs['id'])
                self.got_properties = False
            else:
                raise xml.sax.SAXNotRecognizedException("unrecognized tag %s" % name)
        elif self.level == 2:
            assert(name == 'properties')
            assert(not self.got_properties)
            self.got_properties = True
        elif self.level == 3:
            assert(name == 'property')

            self.tileset.properties[self.tileid][attrs['name']] = attrs['value']

        self.level += 1

    def endElement(self, name):
        self.level -= 1

