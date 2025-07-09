# ----- Importation -----
import pygame
import gym
import time
import csv
import os
from datetime import datetime
from pathlib import Path
from gym_super_mario_bros.actions import SIMPLE_MOVEMENT
from nes_py.wrappers import JoypadSpace


# ----- Constantes -----
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600 # Fond
BACKGROUND_COLOR = (135, 206, 250) # couleurs du fond
FONT_NAME = "arial"
FONT_SIZE = 24
SCOREBOARD_FILE = "scoreboard.csv" # fichier où sont stockés les scores 
CURRENT_LEVEL = 1
LEVEL_DISTANCES = {1: 3155, 2: 3155, 3: 4000}

# ----- Initialisation -----
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mario IA - Joueur Humain")
font = pygame.font.SysFont(FONT_NAME, FONT_SIZE)
clock = pygame.time.Clock()


# ----- Pseudo -----
def ask_pseudo():
    input_box = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, 300, 40)
    pseudo = ""
    color_inactive = pygame.Color("lightskyblue3")
    color_active = pygame.Color("dodgerblue2")
    color = color_active

    while True:
        screen.fill(BACKGROUND_COLOR)
        pygame.draw.rect(screen, (48, 200, 48), (0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, 100))

        title = font.render("Entrez votre pseudo", True, (0,0,0))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 85))

        txt_surface = font.render(pseudo, True, (0, 0, 0))
        width = max(200, txt_surface.get_width() + 10)
        input_box.w = width
        pygame.draw.rect(screen, (255, 255, 255), input_box)
        screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
        pygame.draw.rect(screen, color, input_box, 2)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and pseudo.strip():
                    return pseudo.strip()
                elif event.key == pygame.K_BACKSPACE:
                    pseudo = pseudo[:-1]
                else:
                    if len(pseudo) < 15:
                        pseudo += event.unicode

        clock.tick(30)

# ----- Scoreboard -----
def load_scoreboard():
    scoreboard = []
    if os.path.exists(SCOREBOARD_FILE):
        with open(SCOREBOARD_FILE, newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                scoreboard.append(row)
    return scoreboard

def save_scoreboard(scoreboard):
    with open(SCOREBOARD_FILE, "w", newline='', encoding="utf-8") as f:
        fieldnames = ["pseudo", "niveau", "progression", "temps", "score"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for entry in scoreboard:
            writer.writerow(entry)

# ----- Jeu -----
def play_game(pseudo):
    env = gym.make("SuperMarioBros-v0")
    env = JoypadSpace(env, SIMPLE_MOVEMENT)
    obs = env.reset()
    done = False
    total_reward = 0
    start_time = time.time()

    while not done:
        screen.fill(BACKGROUND_COLOR)
        frame = env.render(mode="rgb_array")
        surf = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        surf = pygame.transform.scale(surf, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(surf, (0, 0))
        pygame.display.flip()

        keys = pygame.key.get_pressed()
        action = 0
        if keys[pygame.K_RIGHT]:
            action = 1 #avancer vers la droite
        if keys[pygame.K_SPACE] or keys[pygame.K_UP]:
            action = 2 # sauter et avancer vers la droite 
        if keys[pygame.K_DOWN] :
            action = 3 # sprinter à droite 
        if keys[pygame.K_LEFT]:
            action = 6 # avancer à gauche 

        obs, reward, done, info = env.step(action)
        print("x_pos:", info["x_pos"], "| world:", info.get("world"), "| stage:", info.get("stage"))
        total_reward += reward

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True

        clock.tick(60)

    env.close()
    elapsed_time = time.time() - start_time
    distance = info.get("x_pos", 0)

    # Calcul du pourcebtage de progression en fonction du niveau dans lequel tu es 
    max_distance = LEVEL_DISTANCES.get(CURRENT_LEVEL, 3186) # 3186 ≈ fin du niveau
    percent_done = min(distance / max_distance, 1.0) * 100  
    level = info.get("stage", 1)

    return {
        "pseudo": pseudo,
        "niveau": level,
        "progression": str(round(percent_done, 1)),
        "temps": str(round(elapsed_time, 2)),
        "score": str(round(total_reward, 2))
    }


# ----- Scoreboard Affichage -----
def show_scoreboard(new_entry):
    scoreboard = load_scoreboard()

    existing = [entry for entry in scoreboard if entry["pseudo"] == new_entry["pseudo"]]
    if existing:
        old = existing[0]
        keep_old = (
            int(old["niveau"]) > int(new_entry["niveau"]) or
            (int(old["niveau"]) == int(new_entry["niveau"]) and float(old["progression"]) > float(new_entry["progression"])) or
            (int(old["niveau"]) == int(new_entry["niveau"]) and float(old["progression"]) == float(new_entry["progression"]) and float(old["temps"]) < float(new_entry["temps"])) or
            (int(old["niveau"]) == int(new_entry["niveau"]) and float(old["progression"]) == float(new_entry["progression"]) and float(old["temps"]) == float(new_entry["temps"]) and float(old["score"]) >= float(new_entry["score"]))
        )
        if not keep_old:
            scoreboard = [entry for entry in scoreboard if entry["pseudo"] != new_entry["pseudo"]]
            scoreboard.append(new_entry)
    else:
        scoreboard.append(new_entry)

    scoreboard = [entry for entry in scoreboard if all(k in entry for k in ['niveau', 'progression', 'temps', 'score'])]
    scoreboard.sort(key=lambda x: (
        -int(x["niveau"]),
        -float(x["progression"]),
        float(x["temps"]),
        -float(x["score"])
    ))

    save_scoreboard(scoreboard)


    # ----- Affichage Pygame -----
    showing = True
    font_title = pygame.font.SysFont(FONT_NAME, 28, bold=True)
    font_data = pygame.font.SysFont(FONT_NAME, 22)

    while showing:
        screen.fill((0, 0, 0))
        title = font_title.render("Classement des Joueurs", True, (255, 255, 255))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 30))

        headers = ["#", "Pseudo", "Niveau", "Progression (%)", "Temps (s)", "Score"]
        col_widths = [40, 160, 100, 170, 110, 100]
        for i, header in enumerate(headers):
            label = font_data.render(header, True, (255, 255, 0))
            screen.blit(label, (50 + sum(col_widths[:i]), 80))
            pygame.draw.line(screen, (255, 255, 255), (50 + sum(col_widths[:i]), 75), (50 + sum(col_widths[:i]), 500), 1)

        for idx, entry in enumerate(scoreboard[:10]):
            y = 120 + idx * 35
            row = [
                str(idx + 1),
                entry["pseudo"],
                entry["niveau"],
                entry["progression"],
                entry["temps"],
                entry["score"]
            ]
            for i, value in enumerate(row):
                txt = font_data.render(str(value) , True, (255, 255, 255))
                screen.blit(txt, (50 + sum(col_widths[:i]), y))

        # Boutons
        button_font = pygame.font.SysFont(FONT_NAME, 24)
        replay_btn = pygame.Rect(250, 540, 120, 40)
        quit_btn = pygame.Rect(430, 540, 120, 40)

        pygame.draw.rect(screen, (0, 128, 0), replay_btn)
        pygame.draw.rect(screen, (200, 0, 0), quit_btn)

        screen.blit(button_font.render("Rejouer", True, (255, 255, 255)), (replay_btn.x + 20, replay_btn.y + 8))
        screen.blit(button_font.render("Quitter", True, (255, 255, 255)), (quit_btn.x + 25, quit_btn.y + 8))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                showing = False
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if replay_btn.collidepoint(event.pos):
                    main()
                elif quit_btn.collidepoint(event.pos):
                    pygame.quit()
                    exit()

        clock.tick(30)

# ----- Main -----
def main():
    pseudo = ask_pseudo()
    stats = play_game(pseudo)
    show_scoreboard(stats)
    

if __name__ == "__main__":
    main()



