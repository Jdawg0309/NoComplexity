import pygame

class Maze:
    def __init__(self, game):
        self.screen = game.screen
        self.settings = game.settings
        self.wall_size = (self.settings.cell_size, self.settings.cell_size)
        self.maze_layout = [
            "XXXXXXXXXXXXXXXXXXXXXXXXX",
            "X............X...........X",
            "X.XXXX.XXXXX.X.XXXXX.XXXX",
            "X.XXXX.XXXXX.X.XXXXX.XXXX",
            "X........................X",
            "X.XXXX.X.XXXXXXX.X.XXXX.X",
            "X......X....X....X......X",
            "XXXXXX.XXXX X XXXX.XXXXXX",
            "     X.XXXX X XXXX.X     ",
            "XXXXXX.X          X.XXXXX",
            "      . .XXXXXXXXX. .    ",
            "XXXXXX.X XXXXXXXXX X.XXXX",
            "     X.X          X.X    ",
            "XXXXXX.X XXXXXXXXX X.XXXX",
            "X............X...........X",
            "X.XXXX.XXXXX.X.XXXXX.XXXX",
            "X...X................X...X",
            "XXX.X.X.XXXXXXX.X.X.X.XXX",
            "X......X....X....X......X",
            "X.XXXXXXXXXX.X.XXXXXXXXXX",
            "X........................X",
            "XXXXXXXXXXXXXXXXXXXXXXXXX"
        ]
        self.walls = []
        self.pellets = []
        self._create_walls()
        self._create_pellets()

    def _create_walls(self):
        for row_index, row in enumerate(self.maze_layout):
            for col_index, cell in enumerate(row):
                if cell == 'X':
                    x = col_index * self.wall_size[0]
                    y = row_index * self.wall_size[1]
                    wall_rect = pygame.Rect(x, y, self.wall_size[0], self.wall_size[1])
                    self.walls.append(wall_rect)

    def _create_pellets(self):
        for row_index, row in enumerate(self.maze_layout):
            for col_index, cell in enumerate(row):
                if cell == '.':
                    x = col_index * self.wall_size[0] + self.wall_size[0] // 2
                    y = row_index * self.wall_size[1] + self.wall_size[1] // 2
                    pellet_rect = pygame.Rect(0, 0, 8, 8)
                    pellet_rect.center = (x, y)
                    self.pellets.append(pellet_rect)

    def draw(self):
        # Draw walls
        wall_color = (0, 0, 255)  # Blue walls
        for wall_rect in self.walls:
            pygame.draw.rect(self.screen, wall_color, wall_rect)
        
        # Draw pellets
        pellet_color = (255, 255, 255)  # White pellets
        for pellet_rect in self.pellets:
            pygame.draw.ellipse(self.screen, pellet_color, pellet_rect)