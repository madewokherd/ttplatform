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
import struct
import xml.sax
import xml.sax.handler
import zlib

loaded_tilesets = {}

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
            assert(self.tileset.tilewidth == 0)

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
        else:
            raise xml.sax.SAXNotRecognizedException("unrecognized tag %s" % name)

        self.level += 1

    def endElement(self, name):
        self.level -= 1

def tileset_from_filename(filename):
    filename = os.path.normpath(os.path.abspath(filename))
    try:
        return loaded_tilesets[filename]
    except KeyError:
        result = Tileset()
        result.load_filename(filename)
        loaded_tilesets.setdefault(filename, result)
        return loaded_tilesets[filename]

class GameObject(object):
    width = 0
    height = 0

    tileset = None
    tileid = None

    positions = None

    exists = True

    frame_created = 0
    frame_destroyed = -1

    def __init__(self):
        self.positions = []

    def copy(self):
        result = type(self)()
        result.width = self.width
        result.height = self.height
        result.tileset = self.tileset
        result.tileid = self.tileid
        result.positions.extend(self.positions)
        result.frame_created = self.frame_created
        result.frame_destroyed = self.frame_destroyed
        result.exists = self.exists
        return result

    def _congruence_attrs(self):
        return (type(self), self.width, self.height, self.tileset, self.tileid)

    def congruent(self, oth):
        return self._congruence_attrs() == oth._congruence_attrs()

class Player(GameObject):
    pass

class Map(object):
    def __init__(self):
        self.filename = ''

        self.tilesets = []
        self.raw_tile_layers = []
        self.tile_layers = []

        self.object_layers = []
        self.objects = []

        self.width = 0
        self.height = 0

        self.tilewidth = 0
        self.tileheight = 0

        self.tileswide = 0
        self.tileshigh = 0

    def load_filename(self, filename):
        assert(self.filename == '')
        self.filename = os.path.abspath(filename)

        handler = _MapSaxHandler(self)
        xml.sax.parse(filename, handler)

        self._find_tile_objects()

    def find_tileset(self, tileid):
        for start, end, tileset in self.tilesets:
            if start <= tileid < end:
                return tileset, tileid - start
        else:
            return None, tileid

    def _find_tile_objects(self):
        for raw_tile_layer in self.raw_tile_layers:
            tiles = list(raw_tile_layer)
            for i, tileid in enumerate(tiles):
                tileset, tilesetid = self.find_tileset(tileid)
                if tileset:
                    typename = tileset.properties[tilesetid].get('type')
                    if typename == 'player':
                        obj = Player()
                    else:
                        continue
                    obj.width = int(tileset.properties[tilesetid].get('width', self.tilewidth))
                    obj.height = int(tileset.properties[tilesetid].get('height', self.tileheight))
                    x, y = divmod(i, self.tileswide)
                    obj.positions.append((x * self.tilewidth, y * self.tileheight))
                    self.objects.append(obj)
                    tiles[i] = 0
            self.tile_layers.append(tuple(tiles))

class _MapSaxHandler(xml.sax.handler.ContentHandler):
    level = 0
    in_layer = False

    def __init__(self, map):
        self.map = map

    def startDocument(self):
        assert(self.map.tilewidth == 0)

    def endDocument(self):
        assert(self.map.tilewidth != 0)
        assert(self.level == 0)

    def startElement(self, name, attrs):
        if self.level == 0:
            assert(name == 'map')
            assert(attrs['version'] == '1.0')
            assert(attrs['orientation'] == 'orthogonal')
            assert(self.map.tilewidth == 0)

            self.map.tileswide = int(attrs['width'])
            self.map.tileshigh = int(attrs['height'])

            self.map.tilewidth = int(attrs['tilewidth'])
            self.map.tileheight = int(attrs['tileheight'])

            self.map.width = self.map.tilewidth * self.map.tileswide
            self.map.height = self.map.tileheight * self.map.tileshigh
        elif self.level == 1:
            if name == 'tileset':
                filename = os.path.join(os.path.dirname(self.map.filename), attrs['source'])
                tileset = tileset_from_filename(filename)

                first_tileid = int(attrs['firstgid'])
                end_tileid = first_tileid + tileset.tileswide * tileset.tileshigh
                self.map.tilesets.append((first_tileid, end_tileid, tileset))
            elif name == 'layer':
                assert(self.map.tileswide == int(attrs['width']))
                assert(self.map.tileshigh == int(attrs['height']))
                self.in_layer = True
        elif self.level == 2:
            if self.in_layer:
                assert(name == 'data')
                self.encoding = attrs['encoding']
                self.compression = attrs['compression']
                self.layerdata = []
        else:
            raise xml.sax.SAXNotRecognizedException("unrecognized tag %s" % name)

        self.level += 1

    def endElement(self, name):
        self.level -= 1

        if self.level == 2 and name == 'data':
            data = ''.join(self.layerdata)

            data = data.decode(self.encoding)

            if self.compression == 'zlib':
                data = zlib.decompress(data)
            else:
                raise xml.sax.SAXNotRecognizedException("unrecognized compression %s" % self.compression)

            tiles = struct.unpack('<%sL' % str(self.map.tileswide * self.map.tileshigh), data)

            self.map.raw_tile_layers.append(tiles)

            self.layerdata = None
        elif self.level == 1 and name == 'layer':
            self.in_layer = False

    def characters(self, content):
        if self.level == 3 and self.in_layer:
            self.layerdata.append(content)

class World(object):
    def __init__(self, map):
        self.map = map

        self.last_frame = 0

        self.objects = []

        for obj in map.objects:
            self.objects.append(obj.copy())

