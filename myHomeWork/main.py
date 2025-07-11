import pygame
from game_objects import Paddle, Ball, Brick, PowerUp, Laser, Particle, Firework
import random
import sys

# Setup (unchanged)
pygame.init()
pygame.mixer.init()
clock = pygame.time.Clock()
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("PyGame Arkanoid")

# Colors, Fonts, Mute Setup (same as before)
BG_COLOR = pygame.Color('grey12')
BRICK_COLORS = [(178, 34, 34), (255, 165, 0), (255, 215, 0), (50, 205, 50)]
title_font = pygame.font.Font(None, 70)
game_font = pygame.font.Font(None, 40)
message_font = pygame.font.Font(None, 30)

# Sound Setup with Mute
muted = False
def toggle_mute():
    global muted
    muted = not muted
    volume = 0 if muted else 1
    for s in [bounce_sound, brick_break_sound, game_over_sound, laser_sound]:
        s.set_volume(volume)

try:
    bounce_sound = pygame.mixer.Sound('bounce.wav')
    brick_break_sound = pygame.mixer.Sound('brick_break.wav')
    game_over_sound = pygame.mixer.Sound('game_over.wav')
    laser_sound = pygame.mixer.Sound('laser.wav')
    toggle_mute()
except:
    class Dummy: 
        def play(self): pass
        def set_volume(self, v): pass
    bounce_sound = brick_break_sound = game_over_sound = laser_sound = Dummy()

# Game Objects
paddle = Paddle(screen_width, screen_height)
ball = Ball(screen_width, screen_height)

# Brick Wall Function with Level Support
def create_brick_wall(level=1):
    bricks = []
    rows = 4 + level
    cols = 10
    brick_width, brick_height = 75, 20
    padding = 5
    for row in range(rows):
        for col in range(cols):
            x = col * (brick_width + padding) + padding
            y = row * (brick_height + padding) + 50
            color = BRICK_COLORS[row % len(BRICK_COLORS)]
            bricks.append(Brick(x, y, brick_width, brick_height, color))
    return bricks

# Variables
bricks = create_brick_wall()
power_ups, lasers, particles, fireworks = [], [], [], []
game_state = 'title_screen'
score, lives, message_timer = 0, 3, 0
display_message = ""
firework_timer, level = 0, 1

# Game Loop
while True:
    # Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if game_state in ['title_screen', 'you_win', 'game_over']:
                    paddle.reset()
                    ball.reset()
                    level = 1
                    bricks = create_brick_wall(level)
                    score, lives = 0, 3
                    power_ups.clear(); lasers.clear(); particles.clear(); fireworks.clear()
                    game_state = 'playing'
                elif ball.is_glued:
                    ball.is_glued = False
            elif event.key == pygame.K_m:
                toggle_mute()
            elif event.key == pygame.K_f and paddle.has_laser:
                lasers.append(Laser(paddle.rect.centerx - 30, paddle.rect.top))
                lasers.append(Laser(paddle.rect.centerx + 30, paddle.rect.top))
                laser_sound.play()

    # Update
    screen.fill(BG_COLOR)

    if game_state == 'title_screen':
        screen.blit(title_font.render("ARKANOID", True, (255,255,255)), (screen_width//2 - 130, screen_height//2 - 80))
        screen.blit(game_font.render("Press SPACE to Start", True, (255,255,255)), (screen_width//2 - 140, screen_height//2 + 10))

    elif game_state == 'playing':
        paddle.update()
        keys = pygame.key.get_pressed()
        ball_status, collision = ball.update(paddle, keys[pygame.K_SPACE])

        if ball_status == 'lost':
            lives -= 1
            if lives <= 0:
                game_state = 'game_over'
                game_over_sound.play()
            else:
                ball.reset()
                paddle.reset()

        elif collision in ['wall', 'paddle']:
            bounce_sound.play()
            for _ in range(5):
                particles.append(Particle(ball.rect.centerx, ball.rect.centery, (255,255,0), 1,3,1,3,0))

        for brick in bricks[:]:
            if ball.rect.colliderect(brick.rect):
                ball.speed_y *= -1
                score += 10
                bricks.remove(brick)
                brick_break_sound.play()
                for _ in range(10):
                    particles.append(Particle(brick.rect.centerx, brick.rect.centery, brick.color, 1, 3, 1, 3, 0.05))
                if random.random() < 0.4:
                    p_type = random.choice(['grow', 'laser', 'glue', 'slow', 'shrink', 'fast', 'extra_life'])
                    power_ups.append(PowerUp(brick.rect.centerx, brick.rect.centery, p_type))
                break

        for power_up in power_ups[:]:
            power_up.update()
            if power_up.rect.top > screen_height:
                power_ups.remove(power_up)
            elif paddle.rect.colliderect(power_up.rect):
                msg = power_up.PROPERTIES[power_up.type]['message']
                display_message = msg
                message_timer = 120
                if power_up.type in ['grow', 'laser', 'glue', 'shrink']:
                    paddle.activate_power_up(power_up.type)
                elif power_up.type in ['slow', 'fast']:
                    ball.activate_power_up(power_up.type)
                elif power_up.type == 'extra_life':
                    lives += 1
                power_ups.remove(power_up)

        for laser in lasers[:]:
            laser.update()
            if laser.rect.bottom < 0:
                lasers.remove(laser)
            else:
                for brick in bricks[:]:
                    if laser.rect.colliderect(brick.rect):
                        score += 10
                        bricks.remove(brick)
                        brick_break_sound.play()
                        lasers.remove(laser)
                        break

        if not bricks:
            level += 1
            bricks = create_brick_wall(level)
            ball.reset()
            paddle.reset()

        paddle.draw(screen)
        ball.draw(screen)
        for b in bricks: b.draw(screen)
        for p in power_ups: p.draw(screen)
        for l in lasers: l.draw(screen)

        screen.blit(game_font.render(f"Score: {score}", True, (255,255,255)), (10, 10))
        screen.blit(game_font.render(f"Lives: {lives}", True, (255,255,255)), (700, 10))
        screen.blit(game_font.render(f"Level: {level}", True, (255,255,255)), (360, 10))

    elif game_state == 'you_win' or game_state == 'game_over':
        msg = "YOU WIN!" if game_state == 'you_win' else "GAME OVER"
        screen.blit(game_font.render(msg, True, (255,255,255)), (screen_width//2 - 80, screen_height//2 - 30))
        screen.blit(game_font.render("Press SPACE to return to Title", True, (255,255,255)), (screen_width//2 - 200, screen_height//2 + 30))

    if message_timer > 0:
        message_timer -= 1
        screen.blit(message_font.render(display_message, True, (255,255,255)), (screen_width//2 - 100, screen_height - 60))

    # Particles
    for p in particles[:]:
        p.update()
        if p.size <= 0:
            particles.remove(p)
    for p in particles:
        p.draw(screen)

    # Mute Status
    mute_text = message_font.render("Muted" if muted else "Sound On", True, (200, 200, 200))
    screen.blit(mute_text, (screen_width - mute_text.get_width() - 10, screen_height - 30))

    pygame.display.flip()
    clock.tick(60)
