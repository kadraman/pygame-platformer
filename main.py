#!/usr/bin/env python
"""
This is an example PyGame animation that uses "delta-time" to ensure that
screen updates are unaffected by framerate. There are three sprites which
move at different velocities (in this case pixels per second). It estimates
the expected time for each of the sprites to cross the screen and displays
the actual time. They should be approximately the same and more importantly
the same in any execution environment.
"""

import os
import sys
import time
import pygame as pg

from decimal import Decimal

vector = pg.math.Vector2 


CAPTION = "Platformer"
SCREEN_SIZE = (600, 400)  # size of screen we are working with
BACKGROUND_COLOR = (100, 200, 200)
DEBUG_OVERLAY_SIZE = (300, 200)
DEBUG_OVERLAY_BACKGROUND_COLOR = (0, 0, 0, 200)
TRANSPARENT = (0, 0, 0, 0)
FPS = 60  # CHANGE ME - to your preferred frame rate

SPRITE_SIZE = (20, 40)
SPRITE_VELOCITY = (100, 0)  # This sprite moves at ~ 100 pixels per second

PLAYER_ACCELERATION = SCREEN_SIZE[0] / 1000 # 0.6
PLAYER_FRICTION = -0.12
PLAYER_JUMP = -10 # how many pixels should the player jump


class DebugOverlay(pg.sprite.Sprite):
    """
    This sprite provides a useful overlay of important information.
    Not really a sprite but we can add it to a SpriteGroup for updates.
    """
    def __init__(self, position, size, color):
        super(DebugOverlay, self).__init__()
        self.size = size
        self.color = color
        self.image = pg.Surface(self.size).convert_alpha()
        self.image.fill(self.color)
        self.rect = self.image.get_rect(center=position)
        self.font = pg.font.SysFont('Consolas', 12)
        self.position = position
        self.start_text_y = self.position[1] + 5
        self.start_time = time.time()
        self.time_now = self.start_time
        self.debug_text = []

    def update(self, keys, screen_rect, dt):
        """
        Update the debug string with latest information.
        """
        self.time_now = time.time()
        self.debug_text = [
            "width: " + str(SCREEN_SIZE[0]),
            "height:" + str(SCREEN_SIZE[1]),
            "FPS: " + str(FPS),
            "dt: " + str(dt),
            "time(s): " + str(Decimal('%2f' % (self.time_now - self.start_time)))
        ]

    def draw(self, surface):
        """
        Basic draw function.
        """
        start_y = self.start_text_y
        surface.blit(self.image, self.rect)
        for string in self.debug_text:
            rect = self.font.render(string, True, (255, 255, 255))
            surface.blit(rect, (5, start_y))
            start_y += 15


class Player(pg.sprite.Sprite):
    """
    This sprite is our player that will move across the screen.
    """
    def __init__(self, app, position, size, color, velocity):
        super(Player, self).__init__()
        self.app = app
        self.direction = 1
        self.size = size
        self.color = color
        self.position = position
        self.velocity = vector(0,0)
        self.acceleration = vector(0,0)
        self.image = pg.Surface(self.size).convert_alpha()
        self.image.fill(self.color)
        self.rect = self.image.get_rect(topright=position)

    def update(self, keys, screen_rect, dt):
        """
        Update accepts an argument dt (time delta between frames).
        Adjustments to position must be multiplied by this delta.
        Set the rect to true_pos once adjusted (automatically converts to int).
        """
        self.acceleration = vector(0, 0.5)
        if keys[pg.K_RIGHT]:
            self.acceleration.x = PLAYER_ACCELERATION
        elif keys[pg.K_LEFT]:
            self.acceleration.x = -PLAYER_ACCELERATION
        else:
            self.acceleration.x = 0
        if keys[pg.K_SPACE]:
            self.jump()        

        self.acceleration.x += self.velocity.x * PLAYER_FRICTION
        self.velocity += self.acceleration
        self.position += self.velocity + vector(0.5, 0.5) * vector(dt,dt) * self.acceleration    
        self.rect.midbottom = self.position  

        # are we on a platform ?
        result = pg.sprite.spritecollide(self, self.app.all_platforms, False)
        if result:
            self.fix_top(result[0].rect.top + 1)

        # have we reached the edge of the screen yet?
        if self.reached_edge():
            self.acceleration.x = 0

        self.clamp(screen_rect)

        # TODO: camera

    def clamp(self, screen_rect):
        """
        Clamp the rect to the screen if needed and reset true_pos to the
        rect position so they don't lose sync.
        """
        if not screen_rect.contains(self.rect):
            self.rect.clamp_ip(screen_rect)
            self.position = vector(self.rect.midbottom)

    def draw(self, surface):
        """
        Basic draw function.
        """
        surface.blit(self.image, self.rect)

    def jump(self):
        result = pg.sprite.spritecollide(self, self.app.all_platforms, False)
        if result:
            self.velocity.y = PLAYER_JUMP

    def fix_top(self, top):
        self.position.y = top + 1
        self.velocity.y = 0

    def reached_edge(self):
        """
        Simple check if right edge is touching right of screen
        """
        return self.rect.right >= SCREEN_SIZE[0]


class Platform(pg.sprite.Sprite):
    def __init__(self, size, position, color):
        super().__init__()
        self.size = size
        self.position = position
        self.color = color
        self.image = pg.Surface(self.size).convert_alpha()
        self.image.fill(self.color)
        #self.rect = self.image.get_rect(center = (SCREEN_SIZE[0]/2, SCREEN_SIZE[1] - 10))
        self.rect = self.image.get_rect(topright=position)


    def draw(self, surface):
        """
        Basic draw function.
        """
        surface.blit(self.image, self.rect)


class App(object):
    """
    Class responsible for program control flow.
    """
    def __init__(self):
        self.screen = pg.display.get_surface()
        self.screen_rect = self.screen.get_rect()
        self.clock = pg.time.Clock()
        self.font = pg.font.SysFont('Consolas', 14)
        self.fps = FPS
        self.start_time = time.time()
        self.final_time = 0
        self.time_now = self.start_time
        self.done = False
        self.keys = pg.key.get_pressed()
        self.player = Player(self, vector(0, 300), SPRITE_SIZE, (255, 0, 0), SPRITE_VELOCITY)
        self.platform1 = Platform((SCREEN_SIZE[0], 10), (SCREEN_SIZE[0], SCREEN_SIZE[1] - 10), (100, 100, 200))
        self.platform2 = Platform((200, 10), (SCREEN_SIZE[0]-200, 300), (100, 100,200))
        self.all_platforms = pg.sprite.Group()
        self.all_platforms.add(self.platform1)
        self.all_platforms.add(self.platform2)
        self.all_sprites = pg.sprite.Group()
        self.all_sprites.add(self.player)
        self.all_sprites.add(self.platform1)
        self.all_sprites.add(self.platform2)
        self.debug_overlay = DebugOverlay((0, 0), DEBUG_OVERLAY_SIZE, DEBUG_OVERLAY_BACKGROUND_COLOR)

    def event_loop(self):
        """
        Basic event loop.
        """
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.done = True
            elif event.type in (pg.KEYDOWN, pg.KEYUP):
                self.keys = pg.key.get_pressed()

    def update(self, dt):
        """
        Update all the sprites
        """
        self.player.update(self.keys, self.screen_rect, dt)
        self.debug_overlay.update(self.keys, self.screen_rect, dt)

    def draw(self):
        """
        Basic draw function.
        """
        self.screen.fill(BACKGROUND_COLOR)
        for entity in self.all_sprites:
            entity.draw(self.screen)
        self.debug_overlay.draw(self.screen)
        pg.display.update()

    def game_loop(self):
        """
        Simple game loop where we use the return value of the call to self.clock.tick
        to get the time delta between frames and pass it to all our sprites.
        """
        dt = 0
        self.clock.tick(self.fps)
        while not self.done:
            self.event_loop()
            self.update(dt)
            self.draw()
            dt = self.clock.tick(self.fps) / 1000.0

def main():
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pg.init()
    pg.display.set_caption(CAPTION)
    pg.display.set_mode(SCREEN_SIZE)
    App().game_loop()
    pg.quit()
    sys.exit()


if __name__ == "__main__":
    main()
