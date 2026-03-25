# Space Shooter Game - Implementation TODO

## Approved Plan Steps (Sequential Execution)

1. **[DONE]** Create ui_manager.py (UIManager class for Menu, High Scores, Game Over screens with search/filter/reports).
2. **[DONE]** Edit entities.py (Consolidate Player/Laser/Block into Entity base; add health; full docstrings/types).
3. **[DONE]** Edit storage.py (Add search_by_name, update_score, delete_score, get_report for avg/top5; types/docs).
4. **[DONE]** Edit game.py (Complete enemy waves, health, collisions, score; integrate UIManager).
5. **[DONE]** Edit main.py (State machine with UIManager: menu/game/gameover/scores; graceful inputs).
6. **[DONE]** Delete duplicates: player.py, laser.py, obstacle.py.
7. **[DONE]** Update requirements.txt if needed.
8. **[DONE]** Ready for testing: python -m venv venv &amp;&amp; venv/Scripts/activate &amp;&amp; pip install -r requirements.txt &amp;&amp; python main.py

Track progress: Mark as [DONE] after each step completion.

