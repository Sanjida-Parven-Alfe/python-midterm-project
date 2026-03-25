import pygame
import random
from typing import Optional, List
from entities import Player, Enemy, Laser
from storage import ScoreStorage
from ui_manager import UIManager

class Game:
    """Manager class for main game loop, collisions, enemy waves.
    Integrates UIManager and ScoreStorage."""
    
    def __init__(self, screen: pygame.Surface, screen_width: int, screen_height: int) -> None:
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.score = 0
        self.game_over = False
        self.player = pygame.sprite.GroupSingle()
        self._spawn_player()
        
        # Enemies
        self.enemies = pygame.sprite.Group()
        self.enemy_event = pygame.USEREVENT + 1
        pygame.time.set_timer(self.enemy_event, 1000)
        
        # All lasers
        self.all_lasers = pygame.sprite.Group()
        
        # Storage & UI
        self.storage = ScoreStorage()
        self.ui = UIManager(self.screen_width, self.screen_height, self.storage)
        
        # Enemy colors
        self.enemy_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]

    def _spawn_player(self) -> None:
        player_pos = (self.screen_width // 2, self.screen_height - 80)
        self.player.add(Player(player_pos, self.screen_width, 5, 'graphics/player.png', self.screen_height))

    def reset_round(self) -> None:
        self.score = 0
        self.game_over = False
        self.enemies.empty()
        self.all_lasers.empty()
        self.player.empty()
        self._spawn_player()

    def create_enemy(self) -> None:
        """Spawn single enemy."""
        size = 40
        color = self.enemy_colors[self.score // 100 % len(self.enemy_colors)]
        x = random.randint(0, self.screen_width - size)
        enemy = Enemy(size, color, x, 0, self.screen_height)
        self.enemies.add(enemy)

    def check_collisions(self) -> None:
        """Handle collisions."""
        # Laser hits enemy
        for laser in self.all_lasers:
            hits = pygame.sprite.spritecollide(laser, self.enemies, False)
            for enemy in hits:
                enemy.health -= 1
                laser.kill()
                if enemy.health <= 0:
                    enemy.kill()
                    self.score += 10
        
        # Enemy hits player
        if self.player.sprite:
            hits = pygame.sprite.spritecollide(self.player.sprite, self.enemies, False)
            for enemy in hits:
                self.player.sprite.health -= 1
                enemy.kill()
                if self.player.sprite.health <= 0:
                    self.game_over = True
                    self.ui.set_game_over(self.score)

    def run(self, events: List[pygame.event.Event]) -> Optional[str]:
        """Run game update."""
        prev_state = self.ui.get_state()
        action: Optional[str] = None
        for event in events:
            event_action = self.ui.handle_event(event)
            if event_action == 'quit':
                action = 'quit'

        if prev_state != 'playing' and self.ui.get_state() == 'playing':
            self.reset_round()

        if action == 'quit':
            return 'quit'

        if self.ui.get_state() == 'playing':
            # Spawn enemies
            for event in events:
                if event.type == self.enemy_event:
                    self.create_enemy()
            
            self.player.update()
            self.enemies.update()
            self.all_lasers.add(self.player.sprite.lasers)
            self.all_lasers.update()
            self.check_collisions()
            
            # Draw game
            self.screen.fill((0, 0, 0))
            self.player.draw(self.screen)
            self.enemies.draw(self.screen)
            self.all_lasers.draw(self.screen)
            
            # UI overlay
            font = pygame.font.Font(None, 36)
            score_text = font.render(f'Score: {self.score}', True, (255, 255, 255))
            self.screen.blit(score_text, (10, 10))
            health_text = font.render(f'Health: {self.player.sprite.health}', True, (255, 0, 0))
            self.screen.blit(health_text, (10, 50))
        else:
            self.screen.fill((0, 0, 0))

            # Draw non-game screens from UI layer.
            self.ui.draw(self.screen, self.score if self.game_over else None)
        
        return None  # No quit

