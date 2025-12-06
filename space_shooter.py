import pygame
import random
import sys

# --- Initial Setup ---
pygame.init()
WIDTH, HEIGHT = 800, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter")

FPS = 60
clock = pygame.time.Clock()

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED   = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE  = (0, 0, 255)
YELLOW = (255, 255, 0)

# --- Player Settings ---
PLAYER_WIDTH, PLAYER_HEIGHT = 50, 40
PLAYER_SPEED = 6

# --- Bullet Settings ---
BULLET_WIDTH, BULLET_HEIGHT = 5, 15
BULLET_SPEED = 10
SHOOT_COOLDOWN = 300  # milliseconds between shots

# --- Enemy Settings ---
ENEMY_WIDTH, ENEMY_HEIGHT = 40, 30
ENEMY_SPEED_MIN = 2
ENEMY_SPEED_MAX = 5
ENEMY_SPAWN_INTERVAL = 700  # ms

FONT = pygame.font.SysFont("arial", 24)


class Player:
    def __init__(self):
        self.rect = pygame.Rect(
            WIDTH // 2 - PLAYER_WIDTH // 2,
            HEIGHT - PLAYER_HEIGHT - 10,
            PLAYER_WIDTH,
            PLAYER_HEIGHT,
        )
        self.speed = PLAYER_SPEED
        self.last_shot_time = 0
        self.lives = 3

    def move(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed

        # Keep inside screen
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH

    def can_shoot(self):
        now = pygame.time.get_ticks()
        return now - self.last_shot_time >= SHOOT_COOLDOWN

    def shoot(self):
        self.last_shot_time = pygame.time.get_ticks()
        bullet = Bullet(self.rect.centerx, self.rect.top)
        return bullet

    def draw(self, surface):
        # Draw a simple triangle spaceship
        pygame.draw.polygon(
            surface,
            BLUE,
            [
                (self.rect.centerx, self.rect.top),
                (self.rect.left, self.rect.bottom),
                (self.rect.right, self.rect.bottom),
            ],
        )


class Bullet:
    def __init__(self, x, y):
        self.rect = pygame.Rect(
            x - BULLET_WIDTH // 2,
            y - BULLET_HEIGHT,
            BULLET_WIDTH,
            BULLET_HEIGHT,
        )
        self.speed = BULLET_SPEED

    def update(self):
        self.rect.y -= self.speed

    def off_screen(self):
        return self.rect.bottom < 0

    def draw(self, surface):
        pygame.draw.rect(surface, YELLOW, self.rect)


class Enemy:
    def __init__(self):
        x = random.randint(0, WIDTH - ENEMY_WIDTH)
        y = random.randint(-150, -ENEMY_HEIGHT)
        self.rect = pygame.Rect(x, y, ENEMY_WIDTH, ENEMY_HEIGHT)
        self.speed = random.randint(ENEMY_SPEED_MIN, ENEMY_SPEED_MAX)

    def update(self):
        self.rect.y += self.speed

    def off_screen(self):
        return self.rect.top > HEIGHT

    def draw(self, surface):
        pygame.draw.rect(surface, RED, self.rect)


def draw_text(surface, text, x, y, color=WHITE):
    img = FONT.render(text, True, color)
    surface.blit(img, (x, y))


def main():
    run = True
    player = Player()
    bullets = []
    enemies = []
    score = 0
    last_enemy_spawn = 0
    game_over = False

    while run:
        clock.tick(FPS)

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Restart on Enter if game over
            if game_over and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return main()

        keys = pygame.key.get_pressed()

        if not game_over:
            # Player Movement
            player.move(keys)

            # Shooting
            if (keys[pygame.K_SPACE] or keys[pygame.K_UP]) and player.can_shoot():
                bullets.append(player.shoot())

            # Spawn Enemies
            now = pygame.time.get_ticks()
            if now - last_enemy_spawn >= ENEMY_SPAWN_INTERVAL:
                enemies.append(Enemy())
                last_enemy_spawn = now

            # Update Bullets
            for bullet in bullets[:]:
                bullet.update()
                if bullet.off_screen():
                    bullets.remove(bullet)

            # Update Enemies
            for enemy in enemies[:]:
                enemy.update()
                if enemy.off_screen():
                    enemies.remove(enemy)
                    # Player loses a life if enemy passes through
                    player.lives -= 1
                    if player.lives <= 0:
                        game_over = True

            # Bullet-Enemy collisions
            for enemy in enemies[:]:
                for bullet in bullets[:]:
                    if enemy.rect.colliderect(bullet.rect):
                        enemies.remove(enemy)
                        bullets.remove(bullet)
                        score += 10
                        break  # enemy is gone, move to next enemy

            # Enemy-Player collisions
            for enemy in enemies[:]:
                if enemy.rect.colliderect(player.rect):
                    enemies.remove(enemy)
                    player.lives -= 1
                    if player.lives <= 0:
                        game_over = True

        # --- Drawing ---
        WIN.fill(BLACK)

        # Background "stars"
        for _ in range(40):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            pygame.draw.circle(WIN, WHITE, (x, y), 1)

        # Draw objects
        player.draw(WIN)
        for bullet in bullets:
            bullet.draw(WIN)
        for enemy in enemies:
            enemy.draw(WIN)

        # HUD
        draw_text(WIN, f"Score: {score}", 10, 10)
        draw_text(WIN, f"Lives: {player.lives}", 10, 40)

        if game_over:
            draw_text(WIN, "GAME OVER", WIDTH // 2 - 80, HEIGHT // 2 - 20, RED)
            draw_text(
                WIN,
                "Press ENTER to play again",
                WIDTH // 2 - 160,
                HEIGHT // 2 + 20,
                WHITE,
            )

        pygame.display.flip()


if __name__ == "__main__":
    main()
