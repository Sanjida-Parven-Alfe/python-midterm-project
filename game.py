import pygame
import random
from typing import List, Optional

from entities import Ammo, Enemy, Player
from storage import ScoreStorage
from ui_manager import UIManager


class Game:
    """Own gameplay flow, enemy spawning, collisions and HUD rendering."""

    def __init__(self, screen: pygame.Surface, screen_width: int, screen_height: int) -> None:
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.score = 0
        self.level = 1
        self.game_over = False
        self.last_powerup_score = 0
        self.last_ship_powerup_score = 0
        self.ship_count = 1
        
        self.background = pygame.image.load("graphics/space.png").convert()
        self.hud_font = pygame.font.Font(None, 36)
        
        # Audio setup
        pygame.mixer.init()
        self.laser_sound = pygame.mixer.Sound("audio/laser.wav")
        self.laser_sound.set_volume(0.3)
        self.explosion_sound = pygame.mixer.Sound("audio/explosion.wav")
        self.explosion_sound.set_volume(0.4)
        pygame.mixer.music.load("audio/music.wav")
        pygame.mixer.music.set_volume(0.3)
        pygame.mixer.music.play(-1)  # Loop background music
        
        self.enemy_event = pygame.USEREVENT + 1
        pygame.time.set_timer(self.enemy_event, 1200)

        self.storage = ScoreStorage()
        self.ui = UIManager(self.screen_width, self.screen_height, self.storage)
        
        # Groups for game entities
        self.player = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.all_lasers = pygame.sprite.Group()
        self.bullet_powerups = pygame.sprite.Group()
        self.ship_powerups = pygame.sprite.Group()
        
        self._spawn_player()

    def _spawn_player(self) -> None:
        self.player.empty()
        center_x = self.screen_width // 2
        center_y = self.screen_height - 80
        
        # Formation offsets based on ship count (Increased spacing for clarity)
        offsets = {
            1: [0],
            2: [-60, 60],
            3: [-120, 0, 120],
            4: [-180, -60, 60, 180]
        }
        
        current_offsets = offsets.get(self.ship_count, [0])
        for offset in current_offsets:
            ship = Player((center_x + offset, center_y), self.screen_width, 5, "graphics/spaceship-1.png", self.screen_height)
            ship.set_ship_by_level(self.level)
            self.player.add(ship)

    def _draw_background(self) -> None:
        tile_width, tile_height = self.background.get_size()
        for x_pos in range(0, self.screen_width, tile_width):
            for y_pos in range(0, self.screen_height, tile_height):
                self.screen.blit(self.background, (x_pos, y_pos))

    def _update_progression(self) -> None:
        # Level changes every 100 score
        new_level = max(1, (self.score // 100) + 1)
        if new_level != self.level:
            self.level = new_level
            for ship in self.player:
                ship.set_ship_by_level(self.level)
            # Scaling: spawn delay decreases with level (start easier)
            spawn_delay = max(250, 1200 - (self.level - 1) * 150)
            pygame.time.set_timer(self.enemy_event, spawn_delay)

        # Bullet Power-up spawning every 20 score (Max level 3)
        current_fire_level = 1
        if self.player.sprites():
            current_fire_level = self.player.sprites()[0].fire_level
            
        if self.score > 0 and self.score % 20 == 0 and self.score > self.last_powerup_score:
            if current_fire_level < 3:
                self.last_powerup_score = self.score
                from entities import BulletPowerUp
                pos = (random.randint(40, self.screen_width - 40), -20)
                self.bullet_powerups.add(BulletPowerUp(pos, self.screen_height))

        # Ship Power-up spawning every 50 score (Max 4 ships)
        if self.score > 0 and self.score % 50 == 0 and self.score > self.last_ship_powerup_score:
            if len(self.player) < 4:
                self.last_ship_powerup_score = self.score
                from entities import ShipPowerUp
                pos = (random.randint(40, self.screen_width - 40), -20)
                self.ship_powerups.add(ShipPowerUp(pos, self.screen_height))

    def reset_round(self) -> None:
        self.score = 0
        self.level = 1
        self.last_powerup_score = 0
        self.last_ship_powerup_score = 0
        self.ship_count = 1
        self.game_over = False
        self.enemies.empty()
        self.all_lasers.empty()
        self.bullet_powerups.empty()
        self.ship_powerups.empty()
        self.player.empty()
        self._spawn_player()
        pygame.time.set_timer(self.enemy_event, 1200)

    def create_enemy(self) -> None:
        """Spawn an enemy with speed based on the current level."""
        size = 40
        enemy_imgs = ["graphics/green.png", "graphics/red.png", "graphics/yellow.png"]
        img_path = random.choice(enemy_imgs)
        x = random.randint(20, self.screen_width - size - 20)
        enemy = Enemy(size, img_path, x, 0, self.screen_height, self.all_lasers)
        # Scaling: speed increases with level (start easier)
        enemy.speed = min(9, 1 + self.level)
        self.enemies.add(enemy)

    def _sync_player_lasers(self) -> None:
        for player_sprite in self.player.sprites():
            for laser in player_sprite.lasers.sprites():
                if laser not in self.all_lasers:
                    self.all_lasers.add(laser)

    def check_collisions(self) -> None:
        """Handle gameplay collisions and game over state."""
        # Laser vs Enemy (Copy group to avoid mutation issues during iteration)
        lasers = self.all_lasers.sprites()
        for laser in lasers:
            hits = pygame.sprite.spritecollide(laser, self.enemies, False)
            for enemy in hits:
                enemy.health -= 1
                laser.kill()
                if enemy.health <= 0:
                    enemy.kill()
                    self.explosion_sound.play()
                    self.score += 10

        # Player vs Objects
        ships = self.player.sprites()
        for player_sprite in ships:
            # Enemy vs Player
            hits = pygame.sprite.spritecollide(player_sprite, self.enemies, False)
            for enemy in hits:
                player_sprite.kill()
                enemy.kill()
                self.explosion_sound.play()
                # Update ship count for spawning logic if a ship is lost
                if len(self.player) == 0:
                    self.game_over = True
                    self.ui.set_game_over(self.score)
            
            # Bullet Powerup vs Player
            bp_hits = pygame.sprite.spritecollide(player_sprite, self.bullet_powerups, True)
            for powerup in bp_hits:
                for ship in self.player:
                    ship.fire_level = min(3, ship.fire_level + 1)
            
            # Ship Powerup vs Player
            sp_hits = pygame.sprite.spritecollide(player_sprite, self.ship_powerups, True)
            for powerup in sp_hits:
                if len(self.player) < 4:
                    self.ship_count = len(self.player) + 1
                    self._spawn_player()

    def _draw_hud(self) -> None:
        hud_lines = [
            f"Score: {self.score}",
            f"Health: {len(self.player)}",
        ]
        for index, line in enumerate(hud_lines):
            text_surface = self.hud_font.render(line, True, (255, 255, 255))
            self.screen.blit(text_surface, (12, 12 + index * 34))

    def run(self, events: List[pygame.event.Event]) -> Optional[str]:
        """Advance one frame of the game and UI state."""
        prev_state = self.ui.get_state()
        action: Optional[str] = None
        for event in events:
            event_action = self.ui.handle_event(event)
            if event_action == "quit":
                action = "quit"

        if prev_state != "playing" and self.ui.get_state() == "playing":
            self.reset_round()

        if action == "quit":
            return "quit"

        if self.ui.get_state() == "playing":
            self._update_progression()
            for event in events:
                if event.type == self.enemy_event:
                    self.create_enemy()

            # Handle collective player movement
            keys = pygame.key.get_pressed()
            move_dir = 0
            if keys[pygame.K_LEFT]:
                # Can only move left if ALL ships are inside the left screen boundary
                if all(ship.rect.left > 0 for ship in self.player):
                    move_dir = -1
            elif keys[pygame.K_RIGHT]:
                # Can only move right if ALL ships are inside the right screen boundary
                if all(ship.rect.right < self.screen_width for ship in self.player):
                    move_dir = 1

            laser_count_before = len(self.all_lasers)
            self.player.update(move_dir, self.all_lasers)
            if len(self.all_lasers) > laser_count_before:
                self.laser_sound.play()
            self.enemies.update()
            self.bullet_powerups.update()
            self.ship_powerups.update()
            self.all_lasers.update()
            self.check_collisions()

            self._draw_background()
            self.player.draw(self.screen)
            self.enemies.draw(self.screen)
            self.bullet_powerups.draw(self.screen)
            self.ship_powerups.draw(self.screen)
            self.all_lasers.draw(self.screen)
            self._draw_hud()
        else:
            self.screen.fill((0, 0, 0))
            self.ui.draw(self.screen, self.score if self.game_over else None)

        return None

