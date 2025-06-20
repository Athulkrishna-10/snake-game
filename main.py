import pygame
import random
import math
import sys
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
GAME_WIDTH = 800
GAME_HEIGHT = 600
SIDEBAR_WIDTH = 200
CELL_SIZE = 20
FPS = 60

# Colors (Modern UI Palette)
class Colors:
    DARK_BG = (18, 18, 25)
    GAME_BG = (25, 25, 35)
    SIDEBAR_BG = (35, 35, 45)
    NEON_GREEN = (57, 255, 20)
    NEON_BLUE = (0, 255, 255)
    NEON_PINK = (255, 20, 147)
    GOLD = (255, 215, 0)
    WHITE = (255, 255, 255)
    RED = (255, 69, 58)
    ORANGE = (255, 149, 0)
    PURPLE = (191, 90, 242)
    GRAY = (142, 142, 147)
    LIGHT_GRAY = (229, 229, 234)
    GRADIENT_START = (138, 43, 226)
    GRADIENT_END = (30, 144, 255)

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    PAUSED = 3
    GAME_OVER = 4
    HIGH_SCORES = 5

@dataclass
class Particle:
    x: float
    y: float
    dx: float
    dy: float
    life: float
    max_life: float
    color: Tuple[int, int, int]
    size: float

class SnakeGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("🐍 Elite Snake - Next Gen Gaming")
        self.clock = pygame.time.Clock()
        
        # Game state
        self.state = GameState.MENU
        self.score = 0
        self.high_score = self.load_high_score()
        self.level = 1
        self.speed = 8
        
        # Snake properties
        self.snake = [(GAME_WIDTH // 2, GAME_HEIGHT // 2)]
        self.direction = (CELL_SIZE, 0)
        self.grow_pending = 0
        
        # Food properties
        self.food_pos = self.spawn_food()
        self.food_type = "normal"
        self.special_food_timer = 0
        
        # Visual effects
        self.particles = []
        self.screen_shake = 0
        self.food_pulse = 0
        self.trail_positions = []
        
        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        # Animation timers
        self.menu_animation = 0
        self.game_time = 0
        
        # Load sounds (create placeholder sound objects)
        self.sounds = self.load_sounds()
        
    def load_sounds(self):
        # In a real implementation, you'd load actual sound files
        # For now, we'll create placeholder sound objects
        sounds = {}
        try:
            # sounds['eat'] = pygame.mixer.Sound('eat.wav')
            # sounds['game_over'] = pygame.mixer.Sound('game_over.wav')
            # sounds['level_up'] = pygame.mixer.Sound('level_up.wav')
            pass
        except:
            pass
        return sounds
    
    def load_high_score(self):
        try:
            with open('snake_highscore.txt', 'r') as f:
                return int(f.read())
        except:
            return 0
    
    def save_high_score(self):
        try:
            with open('snake_highscore.txt', 'w') as f:
                f.write(str(self.high_score))
        except:
            pass
    
    def spawn_food(self):
        while True:
            x = random.randint(1, (GAME_WIDTH - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
            y = random.randint(1, (GAME_HEIGHT - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
            if (x, y) not in self.snake:
                return (x, y)
    
    def create_explosion_particles(self, x, y, color):
        for _ in range(15):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 8)
            self.particles.append(Particle(
                x, y,
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                60, 60, color,
                random.uniform(2, 5)
            ))
    
    def update_particles(self):
        for particle in self.particles[:]:
            particle.x += particle.dx
            particle.y += particle.dy
            particle.life -= 1
            particle.dy += 0.1  # Gravity
            
            if particle.life <= 0:
                self.particles.remove(particle)
    
    def draw_gradient_rect(self, surface, rect, color1, color2):
        for y in range(rect.height):
            ratio = y / rect.height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            pygame.draw.line(surface, (r, g, b), 
                           (rect.x, rect.y + y), (rect.x + rect.width, rect.y + y))
    
    def draw_neon_text(self, text, font, color, x, y, glow=True):
        if glow:
            # Draw glow effect
            for offset in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
                glow_surf = font.render(text, True, (color[0]//3, color[1]//3, color[2]//3))
                self.screen.blit(glow_surf, (x + offset[0], y + offset[1]))
        
        # Draw main text
        text_surf = font.render(text, True, color)
        self.screen.blit(text_surf, (x, y))
        return text_surf.get_rect(topleft=(x, y))
    
    def draw_glowing_rect(self, surface, rect, color, glow_size=3):
        # Draw glow layers
        for i in range(glow_size):
            alpha = 50 - (i * 15)
            if alpha <= 0:
                continue
            glow_surf = pygame.Surface((rect.width + i*4, rect.height + i*4), pygame.SRCALPHA)
            glow_color = (*color, alpha)
            pygame.draw.rect(glow_surf, glow_color, glow_surf.get_rect(), border_radius=5)
            surface.blit(glow_surf, (rect.x - i*2, rect.y - i*2))
        
        # Draw main rectangle
        pygame.draw.rect(surface, color, rect, border_radius=5)
    
    def handle_menu_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                self.start_new_game()
            elif event.key == pygame.K_h:
                self.state = GameState.HIGH_SCORES
            elif event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                return False
        return True
    
    def handle_game_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = GameState.PAUSED
            elif event.key in [pygame.K_LEFT, pygame.K_a] and self.direction != (CELL_SIZE, 0):
                self.direction = (-CELL_SIZE, 0)
            elif event.key in [pygame.K_RIGHT, pygame.K_d] and self.direction != (-CELL_SIZE, 0):
                self.direction = (CELL_SIZE, 0)
            elif event.key in [pygame.K_UP, pygame.K_w] and self.direction != (0, CELL_SIZE):
                self.direction = (0, -CELL_SIZE)
            elif event.key in [pygame.K_DOWN, pygame.K_s] and self.direction != (0, -CELL_SIZE):
                self.direction = (0, CELL_SIZE)
        return True
    
    def start_new_game(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.level = 1
        self.speed = 8
        self.snake = [(GAME_WIDTH // 2, GAME_HEIGHT // 2)]
        self.direction = (CELL_SIZE, 0)
        self.grow_pending = 0
        self.food_pos = self.spawn_food()
        self.food_type = "normal"
        self.particles.clear()
        self.trail_positions.clear()
    
    def update_game(self):
        self.game_time += 1
        
        # Move snake every few frames based on speed
        if self.game_time % max(1, 12 - self.speed) == 0:
            # Add current head to trail
            head = self.snake[0]
            self.trail_positions.append((head[0], head[1], 20))  # x, y, life
            
            # Update trail
            self.trail_positions = [(x, y, life-1) for x, y, life in self.trail_positions if life > 0]
            
            # Move snake
            new_head = (head[0] + self.direction[0], head[1] + self.direction[1])
            
            # Check wall collision
            if (new_head[0] < 0 or new_head[0] >= GAME_WIDTH or 
                new_head[1] < 0 or new_head[1] >= GAME_HEIGHT):
                self.game_over()
                return
            
            # Check self collision
            if new_head in self.snake:
                self.game_over()
                return
            
            self.snake.insert(0, new_head)
            
            # Check food collision
            if new_head == self.food_pos:
                self.eat_food()
            else:
                if self.grow_pending > 0:
                    self.grow_pending -= 1
                else:
                    self.snake.pop()
        
        # Update special food timer
        self.special_food_timer += 1
        if self.special_food_timer > 600:  # 10 seconds at 60 FPS
            self.special_food_timer = 0
            self.food_type = "special" if random.random() < 0.3 else "normal"
        
        # Update food pulse animation
        self.food_pulse = (self.food_pulse + 0.2) % (2 * math.pi)
        
        # Update particles
        self.update_particles()
        
        # Update screen shake
        if self.screen_shake > 0:
            self.screen_shake -= 1
    
    def eat_food(self):
        if self.food_type == "special":
            points = 50
            self.grow_pending += 3
            self.create_explosion_particles(self.food_pos[0], self.food_pos[1], Colors.GOLD)
        else:
            points = 10
            self.grow_pending += 1
            self.create_explosion_particles(self.food_pos[0], self.food_pos[1], Colors.NEON_GREEN)
        
        self.score += points
        if self.score > self.high_score:
            self.high_score = self.score
        
        # Level up logic
        new_level = (self.score // 100) + 1
        if new_level > self.level:
            self.level = new_level
            self.speed = min(15, 8 + self.level)
        
        self.food_pos = self.spawn_food()
        self.food_type = "normal"
        self.special_food_timer = 0
    
    def game_over(self):
        self.state = GameState.GAME_OVER
        self.save_high_score()
        self.screen_shake = 20
        # Create big explosion
        for _ in range(30):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3, 12)
            self.particles.append(Particle(
                self.snake[0][0] + CELL_SIZE//2, self.snake[0][1] + CELL_SIZE//2,
                math.cos(angle) * speed, math.sin(angle) * speed,
                120, 120, Colors.RED, random.uniform(3, 8)
            ))
    
    def draw_menu(self):
        # Animated background
        self.menu_animation += 0.02
        
        # Gradient background
        self.draw_gradient_rect(self.screen, pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT),
                               Colors.GRADIENT_START, Colors.GRADIENT_END)
        
        # Animated particles in background
        for i in range(50):
            x = (i * 20 + self.menu_animation * 50) % WINDOW_WIDTH
            y = 100 + math.sin(self.menu_animation + i * 0.1) * 50
            alpha = int(128 + 127 * math.sin(self.menu_animation * 2 + i))
            color = (*Colors.NEON_BLUE, alpha)
            pygame.draw.circle(self.screen, Colors.NEON_BLUE, (int(x), int(y)), 2)
        
        # Title
        title_y = 150 + math.sin(self.menu_animation) * 10
        self.draw_neon_text("ELITE SNAKE", self.font_large, Colors.NEON_GREEN, 
                           WINDOW_WIDTH//2 - 120, int(title_y))
        
        # Subtitle
        self.draw_neon_text("Next Generation Gaming", self.font_small, Colors.WHITE,
                           WINDOW_WIDTH//2 - 100, int(title_y) + 60)
        
        # Menu options
        menu_y = 350
        self.draw_neon_text("PRESS SPACE TO START", self.font_medium, Colors.NEON_PINK,
                           WINDOW_WIDTH//2 - 140, menu_y)
        self.draw_neon_text("H - HIGH SCORES", self.font_small, Colors.LIGHT_GRAY,
                           WINDOW_WIDTH//2 - 80, menu_y + 50)
        self.draw_neon_text("ESC - QUIT", self.font_small, Colors.LIGHT_GRAY,
                           WINDOW_WIDTH//2 - 50, menu_y + 80)
        
        # High score display
        self.draw_neon_text(f"High Score: {self.high_score}", self.font_medium, Colors.GOLD,
                           WINDOW_WIDTH//2 - 80, menu_y + 120)
    
    def draw_game(self):
        # Apply screen shake
        shake_x = shake_y = 0
        if self.screen_shake > 0:
            shake_x = random.randint(-3, 3)
            shake_y = random.randint(-3, 3)
        
        # Background
        self.screen.fill(Colors.DARK_BG)
        
        # Game area
        game_rect = pygame.Rect(shake_x, shake_y, GAME_WIDTH, GAME_HEIGHT)
        pygame.draw.rect(self.screen, Colors.GAME_BG, game_rect)
        pygame.draw.rect(self.screen, Colors.NEON_BLUE, game_rect, 2)
        
        # Grid (subtle)
        for x in range(0, GAME_WIDTH, CELL_SIZE):
            pygame.draw.line(self.screen, (40, 40, 50), 
                           (x + shake_x, shake_y), (x + shake_x, GAME_HEIGHT + shake_y))
        for y in range(0, GAME_HEIGHT, CELL_SIZE):
            pygame.draw.line(self.screen, (40, 40, 50),
                           (shake_x, y + shake_y), (GAME_WIDTH + shake_x, y + shake_y))
        
        # Draw trail
        for x, y, life in self.trail_positions:
            alpha = int(life * 12.75)  # 255 / 20
            trail_color = (*Colors.NEON_GREEN, alpha)
            trail_surf = pygame.Surface((CELL_SIZE-2, CELL_SIZE-2), pygame.SRCALPHA)
            pygame.draw.rect(trail_surf, trail_color, trail_surf.get_rect(), border_radius=3)
            self.screen.blit(trail_surf, (x + 1 + shake_x, y + 1 + shake_y))
        
        # Draw snake with gradient effect
        for i, (x, y) in enumerate(self.snake):
            if i == 0:  # Head
                head_rect = pygame.Rect(x + shake_x, y + shake_y, CELL_SIZE, CELL_SIZE)
                self.draw_glowing_rect(self.screen, head_rect, Colors.NEON_GREEN, 2)
                # Eyes
                pygame.draw.circle(self.screen, Colors.WHITE, 
                                 (x + 5 + shake_x, y + 5 + shake_y), 2)
                pygame.draw.circle(self.screen, Colors.WHITE,
                                 (x + 15 + shake_x, y + 5 + shake_y), 2)
            else:  # Body
                intensity = max(50, 255 - i * 10)
                body_color = (0, intensity, 0)
                body_rect = pygame.Rect(x + 1 + shake_x, y + 1 + shake_y, 
                                      CELL_SIZE-2, CELL_SIZE-2)
                pygame.draw.rect(self.screen, body_color, body_rect, border_radius=3)
        
        # Draw food with pulsing effect
        pulse_size = 2 + math.sin(self.food_pulse) * 1
        food_color = Colors.GOLD if self.food_type == "special" else Colors.RED
        food_rect = pygame.Rect(self.food_pos[0] - pulse_size + shake_x, 
                               self.food_pos[1] - pulse_size + shake_y,
                               CELL_SIZE + pulse_size * 2, CELL_SIZE + pulse_size * 2)
        self.draw_glowing_rect(self.screen, food_rect, food_color, 3)
        
        # Draw particles
        for particle in self.particles:
            alpha = int(255 * (particle.life / particle.max_life))
            color = (*particle.color, alpha)
            particle_surf = pygame.Surface((particle.size * 2, particle.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surf, color, 
                             (int(particle.size), int(particle.size)), int(particle.size))
            self.screen.blit(particle_surf, (particle.x + shake_x, particle.y + shake_y))
        
        # Sidebar
        sidebar_rect = pygame.Rect(GAME_WIDTH, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(self.screen, Colors.SIDEBAR_BG, sidebar_rect)
        
        # Stats
        self.draw_neon_text("STATS", self.font_medium, Colors.NEON_BLUE, GAME_WIDTH + 20, 50)
        self.draw_neon_text(f"Score: {self.score}", self.font_small, Colors.WHITE, 
                           GAME_WIDTH + 20, 100, False)
        self.draw_neon_text(f"High: {self.high_score}", self.font_small, Colors.GOLD,
                           GAME_WIDTH + 20, 130, False)
        self.draw_neon_text(f"Level: {self.level}", self.font_small, Colors.NEON_PINK,
                           GAME_WIDTH + 20, 160, False)
        self.draw_neon_text(f"Speed: {self.speed}", self.font_small, Colors.ORANGE,
                           GAME_WIDTH + 20, 190, False)
        self.draw_neon_text(f"Length: {len(self.snake)}", self.font_small, Colors.NEON_GREEN,
                           GAME_WIDTH + 20, 220, False)
        
        # Controls
        self.draw_neon_text("CONTROLS", self.font_medium, Colors.NEON_BLUE, 
                           GAME_WIDTH + 20, 300)
        controls = [
            "WASD / Arrows - Move",
            "ESC - Pause"
        ]
        for i, control in enumerate(controls):
            self.draw_neon_text(control, self.font_small, Colors.GRAY,
                               GAME_WIDTH + 20, 340 + i * 25, False)
    
    def draw_game_over(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Game Over text
        self.draw_neon_text("GAME OVER", self.font_large, Colors.RED,
                           WINDOW_WIDTH//2 - 100, 250)
        
        # Final score
        self.draw_neon_text(f"Final Score: {self.score}", self.font_medium, Colors.WHITE,
                           WINDOW_WIDTH//2 - 80, 320)
        
        if self.score == self.high_score:
            self.draw_neon_text("NEW HIGH SCORE!", self.font_medium, Colors.GOLD,
                               WINDOW_WIDTH//2 - 90, 360)
        
        # Restart options
        self.draw_neon_text("SPACE - Play Again", self.font_small, Colors.NEON_GREEN,
                           WINDOW_WIDTH//2 - 80, 420)
        self.draw_neon_text("ESC - Main Menu", self.font_small, Colors.LIGHT_GRAY,
                           WINDOW_WIDTH//2 - 70, 450)
    
    def draw_paused(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))
        
        # Paused text
        self.draw_neon_text("PAUSED", self.font_large, Colors.NEON_BLUE,
                           WINDOW_WIDTH//2 - 70, 300)
        
        self.draw_neon_text("ESC - Resume", self.font_small, Colors.WHITE,
                           WINDOW_WIDTH//2 - 60, 360)
    
    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif self.state == GameState.MENU:
                    running = self.handle_menu_events(event)
                
                elif self.state == GameState.PLAYING:
                    running = self.handle_game_events(event)
                
                elif self.state == GameState.PAUSED:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.state = GameState.PLAYING
                        elif event.key == pygame.K_q:
                            self.state = GameState.MENU
                
                elif self.state == GameState.GAME_OVER:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            self.start_new_game()
                        elif event.key == pygame.K_ESCAPE:
                            self.state = GameState.MENU
            
            # Update
            if self.state == GameState.PLAYING:
                self.update_game()
            
            # Draw
            if self.state == GameState.MENU:
                self.draw_menu()
            elif self.state in [GameState.PLAYING, GameState.PAUSED, GameState.GAME_OVER]:
                self.draw_game()
                if self.state == GameState.PAUSED:
                    self.draw_paused()
                elif self.state == GameState.GAME_OVER:
                    self.draw_game_over()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = SnakeGame()
    game.run()