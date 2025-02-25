import pygame
import sys
import math
import random
from sys import exit
from os import path
import os

# Инициализация Pygame
pygame.init()
pygame.mixer.init()

# Параметры поля
cols, rows = 20, 20
cell_size = 35  # размер одной клетки в пикселях
width, height = cols * cell_size, rows * cell_size


import sys
import os
from os import path
import pygame

def load_image(name: str) -> pygame.Surface:
    """
    Загружает изображение из папки data, работает как в режиме разработки, так и после сборки с PyInstaller.

    :param name: Имя файла изображения (например, "background.jpg").
    :return: Объект pygame.Surface с загруженным изображением.
    """
    try:
        # PyInstaller создаёт временную папку и хранит путь в _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Если _MEIPASS недоступен (режим разработки), используем текущую директорию
        base_path = os.getcwd()

    # Формируем корректный путь к файлу
    full_path = path.join(base_path, name)

    # Проверяем, существует ли файл
    if not path.exists(full_path):
        print(f'Не удалось найти файл {full_path}')
        sys.exit(1)

    # Загружаем изображение
    image = pygame.image.load(full_path).convert_alpha()
    return image

def load_level(filename):
    filename = "data/" + filename
    # читаем уровень, убирая символы перевода строки
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]

    # и подсчитываем максимальную длину
    max_width = max(map(len, level_map))

    # дополняем каждую строку пустыми клетками ('.')
    return list(map(lambda x: x.ljust(max_width, '.'), level_map))


# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
DARK_GREEN = (0, 100, 0)
RED = (255, 0, 0)

# Радиус видимости в клетках
visibility_radius = 3

# Шрифты для текста
font = pygame.font.SysFont(None, 48)
font_small = pygame.font.SysFont(None, 30)

# Создание окна
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Воришка биткоинов")

# Загрузка фонового изображения для меню и "Game Over"
background_image = load_image("data/background.jpg")
background_image = pygame.transform.scale(background_image, (width, height))  # Растягиваем фон на весь экран

gameover_image = load_image("data/gameover.png")  # Убедитесь, что файл 'gameover.png' находится в той же папке
gameover_width = gameover_image.get_width()
gameover_height = gameover_image.get_height()

tile_images = {
    'wall': pygame.transform.scale(load_image('data/wall.jpg'), (35, 35)),
    'coin': pygame.transform.scale(load_image('data/coin.png'), (35, 35)),
    'camera': pygame.transform.scale(load_image('data/camera.jpg'), (35, 35)),
    'home': pygame.transform.scale(load_image('data/home.png'), (35, 35)),
}
player_image = pygame.transform.scale(load_image('data/player.jpg'), (35, 35))
enemy_image = pygame.transform.scale(load_image('data/enemy.jpg'), (35, 35))
tile_width = tile_height = 35
player = None

# группы спрайтов
all_sprites = pygame.sprite.Group()
tiles_group = pygame.sprite.Group()
player_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
tiles = []
cameras = []
coins = []
walls = []
enemies = []
deleted_coins = []
counter_coins = 0
wasted = pygame.mixer.Sound('data/wasted.mp3')
coin_music = pygame.mixer.Sound('data/coin.mp3')

def generate_level(level):
    global all_sprites, tiles_group, player_group, enemy_group, tiles, \
        cameras, coins, walls, enemies, deleted_coins, counter_coins
    all_sprites = pygame.sprite.Group()
    tiles_group = pygame.sprite.Group()
    player_group = pygame.sprite.Group()
    enemy_group = pygame.sprite.Group()
    tiles = []
    cameras = []
    coins = []
    walls = []
    enemies = []
    deleted_coins = []
    counter_coins = 0
    new_player = None
    new_enemy = []
    new_home = None
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '%':
                tiles.append((x, y))
                new_home = Tile('home', x, y)
            elif level[y][x] == '#':
                Tile('wall', x, y)
                tiles.append((x, y))
                walls.append((x, y))
            elif level[y][x] == '@':
                new_player = Player(x, y)
            elif level[y][x] == '*':
                Tile('coin', x, y)
                tiles.append((x, y))
                coins.append((x, y))
            elif level[y][x] == '^':
                Tile('camera', x, y)
                tiles.append((x, y))
                cameras.append((x, y))
            elif level[y][x] == '$':
                new_enemy.append(Enemy(x, y))
                enemies.append((x, y))

    # вернем игрока, а также размер поля в клетках
    return [new_player, new_enemy, new_home]


class Player(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(player_group, all_sprites)
        self.image = player_image
        self.image0 = player_image
        self.rect = self.image.get_rect().move(
            tile_width * pos_x + 15, tile_height * pos_y + 5)
        self.x, self.y = pos_x, pos_y

    def get_pos(self):
        return (self.x, self.y)

    def get_image(self):
        return self.image

    def change_image(self, flip_x, flip_y, n):
        if n == 1:
            self.image = self.image0
        else:
            self.image = pygame.transform.flip(self.image0, flip_x, flip_y)


class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(enemy_group, all_sprites)
        self.image = enemy_image
        self.rect = self.image.get_rect().move(
            tile_width * pos_x + 15, tile_height * pos_y + 5)
        self.x, self.y = pos_x, pos_y
        self.direction = 'left'

    def get_pos(self):
        return (self.x, self.y)

    def get_image(self):
        return self.image

    # движение врагов
    def move(self, x, y, flag=False):
        global enemies
        if flag:
            if self.direction == 'left' and self.x > 0 and (x, y) not in walls:
                circle_center = ((x - 1) * cell_size, y * cell_size)
                screen.blit(enemy_image, circle_center)
                self.x -= 1
            elif self.direction == 'right' and self.x < 19 and (x, y) not in walls:
                circle_center = ((x + 1) * cell_size, y * cell_size)
                image = pygame.transform.flip(enemy_image, True, False)
                screen.blit(image, circle_center)
                self.x += 1
        else:
            if self.direction == 'left' and self.x > 0 and (x, y) not in walls:
                self.x -= 1
            elif self.direction == 'right' and self.x < 19 and (x, y) not in walls:
                self.x += 1
        if (self.x - 1, y) in walls or self.x == 0 and self.direction == 'left':
            self.direction = 'right'
        elif (self.x + 1, y) in walls or self.x + 1 == 20 and self.direction == 'right':
            self.direction = 'left'
        enemies[enemies.index((x, y))] = (self.x, self.y)


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(tiles_group, all_sprites)
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)
        self.x, self.y = pos_x, pos_y

    def get_pos(self):
        return (self.x, self.y)

    def get_image(self):
        return self.image

    def die(self, circle_x, circle_y):
        global counter_coins, deleted_coins
        coin_music.play()
        if (circle_x, circle_y) not in deleted_coins:
            del coins[coins.index((circle_x, circle_y))]
            del tiles[tiles.index((circle_x, circle_y))]
            deleted_coins.append((circle_x, circle_y))
            counter_coins += 1
        self.kill()


# Функция для генерации дома
def generate_house(level):
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '%':
                return (x, y)

def generate_player(level):
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '@':
                return (x, y)


# Функция для отображения главного меню
def show_main_menu():
    screen.blit(background_image, (0, 0))  # Отображаем фон

    # Создание кнопок
    play_button = pygame.Rect(width // 4, height // 2, width // 2, 60)
    instructions_button = pygame.Rect(width // 4, 2 * height // 3, width // 2, 60)

    # Рисование кнопок
    pygame.draw.rect(screen, ('#00416a'), play_button)  # Зеленый фон кнопки "Играть"
    pygame.draw.rect(screen, ('black'), play_button, 3)  # Белая рамка

    pygame.draw.rect(screen, ('#00416a'), instructions_button)  # Зеленый фон кнопки "Инструкция"
    pygame.draw.rect(screen, ('black'), instructions_button, 3)  # Белая рамка

    # Рендер текста на кнопках
    play_text = font.render("Играть", True, 'yellow')
    instructions_text = font.render("Инструкция", True, 'yellow')

    # Центрирование текста на кнопках
    screen.blit(play_text, (play_button.centerx - play_text.get_width() // 2,
                            play_button.centery - play_text.get_height() // 2))
    screen.blit(instructions_text, (instructions_button.centerx - instructions_text.get_width() // 2,
                                    instructions_button.centery - instructions_text.get_height() // 2))

    pygame.display.flip()

    return play_button, instructions_button

def show_choice_level():
    screen.blit(background_image, (0, 0))

    level1_button = pygame.Rect(width // 4, height // 4, width // 2, 60)
    level2_button = pygame.Rect(width // 4, height // 2, width // 2, 60)
    level3_button = pygame.Rect(width // 4, 3 * height // 4, width // 2, 60)

    pygame.draw.rect(screen, ('#00416a'), level1_button)  # синий фон кнопки "Играть"
    pygame.draw.rect(screen, 'black', level1_button, 3)  # чёрная рамка

    pygame.draw.rect(screen, ('#00416a'), level2_button)  # синий фон кнопки "Играть"
    pygame.draw.rect(screen, 'black', level2_button, 3)  # чёрная рамка

    pygame.draw.rect(screen, ('#00416a'), level3_button)  # синий фон кнопки "Играть"
    pygame.draw.rect(screen, 'black', level3_button, 3)  # чёрная рамка

    level1_text = font.render("Уровень 1", True, 'yellow')
    level2_text = font.render("Уровень 2", True, 'yellow')
    level3_text = font.render('Уровень 3', True, 'yellow')

    # Центрирование текста на кнопках
    screen.blit(level1_text, (level1_button.centerx - level1_text.get_width() // 2,
                            level1_button.centery - level1_text.get_height() // 2))
    screen.blit(level2_text, (level2_button.centerx - level2_text.get_width() // 2,
                                    level2_button.centery - level2_text.get_height() // 2))
    screen.blit(level3_text, (level3_button.centerx - level3_text.get_width() // 2,
                              level3_button.centery - level3_text.get_height() // 2))

    pygame.display.flip()

    return level1_button, level2_button, level3_button

# Функция для отображения инструкции
def show_instructions():
    screen.fill(WHITE)

    # Текст инструкции
    instruction_title = font_small.render("Инструкция:", True, BLACK)
    instruction1 = font_small.render("1. Инициализация движения:", True, BLACK)
    instruction2 = font_small.render("При нажатии на стрелку вперёд или на w происходит", True, BLACK)
    instruction3 = font_small.render("движение вперёд. ", True, BLACK)
    instruction4 = font_small.render("При нажатии на стрелку влево или на a происходит", True, BLACK)
    instruction5 = font_small.render("движение влево.", True, BLACK)
    instruction6 = font_small.render("При нажатии на стрелку вправо или на d происходит", True, BLACK)
    instruction7 = font_small.render("движение вправо.", True, BLACK)
    instruction8 = font_small.render("При нажатии на стрелку назад или на s происходит", True, BLACK)
    instruction9 = font_small.render("движение назад.", True, BLACK)
    instruction10 = font_small.render("2. Основная задача:", True, BLACK)
    instruction11 = font_small.render("Добрать домой, при этом избегать камер и полицейских", True, BLACK)
    instruction12 = font_small.render("Если на них попасть, то вы погибните", True, BLACK)
    instruction13 = font_small.render("У персонажа ограниченный радиус обзора", True, BLACK)
    instruction14 = font_small.render("3. Второстепенная задача:", True, BLACK)
    instruction15 =  font_small.render("Собрать все монетки", True, BLACK)
    instruction16 = font_small.render("Удачи!", True, BLACK)

    # Создание кнопки "Назад"
    back_button = pygame.Rect(width // 4, height - 100, width // 2, 60)
    pygame.draw.rect(screen, (255, 0, 0), back_button)  # Красный фон кнопки "Назад"
    pygame.draw.rect(screen, (255, 255, 255), back_button, 3)  # Белая рамка

    back_text = font_small.render("Назад", True, BLACK)
    screen.blit(back_text, (back_button.centerx - back_text.get_width() // 2,
                            back_button.centery - back_text.get_height() // 2))

    # Размещение текста инструкции
    screen.blit(instruction_title, (10, 30))
    screen.blit(instruction1, (10, 50))
    screen.blit(instruction2, (10, 70))
    screen.blit(instruction3, (10, 90))
    screen.blit(instruction4, (10, 110))
    screen.blit(instruction5, (10, 130))
    screen.blit(instruction6, (10, 150))
    screen.blit(instruction7, (10, 170))
    screen.blit(instruction8, (10, 190))
    screen.blit(instruction9, (10, 210))
    screen.blit(instruction10, (10, 260))
    screen.blit(instruction11, (10, 280))
    screen.blit(instruction12, (10, 300))
    screen.blit(instruction13, (10, 320))
    screen.blit(instruction14, (10, 370))
    screen.blit(instruction15, (10, 390))
    screen.blit(instruction16, (250, 500))

    pygame.display.flip()

    return back_button

# Функция для отображения экрана "Game Over" с анимацией
def game_over_screen():
    global counter_coins, deleted_coins, flag_music
    wasted.play()
    flag_music = 1
    deleted_coins = []
    counter_coins = 0
    clock = pygame.time.Clock()
    # Заполнение экрана белым цветом
    screen.fill(WHITE)

    # Растягиваем изображение "Game Over" на весь экран
    screen.blit(pygame.transform.scale(gameover_image, (width, height)), (0, 0))

    pygame.display.flip()
    pygame.time.delay(5000)
    main()

def draw_star(surface, x, y, size, color):
    # Рисует звезду в заданной позиции (x, y) с размером size и цветом color
    points = []
    for i in range(5):
        angle = math.radians(i * 144)  # Углы для рисования 5-лучевой звезды
        x_point = x + size * math.cos(angle)
        y_point = y + size * math.sin(angle)
        points.append((x_point, y_point))
    pygame.draw.polygon(surface, color, points)

# Функция для отображения эффекта звёзд
def show_stars():
    # Черный экран
    screen.fill(BLACK)
    pygame.mixer.music.load('data/ride.mp3')
    pygame.mixer.music.set_volume(0.2)
    pygame.mixer.music.play(-1)

    # Центр экрана для размещения звёзд
    x, y = width // 2, height // 2
    size = 40  # Размер звезды
    star_color = ("gold")  # Белые звезды
    # Рисуем звезды
    if counter_coins == 1:
        draw_star(screen, x, y, size, star_color)
    elif counter_coins == 2:
        for i in range(0, counter_coins + 1, 2):
            draw_star(screen, x + (i - 1) * (size), y, size, star_color)
    elif counter_coins == 3:
        for i in range(counter_coins):
            draw_star(screen, x + (i - 1) * (size * 2), y, size, star_color)

    pygame.display.flip()

    # Задержка, чтобы игрок успел увидеть звезды
    pygame.time.delay(1000)

def generate_random_color():
    # Генерируем случайные значения для красного, зелёного и синего каналов (от 0 до 255)
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return (r, g, b)

# Функция для создания эффекта салюта
def show_fireworks():
    # Цвета для кругов, которые не должны совпадать с цветами звёзд
    firework_colors = ["#d53032", "#44944a", "blue", "orange", "#9966cc", "#00a86b", "#2c75ff", "#7fffd4"]  # Красный, зелёный, синий, оранжевый
    for _ in range(100):  # Увеличиваем количество кругов
        x = random.randint(50, width - 50)
        y = random.randint(50, height - 50)
        color = random.choice(firework_colors)  # Случайный цвет для круга
        size = random.randint(10, 30)  # Рандомизируем размер круга

        # Рисуем круг
        pygame.draw.circle(screen, color, (x, y), size)
        pygame.display.flip()
        pygame.time.delay(50)  # Задержка между рисованием кругов

    pygame.time.delay(500)  # Задержка, чтобы игрок успел увидеть весь эффект

# Главный игровой цикл
def game_loop(map):
    global circle_x, circle_y, house_pos, counter_coins, deleted_coins
    pygame.mixer.music.load('data/smackthat.mp3')
    pygame.mixer.music.set_volume(0.2)
    pygame.mixer.music.play(-1)
    deleted_coins = []
    counter_coins = 0
    level_map = load_level(map)
    # Начальная позиция кружка (координаты в клетках)
    circle_x, circle_y = generate_player(level_map)  # Можно установить в любое место
    house_pos = generate_house(level_map)
    player, all_enemies, home = generate_level(level_map)
    clock = pygame.time.Clock()
    game_over = False
    pred_x, pred_y = circle_x, circle_y
    time = 0

    while not game_over:
        clock.tick(7)  # FPS, регулирует скорость обновления
        time += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        # Обработка клавиш
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            if circle_y > 0:
                pred_x, pred_y = circle_x, circle_y
                circle_y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            if circle_y < rows - 1:
                pred_x, pred_y = circle_x, circle_y
                circle_y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            if circle_x > 0:
                player.change_image(True, False, 1)
                pred_x, pred_y = circle_x, circle_y
                circle_x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            if circle_x < cols - 1:
                player.change_image(True, False, 0)
                pred_x, pred_y = circle_x, circle_y
                circle_x += 1

        # Проверка столкновения: если координаты кружка совпадают с координатой объекта
        if (circle_x, circle_y) in tiles:
            if (circle_x, circle_y) in cameras:
                pygame.mixer.music.stop()
                game_over = True
            elif (circle_x, circle_y) in walls:
                circle_x, circle_y = pred_x, pred_y
            elif (circle_x, circle_y) in coins:
                for i in tiles_group:
                    if i.get_pos() == (circle_x, circle_y):
                        i.die(circle_x, circle_y)

        if (circle_x, circle_y) in enemies:
            pygame.mixer.music.stop()
            game_over = True

        # Проверка, что игрок наступил на дом
        if (circle_x, circle_y) == house_pos:
            pygame.mixer.music.stop()
            show_stars()  # Показать звезды
            show_fireworks()  # Показать салют
            pygame.time.delay(1000)
            pygame.mixer.music.stop()
            main()

        # Отрисовка поля
        for y in range(rows):
            for x in range(cols):
                distance = math.sqrt((x - circle_x) ** 2 + (y - circle_y) ** 2)
                rect = pygame.Rect(x * cell_size, y * cell_size, cell_size, cell_size)
                if distance <= visibility_radius:
                    pygame.draw.rect(screen, WHITE, rect)
                    pygame.draw.rect(screen, BLACK, rect, 1)
                else:
                    pygame.draw.rect(screen, BLACK, rect)

        for i in tiles_group:
            x, y = i.get_pos()
            distance = math.sqrt((x - circle_x) ** 2 + (y - circle_y) ** 2)
            if distance <= visibility_radius:
                screen.blit(i.get_image(), (35 * x, 35 * y))


        for i in all_enemies:
            x, y = i.get_pos()
            distance = math.sqrt((x - circle_x) ** 2 + (y - circle_y) ** 2)
            if time % 3 == 0:
                if distance < visibility_radius:
                    i.move(x, y, True)
                else:
                    i.move(x, y, False)
            else:
                if i.direction == 'left' and distance <= visibility_radius:
                    screen.blit(enemy_image, (35 * x, 35 * y))
                elif i.direction == 'right' and distance <= visibility_radius:
                    image_en = pygame.transform.flip(enemy_image, True, False)
                    screen.blit(image_en, (35 * x, 35 * y))

        # Отрисовка дома
        hx, hy = house_pos
        screen.blit(tile_images['home'], (hx * 35, hy * 35))

        # Отрисовка игрока по центру текущей клетки
        circle_center = (circle_x * cell_size,
                         circle_y * cell_size)
        screen.blit(player.get_image(), circle_center)

        pygame.display.flip()

    # После окончания игры показываем экран "Game Over"
    game_over_screen()

# Главное меню
def main():
    global flag_music
    pygame.mixer.music.load('data/stillDRE.mp3')
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)
    running = True
    while running:
        play_button, instructions_button = show_main_menu()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if play_button.collidepoint(mouse_pos):
                    level1, level2, level3 = show_choice_level()
                    in_levels = True
                    while in_levels:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                exit()
                            if event.type == pygame.MOUSEBUTTONDOWN:
                                pygame.mixer.music.stop()
                                in_levels = False
                                if level1.collidepoint(pygame.mouse.get_pos()):
                                    game_loop('map1')
                                elif level2.collidepoint(pygame.mouse.get_pos()):
                                    game_loop('map2')
                                elif level3.collidepoint(pygame.mouse.get_pos()):
                                    game_loop('map3')
                        pygame.display.update()
                elif instructions_button.collidepoint(mouse_pos):
                    back_button = show_instructions()

                    # Цикл для инструкции
                    in_instructions = True
                    while in_instructions:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                exit()
                            if event.type == pygame.MOUSEBUTTONDOWN:
                                if back_button.collidepoint(pygame.mouse.get_pos()):
                                    in_instructions = False
                        pygame.display.update()
    pygame.mixer.quit()
    pygame.quit()
    exit()

if __name__ == "__main__":
    main()