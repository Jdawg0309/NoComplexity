import pygame
import sys
import random

def draw_pipes(screen, pipes, pipe_width, pipe_height, gap_size):
    """Draws the pipes on the screen with a pixelated effect."""
    for pipe in pipes:
        # Upper pipe
        pygame.draw.rect(screen, pygame.Color('darkgreen'), pygame.Rect(pipe['x'], 0, pipe_width, pipe['top']), border_radius=0)
        # Lower pipe
        pygame.draw.rect(screen, pygame.Color('darkgreen'), pygame.Rect(pipe['x'], pipe['bottom'], pipe_width, pipe_height - pipe['bottom']), border_radius=0)

def draw_bird(screen, bird_pos, bird_size):
    """Draws a pixelated bird on the screen."""
    bird_body = pygame.Rect(bird_pos[0], bird_pos[1], bird_size, bird_size)
    pygame.draw.rect(screen, pygame.Color('yellow'), bird_body)  # Body
    pygame.draw.rect(screen, pygame.Color('black'), (bird_body.x + bird_size * 0.6, bird_body.y + bird_size * 0.2, 3, 3))  # Eye

def draw_clouds(screen, clouds):
    """Draws clouds on the screen."""
    for cloud in clouds:
        pygame.draw.ellipse(screen, pygame.Color('white'), cloud)

def update_clouds(clouds, screen_width):
    """Updates the position of clouds and removes off-screen clouds."""
    for cloud in clouds:
        cloud.x -= 2  # Move clouds to the left
    return [cloud for cloud in clouds if cloud.x + cloud.width > 0]

def check_collision(bird_pos, bird_size, pipes, pipe_width, pipe_height, gap_size):
    """Checks for collisions between the bird and the pipes or the ground."""
    bird_rect = pygame.Rect(bird_pos[0], bird_pos[1], bird_size, bird_size)
    for pipe in pipes:
        pipe_top = pygame.Rect(pipe['x'], 0, pipe_width, pipe['top'])
        pipe_bottom = pygame.Rect(pipe['x'], pipe['bottom'], pipe_width, pipe_height - pipe['bottom'])
        if bird_rect.colliderect(pipe_top) or bird_rect.colliderect(pipe_bottom):
            return True
    if bird_pos[1] + bird_size > pipe_height:
        return True
    return False

def draw_score(screen, score, font):
    """Draws the score on the top right corner of the screen."""
    score_surf = font.render(f"Score: {score}", True, pygame.Color('black'))
    score_rect = score_surf.get_rect(topright=(390, 10))
    screen.blit(score_surf, score_rect)

def main():
    pygame.init()
    screen_width, screen_height = 400, 600
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.SCALED | pygame.RESIZABLE)
    pygame.display.set_caption("Flappy Bird")

    clock = pygame.time.Clock()
    bird_size = 20
    bird_pos = [50, screen_height // 2]
    gravity = 0.5
    bird_velocity = 0
    jump_height = -10
    pipe_width = 60
    pipe_gap = 150
    pipe_frequency = 1500  # milliseconds
    last_pipe = pygame.time.get_ticks() - pipe_frequency
    pipes = []
    clouds = [pygame.Rect(random.randint(0, screen_width), random.randint(0, 100), 60, 30) for _ in range(5)]
    score = 0
    font = pygame.font.Font(None, 36)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird_velocity = jump_height

        # Bird physics
        bird_velocity += gravity
        bird_pos[1] += bird_velocity

        # Pipe generation
        current_time = pygame.time.get_ticks()
        if current_time - last_pipe > pipe_frequency:
            pipe_height = random.randint(100, 300)
            pipes.append({'x': screen_width, 'top': pipe_height, 'bottom': pipe_height + pipe_gap})
            last_pipe = current_time
            score += 1  # Increase score for each new pipe

        # Move pipes
        for pipe in pipes:
            pipe['x'] -= 5
        pipes = [pipe for pipe in pipes if pipe['x'] > -pipe_width]

        # Update clouds
        clouds = update_clouds(clouds, screen_width)
        if len(clouds) < 5 and random.random() < 0.01:
            clouds.append(pygame.Rect(screen_width, random.randint(0, 100), 60, 30))

        # Check for collisions
        if check_collision(bird_pos, bird_size, pipes, pipe_width, screen_height, pipe_gap):
            running = False

        # Drawing
        screen.fill(pygame.Color('skyblue'))
        draw_clouds(screen, clouds)
        draw_pipes(screen, pipes, pipe_width, screen_height, pipe_gap)
        draw_bird(screen, bird_pos, bird_size)
        draw_score(screen, score, font)

        pygame.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    main()