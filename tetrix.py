import pygame
import random
import time

# Configuración del Juego
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
GRID_SIZE = 30
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE
SIDE_PANEL_WIDTH = 200
TOTAL_WIDTH = SCREEN_WIDTH + SIDE_PANEL_WIDTH

# Colores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
PURPLE = (128, 0, 128)
RED = (255, 0, 0)
LINE_COLOR = (50, 50, 50)

# Formas de los Tetrominós y sus colores
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1, 0], [0, 1, 1]],  # S
    [[0, 1, 1], [1, 1, 0]],  # Z
    [[1, 1, 1], [0, 1, 0]],  # T
    [[1, 1, 1], [1, 0, 0]],  # L
    [[1, 1, 1], [0, 0, 1]],  # J
    [[1, 1], [1, 1]]   # O
]
SHAPE_COLORS = [CYAN, GREEN, RED, PURPLE, ORANGE, BLUE, YELLOW]

# Poderes (conceptual)
POWER_BOMB = "BOMB"
POWER_SLOW = "SLOW"
POWER_WILD = "WILD"
POWER_UP_TYPES = [POWER_BOMB, POWER_SLOW, POWER_WILD]
POWER_UP_COLORS = {
    POWER_BOMB: (255, 69, 0),  # Rojo anaranjado
    POWER_SLOW: (135, 206, 250), # Azul claro
    POWER_WILD: (220, 220, 220)  # Gris claro (para distinguirlo)
}
POWER_UP_CHANCE = 0.1 # Probabilidad de que una pieza sea un poder


class Piece:
    def __init__(self, x, y, shape_index, is_power_up=False, power_type=None):
        self.x = x
        self.y = y
        self.shape_index = shape_index
        self.shape = SHAPES[shape_index]
        self.color = SHAPE_COLORS[shape_index]
        self.rotation = 0
        self.is_power_up = is_power_up
        self.power_type = power_type
        if self.is_power_up and self.power_type:
            self.color = POWER_UP_COLORS[self.power_type]

    def rotate(self):
        if self.shape_index == 6: # 'O' shape, no rotation
            return
        rotated_shape = []
        for i in range(len(self.shape[0])):
            new_row = []
            for j in range(len(self.shape)):
                new_row.append(self.shape[len(self.shape) - 1 - j][i])
            rotated_shape.append(new_row)
        self.shape = rotated_shape

    def unrotate(self): # Para revertir una rotación inválida
        if self.shape_index == 6:
            return
        # Rotar 3 veces es equivalente a una rotación inversa
        for _ in range(3):
            self.rotate()

class Tetris:
    def __init__(self):
        self.grid = [[BLACK for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = self.new_piece()
        self.next_pieces = [self.new_piece() for _ in range(3)] # 3 piezas siguientes
        self.held_piece = None
        self.can_hold = True
        self.score = 0
        self.level = 1
        self.lines_cleared_total = 0
        self.fall_time = 0
        self.fall_speed = 0.5  # Segundos por caída de un bloque
        self.game_over = False
        self.last_move_time = time.time()
        self.key_press_delay = 0.1 # Para movimiento continuo

        # Poderes
        self.slow_active = False
        self.slow_timer = 0
        self.WILD_PIECE_SHAPE_INDEX = -1 # Para identificar la pieza comodín

    def new_piece(self):
        shape_idx = random.randint(0, len(SHAPES) - 1)
        is_power = random.random() < POWER_UP_CHANCE
        power_t = None
        if is_power:
            power_t = random.choice(POWER_UP_TYPES)
        return Piece(GRID_WIDTH // 2 - len(SHAPES[shape_idx][0]) // 2, 0, shape_idx, is_power, power_t)

    def check_collision(self, piece, offset_x=0, offset_y=0):
        for r_idx, row in enumerate(piece.shape):
            for c_idx, cell in enumerate(row):
                if cell:
                    x = piece.x + c_idx + offset_x
                    y = piece.y + r_idx + offset_y
                    if not (0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT and self.grid[y][x] == BLACK):
                        return True
        return False

    def lock_piece(self):
        lines_cleared_this_lock = 0
        power_activated_this_lock = None

        for r_idx, row in enumerate(self.current_piece.shape):
            for c_idx, cell in enumerate(row):
                if cell:
                    x = self.current_piece.x + c_idx
                    y = self.current_piece.y + r_idx
                    if 0 <= y < GRID_HEIGHT and 0 <= x < GRID_WIDTH: # Asegurar que la pieza esté dentro de los límites
                        self.grid[y][x] = self.current_piece.color
                        # Si la pieza era un poder, marcar su tipo en la grilla para la activación
                        if self.current_piece.is_power_up:
                            self.grid[y][x] = (self.current_piece.color, self.current_piece.power_type)


        # Activar poderes y limpiar líneas
        new_grid = [row for row in self.grid if any(cell == BLACK or (isinstance(cell, tuple) and cell[0] == BLACK) for cell in row)]
        lines_cleared_count = GRID_HEIGHT - len(new_grid)

        for r in range(GRID_HEIGHT - 1, -1, -1):
            is_line_full = True
            line_had_power = None
            for c in range(GRID_WIDTH):
                cell_content = self.grid[r][c]
                if cell_content == BLACK:
                    is_line_full = False
                    break
                if isinstance(cell_content, tuple) and cell_content[1] in POWER_UP_TYPES:
                    line_had_power = cell_content[1] # Captura el último poder en la línea

            if is_line_full:
                lines_cleared_this_lock += 1
                if line_had_power:
                    power_activated_this_lock = line_had_power
                # Eliminar la línea (se hace reconstruyendo la grilla abajo)


        if lines_cleared_this_lock > 0:
            # Reconstruir la grilla eliminando las líneas llenas
            temp_grid = [[BLACK for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
            current_row_temp = GRID_HEIGHT - 1
            for r_old in range(GRID_HEIGHT - 1, -1, -1):
                is_line_full_check = all(self.grid[r_old][c_check] != BLACK for c_check in range(GRID_WIDTH))
                if not is_line_full_check:
                    if current_row_temp >= 0: # Asegurar no escribir fuera de los límites
                         temp_grid[current_row_temp] = self.grid[r_old][:]
                         current_row_temp -= 1
            self.grid = temp_grid
            self.update_score(lines_cleared_this_lock)
            self.lines_cleared_total += lines_cleared_this_lock


        if power_activated_this_lock:
            self.activate_power(power_activated_this_lock)


        self.current_piece = self.next_pieces.pop(0)
        self.next_pieces.append(self.new_piece())
        self.can_hold = True

        if self.check_collision(self.current_piece):
            self.game_over = True

    def activate_power(self, power_type):
        print(f"Power Activated: {power_type}") # Para debugging
        if power_type == POWER_BOMB:
            # La bomba ya eliminó su línea. Se podría añadir un efecto visual o sonoro.
            self.score += 50 # Bonus por activar bomba
        elif power_type == POWER_SLOW:
            self.slow_active = True
            self.slow_timer = time.time() + 5 # Ralentiza por 5 segundos
            self.fall_speed *= 2 # Duplica el tiempo de caída (más lento)
        elif power_type == POWER_WILD:
            # Conceptual: La próxima pieza se convierte en una 'I' (la más útil)
            # Esto se maneja cuando se genera la siguiente pieza, o se reemplaza la actual.
            # Por simplicidad, haremos que la *siguiente* pieza en la cola sea una 'I'.
            if self.next_pieces:
                 self.next_pieces[0] = Piece(GRID_WIDTH // 2 - 2, 0, 0) # Pieza 'I'
            self.score += 30 # Bonus por comodín

    def update_score(self, lines_cleared):
        base_points = {1: 40, 2: 100, 3: 300, 4: 1200}
        self.score += base_points.get(lines_cleared, 0) * self.level
        if self.lines_cleared_total // 10 >= self.level:
            self.level += 1
            self.fall_speed = max(0.1, 0.5 - (self.level -1) * 0.035)
            if self.slow_active: # Si está activo el slow, se recalcula sobre la nueva velocidad
                self.fall_speed *=2


    def move(self, dx, dy):
        if not self.check_collision(self.current_piece, dx, dy):
            self.current_piece.x += dx
            self.current_piece.y += dy
            return True
        return False

    def rotate_piece(self):
        original_shape = [row[:] for row in self.current_piece.shape]
        original_x = self.current_piece.x
        original_y = self.current_piece.y

        self.current_piece.rotate()
        if self.check_collision(self.current_piece):
            # Wall kick simple (intentar mover 1 a la izq, luego 1 a la der)
            if not self.check_collision(self.current_piece, -1, 0):
                self.current_piece.x -=1
            elif not self.check_collision(self.current_piece, 1, 0):
                self.current_piece.x +=1
            elif self.current_piece.shape_index == 0: # Pieza 'I' puede necesitar más kicks
                if not self.check_collision(self.current_piece, -2, 0):
                    self.current_piece.x -=2
                elif not self.check_collision(self.current_piece, 2, 0):
                    self.current_piece.x +=2
                else: # No se pudo rotar
                    self.current_piece.shape = original_shape
                    self.current_piece.x = original_x
                    self.current_piece.y = original_y
            else: # No se pudo rotar
                self.current_piece.shape = original_shape
                self.current_piece.x = original_x
                self.current_piece.y = original_y


    def hard_drop(self):
        while not self.check_collision(self.current_piece, 0, 1):
            self.current_piece.y += 1
        self.lock_piece()

    def hold(self):
        if self.can_hold:
            if self.held_piece is None:
                self.held_piece = Piece(0,0, self.current_piece.shape_index) # Reset position for held piece
                self.current_piece = self.next_pieces.pop(0)
                self.next_pieces.append(self.new_piece())
            else:
                # No resetear is_power_up o power_type al intercambiar
                temp_shape_idx = self.current_piece.shape_index
                temp_is_power = self.current_piece.is_power_up
                temp_power_type = self.current_piece.power_type

                self.current_piece = Piece(GRID_WIDTH // 2 - len(SHAPES[self.held_piece.shape_index][0]) // 2, 0,
                                           self.held_piece.shape_index,
                                           self.held_piece.is_power_up, self.held_piece.power_type)
                self.held_piece = Piece(0,0, temp_shape_idx, temp_is_power, temp_power_type)

            self.held_piece.x = GRID_WIDTH // 2 - len(self.held_piece.shape[0]) // 2
            self.held_piece.y = 0
            self.can_hold = False


    def update(self):
        if self.game_over:
            return

        current_time = time.time()
        if self.slow_active and current_time > self.slow_timer:
            self.slow_active = False
            self.fall_speed /= 2 # Volver a la velocidad normal (ajustada por nivel)
            self.fall_speed = max(0.1, 0.5 - (self.level -1) * 0.035) # Re-asegurar velocidad base de nivel

        if current_time - self.fall_time > self.fall_speed:
            if not self.move(0, 1):
                self.lock_piece()
            self.fall_time = current_time

    def get_ghost_piece_y(self):
        ghost = Piece(self.current_piece.x, self.current_piece.y, self.current_piece.shape_index)
        ghost.shape = [row[:] for row in self.current_piece.shape] # Copia de la forma actual
        while not self.check_collision(ghost, 0, 1):
            ghost.y += 1
        return ghost.y

# Funciones de Dibujo
def draw_grid(surface, grid_matrix):
    for r_idx, row in enumerate(grid_matrix):
        for c_idx, cell_color in enumerate(row):
            color_to_draw = cell_color
            if isinstance(cell_color, tuple): # Es un poder
                color_to_draw = cell_color[0]

            pygame.draw.rect(surface, color_to_draw, (c_idx * GRID_SIZE, r_idx * GRID_SIZE, GRID_SIZE, GRID_SIZE))
            if color_to_draw != BLACK: # Dibujar borde más claro para piezas
                 pygame.draw.rect(surface, tuple(min(c+50, 255) for c in color_to_draw), (c_idx * GRID_SIZE, r_idx * GRID_SIZE, GRID_SIZE, GRID_SIZE), 1)
            else: # Dibujar líneas de la grilla
                pygame.draw.rect(surface, LINE_COLOR, (c_idx * GRID_SIZE, r_idx * GRID_SIZE, GRID_SIZE, GRID_SIZE), 1)


def draw_piece(surface, piece, offset_x=0, offset_y=0, ghost=False):
    color_to_draw = piece.color
    if ghost:
        # Color fantasma: color de la pieza pero más transparente/oscuro
        color_to_draw = tuple(c // 2 for c in piece.color)

    for r_idx, row in enumerate(piece.shape):
        for c_idx, cell in enumerate(row):
            if cell:
                pygame.draw.rect(surface, color_to_draw,
                                 ((piece.x + c_idx + offset_x) * GRID_SIZE,
                                  (piece.y + r_idx + offset_y) * GRID_SIZE,
                                  GRID_SIZE, GRID_SIZE))
                if not ghost:
                     pygame.draw.rect(surface, tuple(min(c+70, 255) for c in color_to_draw),
                                     ((piece.x + c_idx + offset_x) * GRID_SIZE,
                                      (piece.y + r_idx + offset_y) * GRID_SIZE,
                                      GRID_SIZE, GRID_SIZE), 2) # Borde más grueso


def draw_side_panel(surface, score, level, next_pieces, held_piece, font):
    surface.fill(GRAY) # Fondo del panel lateral

    score_text = font.render(f"Score: {score}", True, BLACK)
    level_text = font.render(f"Level: {level}", True, BLACK)
    surface.blit(score_text, (10, 10))
    surface.blit(level_text, (10, 50))

    next_text = font.render("Next:", True, BLACK)
    surface.blit(next_text, (10, 100))
    for i, piece in enumerate(next_pieces):
        draw_piece(surface, piece, offset_x=0.5, offset_y=4 + i * 4) # Ajustar offset para el panel

    hold_text = font.render("Hold:", True, BLACK)
    surface.blit(hold_text, (10, 280))
    if held_piece:
        draw_piece(surface, held_piece, offset_x=0.5, offset_y=10) # Ajustar offset para el panel

def main():
    pygame.init()
    screen = pygame.display.set_mode((TOTAL_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Enhanced Tetris - Collaborative AI Edition")
    clock = pygame.time.Clock()
    game = Tetris()
    font = pygame.font.Font(None, 36)
    game_area_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    side_panel_surface = pygame.Surface((SIDE_PANEL_WIDTH, SCREEN_HEIGHT))

    last_key_times = {} # Para controlar repetición de teclas
    key_repeat_delay = 0.2 # Delay inicial antes de que la repetición comience
    key_repeat_interval = 0.05 # Intervalo entre repeticiones una vez que comienza

    running = True
    while running:
        game_area_surface.fill(BLACK) # Limpiar área de juego

        current_time = time.time()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if not game.game_over:
                    if event.key == pygame.K_LEFT:
                        game.move(-1, 0)
                        last_key_times[pygame.K_LEFT] = current_time
                    elif event.key == pygame.K_RIGHT:
                        game.move(1, 0)
                        last_key_times[pygame.K_RIGHT] = current_time
                    elif event.key == pygame.K_DOWN:
                        game.move(0, 1)
                        game.fall_time = current_time # Resetear timer de caída para evitar doble movimiento
                        last_key_times[pygame.K_DOWN] = current_time
                    elif event.key == pygame.K_UP:
                        game.rotate_piece()
                    elif event.key == pygame.K_SPACE:
                        game.hard_drop()
                    elif event.key == pygame.K_c: # Tecla para Hold
                        game.hold()
                if event.key == pygame.K_r and game.game_over: # Reiniciar
                    game = Tetris()


        if not game.game_over:
            # Manejo de movimiento continuo al mantener presionada la tecla
            keys = pygame.key.get_pressed()
            for key_code, action_dx, action_dy in [(pygame.K_LEFT, -1, 0), (pygame.K_RIGHT, 1, 0), (pygame.K_DOWN, 0, 1)]:
                if keys[key_code]:
                    if key_code not in last_key_times or \
                       (current_time - last_key_times[key_code] > key_repeat_delay and \
                        current_time - getattr(game, f"last_continuous_move_time_{key_code}", 0) > key_repeat_interval):
                        game.move(action_dx, action_dy)
                        if key_code == pygame.K_DOWN: game.fall_time = current_time
                        setattr(game, f"last_continuous_move_time_{key_code}", current_time)
                else:
                    if key_code in last_key_times:
                        del last_key_times[key_code] # Limpiar si la tecla se suelta
                        if hasattr(game, f"last_continuous_move_time_{key_code}"):
                             delattr(game, f"last_continuous_move_time_{key_code}")


            game.update()

        draw_grid(game_area_surface, game.grid)

        # Dibujar pieza fantasma
        ghost_y = game.get_ghost_piece_y()
        ghost_piece_vis = Piece(game.current_piece.x, ghost_y, game.current_piece.shape_index)
        ghost_piece_vis.shape = [row[:] for row in game.current_piece.shape]
        draw_piece(game_area_surface, ghost_piece_vis, ghost=True)

        draw_piece(game_area_surface, game.current_piece)

        screen.blit(game_area_surface, (0, 0))
        draw_side_panel(side_panel_surface, game.score, game.level, game.next_pieces, game.held_piece, font)
        screen.blit(side_panel_surface, (SCREEN_WIDTH, 0))


        if game.game_over:
            game_over_text_big = pygame.font.Font(None, 72).render("GAME OVER", True, RED)
            game_over_text_small = font.render("Press 'R' to Restart", True, WHITE)
            screen.blit(game_over_text_big, (SCREEN_WIDTH // 2 - game_over_text_big.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
            screen.blit(game_over_text_small, (SCREEN_WIDTH // 2 - game_over_text_small.get_width() // 2, SCREEN_HEIGHT // 2 + 20))


        pygame.display.flip()
        clock.tick(30)  # Limitar a 30 FPS

    pygame.quit()

if __name__ == '__main__':
    main()
