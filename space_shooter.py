import pygame
import random
import sys
import os

# --- Initial Setup ---
pygame.init()
WIDTH, HEIGHT = 800, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter - Upgraded")

FPS = 60
clock = pygame.time.Clock()

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED   = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE  = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
PURPLE = (180, 0, 255)

# --- Player Settings ---
PLAYER_WIDTH, PLAYER_HEIGHT = 50, 40
PLAYER_SPEED = 6
BASE_SHOOT_COOLDOWN = 300      # ms
RAPID_FIRE_COOLDOWN = 120      # ms

# --- Bullet Settings ---
BULLET_WIDTH, BULLET_HEIGHT = 5, 15
BULLET_SPEED = 10

# --- Enemy Settings (base) ---
ENEMY_WIDTH, ENEMY_HEIGHT = 40, 30
ENEMY_SPEED_MIN = 2
ENEMY_SPEED_MAX = 5
ENEMY_SPAWN_INTERVAL = 700  # ms

# --- Power-Up Settings ---
POWERUP_WIDTH, POWERUP_HEIGHT = 25, 25
POWERUP_SPEED = 3
POWERUP_INTERVAL = 10000  # ms between spawns
POWERUP_DURATION = 6000   # ms duration for timed powerups

FONT = pygame.font.SysFont("arial", 24)

# --- Asset holders (may stay None if files not found) ---
PLAYER_IMG = None
ENEMY_IMG = None
BULLET_IMG = None
BG_IMG = None
POWERUP_IMG = None

SHOOT_SOUND = None
EXPLOSION_SOUND = None
POWERUP_SOUND = None


def safe_load_image(name, size=None):
    """Try to load an image, return None if it fails."""
    if not os.path.exists(name):
        return None
    try:
        img = pygame.image.load(name).convert_alpha()
        if size:
            img = pygame.transform.scale(img, size)
        return img
    except Exception:
        return None


def safe_load_sound(name):
    """Try to load a sound, return None if it fails."""
    if not os.path.exists(name):
        return None
    try:
        return pygame.mixer.Sound(name)
    except Exception:
        return None


def load_assets():
    global PLAYER_IMG, ENEMY_IMG, BULLET_IMG, BG_IMG, POWERUP_IMG
    global SHOOT_SOUND, EXPLOSION_SOUND, POWERUP_SOUND

    # Images – put PNGs in the same folder as this script with these names
    PLAYER_IMG = safe_load_image("player.png", (PLAYER_WIDTH, PLAYER_HEIGHT))
    ENEMY_IMG = safe_load_image("enemy.png", (ENEMY_WIDTH, ENEMY_HEIGHT))
    BULLET_IMG = safe_load_image("bullet.png", (BULLET_WIDTH, BULLET_HEIGHT))
    POWERUP_IMG = safe_load_image("powerup.png", (POWERUP_WIDTH, POWERUP_HEIGHT))
    BG_IMG = safe_load_image("background.png", (WIDTH, HEIGHT))

    # Sounds – optional .wav files
    SHOOT_SOUND = safe_load_sound("shoot.wav")
    EXPLOSION_SOUND = safe_load_sound("explosion.wav")
    POWERUP_SOUND = safe_load_sound("powerup.wav")


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

        self.shield_ms = 0
        self.rapid_fire_ms = 0

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

    def current_cooldown(self):
        if self.rapid_fire_ms > 0:
            return RAPID_FIRE_COOLDOWN
        return BASE_SHOOT_COOLDOWN

    def can_shoot(self):
        now = pygame.time.get_ticks()
        return now - self.last_shot_time >= self.current_cooldown()

    def shoot(self):
        self.last_shot_time = pygame.time.get_ticks()
        if SHOOT_SOUND:
            SHOOT_SOUND.play()
        bullet = Bullet(self.rect.centerx, self.rect.top)
        return bullet

    def update_powerups(self, dt_ms):
        if self.shield_ms > 0:
            self.shield_ms = max(0, self.shield_ms - dt_ms)
        if self.rapid_fire_ms > 0:
            self.rapid_fire_ms = max(0, self.rapid_fire_ms - dt_ms)

    def has_shield(self):
        return self.shield_ms > 0

    def give_shield(self):
        self.shield_ms = POWERUP_DURATION

    def give_rapid_fire(self):
        self.rapid_fire_ms = POWERUP_DURATION

    def draw(self, surface):
        if PLAYER_IMG:
            surface.blit(PLAYER_IMG, self.rect)
        else:
            # Fallback: triangle spaceship
            pygame.draw.polygon(
                surface,
                BLUE,
                [
                    (self.rect.centerx, self.rect.top),
                    (self.rect.left, self.rect.bottom),
                    (self.rect.right, self.rect.bottom),
                ],
            )

        # Draw shield glow if active
        if self.has_shield():
            pygame.draw.circle(
                surface,
                CYAN,
                self.rect.center,
                max(self.rect.width, self.rect.height) // 2 + 8,
                2,
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
        if BULLET_IMG:
            surface.blit(BULLET_IMG, self.rect)
        else:
            pygame.draw.rect(surface, YELLOW, self.rect)


class Enemy:
    def __init__(self, speed_min, speed_max):
        x = random.randint(0, WIDTH - ENEMY_WIDTH)
        y = random.randint(-150, -ENEMY_HEIGHT)
        self.rect = pygame.Rect(x, y, ENEMY_WIDTH, ENEMY_HEIGHT)
        self.speed = random.randint(speed_min, speed_max)

    def update(self):
        self.rect.y += self.speed

    def off_screen(self):
        return self.rect.top > HEIGHT

    def draw(self, surface):
        if ENEMY_IMG:
            surface.blit(ENEMY_IMG, self.rect)
        else:
            pygame.draw.rect(surface, RED, self.rect)


class PowerUp:
    def __init__(self, kind):
        # kind: "shield" or "rapid_fire"
        self.kind = kind
        x = random.randint(0, WIDTH - POWERUP_WIDTH)
        y = random.randint(-200, -POWERUP_HEIGHT)
        self.rect = pygame.Rect(x, y, POWERUP_WIDTH, POWERUP_HEIGHT)
        self.speed = POWERUP_SPEED

    def update(self):
        self.rect.y += self.speed

    def off_screen(self):
        return self.rect.top > HEIGHT

    def draw(self, surface):
        if POWERUP_IMG:
            surface.blit(POWERUP_IMG, self.rect)
        else:
            color = CYAN if self.kind == "shield" else PURPLE
            pygame.draw.ellipse(surface, color, self.rect)


def draw_text(surface, text, x, y, color=WHITE):
    img = FONT.render(text, True, color)
    surface.blit(img, (x, y))


def draw_background():
    if BG_IMG:
        WIN.blit(BG_IMG, (0, 0))
    else:
        WIN.fill(BLACK)
        # basic stars
        for _ in range(40):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            pygame.draw.circle(WIN, WHITE, (x, y), 1)


def main():
    load_assets()

    run = True
    player = Player()
    bullets = []
    enemies = []
    powerups = []
    score = 0

    last_enemy_spawn = 0
    last_powerup_spawn = 0
    game_over = False

    while run:
        dt = clock.tick(FPS)  # ms since last frame

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if game_over and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return main()

        keys = pygame.key.get_pressed()

        # Difficulty scaling based on score
        difficulty_level = score // 100  # every 100 points -> harder
        enemy_spawn_interval = max(ENEMY_SPAWN_INTERVAL - difficulty_level * 70, 250)
        enemy_speed_min = ENEMY_SPEED_MIN + difficulty_level
        enemy_speed_max = ENEMY_SPEED_MAX + difficulty_level

        if not game_over:
            # Player updates
            player.move(keys)
            player.update_powerups(dt)

            # Shooting
            if (keys[pygame.K_SPACE] or keys[pygame.K_UP]) and player.can_shoot():
                bullets.append(player.shoot())

            now = pygame.time.get_ticks()

            # Spawn Enemies
            if now - last_enemy_spawn >= enemy_spawn_interval:
                enemies.append(Enemy(enemy_speed_min, enemy_speed_max))
                last_enemy_spawn = now

            # Spawn PowerUps occasionally
            if now - last_powerup_spawn >= POWERUP_INTERVAL:
                kind = random.choice(["shield", "rapid_fire"])
                powerups.append(PowerUp(kind))
                last_powerup_spawn = now

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
                    # Enemy slipped through -> damage
                    if player.has_shield():
                        player.shield_ms = 0  # shield absorbs it
                    else:
                        player.lives -= 1
                        if player.lives <= 0:
                            game_over = True

            # Update PowerUps
            for pu in powerups[:]:
                pu.update()
                if pu.off_screen():
                    powerups.remove(pu)

            # Bullet-Enemy collisions
            for enemy in enemies[:]:
                for bullet in bullets[:]:
                    if enemy.rect.colliderect(bullet.rect):
                        enemies.remove(enemy)
                        bullets.remove(bullet)
                        score += 10
                        if EXPLOSION_SOUND:
                            EXPLOSION_SOUND.play()
                        break

            # Enemy-Player collisions
            for enemy in enemies[:]:
                if enemy.rect.colliderect(player.rect):
                    enemies.remove(enemy)
                    if player.has_shield():
                        player.shield_ms = 0
                    else:
                        player.lives -= 1
                        if player.lives <= 0:
                            game_over = True

            # PowerUp-Player collisions
            for pu in powerups[:]:
                if pu.rect.colliderect(player.rect):
                    powerups.remove(pu)
                    if POWERUP_SOUND:
                        POWERUP_SOUND.play()
                    if pu.kind == "shield":
                        player.give_shield()
                    elif pu.kind == "rapid_fire":
                        player.give_rapid_fire()

        # --- Drawing ---
        draw_background()

        # Draw objects
        player.draw(WIN)
        for bullet in bullets:
            bullet.draw(WIN)
        for enemy in enemies:
            enemy.draw(WIN)
        for pu in powerups:
            pu.draw(WIN)

        # HUD
        draw_text(WIN, f"Score: {score}", 10, 10)
        draw_text(WIN, f"Lives: {player.lives}", 10, 40)

        if player.rapid_fire_ms > 0:
            draw_text(WIN, "RAPID FIRE", WIDTH - 170, 10, YELLOW)
        if player.shield_ms > 0:
            draw_text(WIN, "SHIELD", WIDTH - 130, 40, CYAN)

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
