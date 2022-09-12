from random import choice
import pygame
from settings import *
from support import *
from pytmx.util_pygame import load_pygame

class SoilTile(pygame.sprite.Sprite):
    def __init__(self, pos, surface, groups):
        super().__init__(groups)
        self.image = surface
        self.rect = self.image.get_rect(topleft = pos)
        self.z = LAYERS['soil']

class WaterTile(pygame.sprite.Sprite):
    def __init__(self, pos, surface, groups):
        super().__init__(groups)
        self.image = surface
        self.rect = self.image.get_rect(topleft = pos)
        self.z = LAYERS['soil water']

class Plant(pygame.sprite.Sprite):
    def __init__(self, plant_type, groups, soil, watered):
        super().__init__(groups)
        
        # Setup
        self.plant_type = plant_type
        self.frames = import_folder(f'../graphics/fruit/{plant_type}')
        self.soil = soil
        self.check_watered = watered

        # Plant Growing
        self.age = 0
        self.max_age = len(self.frames) - 1
        self.grow_speed = GROW_SPEED[plant_type]
        self.harvestable = False

        # Sprite Setup
        self.image = self.frames[int(self.age)]
        self.y_offset = -16 if plant_type == 'corn' else -8
        self.rect = self.image.get_rect(midbottom = soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))
        self.z = LAYERS['ground plant']



    def grow(self):
        if self.check_watered(self.rect.center):
            self.age += self.grow_speed

            if int(self.age) > 0:
                self.z = LAYERS['main']
                self.hitbox = self.rect.copy().inflate(-26, -self.rect.height * 0.4)

            if self.age >= self.max_age:
                self.age = self.max_age
                self.harvestable = True

            self.image = self.frames[int(self.age)]
            self.rect = self.image.get_rect(midbottom = self.soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))

class SoilLayer:
    def __init__(self, all_sprites, collision_sprites):

        # Sprite Groups
        self.all_sprites = all_sprites
        self.collision_sprites = collision_sprites
        self.soil_sprites = pygame.sprite.Group()
        self.water_sprites = pygame.sprite.Group()
        self.plant_sprites = pygame.sprite.Group()

        # Graphics
        self.soil_surfaces = import_folder_dict('../graphics/soil/')
        self.water_surfaces = import_folder('../graphics/soil_water')

        self.create_soil_grid()
        self.create_hit_rects()

    def create_soil_grid(self):
        ground = pygame.image.load('../graphics/world/ground.png')
        h_tiles, v_tiles = ground.get_width() // TILE_SIZE, ground.get_height() // TILE_SIZE

        self.grid = [[[] for col in range(h_tiles)] for row in range(v_tiles)]
        for x, y, _ in load_pygame('../data/map.tmx').get_layer_by_name('Farmable').tiles():
            self.grid[y][x].append('F')
    
    def create_hit_rects(self):
        self.hit_rects = []
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'F' in cell:
                    x = index_col * TILE_SIZE
                    y = index_row * TILE_SIZE
                    rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                    self.hit_rects.append(rect)

    def get_hit(self, point):
        for rect in self.hit_rects:
            if rect.collidepoint(point):
                x = rect.x // TILE_SIZE
                y = rect.y // TILE_SIZE
                if 'F' in self.grid[y][x]:
                    self.grid[y][x].append('X')
                    self.create_soil_tiles()
                    if self.raining:
                        self.water_all()

    def water(self, target_pos):
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(target_pos):

                x = soil_sprite.rect.x // TILE_SIZE
                y = soil_sprite.rect.y // TILE_SIZE
                self.grid[y][x].append('W')
                
                water_surface = choice(self.water_surfaces)
                WaterTile(
                    pos = soil_sprite.rect.topleft,
                    surface = water_surface,
                    groups = [self.all_sprites, self.water_sprites]
                )

    def water_all(self):
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'X' in cell and 'W' not in cell:
                    cell.append('W')
                    x = index_col * TILE_SIZE
                    y = index_row * TILE_SIZE
                    WaterTile(
                        pos = (x, y),
                        surface = choice(self.water_surfaces),
                        groups = [self.all_sprites, self.water_sprites]
                    )

    def remove_water(self):
        # Destroy all water sprites
        for sprite in self.water_sprites:
            sprite.kill()
        
        # Clean up the grid
        for row in self.grid:
            for cell in row:
                if 'W' in cell:
                    cell.remove('W')

    def check_watered(self, pos):
        x = pos[0] // TILE_SIZE
        y = pos[1] // TILE_SIZE
        cell = self.grid[y][x]
        is_watered = 'W' in cell 
        return is_watered

    def plant_seed(self, target_pos, seed):
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(target_pos):

                x = soil_sprite.rect.x // TILE_SIZE
                y = soil_sprite.rect.y // TILE_SIZE

                if 'P' not in self.grid[y][x]:
                    self.grid[y][x].append('P')
                    Plant(
                        plant_type = seed, 
                        groups = [self.all_sprites, self.plant_sprites, self.collision_sprites], 
                        soil = soil_sprite,
                        watered = self.check_watered
                        )

    def update_plants(self):
        for plant in self.plant_sprites.sprites():
            plant.grow()

    def create_soil_tiles(self):
        self.soil_sprites.empty()
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'X' in cell:
                    
                    # Tile Options
                    t = 'X' in self.grid[index_row - 1][index_col]
                    b = 'X' in self.grid[index_row + 1][index_col]
                    r = 'X' in row[index_col + 1]
                    l = 'X' in row[index_col - 1]

                    tile_type = 'o'

                    # All Sides
                    if all((t,r,b,l)): tile_type = 'x'

                    # Horizontal Tiles Only
                    if l and not any((t,r,b)): tile_type = 'r'
                    if r and not any((t,b,l)): tile_type = 'l'
                    if r and l and not any((t,b)): tile_type = 'lr'

                    # Vertical Tiles Only
                    if t and not any((r,b,l)): tile_type = 'b'
                    if b and not any((t,r,l)): tile_type = 't'
                    if t and b and not any((r,l)): tile_type = 'tb'

                    # Corners
                    if l and b and not any((t,r)): tile_type = 'tr'
                    if r and b and not any((t,l)): tile_type = 'tl'
                    if l and t and not any((r,b)): tile_type = 'br'
                    if r and t and not any((b,l)): tile_type = 'bl'
                    
                    # T Shapes
                    if all((t,r,b)) and not l: tile_type = 'tbr'
                    if all((t,l,b)) and not r: tile_type = 'tbl'
                    if all((t,r,l)) and not b: tile_type = 'lrb'
                    if all((r,b,l)) and not t: tile_type = 'lrt'


                    SoilTile(
                        pos = (index_col * TILE_SIZE, index_row * TILE_SIZE),
                        surface = self.soil_surfaces[tile_type],
                        groups = [self.all_sprites, self.soil_sprites]
                    ) 
