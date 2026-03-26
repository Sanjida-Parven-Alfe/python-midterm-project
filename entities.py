import pygame
from typing import Tuple, Any

# Pixel art SHAPE for obstacles
SHAPE = [
    '  xxxxxxx',
    ' xxxxxxxxx',
    'xxxxxxxxxxx',
    'xxxxxxxxxxx',
    'xxxxxxxxxxx',
    'xxx     xxx',
    'xx       xx'
]


def load_image(path: str, target_size: Tuple[int, int] | None = None, trim: bool = False) -> pygame.Surface:
    """Load a PNG, optionally trim transparent area, then resize."""
    image = pygame.image.load(path).convert_alpha()
    if trim:
        bounds = image.get_bounding_rect()
        if bounds.width > 0 and bounds.height > 0:
            image = image.subsurface(bounds).copy()
    if target_size:
        image = pygame.transform.smoothscale(image, target_size)
    return image

class Entity(pygame.sprite.Sprite):
    """Base class for entities."""
    
    def __init__(self, pos: Tuple[int, int], color_or_img: Any) -> None:
        super().__init__()
        if isinstance(color_or_img, str):
            self.image = load_image(color_or_img)
        else:
            self.image = pygame.Surface((40, 40))
            self.image.fill(color_or_img)
        self.rect = self.image.get_rect(center=pos)
        self.health = 3

class Laser(Entity):
    """Base laser."""
    
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

class PlayerLaser(Laser):
    """Player upward laser."""
    def __init__(self, pos: Tuple[int, int], screen_height: int) -> None:
        super().__init__(pos, -8, screen_height, (255, 255, 255))

class EnemyLaser(Laser):
    """Enemy downward laser."""
    def __init__(self, pos: Tuple[int, int], screen_height: int) -> None:
        super().__init__(pos, 6, screen_height, (255, 100, 100))

class Enemy(Entity):
    """Enemy spaceship."""
    
    def __init__(self, size: int, img_path: str, x: int, y: int, screen_height: int, enemy_lasers: pygame.sprite.Group) -> None:
        super().__init__((x, y), img_path)
        self.image = load_image(img_path, (size, size))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = 2
        self.screen_height = screen_height
        self.enemy_lasers = enemy_lasers
        self.fire_cooldown = 2200
        self.fire_timer = 0
        self.fire_enabled = False
        self.fire_bullet_count = 1

    def update(self) -> None:
        self.rect.y += self.speed
        if self.rect.top > self.screen_height:
            self.kill()
        
        now = pygame.time.get_ticks()
        if self.fire_enabled and now - self.fire_timer > self.fire_cooldown:
            self.fire_timer = now
            self._shoot()

    def _shoot(self) -> None:
        count = max(1, self.fire_bullet_count)
        spacing = 12
        start_x = self.rect.centerx - ((count - 1) * spacing) // 2
        positions = [(start_x + i * spacing, self.rect.centery) for i in range(count)]
        for pos in positions:
            self.enemy_lasers.add(EnemyLaser(pos, self.screen_height))

class Ammo(Entity):
    """Ammo powerup drop."""
    
    def __init__(self, pos: Tuple[int, int], screen_height: int):
        super().__init__(pos, 'graphics/ammo.png')
        self.image = load_image('graphics/ammo.png', (22, 22), trim=True)
        self.rect = self.image.get_rect(center=pos)
        self.speed = 2
        self.screen_height = screen_height

    def update(self) -> None:
        self.rect.y += self.speed
        if self.rect.top > self.screen_height:
            self.kill()

class Obstacle:
    """Obstacle structure."""
    
    def __init__(self, block_size: int, img_path: str, x: int, y: int, obstacles: pygame.sprite.Group):
        self.blocks = pygame.sprite.Group()
        for row_index, row in enumerate(SHAPE):
            for col_index, col in enumerate(row):
                if col == 'x':
                    bx = x + col_index * block_size
                    by = y + row_index * block_size
                    block = Entity((bx, by), img_path)
                    block.image = load_image(img_path, (block_size, block_size), trim=True)
                    block.rect = block.image.get_rect(topleft=(bx, by))
                    block.health = 1
                    self.blocks.add(block)
        obstacles.add(*self.blocks)

class Player(Entity):
    """Player with multi-fire."""
    
    def __init__(self, pos: Tuple[int, int], constraint: int, speed: int, img_path: str, screen_height: int) -> None:
        super().__init__(pos, img_path)
        self.ship_paths = [f'graphics/spaceship-{i}.png' for i in range(1, 7)]
        self.ship_size = (72, 56)
        self.ship_index = 0
        self.image = load_image(self.ship_paths[self.ship_index], self.ship_size, trim=True)
        self.rect = self.image.get_rect(center=pos)
        self.speed = speed
        self.max_x_constraint = constraint
        self.screen_height = screen_height
        self.lasers = pygame.sprite.Group()
        self.ready = True
        self.laser_time = 0
        self.cooldown = 240
        self.fire_level = 1  # 1-3
        self.laser_sound = pygame.mixer.Sound('audio/laser.wav')
        self.laser_sound.set_volume(0.5)

    def get_input(self) -> None:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed

    def shoot(self) -> None:
        positions = [self.rect.center]
        if self.fire_level >= 2:
            positions = [(self.rect.centerx - 12, self.rect.centery), (self.rect.centerx + 12, self.rect.centery)]
        if self.fire_level >= 3:
            positions = [
                (self.rect.centerx - 14, self.rect.centery),
                self.rect.center,
                (self.rect.centerx + 14, self.rect.centery)
            ]
        for p in positions:
            self.lasers.add(PlayerLaser(p, self.screen_height))
        self.laser_sound.play()
        self.ready = False
        self.laser_time = pygame.time.get_ticks()

    def set_ship_by_level(self, level: int) -> None:
        target_index = max(0, min(level - 1, len(self.ship_paths) - 1))
        if target_index == self.ship_index:
            return
        center = self.rect.center
        self.ship_index = target_index
        self.image = load_image(self.ship_paths[self.ship_index], self.ship_size, trim=True)
        self.rect = self.image.get_rect(center=center)

    def update(self) -> None:
        self.get_input()
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > self.max_x_constraint:
            self.rect.right = self.max_x_constraint
        if not self.ready and pygame.time.get_ticks() - self.laser_time > self.cooldown:
            self.ready = True
        if self.ready:
            self.shoot()
        self.lasers.update()
