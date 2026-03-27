from typing import Any, Dict, List, Optional

import pygame

from storage import ScoreStorage


class UIManager:
    """Manage menu, high-score and game-over screens."""

    MENU = "menu"
    PLAYING = "playing"
    GAME_OVER = "game_over"
    HIGH_SCORES = "high_scores"

    def __init__(self, screen_width: int, screen_height: int, storage: ScoreStorage) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.storage = storage
        self.state = self.MENU
        self.input_text = ""
        self.pending_score = 0
        self.status_message = "Press Enter or click a button."

        self.title_font = pygame.font.Font(None, 72)
        self.menu_font = pygame.font.Font(None, 44)
        self.text_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 24)

        self.bg_color = (8, 12, 28)
        self.panel_color = (19, 27, 48)
        self.text_color = (225, 240, 255)
        self.accent_color = (90, 210, 255)
        self.button_color = (36, 60, 96)
        self.button_hover = (60, 92, 136)
        self.warning_color = (255, 202, 102)

        self.button_rects: Dict[str, pygame.Rect] = {}
        self.filtered_scores: List[Dict[str, Any]] = []
        self.report = self.storage.get_report()
        self.refresh_scores()
        self.update_buttons()

    def update_buttons(self) -> None:
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        button_width, button_height = 300, 56

        if self.state == self.MENU:
            self.button_rects = {
                "start": pygame.Rect(center_x - button_width // 2, center_y - 30, button_width, button_height),
                "scores": pygame.Rect(center_x - button_width // 2, center_y + 42, button_width, button_height),
                "quit": pygame.Rect(center_x - button_width // 2, center_y + 114, button_width, button_height),
            }
        elif self.state == self.GAME_OVER:
            self.button_rects = {
                "save": pygame.Rect(center_x - button_width // 2, center_y + 32, button_width, button_height),
                "play_again": pygame.Rect(center_x - button_width // 2, center_y + 104, button_width, button_height),
                "menu": pygame.Rect(center_x - button_width // 2, center_y + 176, button_width, button_height),
            }
        elif self.state == self.HIGH_SCORES:
            self.button_rects = {
                "search": pygame.Rect(60, self.screen_height - 96, 120, 42),
                "reset": pygame.Rect(192, self.screen_height - 96, 120, 42),
                "back": pygame.Rect(self.screen_width - 170, 24, 120, 42),
            }
        else:
            self.button_rects = {}

    def refresh_scores(self) -> None:
        self.report = self.storage.get_report()
        self.filtered_scores = list(self.report["top5"])

    def _switch_state(self, next_state: str, message: Optional[str] = None) -> None:
        self.state = next_state
        if message is not None:
            self.status_message = message
        self.update_buttons()

    def _append_input(self, text: str) -> None:
        if len(self.input_text) < 18:
            self.input_text += text

    def _handle_score_search(self) -> None:
        self.filtered_scores = self.storage.search_by_name(self.input_text)
        if self.input_text.strip():
            if self.filtered_scores:
                self.status_message = f"Showing search result for '{self.input_text.strip()}'."
            else:
                self.status_message = f"No score found for '{self.input_text.strip()}'."
        else:
            self.filtered_scores = list(self.report["top5"])
            self.status_message = "Showing top scores."

    def _save_score(self) -> None:
        saved_record = self.storage.add_new_score(self.input_text, self.pending_score)
        self.refresh_scores()
        self.input_text = ""
        self._switch_state(self.MENU, f"Saved score for {saved_record['name']}.")

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        changed = False

        if event.type == pygame.KEYDOWN:
            if self.state == self.MENU:
                if event.key == pygame.K_RETURN:
                    self._switch_state(self.PLAYING, "Starting a new round.")
                    changed = True
                elif event.key == pygame.K_h:
                    self.refresh_scores()
                    self.input_text = ""
                    self._switch_state(self.HIGH_SCORES, "Browse saved scores.")
                    changed = True
                elif event.key == pygame.K_ESCAPE:
                    return "quit"

            elif self.state == self.GAME_OVER:
                if event.key == pygame.K_RETURN:
                    self._save_score()
                    changed = True
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self._switch_state(self.MENU, "Returned to menu without saving.")
                    self.input_text = ""
                    changed = True
                elif event.unicode.isalnum() or event.unicode in " _-":
                    self._append_input(event.unicode)

            elif self.state == self.HIGH_SCORES:
                if event.key == pygame.K_RETURN:
                    self._handle_score_search()
                    changed = True
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.input_text = ""
                    self.filtered_scores = list(self.report["top5"])
                    self._switch_state(self.MENU, "Returned to menu.")
                    changed = True
                elif event.key == pygame.K_r:
                    self.input_text = ""
                    self.filtered_scores = list(self.report["top5"])
                    self.status_message = "Filters reset."
                    changed = True
                elif event.unicode.isalnum() or event.unicode in " _-":
                    self._append_input(event.unicode)

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            if self.state == self.MENU:
                if self.button_rects["start"].collidepoint(mouse_pos):
                    self._switch_state(self.PLAYING, "Starting a new round.")
                    changed = True
                elif self.button_rects["scores"].collidepoint(mouse_pos):
                    self.refresh_scores()
                    self.input_text = ""
                    self._switch_state(self.HIGH_SCORES, "Browse saved scores.")
                    changed = True
                elif self.button_rects["quit"].collidepoint(mouse_pos):
                    return "quit"

            elif self.state == self.GAME_OVER:
                if self.button_rects["save"].collidepoint(mouse_pos):
                    self._save_score()
                    changed = True
                elif self.button_rects["play_again"].collidepoint(mouse_pos):
                    self.input_text = ""
                    self._switch_state(self.PLAYING, "Starting a new round.")
                    changed = True
                elif self.button_rects["menu"].collidepoint(mouse_pos):
                    self.input_text = ""
                    self._switch_state(self.MENU, "Returned to menu without saving.")
                    changed = True

            elif self.state == self.HIGH_SCORES:
                if self.button_rects["search"].collidepoint(mouse_pos):
                    self._handle_score_search()
                    changed = True
                elif self.button_rects["reset"].collidepoint(mouse_pos):
                    self.input_text = ""
                    self.filtered_scores = list(self.report["top5"])
                    self.status_message = "Filters reset."
                    changed = True
                elif self.button_rects["back"].collidepoint(mouse_pos):
                    self.input_text = ""
                    self.filtered_scores = list(self.report["top5"])
                    self._switch_state(self.MENU, "Returned to menu.")
                    changed = True

        if changed:
            self.update_buttons()
        return None

    def _draw_button(self, screen: pygame.Surface, rect: pygame.Rect, label: str) -> None:
        color = self.button_hover if rect.collidepoint(pygame.mouse.get_pos()) else self.button_color
        pygame.draw.rect(screen, color, rect, border_radius=8)
        pygame.draw.rect(screen, self.accent_color, rect, width=2, border_radius=8)
        text_surface = self.text_font.render(label, True, self.text_color)
        screen.blit(text_surface, text_surface.get_rect(center=rect.center))

    def _draw_panel(self, screen: pygame.Surface, rect: pygame.Rect) -> None:
        pygame.draw.rect(screen, self.panel_color, rect, border_radius=12)
        pygame.draw.rect(screen, self.accent_color, rect, width=2, border_radius=12)

    def draw(self, screen: pygame.Surface, final_score: Optional[int] = None) -> None:
        screen.fill(self.bg_color)

        if self.state == self.MENU:
            title = self.title_font.render("SPACE SHOOTER", True, self.text_color)
            subtitle = self.small_font.render("Press H for High Scores", True, self.accent_color)
            screen.blit(title, title.get_rect(center=(self.screen_width // 2, 110)))
            screen.blit(subtitle, subtitle.get_rect(center=(self.screen_width // 2, 160)))

            self._draw_button(screen, self.button_rects["start"], "Start Game")
            self._draw_button(screen, self.button_rects["scores"], "High Scores")
            self._draw_button(screen, self.button_rects["quit"], "Quit")

        elif self.state == self.HIGH_SCORES:
            title = self.title_font.render("HIGH SCORES", True, self.text_color)
            screen.blit(title, title.get_rect(center=(self.screen_width // 2, 60)))

            report_panel = pygame.Rect(40, 110, self.screen_width - 80, 86)
            list_panel = pygame.Rect(40, 214, self.screen_width - 80, 280)
            self._draw_panel(screen, report_panel)
            self._draw_panel(screen, list_panel)

            report_lines = [
                f"Players: {self.report['total_players']}",
                f"Average: {self.report['average']}",
                f"Highest: {self.report['highest']}",
            ]
            for index, line in enumerate(report_lines):
                line_surface = self.text_font.render(line, True, self.text_color)
                screen.blit(line_surface, (60 + index * 210, 140))

            scores_to_show = self.filtered_scores[:8]
            for index, score in enumerate(scores_to_show):
                score_line = f"{index + 1}. {score['name']} - {score['score']}"
                line_surface = self.text_font.render(score_line, True, self.text_color)
                screen.blit(line_surface, (60, 236 + index * 30))

            if not scores_to_show:
                empty_surface = self.text_font.render("No scores to display.", True, self.warning_color)
                screen.blit(empty_surface, (60, 236))

            search_prompt = self.small_font.render(
                f"Search player: {self.input_text}",
                True,
                self.accent_color,
            )
            help_prompt = self.small_font.render("Enter = search, R = reset, Esc = back", True, self.text_color)
            screen.blit(search_prompt, (60, self.screen_height - 126))
            screen.blit(help_prompt, (60, self.screen_height - 58))

            self._draw_button(screen, self.button_rects["search"], "Search")
            self._draw_button(screen, self.button_rects["reset"], "Reset")
            self._draw_button(screen, self.button_rects["back"], "Back")

        elif self.state == self.GAME_OVER:
            title = self.title_font.render("GAME OVER", True, self.text_color)
            score_surface = self.menu_font.render(f"Score: {final_score or self.pending_score}", True, self.accent_color)
            input_surface = self.text_font.render(
                f"Player Name: {self.input_text or 'Type name and press Enter'}",
                True,
                self.text_color,
            )

            screen.blit(title, title.get_rect(center=(self.screen_width // 2, 100)))
            screen.blit(score_surface, score_surface.get_rect(center=(self.screen_width // 2, 180)))
            screen.blit(input_surface, input_surface.get_rect(center=(self.screen_width // 2, 260)))

            self._draw_button(screen, self.button_rects["save"], "Save Score")
            self._draw_button(screen, self.button_rects["play_again"], "Play Again")
            self._draw_button(screen, self.button_rects["menu"], "Menu")

        status_surface = self.small_font.render(self.status_message, True, self.warning_color)
        state_surface = self.small_font.render(f"State: {self.state}", True, self.text_color)
        screen.blit(status_surface, (24, self.screen_height - 28))
        screen.blit(state_surface, (self.screen_width - 140, 20))

    def get_state(self) -> str:
        return self.state

    def set_game_over(self, final_score: int) -> None:
        self.pending_score = final_score
        self.input_text = ""
        self._switch_state(self.GAME_OVER, "Enter your name to save the score.")
