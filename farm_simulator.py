import pygame
import random
import math
import sys
import time

# --- Configuration ---
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60
DATA_FILE = "ldr_data.txt"

# Colors
GRASS_COLOR = (34, 139, 34)
FENCE_COLOR = (255, 0, 0)
CROP_COLOR = (154, 205, 50)
ANIMAL_COLOR = (255, 255, 255) # White circles if emoji fails

# Fence boundaries
FENCE_X = 200
FENCE_Y = 150
FENCE_WIDTH = 400
FENCE_HEIGHT = 300

class Animal:
    def __init__(self):
        # Start at edges (outside the fence)
        if random.choice([True, False]):
            self.x = random.choice([random.randint(0, FENCE_X - 50), random.randint(FENCE_X + FENCE_WIDTH + 50, WINDOW_WIDTH)])
            self.y = random.randint(0, WINDOW_HEIGHT)
        else:
            self.x = random.randint(0, WINDOW_WIDTH)
            self.y = random.choice([random.randint(0, FENCE_Y - 50), random.randint(FENCE_Y + FENCE_HEIGHT + 50, WINDOW_HEIGHT)])
            
        self.radius = 15
        # Pick a random direction
        angle = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(1.0, 2.5)
        self.vx = math.cos(angle) * self.speed
        self.vy = math.sin(angle) * self.speed
        
        self.change_dir_timer = random.randint(60, 180)
        
    def move(self):
        self.change_dir_timer -= 1
        if self.change_dir_timer <= 0:
            angle = random.uniform(0, 2 * math.pi)
            self.vx = math.cos(angle) * self.speed
            self.vy = math.sin(angle) * self.speed
            self.change_dir_timer = random.randint(60, 180)
            
        self.x += self.vx
        self.y += self.vy
        
        # Bounce off screen edges
        if self.x < self.radius or self.x > WINDOW_WIDTH - self.radius:
            self.vx *= -1
            self.x = max(self.radius, min(self.x, WINDOW_WIDTH - self.radius))
        if self.y < self.radius or self.y > WINDOW_HEIGHT - self.radius:
            self.vy *= -1
            self.y = max(self.radius, min(self.y, WINDOW_HEIGHT - self.radius))

    def check_laser_collision(self):
        # Bounding box collision with the 4 lines of the fence
        left = self.x - self.radius
        right = self.x + self.radius
        top = self.y - self.radius
        bottom = self.y + self.radius
        
        # Check Top Line
        if (left < FENCE_X + FENCE_WIDTH and right > FENCE_X) and (abs(self.y - FENCE_Y) < self.radius):
            return True
        # Check Bottom Line
        if (left < FENCE_X + FENCE_WIDTH and right > FENCE_X) and (abs(self.y - (FENCE_Y + FENCE_HEIGHT)) < self.radius):
            return True
        # Check Left Line
        if (top < FENCE_Y + FENCE_HEIGHT and bottom > FENCE_Y) and (abs(self.x - FENCE_X) < self.radius):
            return True
        # Check Right Line
        if (top < FENCE_Y + FENCE_HEIGHT and bottom > FENCE_Y) and (abs(self.x - (FENCE_X + FENCE_WIDTH)) < self.radius):
            return True
            
        return False

def write_data(ldr_value, status):
    try:
        with open(DATA_FILE, "w") as f:
            f.write(f"{ldr_value},{status}")
    except:
        pass

def main():
    # Ensure Pygame is installed
    try:
        pygame.init()
    except Exception as e:
        print("Pygame could not be initialized:", e)
        sys.exit(1)
        
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Farm Laser Fencing Simulation")
    clock = pygame.time.Clock()
    
    # Simple fallback font
    font = pygame.font.SysFont("Arial", 24, bold=True)
    title_text = font.render("Farm Perimeter Monitor", True, (255,255,255))
    
    animals = [Animal() for _ in range(8)]
    last_data_update = time.time()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
        # Update logic
        intrusion = False
        for a in animals:
            a.move()
            if a.check_laser_collision():
                intrusion = True
                
        # Update data file every 0.2 seconds to interface with Streamlit
        if time.time() - last_data_update > 0.2:
            if intrusion:
                write_data(random.randint(800, 950), "INTRUSION")
            else:
                write_data(random.randint(100, 300), "SECURE")
            last_data_update = time.time()

        # Render Graphics
        screen.fill(GRASS_COLOR)
        
        # Draw Crop Area (inside fence)
        pygame.draw.rect(screen, CROP_COLOR, (FENCE_X, FENCE_Y, FENCE_WIDTH, FENCE_HEIGHT))
        
        # Draw Label inside crops
        crop_text = font.render("Protected Crops", True, (0, 100, 0))
        screen.blit(crop_text, (FENCE_X + FENCE_WIDTH//2 - crop_text.get_width()//2, FENCE_Y + FENCE_HEIGHT//2 - crop_text.get_height()//2))

        # Draw Laser Fence
        # Make it blink wildly if there's an intrusion
        if intrusion:
            if int(time.time() * 10) % 2 == 0:
                pygame.draw.rect(screen, (255, 255, 0), (FENCE_X, FENCE_Y, FENCE_WIDTH, FENCE_HEIGHT), 8)
            else:
                pygame.draw.rect(screen, (255, 0, 0), (FENCE_X, FENCE_Y, FENCE_WIDTH, FENCE_HEIGHT), 8)
        else:
            pygame.draw.rect(screen, FENCE_COLOR, (FENCE_X, FENCE_Y, FENCE_WIDTH, FENCE_HEIGHT), 3)
            
        # Draw Animals
        for a in animals:
            pygame.draw.circle(screen, (0,0,0), (int(a.x), int(a.y)), a.radius + 2) # outline
            pygame.draw.circle(screen, ANIMAL_COLOR, (int(a.x), int(a.y)), a.radius)
                
        # Title text
        screen.blit(title_text, (20, 20))
        
        # Intrusion warning
        if intrusion:
            warn_font = pygame.font.SysFont("Arial", 36, bold=True)
            warn_text = warn_font.render("⚠️ INTRUSION DETECTED ⚠️", True, (255, 0, 0))
            screen.blit(warn_text, (WINDOW_WIDTH//2 - warn_text.get_width()//2, 20))

        pygame.display.flip()
        clock.tick(FPS)
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
