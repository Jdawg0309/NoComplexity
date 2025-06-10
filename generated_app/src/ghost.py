import pygame
import random

class Ghost:
    def __init__(self, game, name):
        self.screen = game.screen
        self.settings = game.settings
        self.name = name
        self.color = self.get_color(name)
        self.rect = pygame.Rect(100, 100, 30, 30)  # Initial position and size
        self.speed = 2
        self.directions = [pygame.Vector2(1, 0), pygame.Vector2(-1, 0), pygame.Vector2(0, 1), pygame.Vector2(0, -1)]
        self.direction = random.choice(self.directions)

    def get_color(self, name):
        colors = {
            'blinky': (255, 0, 0),  # Red
            'pinky': (255, 184, 255),  # Pink
            'inky': (0, 255, 255),  # Cyan
            'clyde': (255, 165, 0)  # Orange
        }
        return colors.get(name, (255, 255, 255))  # Default to white if name not found

    def update(self, maze):
        # Ghost movement logic here
        self.rect.x += self.direction.x * self.speed
        self.rect.y += self.direction.y * self.speed

        # Check for collisions with walls and change direction randomly
        for row_index, row in enumerate(maze.maze_layout):
            for col_index, cell in enumerate(row):
                if cell == 'X':
                    wall_rect = pygame.Rect(col_index * maze.wall_size[0], row_index * maze.wall_size[1], maze.wall_size[0], maze.wall_size[1])
                    if self.rect.colliderect(wall_rect):
                        self.rect.x -= self.direction.x * self.speed
                        self.rect.y -= self.direction.y * self.speed
                        self.direction = random.choice(self.directions)  # Change direction

    def draw(self):
        pygame.draw.rect(self.screen, self.color, self.rect)