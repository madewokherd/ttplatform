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

import sys

import pygame
from pygame.locals import *

import impcore

pygame.init()

def get_tileset_surface(tileset):
    try:
        return tileset._pygame_surface
    except AttributeError:
        tileset._pygame_surface = pygame.image.load(tileset.image_filename)
        return tileset._pygame_surface

def get_tile_image(world, frame, tileid):
    tileset, tileid = world.map.find_tileset(tileid)

    if tileset is None:
        return None, None

    surface = get_tileset_surface(tileset)

    if 'drawas' in tileset.properties[tileid]:
        tileid = int(tileset.properties[tileid]['drawas'])

    return surface, Rect((tileid % tileset.tileswide) * tileset.tilewidth, (tileid // tileset.tileshigh) * tileset.tileheight, tileset.tilewidth, tileset.tileheight)

def draw_world(surface, world, frame, x, y, width, height):
    surface.fill(Color(168,168,168,255), Rect(x, y, width, height))

    for layer in world.map.tile_layers:
        index = 0
        for yt in range(world.map.tileshigh):
            for xt in range(world.map.tileswide):
                tileid = layer[index]
                src, rect = get_tile_image(world, frame, tileid)
                if src:
                    surface.blit(src,
                        (xt * world.map.tilewidth * world.map.width // width + x,
                         yt * world.map.tileheight * world.map.height // height + y),
                        rect)
                index += 1

def run(world, x, y, width, height):
    screen = pygame.display.get_surface()

    pygame.mouse.set_visible(False)

    draw_world(screen, world, 0, x, y, width, height)

    pygame.display.flip()

    while True:
        event = pygame.event.wait()
        
        if event.type == QUIT:
            return
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                return

def main(argv):
    if len(argv) == 1:
        print 'usage: python impgame.py <mapfile>'
        return 2

    map = impcore.Map()
    map.load_filename(argv[1])
    world = impcore.World(map)

    pygame.display.set_mode((map.width, map.height))

    run(world, 0, 0, map.width, map.height)

if __name__ == '__main__':
    sys.exit(main(sys.argv))

