import pygame
import sys
from typing import List
from game import Game

def main() -> None:
    """Main entry point for Space Shooter game."""
    pygame.init()
    screen_width, screen_height = 800, 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption('Space Shooter - AIUB Midterm')
    clock = pygame.time.Clock()
    
    game = Game(screen, screen_width, screen_height)
    
    running = True
    while running:
        events = pygame.event.get()
        
        for event in events:
            if event.type == pygame.QUIT:
                running = False
        
        quit_flag = game.run(events)
        if quit_flag == 'quit':
            running = False
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
