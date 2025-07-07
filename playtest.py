import gym
import pygame
import numpy as np
import time
import csv
from pathlib import Path
from datetime import datetime
from gym_super_mario_bros.actions import SIMPLE_MOVEMENT
from nes_py.wrappers import JoypadSpace
from metrics import MetricLogger

# ----- PARAMÈTRES -----
LEVEL_END = 3266
LIVES = 3
SCOREBOARD_FILE = Path("scoreboard.csv")

# ----- INIT PYGAME (jeu) -----
pygame.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode((512, 480))
pygame.display.set_caption("Joueur humain vs Mario")
font = pygame.font.SysFont("Arial", 20)

# ----- PSEUDO -----
pseudo = input("Entrez votre pseudo : ").strip()

# ----- DOSSIER DE SAUVEGARDE -----
now = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
save_dir = Path("logs_humain") / now
save_dir.mkdir(parents=True, exist_ok=True)

# ----- ENVIRONNEMENT -----
env = gym.make("SuperMarioBros-v0")
env = JoypadSpace(env, SIMPLE_MOVEMENT)
logger = MetricLogger(save_dir)

# ----- VARIABLES -----
total_reward = 0
steps = 0
max_x_pos = 0
start_time = time.time()

# ----- BOUCLE DE JEU -----
for life in range(1, LIVES + 1):
    obs = env.reset()
    done = False

    while not done:
        clock.tick(60)
        screen_buffer = env.render(mode='rgb_array')
        surf = pygame.surfarray.make_surface(np.transpose(screen_buffer, (1, 0, 2)))
        screen.blit(pygame.transform.scale(surf, (512, 480)), (0, 0))
        pygame.display.flip()

        action = 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
                break

        keys = pygame.key.get_pressed()
        pressed = []
        if keys[pygame.K_RIGHT]: pressed.append("right")
        if keys[pygame.K_LEFT]: pressed.append("left")
        if keys[pygame.K_SPACE] or keys[pygame.K_UP]: pressed.append("A")
        if keys[pygame.K_LSHIFT] or keys[pygame.K_DOWN]: pressed.append("B")

        try:
            action = SIMPLE_MOVEMENT.index(pressed)
        except ValueError:
            action = 0

        obs, reward, done, info = env.step(action)
        total_reward += reward
        steps += 1
        max_x_pos = max(max_x_pos, info.get("x_pos", 0))
        logger.log_step(reward, info.get("coins"), info.get("score"))

# ----- FIN DE JEU -----
end_time = time.time()
elapsed_time = round(end_time - start_time, 2)
percent_done = round(min(max_x_pos / LEVEL_END, 1.0) * 100, 2)

logger.log_episode()
logger.record(episode=0, epsilon=0, step=steps)

# ----- SCOREBOARD -----
def load_scoreboard():
    if not SCOREBOARD_FILE.exists():
        return {}
    with open(SCOREBOARD_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row['pseudo']: row for row in reader}

def save_scoreboard(data):
    with open(SCOREBOARD_FILE, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["pseudo", "progression", "temps", "score"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for entry in data:
            writer.writerow(entry)

scoreboard = load_scoreboard()
current_entry = {
    "pseudo": pseudo,
    "progression": str(percent_done),
    "temps": str(elapsed_time),
    "score": str(round(total_reward, 2))
}

if pseudo in scoreboard:
    old = scoreboard[pseudo]
    keep_old = (
        float(old["progression"]) > percent_done or
        (float(old["progression"]) == percent_done and float(old["temps"]) < elapsed_time)
    )
    if keep_old:
        current_entry = old

scoreboard[pseudo] = current_entry

scoreboard_list = list(scoreboard.values())
scoreboard_list.sort(key=lambda x: (-float(x["progression"]), float(x["temps"]), -float(x["score"])))
save_scoreboard(scoreboard_list)

# ----- QUITTE ENVIRONNEMENT -----
env.close()

# ----- AFFICHAGE PYGAME DU CLASSEMENT -----
SCREEN_WIDTH, SCREEN_HEIGHT = 600, 520
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Classement Joueurs")
font_title = pygame.font.SysFont("Arial", 28, bold=True)
font_row = pygame.font.SysFont("Arial", 20)

row_height = 32
col_widths = [160, 140, 120, 100]
headers = ["Pseudo", "Progression (%)", "Temps (s)", "Score"]

# couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (108, 194, 236)
GRASS_GREEN = (64, 200, 64)
LINE_COLOR = (255, 255, 255)

def draw_table():
    screen.fill(SKY_BLUE)

    # Sol vert
    pygame.draw.rect(screen, GRASS_GREEN, pygame.Rect(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40))

    # Titre
    title_surface = font_title.render("Classement des joueurs", True, BLACK)
    title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 30))
    screen.blit(title_surface, title_rect)

    # Header
    y_start = 80
    x_start = 30
    for i, header in enumerate(headers):
        header_surface = font_row.render(header, True, BLACK)
        screen.blit(header_surface, (x_start + sum(col_widths[:i]), y_start))

    # Ligne horizontale sous l'en-tête
    pygame.draw.line(screen, LINE_COLOR, (x_start, y_start + row_height - 5), (SCREEN_WIDTH - x_start, y_start + row_height - 5), 2)

    # Lignes du classement
    for idx, row in enumerate(scoreboard_list[:10]):
        y = y_start + row_height * (idx + 1)
        row_data = [row["pseudo"], row["progression"], row["temps"], row["score"]]
        for j, data in enumerate(row_data):
            text = font_row.render(str(data), True, BLACK)
            screen.blit(text, (x_start + sum(col_widths[:j]), y))

        # Ligne de séparation
        pygame.draw.line(screen, LINE_COLOR, (x_start, y + row_height - 5), (SCREEN_WIDTH - x_start, y + row_height - 5), 1)

running = True
while running:
    draw_table()
    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

pygame.quit()
