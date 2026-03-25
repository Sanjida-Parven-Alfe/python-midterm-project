import pygame
from typing import Tuple, Any

# Enemy shape design (optional pixel art)
SHAPE = [
    '  xxxxxxx',
    ' xxxxxxxxx',
    'xxxxxxxxxxx',
    'xxxxxxxxxxx',
    'xxxxxxxxxxx',
    'xxx     xxx',
    'xx       xx'
]

class Entity(pygame.sprite.Sprite):
    """Base class for all game entities (Player, Enemy, Laser) with health."""
    
    def __init__(self, pos: Tuple[int, int], color_or_img: Any) -> None:
        super().__init__()
        if isinstance(color_or_img, str):
            self.image = pygame.image.load(color_or_img).convert_alpha()
        else:
            self.image = pygame.Surface((40, 40))
            self.image.fill(color_or_img)
        self.rect = self.image.get_rect(center=pos)
        self.health = 3

class Laser(Entity):
    """Laser class for player shooting."""
    
    def __init__(self, pos: Tuple[int, int], speed: int, screen_height: int, color: tuple) -> None:
        super().__init__(pos, color)
        self.image = pygame.Surface((4, 20))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=pos)
        self.speed = speed
        self.screen_height = screen_height

    def update(self) -> None:
        self.rect.y += self.speed
        if self.rect.y <= -50 or self.rect.y >= self.screen_height + 50:
            self.kill()

class Enemy(Entity):
    """Enemy class for space shooter obstacles."""
    
    def __init__(self, size: int, color: tuple, x: int, y: int, screen_height: int) -> None:
        super().__init__((x, y), color)
        self.image = pygame.Surface((size, size))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = 2
        self.screen_height = screen_height

    def update(self) -> None:
        self.rect.y += self.speed
        if self.rect.top > self.screen_height:
            self.kill()

class Player(Entity):
    """Player class with control, shooting, health."""
    
    def __init__(self, pos: Tuple[int, int], constraint: int, speed: int, img_path: str, screen_height: int) -> None:
        super().__init__(pos, img_path)
        self.speed = speed
        self.max_x_constraint = constraint
        self.screen_height = screen_height
        self.lasers = pygame.sprite.Group()
        self.ready = True
        self.laser_time = 0
        self.cooldown = 300

    def get_input(self) -> None:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_SPACE] and self.ready:
            self.lasers.add(Laser(self.rect.center, -8, self.screen_height, (255, 255, 255)))
            self.ready = False
            self.laser_time = pygame.time.get_ticks()

    def update(self) -> None:
        self.get_input()
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > self.max_x_constraint:
            self.rect.right = self.max_x_constraint
        if not self.ready and pygame.time.get_ticks() - self.laser_time > self.cooldown:
            self.ready = True
        self.lasers.update()

