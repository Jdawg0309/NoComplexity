import pygame
import sys
import random
from settings import Settings
from pacman import Pacman
from maze import Maze
from ghost import Ghost

class Game:
    def __init__(self):
        pygame.init()
        self.settings = Settings()
        self.screen = pygame.display.set_mode((self.settings.screen_width, self.settings.screen_height))
        pygame.display.set_caption("Pac-Man")
        self.clock = pygame.time.Clock()
        self.reset_game()

    def reset_game(self):
        self.maze = Maze(self)
        self.pacman = Pacman(self)
        self.ghosts = [Ghost(self, 'blinky'), Ghost(self, 'pinky'), Ghost(self, 'inky'), Ghost(self, 'clyde')]
        self.score = 0
        self.game_over = False
        self.font = pygame.font.SysFont(None, 36)

    def run_game(self):
        while True:
            self.handle_events()
            if not self.game_over:
                self.update_game()
            self.draw_game()
            self.clock.tick(60)  # 60 FPS

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.game_over:
                    self.reset_game()
                elif not self.game_over:
                    self.pacman.check_events(event)

    def update_game(self):
        self.pacman.update(self.maze)
        for ghost in self.ghosts:
            ghost.update(self.maze)
        self.check_collisions()
        self.check_pellets()

    def draw_game(self):
        self.screen.fill(self.settings.bg_color)
        self.maze.draw()
        self.pacman.draw()
        for ghost in self.ghosts:
            ghost.draw()
        
        # Draw score
        score_text = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))
        
        # Draw game over message
        if self.game_over:
            game_over_text = self.font.render("GAME OVER! Press R to restart", True, (255, 0, 0))
            text_rect = game_over_text.get_rect(center=(self.settings.screen_width//2, self.settings.screen_height//2))
            self.screen.blit(game_over_text, text_rect)
        
        pygame.display.flip()

    def check_collisions(self):
        for ghost in self.ghosts:
            if self.pacman.rect.colliderect(ghost.rect):
                self.game_over = True

    def check_pellets(self):
        # Check if Pacman collected any pellets
        center = self.pacman.rect.center
        for i, pellet in enumerate(self.maze.pellets[:]):
            if pellet.collidepoint(center):
                self.maze.pellets.pop(i)
                self.score += 10
                
        # Check for win condition (all pellets collected)
        if len(self.maze.pellets) == 0:
            self.game_over = True

if __name__ == '__main__':
    game = Game()
    game.run_game()