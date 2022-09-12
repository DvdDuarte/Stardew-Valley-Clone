import pygame
from settings import *
from support import import_folder
from sprites import Generic
from timer import Timer
from random import choice, randint

class Drop(Generic):
    def __init__(self, moving, pos, surface, groups, z):

        # General Setup
        super().__init__(pos, surface, groups, z)
        self.lifetime = randint(400,500)
        self.start_time = pygame.time.get_ticks()

        # Moving
        self.moving = moving
        if self.moving:
            self.pos = pygame.math.Vector2(self.rect.topleft)
            self.direction = pygame.math.Vector2(-2,4)
            self.speed = randint(200,250)

    def update(self, dt):

        # Movement
        if self.moving:
            self.pos += self.direction * self.speed * dt
            self.rect.topleft = (round(self.pos.x), round(self.pos.y))

        # Timer
        if pygame.time.get_ticks() - self.start_time >= self.lifetime:
            self.kill()


class Rain:
    def __init__ (self, all_sprites):
        self.all_sprites = all_sprites
        self.rain_drops = import_folder('../graphics/rain/drops')
        self.rain_floor = import_folder('../graphics/rain/floor')
        self.floor_w, self.floor_h = pygame.image.load('../graphics/world/ground.png').get_size()

    def create_floor(self):
        Drop(
            moving = False, 
            pos = (randint(0, self.floor_w), randint(0, self.floor_h)), 
            surface = choice(self.rain_floor), 
            groups = self.all_sprites, 
            z = LAYERS['rain floor']
            )
    
    def create_drops(self):
        Drop(
            moving = True, 
            pos = (randint(0, self.floor_w), randint(0, self.floor_h)), 
            surface = choice(self.rain_drops), 
            groups = self.all_sprites, 
            z = LAYERS['rain drops']
            )
    
    def update(self):
        self.create_floor()
        self.create_drops()