import pygame
from typing import Dict, Optional, Any
from storage import ScoreStorage

class UIManager:
    """Controller class for all UI screens: Menu, High Scores (with search/filter/reports), Game Over.
    Handles state transitions, input validation, modern space theme."""
    
    MENU = 'menu'
    PLAYING = 'playing'
    GAME_OVER = 'game_over'
    HIGH_SCORES = 'high_scores'
    
    def __init__(self, screen_width: int, screen_height: int, storage: ScoreStorage) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.storage = storage
        self.state = self.MENU
        self.input_text = ''
        
        self.title_font = pygame.font.Font(None, 72)
        self.menu_font = pygame.font.Font(None, 48)
        self.text_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        self.bg_color = (0, 0, 20)
        self.text_color = (200, 255, 255)
        self.accent_color = (100, 200, 255)
        self.button_color = (50, 50, 100)
        self.button_hover = (100, 100, 150)
        
        self.button_rects = {}
        self.update_buttons()
        
        self.report = self._get_report()
        self.pending_score = 0

    def update_buttons(self) -> None:
        w, h = self.screen_width // 2, self.screen_height // 2
        btn_w, btn_h = 300, 60
        
        if self.state == self.MENU:
            self.button_rects = {
                'start': pygame.Rect(w - btn_w//2, h - 50, btn_w, btn_h),
                'scores': pygame.Rect(w - btn_w//2, h + 30, btn_w, btn_h),
                'quit': pygame.Rect(w - btn_w//2, h + 110, btn_w, btn_h)
            }
        elif self.state == self.GAME_OVER:
            self.button_rects = {
                'play_again': pygame.Rect(w - btn_w//2, h + 50, btn_w, btn_h),
                'menu': pygame.Rect(w - btn_w//2, h + 140, btn_w, btn_h)
            }
        elif self.state == self.HIGH_SCORES:
            self.button_rects = {
                'back': pygame.Rect(20, 20, 120, 40)
            }

    def _get_report(self) -> Dict[str, Any]:
        scores = self.storage.load_scores()
        if not scores:
            return {'avg': 0, 'top5': []}
        avg = sum(s['score'] for s in scores) / len(scores)
        return {'avg': round(avg, 2), 'top5': self.storage.get_top_scores(5)}

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        changed = False
        
        if event.type == pygame.KEYDOWN:
            if self.state in (self.GAME_OVER, self.HIGH_SCORES):
                if event.key == pygame.K_RETURN:
                    self.input_text = self.input_text.strip()
                    if self.state == self.GAME_OVER and self.input_text:
                        self.storage.add_new_score(self.input_text, self.pending_score)
                        self.report = self._get_report()
                        self.state = self.MENU
                        changed = True
                    elif self.state == self.HIGH_SCORES:
                        self._handle_search()
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.unicode.isalnum() or event.unicode in ' _-':
                    self.input_text += event.unicode
            elif event.key == pygame.K_ESCAPE:
                self.state = self.MENU
                changed = True
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.state == self.MENU:
                if self.button_rects['start'].collidepoint(mouse_pos):
                    self.state = self.PLAYING
                    changed = True
                elif self.button_rects['scores'].collidepoint(mouse_pos):
                    self.state = self.HIGH_SCORES
                    changed = True
                elif self.button_rects['quit'].collidepoint(mouse_pos):
                    return 'quit'
            elif self.state == self.GAME_OVER:
                if self.button_rects['play_again'].collidepoint(mouse_pos):
                    self.state = self.PLAYING
                    changed = True
                elif self.button_rects['menu'].collidepoint(mouse_pos):
                    self.state = self.MENU
                    changed = True
            elif self.state == self.HIGH_SCORES:
                if self.button_rects['back'].collidepoint(mouse_pos):
                    self.state = self.MENU
                    changed = True
        
        if changed:
            self.update_buttons()
        return None
    
    def _handle_search(self) -> None:
        results = self.storage.search_by_name(self.input_text)
        self.report['top5'] = results or self.report['top5']  # Show filtered

    def draw(self, screen: pygame.Surface, final_score: Optional[int] = None) -> None:
        screen.fill(self.bg_color)
        
        if self.state == self.MENU:
            title = self.title_font.render('SPACE SHOOTER', True, self.text_color)
            screen.blit(title, (self.screen_width//2 - title.get_width()//2, 100))
            
            texts = ['Start Game', 'High Scores', 'Quit']
            rects = [self.button_rects['start'], self.button_rects['scores'], self.button_rects['quit']]
            for t, rect in zip(texts, rects):
                color = self.button_hover if rect.collidepoint(pygame.mouse.get_pos()) else self.button_color
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, self.accent_color, rect, 3)
                text_surf = self.menu_font.render(t, True, self.text_color)
                screen.blit(text_surf, (rect.centerx - text_surf.get_width()//2, rect.centery - text_surf.get_height()//2))
        
        elif self.state == self.HIGH_SCORES:
            title = self.title_font.render('HIGH SCORES', True, self.text_color)
            screen.blit(title, (self.screen_width//2 - title.get_width()//2, 50))
            
            report_t = self.text_font.render(f'Average: {self.report["avg"]}', True, self.text_color)
            screen.blit(report_t, (50, 150))
            
            for i, s in enumerate(self.report['top5']):
                line = self.text_font.render(f'{i+1}. {s["name"]} - {s["score"]}', True, self.text_color)
                screen.blit(line, (50, 200 + i*40))
            
            prompt = self.small_font.render(f'Search: {self.input_text or ""} (Enter/Backspace)', True, self.accent_color)
            screen.blit(prompt, (50, self.screen_height - 100))
            
            pygame.draw.rect(screen, self.button_color, self.button_rects['back'])
            back_t = self.small_font.render('Back', True, self.text_color)
            screen.blit(back_t, (25, 25))
        
        elif self.state == self.GAME_OVER:
            title = self.title_font.render('GAME OVER', True, self.text_color)
            screen.blit(title, (self.screen_width//2 - title.get_width()//2, 100))
            
            score_t = self.text_font.render(f'Score: {final_score or 0}', True, self.accent_color)
            screen.blit(score_t, (self.screen_width//2 - score_t.get_width()//2, 200))
            
            prompt = self.text_font.render(f'Name: {self.input_text or "Enter name (Enter to save)"}', True, self.text_color)
            screen.blit(prompt, (self.screen_width//2 - prompt.get_width()//2, 300))
            
            for name, rect in self.button_rects.items():
                text = 'Play Again' if name == 'play_again' else 'Menu'
                t = self.menu_font.render(text, True, self.text_color)
                color = self.button_hover if rect.collidepoint(pygame.mouse.get_pos()) else self.button_color
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, self.accent_color, rect, 3)
                screen.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))
        
        state_text = self.small_font.render(f'State: {self.state}', True, self.text_color)
        screen.blit(state_text, (self.screen_width - 150, 20))

    def get_state(self) -> str:
        return self.state

    def set_game_over(self, final_score: int) -> None:
        self.state = self.GAME_OVER
        self.input_text = ''
        self.pending_score = final_score
        self.update_buttons()

