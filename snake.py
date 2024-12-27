import pygame
import random
import sys

# init pygame
pygame.init()

# constants
WIDTH = 800
HEIGHT = 600
BLOCK_SIZE = 20
SPEED = 15

# colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# create window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Snake Strategy')
clock = pygame.time.Clock()

class Snake:
    def __init__(self, position, is_friendly=True):
        # Basic snake parameters
        self.body = [position]  # Snake body (list of coordinates)
        self.is_friendly = is_friendly  # Friendly or enemy
        self.color = GREEN if is_friendly else RED  # Green - friendly, red - enemy
        self.target = None  # Target for attack
        self.health = 100  # Health points
        self.damage = 10  # Attack damage
        self.speed = 15  # Movement speed
        self.move_counter = 0  # Counter for speed control
        
    @staticmethod
    def distance(pos1, pos2):
        # Calculate distance between two points using Pythagorean theorem
        return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5
    
    def move(self, target_pos):
        # Movement speed control
        self.move_counter += 1
        if self.move_counter < SPEED / self.speed:
            return
        self.move_counter = 0
        
        # Current position of snake's head
        head_x, head_y = self.body[0]
        target_x, target_y = target_pos
        
        # Determine movement direction
        dx = target_x - head_x  # X difference
        dy = target_y - head_y  # Y difference
        
        # Move in direction of larger difference
        if abs(dx) > abs(dy):
            new_x = head_x + (BLOCK_SIZE if dx > 0 else -BLOCK_SIZE)
            new_y = head_y
        else:
            new_x = head_x
            new_y = head_y + (BLOCK_SIZE if dy > 0 else -BLOCK_SIZE)
        
        # If snake goes off screen - appear on the other side
        new_x = new_x % WIDTH
        new_y = new_y % HEIGHT
        
        # Update snake position
        self.body.insert(0, (new_x, new_y))  # Add new head
        self.body.pop()  # Remove tail
    
    def draw(self):
        # draw snake body
        for segment in self.body:
            pygame.draw.rect(screen, self.color, 
                           (segment[0], segment[1], BLOCK_SIZE, BLOCK_SIZE))
        # draw health bar
        health_width = 30
        health_height = 5
        health_x = self.body[0][0] - (health_width - BLOCK_SIZE) // 2
        health_y = self.body[0][1] - 10
        
        pygame.draw.rect(screen, RED, 
                        (health_x, health_y, health_width, health_height))
        pygame.draw.rect(screen, GREEN,
                        (health_x, health_y, health_width * (self.health/100), health_height))

class Projectile:
    def __init__(self, position, target_pos, is_friendly):
        # Projectile parameters
        self.position = list(position)  # Current position
        self.is_friendly = is_friendly  # Friendly or enemy projectile
        self.speed = 5  # Flight speed
        self.damage = 5  # Impact damage
        self.color = GREEN if is_friendly else RED  # Projectile color
        
        # Calculate projectile movement vector
        dx = target_pos[0] - position[0]
        dy = target_pos[1] - position[1]
        distance = (dx**2 + dy**2)**0.5
        self.velocity = [dx/distance * self.speed, dy/distance * self.speed]
    
    def move(self):
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]
    
    def draw(self):
        pygame.draw.circle(screen, self.color, 
                         (int(self.position[0]), int(self.position[1])), 4)

class RangedSnake(Snake):
    def __init__(self, position, is_friendly=True):
        super().__init__(position, is_friendly)
        # Ranged combat parameters
        self.attack_range = 200  # Attack range
        self.attack_cooldown = 30  # Reload time
        self.current_cooldown = 0  # Current cooldown
        self.color = (0, 200, 0) if is_friendly else (200, 0, 0)  # Darker color than regular snakes
    
    def can_attack(self, target_pos):
        # Check if target can be attacked
        distance = self.distance(self.body[0], target_pos)
        return distance <= self.attack_range and self.current_cooldown == 0
    
    def update(self):
        # Update cooldown timer
        if self.current_cooldown > 0:
            self.current_cooldown -= 1

class GameState:
    def __init__(self):
        self.friendly_snakes = []
        self.enemy_snakes = []
        self.friendly_ranged = []
        self.enemy_ranged = []
        self.projectiles = []
        self.selected_snake = None
        self.editor_mode = True
        self.placing_friendly = True
        self.placing_melee = True  # True for melee, False for ranged
    
    def update(self):
        # Update projectiles
        for proj in self.projectiles[:]:
            proj.move()
            # Check for collision
            targets = self.enemy_snakes + self.enemy_ranged if proj.is_friendly else self.friendly_snakes + self.friendly_ranged
            for target in targets:
                if self.check_collision(proj.position, target.body[0]):
                    target.health -= proj.damage
                    if target.health <= 0:
                        if target in self.enemy_snakes:
                            self.enemy_snakes.remove(target)
                        elif target in self.enemy_ranged:
                            self.enemy_ranged.remove(target)
                        elif target in self.friendly_snakes:
                            self.friendly_snakes.remove(target)
                        elif target in self.friendly_ranged:
                            self.friendly_ranged.remove(target)
                    if proj in self.projectiles:
                        self.projectiles.remove(proj)
                    break
            
            # Remove projectiles out of bounds
            if proj in self.projectiles and (
                proj.position[0] < 0 or proj.position[0] > WIDTH or
                proj.position[1] < 0 or proj.position[1] > HEIGHT):
                self.projectiles.remove(proj)
        
        # Update friendly snakes
        for snake in self.friendly_snakes + self.friendly_ranged:
            # If no target, find nearest enemy
            if not snake.target or snake.target.health <= 0:
                targets = self.enemy_snakes + self.enemy_ranged
                if targets:
                    snake.target = min(targets, 
                                     key=lambda x: self.distance(snake.body[0], x.body[0]))
            
            if snake.target:
                if isinstance(snake, RangedSnake):
                    snake.update()  # Update cooldown
                    if snake.can_attack(snake.target.body[0]):
                        self.projectiles.append(Projectile(snake.body[0], 
                                                         snake.target.body[0], True))
                        snake.current_cooldown = snake.attack_cooldown
                    elif self.distance(snake.body[0], snake.target.body[0]) > snake.attack_range/2:
                        snake.move(snake.target.body[0])
                else:
                    snake.move(snake.target.body[0])
                    if self.check_collision(snake.body[0], snake.target.body[0]):
                        snake.target.health -= snake.damage
                        if snake.target.health <= 0:
                            if snake.target in self.enemy_snakes:
                                self.enemy_snakes.remove(snake.target)
                            elif snake.target in self.enemy_ranged:
                                self.enemy_ranged.remove(snake.target)
                            snake.target = None
        
        # Update enemy snakes
        for snake in self.enemy_snakes + self.enemy_ranged:
            # If no target, find nearest enemy
            if not hasattr(snake, 'target') or not snake.target or snake.target.health <= 0:
                targets = self.friendly_snakes + self.friendly_ranged
                if targets:
                    snake.target = min(targets, 
                                     key=lambda x: self.distance(snake.body[0], x.body[0]))
            
            if hasattr(snake, 'target') and snake.target:
                if isinstance(snake, RangedSnake):
                    snake.update()
                    if snake.can_attack(snake.target.body[0]):
                        self.projectiles.append(Projectile(snake.body[0], 
                                                         snake.target.body[0], False))
                        snake.current_cooldown = snake.attack_cooldown
                    elif self.distance(snake.body[0], snake.target.body[0]) > snake.attack_range/2:
                        snake.move(snake.target.body[0])
                else:
                    snake.move(snake.target.body[0])
                    if self.check_collision(snake.body[0], snake.target.body[0]):
                        snake.target.health -= snake.damage
                        if snake.target.health <= 0:
                            if snake.target in self.friendly_snakes:
                                self.friendly_snakes.remove(snake.target)
                            elif snake.target in self.friendly_ranged:
                                self.friendly_ranged.remove(snake.target)
                            snake.target = None

    @staticmethod
    def distance(pos1, pos2):
        return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5
    
    @staticmethod
    def check_collision(pos1, pos2):
        return abs(pos1[0] - pos2[0]) < BLOCK_SIZE and abs(pos1[1] - pos2[1]) < BLOCK_SIZE

def draw_ui(game_state):
    # draw control buttons
    pygame.draw.rect(screen, BLUE if game_state.editor_mode else WHITE, 
                    (10, HEIGHT - 40, 100, 30))
    font = pygame.font.Font(None, 24)
    text = font.render("Editor Mode", True, BLACK)
    screen.blit(text, (15, HEIGHT - 35))
    
    if game_state.editor_mode:
        # side selection button
        pygame.draw.rect(screen, GREEN if game_state.placing_friendly else RED, 
                        (120, HEIGHT - 40, 100, 30))
        text = font.render("Friendly" if game_state.placing_friendly else "Enemy", True, BLACK)
        screen.blit(text, (125, HEIGHT - 35))
        
        # unit type selection button
        pygame.draw.rect(screen, BLUE if game_state.placing_melee else YELLOW, 
                        (230, HEIGHT - 40, 100, 30))
        text = font.render("Melee" if game_state.placing_melee else "Ranged", True, BLACK)
        screen.blit(text, (235, HEIGHT - 35))

def main():
    game_state = GameState()
    running = True

    while running:
        screen.fill(BLACK)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # check for UI button click
                if HEIGHT - 40 <= mouse_pos[1] <= HEIGHT - 10:
                    if 10 <= mouse_pos[0] <= 110:
                        game_state.editor_mode = not game_state.editor_mode
                    elif 120 <= mouse_pos[0] <= 220 and game_state.editor_mode:
                        game_state.placing_friendly = not game_state.placing_friendly
                    elif 230 <= mouse_pos[0] <= 330 and game_state.editor_mode:
                        game_state.placing_melee = not game_state.placing_melee
                
                # placing snakes in editor mode
                elif game_state.editor_mode and mouse_pos[1] < HEIGHT - 50:
                    pos = (mouse_pos[0] - mouse_pos[0] % BLOCK_SIZE,
                          mouse_pos[1] - mouse_pos[1] % BLOCK_SIZE)
                    if game_state.placing_melee:
                        if game_state.placing_friendly:
                            game_state.friendly_snakes.append(Snake(pos, True))
                        else:
                            game_state.enemy_snakes.append(Snake(pos, False))
                    else:
                        if game_state.placing_friendly:
                            game_state.friendly_ranged.append(RangedSnake(pos, True))
                        else:
                            game_state.enemy_ranged.append(RangedSnake(pos, False))
                
                # select friendly snake
                elif not game_state.editor_mode:
                    game_state.selected_snake = None
                    for snake in game_state.friendly_snakes + game_state.friendly_ranged:
                        if game_state.check_collision(mouse_pos, snake.body[0]):
                            game_state.selected_snake = snake
                            break
            
            # assign target to selected snake
            elif event.type == pygame.MOUSEBUTTONUP and not game_state.editor_mode:
                if game_state.selected_snake:
                    for enemy in game_state.enemy_snakes + game_state.enemy_ranged:
                        if game_state.check_collision(mouse_pos, enemy.body[0]):
                            game_state.selected_snake.target = enemy
                            break
        
        if not game_state.editor_mode:
            # update game state
            game_state.update()
        
        # draw all objects
        for snake in (game_state.friendly_snakes + game_state.enemy_snakes +
                     game_state.friendly_ranged + game_state.enemy_ranged):
            snake.draw()
            
            # highlight selected snake
            if snake == game_state.selected_snake:
                pygame.draw.rect(screen, YELLOW, 
                               (snake.body[0][0], snake.body[0][1], 
                                BLOCK_SIZE, BLOCK_SIZE), 2)
        
        for proj in game_state.projectiles:
            proj.draw()
        
        draw_ui(game_state)
        
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
