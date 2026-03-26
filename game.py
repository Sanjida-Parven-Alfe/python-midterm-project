import pygame
import random
from typing import List, Optional

from entities import Enemy, Player
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
        self.player = pygame.sprite.GroupSingle()
        self._spawn_player()

        self.enemies = pygame.sprite.Group()
        self.enemy_event = pygame.USEREVENT + 1
        pygame.time.set_timer(self.enemy_event, 900)

        self.all_lasers = pygame.sprite.Group()
        self.storage = ScoreStorage()
        self.ui = UIManager(self.screen_width, self.screen_height, self.storage)
        self.background = pygame.image.load("graphics/space.png").convert()
        self.hud_font = pygame.font.Font(None, 36)
        self.enemy_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]

    def _spawn_player(self) -> None:
        player_pos = (self.screen_width // 2, self.screen_height - 80)
        self.player.add(Player(player_pos, self.screen_width, 5, "graphics/player.png", self.screen_height))

    def _draw_background(self) -> None:
        tile_width, tile_height = self.background.get_size()
        for x_pos in range(0, self.screen_width, tile_width):
            for y_pos in range(0, self.screen_height, tile_height):
                self.screen.blit(self.background, (x_pos, y_pos))

    def _update_progression(self) -> None:
        self.level = max(1, (self.score // 50) + 1)
        spawn_delay = max(320, 900 - (self.level - 1) * 90)
        pygame.time.set_timer(self.enemy_event, spawn_delay)
        for enemy in self.enemies:
            enemy.speed = min(8, 2 + self.level)

    def reset_round(self) -> None:
        self.score = 0
        self.level = 1
        self.game_over = False
        self.enemies.empty()
        self.all_lasers.empty()
        self.player.empty()
        self._spawn_player()
        pygame.time.set_timer(self.enemy_event, 900)

    def create_enemy(self) -> None:
        """Spawn an enemy with speed based on the current level."""
        size = 40
        color = self.enemy_colors[self.score // 100 % len(self.enemy_colors)]
        x = random.randint(20, self.screen_width - size - 20)
        enemy = Enemy(size, color, x, 0, self.screen_height)
        enemy.speed = min(8, 2 + self.level)
        self.enemies.add(enemy)

    def _sync_player_lasers(self) -> None:
        player_sprite = self.player.sprite
        if player_sprite is None:
            return
        for laser in player_sprite.lasers.sprites():
            if laser not in self.all_lasers:
                self.all_lasers.add(laser)

    def check_collisions(self) -> None:
        """Handle gameplay collisions and game over state."""
        for laser in self.all_lasers.copy():
            hits = pygame.sprite.spritecollide(laser, self.enemies, False)
            for enemy in hits:
                enemy.health -= 1
                laser.kill()
                if enemy.health <= 0:
                    enemy.kill()
                    self.score += 10

        player_sprite = self.player.sprite
        if player_sprite:
            hits = pygame.sprite.spritecollide(player_sprite, self.enemies, False)
            for enemy in hits:
                player_sprite.health -= 1
                enemy.kill()
                if player_sprite.health <= 0:
                    self.game_over = True
                    self.ui.set_game_over(self.score)

    def _draw_hud(self) -> None:
        player_sprite = self.player.sprite
        health = player_sprite.health if player_sprite else 0
        hud_lines = [
            f"Score: {self.score}",
            f"Level: {self.level}",
            f"Health: {health}",
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

            self.player.update()
            self.enemies.update()
            self._sync_player_lasers()
            self.all_lasers.update()
            self.check_collisions()

            self._draw_background()
            self.player.draw(self.screen)
            self.enemies.draw(self.screen)
            self.all_lasers.draw(self.screen)
            self._draw_hud()
        else:
            self.screen.fill((0, 0, 0))
            self.ui.draw(self.screen, self.score if self.game_over else None)

        return None

