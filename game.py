import pygame
import random
from typing import Optional, List
from entities import Player, Enemy, Laser, Obstacle, Ammo
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
        self.space_bg = pygame.image.load('graphics/space.png').convert()
        
        # Enemies
        self.enemies = pygame.sprite.Group()
        self.enemy_event = pygame.USEREVENT + 1
        pygame.time.set_timer(self.enemy_event, 800)
        
        # Groups
        self.player_lasers = pygame.sprite.Group()
        self.enemy_lasers = pygame.sprite.Group()
        self.ammo_drops = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.obstacle_paths = ['graphics/green.png', 'graphics/red.png', 'graphics/yellow.png', 'graphics/extra.png']
        self.next_obstacle_score = 20
        self._create_obstacles()
        
        self.level = 1
        
        # Storage & UI
        self.storage = ScoreStorage()
        self.ui = UIManager(self.screen_width, self.screen_height, self.storage)
        
        # Audio
        self.music = pygame.mixer.Sound('audio/music.wav')
        self.music.set_volume(0.2)
        self.music.play(loops=-1)
        self.explosion_sound = pygame.mixer.Sound('audio/explosion.wav')
        self.explosion_sound.set_volume(0.3)

    def _spawn_player(self) -> None:
        player_pos = (self.screen_width // 2, self.screen_height - 80)
        self.player.add(Player(player_pos, self.screen_width, 5, 'graphics/spaceship-1.png', self.screen_height))

    def _create_obstacles(self) -> None:
        """Create 4 obstacle groups at bottom."""
        block_size = 6
        y_start = self.screen_height - 120
        for i in range(4):
            x_start = i * (self.screen_width // 4) + 20
            img_path = self.obstacle_paths[i % len(self.obstacle_paths)]
            obs = Obstacle(block_size, img_path, x_start, y_start, self.obstacles)

    def _add_bonus_obstacle(self) -> None:
        block_size = 6
        y_start = self.screen_height - 120
        x_start = random.randint(20, self.screen_width - 100)
        img_path = random.choice(self.obstacle_paths)
        Obstacle(block_size, img_path, x_start, y_start, self.obstacles)

    def _get_enemy_fire_bullet_count(self) -> int:
        # 0-49: no fire, 50-74: 1, 75-99: 2, 100-149: 4, 150+: 6
        if self.score < 50:
            return 0
        if self.score < 75:
            return 1
        if self.score < 100:
            return 2
        if self.score < 150:
            return 4
        return 6

    def _get_enemy_fire_cooldown(self) -> int:
        # Start slower, then become faster as level increases.
        return max(650, 2200 - (self.level - 1) * 260)

    def _update_progression(self) -> None:
        # Level up every 100 score and switch spaceship image (up to spaceship-6).
        self.level = min((self.score // 100) + 1, 6)
        if self.player.sprite:
            self.player.sprite.set_ship_by_level(self.level)
            if self.score >= 80:
                self.player.sprite.fire_level = 3
            elif self.score >= 40:
                self.player.sprite.fire_level = 2
            else:
                self.player.sprite.fire_level = 1

        # Add one more obstacle every 20 score.
        while self.score >= self.next_obstacle_score:
            self._add_bonus_obstacle()
            self.next_obstacle_score += 20

        enemy_bullet_count = self._get_enemy_fire_bullet_count()
        enemy_fire_cooldown = self._get_enemy_fire_cooldown()
        for enemy in self.enemies:
            enemy.fire_enabled = enemy_bullet_count > 0
            enemy.fire_bullet_count = max(1, enemy_bullet_count)
            enemy.fire_cooldown = enemy_fire_cooldown

    def reset_round(self) -> None:
        self.score = 0
        self.game_over = False
        self.level = 1
        self.next_obstacle_score = 20
        self.enemies.empty()
        self.player_lasers.empty()
        self.enemy_lasers.empty()
        self.ammo_drops.empty()
        self.obstacles.empty()
        self.player.empty()
        self._spawn_player()
        self._create_obstacles()

    def create_enemy(self) -> None:
        """Spawn enemy with image."""
        size = 40
        img_paths = ['graphics/red.png', 'graphics/green.png', 'graphics/yellow.png']
        img_path = random.choice(img_paths)
        x = random.randint(20, self.screen_width - size - 20)
        enemy = Enemy(size, img_path, x, -size, self.screen_height, self.enemy_lasers)
        enemy.speed = 2 + (self.level - 1) * 1.5
        enemy_bullet_count = self._get_enemy_fire_bullet_count()
        enemy.fire_enabled = enemy_bullet_count > 0
        enemy.fire_bullet_count = max(1, enemy_bullet_count)
        enemy.fire_cooldown = self._get_enemy_fire_cooldown()
        self.enemies.add(enemy)

    def check_collisions(self) -> None:
        """Handle all collisions."""
        # Player lasers hit enemies
        for laser in self.player_lasers:
            hits = pygame.sprite.spritecollide(laser, self.enemies, False)
            for enemy in hits:
                enemy.health -= 1
                laser.kill()
                if enemy.health <= 0:
                    enemy.kill()
                    self.score += 10
                    self.explosion_sound.play()
            
            # Player lasers hit obstacles
            hits = pygame.sprite.spritecollide(laser, self.obstacles, False)
            for obs in hits:
                obs.health -= 1
                laser.kill()
                if obs.health <= 0:
                    obs.kill()
        
        # Enemy lasers hit player
        if self.player.sprite:
            hits = pygame.sprite.spritecollide(self.player.sprite, self.enemy_lasers, True)
            if hits:
                self.player.sprite.health = max(0, self.player.sprite.health - len(hits))
                if self.player.sprite.health <= 0:
                    self.game_over = True
                    self.ui.set_game_over(self.score)
        
        # Enemies hit player
        if self.player.sprite:
            hits = pygame.sprite.spritecollide(self.player.sprite, self.enemies, False)
            for enemy in hits:
                self.player.sprite.health = max(0, self.player.sprite.health - 1)
                enemy.kill()
                if self.player.sprite.health <= 0:
                    self.game_over = True
                    self.ui.set_game_over(self.score)
        
        # Player collects ammo
        if self.player.sprite:
            hits = pygame.sprite.spritecollide(self.player.sprite, self.ammo_drops, True)
            for ammo in hits:
                old_level = getattr(self.player.sprite, 'fire_level', 1)
                self.player.sprite.fire_level = min(old_level + 1, 3)

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
            self._update_progression()
            
            # Spawn enemies
            for event in events:
                if event.type == self.enemy_event:
                    self.create_enemy()
            
            self.player.update()
            self.enemies.update()
            self.enemy_lasers.update()
            self.ammo_drops.update()
            self.player_lasers.add(self.player.sprite.lasers)
            self.player_lasers.update()
            self.check_collisions()
            
            # Draw
            if self.level == 1:
                self.screen.fill((0, 0, 20))
            else:
                tw, th = self.space_bg.get_size()
                for x in range(0, self.screen_width, tw):
                    for y in range(0, self.screen_height, th):
                        self.screen.blit(self.space_bg, (x, y))
            
            self.obstacles.draw(self.screen)
            self.player.draw(self.screen)
            self.enemies.draw(self.screen)
            self.player_lasers.draw(self.screen)
            self.enemy_lasers.draw(self.screen)
            self.ammo_drops.draw(self.screen)
            
            # UI
            font = pygame.font.Font(None, 36)
            score_text = font.render(f'Score: {self.score} Level: {self.level}', True, (255, 255, 255))
            self.screen.blit(score_text, (10, 10))
            health_text = font.render(f'Health: {self.player.sprite.health if self.player.sprite else 0}', True, (255, 0, 0))
            self.screen.blit(health_text, (10, 50))
            fire_text = font.render(f'Fire: x{getattr(self.player.sprite, "fire_level", 1) if self.player.sprite else 1}', True, (0, 255, 0))
            self.screen.blit(fire_text, (10, 90))
        else:
            self.screen.fill((0, 0, 20))
            self.ui.draw(self.screen, self.score if self.game_over else None)
        
        return None
