import pygame

class Pacman:
    def __init__(self, game):
        self.screen = game.screen
        self.settings = game.settings
        self.color = (255, 255, 0)  # Yellow
        self.radius = self.settings.cell_size // 2
        self.rect = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)
        self.rect.center = (self.settings.screen_width // 2, self.settings.screen_height // 2)
        self.speed = 5
        self.direction = pygame.Vector2(0, 0)
        self.next_direction = pygame.Vector2(0, 0)

    def check_events(self, event):
        if event.key == pygame.K_RIGHT:
            self.next_direction = pygame.Vector2(1, 0)
        elif event.key == pygame.K_LEFT:
            self.next_direction = pygame.Vector2(-1, 0)
        elif event.key == pygame.K_UP:
            self.next_direction = pygame.Vector2(0, -1)
        elif event.key == pygame.K_DOWN:
            self.next_direction = pygame.Vector2(0, 1)

    def update(self, maze):
        # Try to change direction if possible
        test_rect = self.rect.copy()
        test_rect.x += self.next_direction.x * self.speed
        test_rect.y += self.next_direction.y * self.speed
        
        if not test_rect.collidelist(maze.walls) != -1:
            self.direction = self.next_direction
        
        # Move in current direction
        self.rect.x += self.direction.x * self.speed
        self.rect.y += self.direction.y * self.speed
        
        # Check for wall collisions and correct position
        collision_index = self.rect.collidelist(maze.walls)
        if collision_index != -1:
            wall_rect = maze.walls[collision_index]
            if self.direction.x > 0:  # Moving right
                self.rect.right = wall_rect.left
            elif self.direction.x < 0:  # Moving left
                self.rect.left = wall_rect.right
            elif self.direction.y > 0:  # Moving down
                self.rect.bottom = wall_rect.top
            elif self.direction.y < 0:  # Moving up
                self.rect.top = wall_rect.bottom

    def draw(self):
        pygame.draw.circle(self.screen, self.color, self.rect.center, self.radius)
        
        # Draw Pacman's mouth
        if self.direction.length() > 0:
            start_angle = 0
            if self.direction.x > 0:
                start_angle = 30
            elif self.direction.x < 0:
                start_angle = 210
            elif self.direction.y > 0:
                start_angle = 120
            elif self.direction.y < 0:
                start_angle = 300
            
            pygame.draw.arc(
                self.screen, 
                (0, 0, 0), 
                self.rect, 
                start_angle * 0.0174533, 
                (start_angle + 300) * 0.0174533,
                self.radius // 2
            )