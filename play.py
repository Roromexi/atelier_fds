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
LEVEL_ENDS = {"1-1": 4500}  # Fin du niveau (à ajuster pour d'autres mondes)
CURRENT_LEVEL = "1-1"
SCOREBOARD_FILE = Path("scoreboard.csv")

# ----- INIT PYGAME -----
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

# ----- SESSION DE JEU -----
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

# ----- FIN DE PARTIE -----
end_time = time.time()
elapsed_time = round(end_time - start_time, 2)
percent_done = round(min(max_x_pos / LEVEL_ENDS[CURRENT_LEVEL], 1.0) * 100, 2)

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
        fieldnames = ["pseudo", "niveau", "progression", "temps", "score"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for entry in data:
            writer.writerow(entry)

scoreboard = load_scoreboard()
scoreboard = [entry for entry in scoreboard if all(k in entry for k in ['iveay', 'progression', "temps", "score"])]
scoreboard.sort(key=lambda x: (
    int(x["niveau"]),
    -float(x["progression"]),
    float(x["temps"]),
    -float(x["score"])
), reverse=False)



current_entry = {
    "pseudo": pseudo,
    "niveau": CURRENT_LEVEL,
    "progression": str(percent_done),
    "temps": str(elapsed_time),
    "score": str(round(total_reward, 2))
}

old = next((entry for entry in scoreboard if entry["pseudo"] == pseudo), None)

if old:
    keep_old = (
        old["niveau"] > CURRENT_LEVEL
        or (old["niveau"] == CURRENT_LEVEL and float(old["progression"]) > percent_done)
        or (old["niveau"] == CURRENT_LEVEL and float(old["progression"]) == percent_done and float(old["temps"]) < elapsed_time)
    )

    if keep_old:
        current_entry = old
    else:
        scoreboard = [entry for entry in scoreboard if entry["pseudo"] != pseudo]



scoreboard[pseudo] = current_entry

scoreboard_list = list(scoreboard.values())
scoreboard_list.sort(key=lambda x: (x["niveau"], -float(x["progression"]), float(x["temps"]), -float(x["score"])))
save_scoreboard(scoreboard_list)

# ----- AFFICHAGE CLASSEMENT -----
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 650
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Classement Joueurs")
font_title = pygame.font.SysFont("Arial", 28, bold=True)
font_row = pygame.font.SysFont("Arial", 20)

row_height = 34
col_widths = [60, 140, 80, 120, 100, 100]
headers = ["#", "Pseudo", "Niveau", "Progression (%)", "Temps (s)", "Score"]

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (108, 194, 236)
GRASS_GREEN = (64, 200, 64)
LINE_COLOR = (255, 255, 255)
BUTTON_COLOR = (200, 100, 100)
BUTTON_HOVER = (255, 150, 150)

cloud = pygame.Surface((80, 40), pygame.SRCALPHA)
pygame.draw.ellipse(cloud, WHITE, cloud.get_rect())

rejouer_rect = pygame.Rect(SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT - 60, 140, 40)
quitter_rect = pygame.Rect(SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT - 60, 140, 40)

visible_rows = [row for row in scoreboard_list if row["pseudo"].lower() != "log"]

def draw_table():
    screen.fill(SKY_BLUE)
    pygame.draw.rect(screen, GRASS_GREEN, pygame.Rect(0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, 100))
    screen.blit(cloud, (80, 50))
    screen.blit(cloud, (400, 100))

    title_surface = font_title.render("Classement des joueurs", True, BLACK)
    title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 30))
    screen.blit(title_surface, title_rect)

    y_start = 80
    x_start = 30
    for i, header in enumerate(headers):
        header_surface = font_row.render(header, True, BLACK)
        screen.blit(header_surface, (x_start + sum(col_widths[:i]), y_start))

    pygame.draw.line(screen, LINE_COLOR, (x_start, y_start + row_height - 5), (SCREEN_WIDTH - x_start, y_start + row_height - 5), 2)

    for idx, row in enumerate(visible_rows[:10]):
        y = y_start + row_height * (idx + 1)
        row_data = [str(idx + 1), row["pseudo"], row["niveau"], row["progression"], row["temps"], row["score"]]
        for j, data in enumerate(row_data):
            text = font_row.render(str(data), True, BLACK)
            screen.blit(text, (x_start + sum(col_widths[:j]), y))
        pygame.draw.line(screen, LINE_COLOR, (x_start, y + row_height - 5), (SCREEN_WIDTH - x_start, y + row_height - 5), 1)

    # Boutons
    mouse_pos = pygame.mouse.get_pos()
    for rect, label in [(rejouer_rect, "Rejouer"), (quitter_rect, "Quitter")]:
        color = BUTTON_HOVER if rect.collidepoint(mouse_pos) else BUTTON_COLOR
        pygame.draw.rect(screen, color, rect)
        text_surf = font_row.render(label, True, BLACK)
        screen.blit(text_surf, (rect.x + 20, rect.y + 10))

# ----- BOUCLE CLASSEMENT -----
running = True
while running:
    draw_table()
    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if rejouer_rect.collidepoint(event.pos):
                pygame.quit()
                exec(open(__file__).read())  # relance le script complet
            elif quitter_rect.collidepoint(event.pos):
                running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

pygame.quit()


