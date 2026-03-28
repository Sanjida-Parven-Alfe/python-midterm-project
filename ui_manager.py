"""
UI Manager for Space Shooter — handles menu, login, register, settings,
high-score and game-over screens with Pygame rendering.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pygame

from storage import PlayerStorage


class UIManager:
    """Manage menu, login, register, settings, high-score and game-over screens."""

    MENU = "menu"
    PLAYING = "playing"
    GAME_OVER = "game_over"
    HIGH_SCORES = "high_scores"
    LOGIN = "login"
    REGISTER = "register"
    SETTINGS = "settings"

    def __init__(self, screen_width: int, screen_height: int, storage: PlayerStorage) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.storage = storage
        self.state = self.MENU
        self.input_text = ""
        self.input_text_2 = ""           # Second input for age in register
        self.active_input = 1            # Which input field is active (1 or 2)
        self.pending_score = 0
        self.status_message = ""
        self.current_player: Optional[Dict[str, Any]] = None

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
        self.success_color = (80, 255, 130)
        self.danger_color = (255, 100, 100)

        self.button_rects: Dict[str, pygame.Rect] = {}
        self.filtered_scores: List[Dict[str, Any]] = []
        self.report = self.storage.get_report()
        self.refresh_scores()
        self.update_buttons()

    # ------------------------------------------------------------------ #
    #  Button layout per state                                            #
    # ------------------------------------------------------------------ #

    def update_buttons(self) -> None:
        cx = self.screen_width // 2
        cy = self.screen_height // 2
        bw, bh = 300, 56

        if self.state == self.MENU:
            self.button_rects = {
                "start": pygame.Rect(cx - bw // 2, cy - 30, bw, bh),
                "scores": pygame.Rect(cx - bw // 2, cy + 42, bw, bh),
                "settings": pygame.Rect(cx - bw // 2, cy + 114, bw, bh),
                "quit": pygame.Rect(cx - bw // 2, cy + 186, bw, bh),
            }
        elif self.state == self.LOGIN:
            self.button_rects = {
                "login": pygame.Rect(cx - bw // 2, cy + 40, bw, bh),
                "register": pygame.Rect(cx - bw // 2, cy + 112, bw, bh),
                "back": pygame.Rect(cx - bw // 2, cy + 184, bw, bh),
            }
        elif self.state == self.REGISTER:
            self.button_rects = {
                "create": pygame.Rect(cx - bw // 2, cy + 80, bw, bh),
                "back": pygame.Rect(cx - bw // 2, cy + 152, bw, bh),
            }
        elif self.state == self.SETTINGS:
            self.button_rects = {
                "update_name": pygame.Rect(cx - bw // 2, cy + 20, bw, bh),
                "delete_account": pygame.Rect(cx - bw // 2, cy + 92, bw, bh),
                "back": pygame.Rect(cx - bw // 2, cy + 164, bw, bh),
            }
        elif self.state == self.GAME_OVER:
            self.button_rects = {
                "play_again": pygame.Rect(cx - bw // 2, cy + 60, bw, bh),
                "menu": pygame.Rect(cx - bw // 2, cy + 132, bw, bh),
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

    def _append_input(self, text: str, field: int = 1) -> None:
        if field == 1 and len(self.input_text) < 18:
            self.input_text += text
        elif field == 2 and len(self.input_text_2) < 3:
            self.input_text_2 += text

    # ------------------------------------------------------------------ #
    #  Login / Register logic                                             #
    # ------------------------------------------------------------------ #

    def _try_login(self) -> None:
        """Attempt to find existing player by name."""
        name = self.input_text.strip()
        if not name:
            self.status_message = "Please enter your name."
            return

        player = self.storage.find_player_by_name(name)
        if player:
            self.current_player = player
            self.input_text = ""
            self._switch_state(self.PLAYING, f"Welcome back, {player['Name']}!")
        else:
            self.status_message = f"No account found for '{name}'. Please register first."

    def _try_register(self) -> None:
        """Create a new player account."""
        name = self.input_text.strip()
        age_str = self.input_text_2.strip()

        if not name:
            self.status_message = "Please enter your name."
            return
        if not age_str:
            self.status_message = "Please enter your age."
            return
        try:
            age = int(age_str)
        except ValueError:
            self.status_message = "Age must be a number."
            return
        if age < 1 or age > 120:
            self.status_message = "Please enter a valid age (1-120)."
            return

        # Check if name already exists
        existing = self.storage.find_player_by_name(name)
        if existing:
            self.status_message = f"Account '{existing['Name']}' already exists! Go back and login."
            return

        player = self.storage.add_player(name, age)
        self.current_player = player
        self.input_text = ""
        self.input_text_2 = ""
        self.active_input = 1
        self._switch_state(self.PLAYING, f"Account created! Welcome, {player['Name']}!")

    # ------------------------------------------------------------------ #
    #  Settings logic                                                     #
    # ------------------------------------------------------------------ #

    def _update_name(self) -> None:
        """Update logged-in player's name."""
        new_name = self.input_text.strip()
        if not new_name:
            self.status_message = "Please type a new name first."
            return
        if not self.current_player:
            self.status_message = "No player logged in."
            return

        # Check if new name already taken
        existing = self.storage.find_player_by_name(new_name)
        if existing and existing["Id"] != self.current_player["Id"]:
            self.status_message = f"Name '{existing['Name']}' is already taken."
            return

        old_name = self.current_player["Name"]
        if self.storage.update_player_name(self.current_player["Id"], new_name):
            self.current_player = self.storage.find_player_by_id(self.current_player["Id"])
            self.input_text = ""
            self.status_message = f"Name updated: {old_name} -> {self.current_player['Name']}"
        else:
            self.status_message = "Failed to update name."

    def _delete_account(self) -> None:
        """Delete logged-in player's account."""
        if not self.current_player:
            self.status_message = "No player logged in."
            return
        name = self.current_player["Name"]
        if self.storage.delete_player(self.current_player["Id"]):
            self.current_player = None
            self.input_text = ""
            self._switch_state(self.MENU, f"Account '{name}' deleted.")
        else:
            self.status_message = "Failed to delete account."

    # ------------------------------------------------------------------ #
    #  Score auto-save (called from Game)                                  #
    # ------------------------------------------------------------------ #

    def auto_save_score(self, score: int) -> None:
        """Auto-save the score for the logged-in player."""
        if self.current_player:
            self.storage.update_score(self.current_player["Id"], score)
            # Reload fresh player data
            self.current_player = self.storage.find_player_by_id(self.current_player["Id"])
            self.refresh_scores()

    # ------------------------------------------------------------------ #
    #  High scores search                                                  #
    # ------------------------------------------------------------------ #

    def _handle_score_search(self) -> None:
        self.filtered_scores = self.storage.search_by_name(self.input_text)
        if self.input_text.strip():
            if self.filtered_scores:
                self.status_message = f"Results for '{self.input_text.strip()}'."
            else:
                self.status_message = f"No player found for '{self.input_text.strip()}'."
        else:
            self.filtered_scores = list(self.report["top5"])
            self.status_message = "Showing top scores."

    # ------------------------------------------------------------------ #
    #  Event handling                                                      #
    # ------------------------------------------------------------------ #

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        changed = False

        if event.type == pygame.KEYDOWN:
            # ---- MENU ----
            if self.state == self.MENU:
                if event.key == pygame.K_RETURN:
                    self.input_text = ""
                    self._switch_state(self.LOGIN, "Enter your name to login.")
                    changed = True
                elif event.key == pygame.K_h:
                    self.refresh_scores()
                    self.input_text = ""
                    self._switch_state(self.HIGH_SCORES, "Browse player scores.")
                    changed = True
                elif event.key == pygame.K_ESCAPE:
                    return "quit"

            # ---- LOGIN ----
            elif self.state == self.LOGIN:
                if event.key == pygame.K_RETURN:
                    self._try_login()
                    changed = True
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.input_text = ""
                    self._switch_state(self.MENU, "")
                    changed = True
                elif event.unicode.isalnum() or event.unicode in " _-":
                    self._append_input(event.unicode, 1)

            # ---- REGISTER ----
            elif self.state == self.REGISTER:
                if event.key == pygame.K_TAB:
                    # Switch between name and age fields
                    self.active_input = 2 if self.active_input == 1 else 1
                elif event.key == pygame.K_RETURN:
                    self._try_register()
                    changed = True
                elif event.key == pygame.K_BACKSPACE:
                    if self.active_input == 1:
                        self.input_text = self.input_text[:-1]
                    else:
                        self.input_text_2 = self.input_text_2[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.input_text = ""
                    self.input_text_2 = ""
                    self.active_input = 1
                    self._switch_state(self.LOGIN, "Enter your name to login.")
                    changed = True
                elif self.active_input == 1 and (event.unicode.isalnum() or event.unicode in " _-"):
                    self._append_input(event.unicode, 1)
                elif self.active_input == 2 and event.unicode.isdigit():
                    self._append_input(event.unicode, 2)

            # ---- SETTINGS ----
            elif self.state == self.SETTINGS:
                if event.key == pygame.K_ESCAPE:
                    self.input_text = ""
                    self._switch_state(self.MENU, "")
                    changed = True
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.unicode.isalnum() or event.unicode in " _-":
                    self._append_input(event.unicode, 1)

            # ---- GAME OVER ----
            elif self.state == self.GAME_OVER:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    self.input_text = ""
                    self._switch_state(self.PLAYING, "Starting a new round.")
                    changed = True
                elif event.key == pygame.K_ESCAPE:
                    self._switch_state(self.MENU, "")
                    changed = True

            # ---- HIGH SCORES ----
            elif self.state == self.HIGH_SCORES:
                if event.key == pygame.K_RETURN:
                    self._handle_score_search()
                    changed = True
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.input_text = ""
                    self.filtered_scores = list(self.report["top5"])
                    self._switch_state(self.MENU, "")
                    changed = True
                elif event.key == pygame.K_r:
                    self.input_text = ""
                    self.filtered_scores = list(self.report["top5"])
                    self.status_message = "Filters reset."
                    changed = True
                elif event.unicode.isalnum() or event.unicode in " _-":
                    self._append_input(event.unicode, 1)

        # ---- MOUSE CLICKS ----
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()

            if self.state == self.MENU:
                if self.button_rects["start"].collidepoint(pos):
                    self.input_text = ""
                    self._switch_state(self.LOGIN, "Enter your name to login.")
                    changed = True
                elif self.button_rects["scores"].collidepoint(pos):
                    self.refresh_scores()
                    self.input_text = ""
                    self._switch_state(self.HIGH_SCORES, "Browse player scores.")
                    changed = True
                elif self.button_rects["settings"].collidepoint(pos):
                    if self.current_player:
                        self.input_text = ""
                        self._switch_state(self.SETTINGS, f"Logged in as {self.current_player['Name']}")
                    else:
                        self.status_message = "Login first to access settings."
                    changed = True
                elif self.button_rects["quit"].collidepoint(pos):
                    return "quit"

            elif self.state == self.LOGIN:
                if self.button_rects["login"].collidepoint(pos):
                    self._try_login()
                    changed = True
                elif self.button_rects["register"].collidepoint(pos):
                    self.input_text_2 = ""
                    self.active_input = 1
                    self._switch_state(self.REGISTER, "Create a new account.")
                    changed = True
                elif self.button_rects["back"].collidepoint(pos):
                    self.input_text = ""
                    self._switch_state(self.MENU, "")
                    changed = True

            elif self.state == self.REGISTER:
                if self.button_rects["create"].collidepoint(pos):
                    self._try_register()
                    changed = True
                elif self.button_rects["back"].collidepoint(pos):
                    self.input_text = ""
                    self.input_text_2 = ""
                    self.active_input = 1
                    self._switch_state(self.LOGIN, "Enter your name to login.")
                    changed = True

            elif self.state == self.SETTINGS:
                if self.button_rects["update_name"].collidepoint(pos):
                    self._update_name()
                    changed = True
                elif self.button_rects["delete_account"].collidepoint(pos):
                    self._delete_account()
                    changed = True
                elif self.button_rects["back"].collidepoint(pos):
                    self.input_text = ""
                    self._switch_state(self.MENU, "")
                    changed = True

            elif self.state == self.GAME_OVER:
                if self.button_rects["play_again"].collidepoint(pos):
                    self.input_text = ""
                    self._switch_state(self.PLAYING, "Starting a new round.")
                    changed = True
                elif self.button_rects["menu"].collidepoint(pos):
                    self._switch_state(self.MENU, "")
                    changed = True

            elif self.state == self.HIGH_SCORES:
                if self.button_rects["search"].collidepoint(pos):
                    self._handle_score_search()
                    changed = True
                elif self.button_rects["reset"].collidepoint(pos):
                    self.input_text = ""
                    self.filtered_scores = list(self.report["top5"])
                    self.status_message = "Filters reset."
                    changed = True
                elif self.button_rects["back"].collidepoint(pos):
                    self.input_text = ""
                    self.filtered_scores = list(self.report["top5"])
                    self._switch_state(self.MENU, "")
                    changed = True

        if changed:
            self.update_buttons()
        return None

    # ------------------------------------------------------------------ #
    #  Drawing helpers                                                     #
    # ------------------------------------------------------------------ #

    def _draw_button(self, screen: pygame.Surface, rect: pygame.Rect, label: str,
                     color: Optional[tuple] = None) -> None:
        base = color or self.button_color
        hover = self.button_hover if color is None else tuple(min(c + 30, 255) for c in base)
        fill = hover if rect.collidepoint(pygame.mouse.get_pos()) else base
        pygame.draw.rect(screen, fill, rect, border_radius=8)
        border = self.accent_color if color is None else self.text_color
        pygame.draw.rect(screen, border, rect, width=2, border_radius=8)
        text_surface = self.text_font.render(label, True, self.text_color)
        screen.blit(text_surface, text_surface.get_rect(center=rect.center))

    def _draw_panel(self, screen: pygame.Surface, rect: pygame.Rect) -> None:
        pygame.draw.rect(screen, self.panel_color, rect, border_radius=12)
        pygame.draw.rect(screen, self.accent_color, rect, width=2, border_radius=12)

    def _draw_input_field(self, screen: pygame.Surface, label: str, value: str,
                          y: int, active: bool = True) -> None:
        """Draw a labeled input field."""
        cx = self.screen_width // 2
        # Label
        label_surf = self.text_font.render(label, True, self.accent_color)
        screen.blit(label_surf, label_surf.get_rect(center=(cx, y)))
        # Input box
        box_rect = pygame.Rect(cx - 150, y + 14, 300, 38)
        box_color = self.accent_color if active else (60, 70, 90)
        pygame.draw.rect(screen, (15, 20, 40), box_rect, border_radius=6)
        pygame.draw.rect(screen, box_color, box_rect, width=2, border_radius=6)
        cursor = "_" if active else ""
        text_surf = self.text_font.render(value + cursor, True, self.text_color)
        screen.blit(text_surf, (box_rect.x + 10, box_rect.y + 6))

    # ------------------------------------------------------------------ #
    #  Main draw                                                           #
    # ------------------------------------------------------------------ #

    def draw(self, screen: pygame.Surface, final_score: Optional[int] = None) -> None:
        screen.fill(self.bg_color)

        # ---- MENU ----
        if self.state == self.MENU:
            title = self.title_font.render("SPACE SHOOTER", True, self.text_color)
            screen.blit(title, title.get_rect(center=(self.screen_width // 2, 80)))

            # Show logged-in player info
            if self.current_player:
                info = self.small_font.render(
                    f"Logged in: {self.current_player['Name']}  |  Best Score: {self.current_player['Score']}",
                    True, self.success_color
                )
                screen.blit(info, info.get_rect(center=(self.screen_width // 2, 130)))
            else:
                info = self.small_font.render("No account logged in", True, self.warning_color)
                screen.blit(info, info.get_rect(center=(self.screen_width // 2, 130)))

            tip = self.small_font.render(
                "Tip: Collect EXTRA items for double ships and bigger bullets!",
                True, self.warning_color
            )
            screen.blit(tip, tip.get_rect(center=(self.screen_width // 2, 160)))

            # Status message
            if self.status_message:
                msg = self.small_font.render(self.status_message, True, self.accent_color)
                screen.blit(msg, msg.get_rect(center=(self.screen_width // 2, 190)))

            self._draw_button(screen, self.button_rects["start"], "Start Game")
            self._draw_button(screen, self.button_rects["scores"], "High Scores")
            self._draw_button(screen, self.button_rects["settings"], "Settings")
            self._draw_button(screen, self.button_rects["quit"], "Quit")

        # ---- LOGIN ----
        elif self.state == self.LOGIN:
            title = self.title_font.render("LOGIN", True, self.text_color)
            screen.blit(title, title.get_rect(center=(self.screen_width // 2, 80)))

            subtitle = self.text_font.render(
                "Enter your name to start playing",
                True, self.accent_color
            )
            screen.blit(subtitle, subtitle.get_rect(center=(self.screen_width // 2, 140)))

            self._draw_input_field(screen, "Player Name:", self.input_text, 190)

            # Status message
            if self.status_message:
                color = self.warning_color
                msg = self.small_font.render(self.status_message, True, color)
                screen.blit(msg, msg.get_rect(center=(self.screen_width // 2, 260)))

            self._draw_button(screen, self.button_rects["login"], "Login")
            self._draw_button(screen, self.button_rects["register"], "Create Account")
            self._draw_button(screen, self.button_rects["back"], "Back")

        # ---- REGISTER ----
        elif self.state == self.REGISTER:
            title = self.title_font.render("REGISTER", True, self.text_color)
            screen.blit(title, title.get_rect(center=(self.screen_width // 2, 80)))

            subtitle = self.text_font.render(
                "Create a new player account",
                True, self.accent_color
            )
            screen.blit(subtitle, subtitle.get_rect(center=(self.screen_width // 2, 130)))

            self._draw_input_field(screen, "Player Name:", self.input_text, 170,
                                   active=(self.active_input == 1))
            self._draw_input_field(screen, "Age:", self.input_text_2, 240,
                                   active=(self.active_input == 2))

            tab_hint = self.small_font.render("Press TAB to switch fields", True, (100, 120, 150))
            screen.blit(tab_hint, tab_hint.get_rect(center=(self.screen_width // 2, 300)))

            if self.status_message:
                msg = self.small_font.render(self.status_message, True, self.warning_color)
                screen.blit(msg, msg.get_rect(center=(self.screen_width // 2, 325)))

            self._draw_button(screen, self.button_rects["create"], "Create Account")
            self._draw_button(screen, self.button_rects["back"], "Back")

        # ---- SETTINGS ----
        elif self.state == self.SETTINGS:
            title = self.title_font.render("SETTINGS", True, self.text_color)
            screen.blit(title, title.get_rect(center=(self.screen_width // 2, 80)))

            if self.current_player:
                # Player info panel
                panel_rect = pygame.Rect(self.screen_width // 2 - 200, 120, 400, 120)
                self._draw_panel(screen, panel_rect)

                lines = [
                    f"Id: {self.current_player['Id']}",
                    f"Name: {self.current_player['Name']}",
                    f"Age: {self.current_player['Age']}",
                    f"Best Score: {self.current_player['Score']}",
                ]
                for i, line in enumerate(lines):
                    surf = self.text_font.render(line, True, self.text_color)
                    screen.blit(surf, (self.screen_width // 2 - 180, 132 + i * 26))

                # New name input
                self._draw_input_field(screen, "New Name:", self.input_text, 260)

            # Status message
            if self.status_message:
                msg = self.small_font.render(self.status_message, True, self.warning_color)
                screen.blit(msg, msg.get_rect(center=(self.screen_width // 2, 320)))

            self._draw_button(screen, self.button_rects["update_name"], "Update Name")
            self._draw_button(screen, self.button_rects["delete_account"], "Delete Account",
                              color=self.danger_color)
            self._draw_button(screen, self.button_rects["back"], "Back")

        # ---- HIGH SCORES ----
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
                score_line = f"{index + 1}. {score['Name']} - {score['Score']}"
                line_surface = self.text_font.render(score_line, True, self.text_color)
                screen.blit(line_surface, (60, 236 + index * 30))

            if not scores_to_show:
                empty_surface = self.text_font.render("No scores to display.", True, self.warning_color)
                screen.blit(empty_surface, (60, 236))

            search_prompt = self.small_font.render(
                f"Search player: {self.input_text}_",
                True, self.accent_color,
            )
            screen.blit(search_prompt, (60, self.screen_height - 126))

            self._draw_button(screen, self.button_rects["search"], "Search")
            self._draw_button(screen, self.button_rects["reset"], "Reset")
            self._draw_button(screen, self.button_rects["back"], "Back")

        # ---- GAME OVER ----
        elif self.state == self.GAME_OVER:
            title = self.title_font.render("GAME OVER", True, self.text_color)
            score_val = final_score if final_score is not None else self.pending_score
            score_surface = self.menu_font.render(f"Score: {score_val}", True, self.accent_color)

            screen.blit(title, title.get_rect(center=(self.screen_width // 2, 100)))
            screen.blit(score_surface, score_surface.get_rect(center=(self.screen_width // 2, 180)))

            # Show auto-save confirmation
            if self.current_player:
                saved_msg = self.text_font.render(
                    f"Score saved for {self.current_player['Name']}!",
                    True, self.success_color
                )
                screen.blit(saved_msg, saved_msg.get_rect(center=(self.screen_width // 2, 240)))

                best = self.text_font.render(
                    f"Best Score: {self.current_player['Score']}",
                    True, self.text_color
                )
                screen.blit(best, best.get_rect(center=(self.screen_width // 2, 275)))

            self._draw_button(screen, self.button_rects["play_again"], "Play Again")
            self._draw_button(screen, self.button_rects["menu"], "Menu")

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def get_state(self) -> str:
        return self.state

    def set_game_over(self, final_score: int) -> None:
        self.pending_score = final_score
        self.input_text = ""
        # Auto-save score
        self.auto_save_score(final_score)
        self._switch_state(self.GAME_OVER, "Score saved automatically!")
