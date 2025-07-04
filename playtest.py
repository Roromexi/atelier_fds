import gym
import pygame
import numpy as np
import time
from pathlib import Path
from datetime import datetime
from gym_super_mario_bros.actions import SIMPLE_MOVEMENT
from nes_py.wrappers import JoypadSpace
from metrics import MetricLogger

# ----- Initialisation Pygame -----
pygame.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode((512, 480))
pygame.display.set_caption("Joueur humain vs Mario")

# ----- Création du dossier de sauvegarde -----
now = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
save_dir = Path("logs_humain") / now 
save_dir.mkdir(parents=True, exist_ok=True)

# ----- Environnement Mario -----
env = gym.make("SuperMarioBros-v0")
env = JoypadSpace(env, SIMPLE_MOVEMENT)

# ----- Logger -----
logger = MetricLogger(save_dir = Path("logs_humain"))

# ----- Boucle de jeu (1 seule vie) -----
running = True
obs = env.reset()
done = False
total_reward = 0
steps = 0

while running and not done:
    clock.tick(60)
    env.render(mode='rgb_array')
    screen_buffer = env.render(mode='rgb_array')
    surf = pygame.surfarray.make_surface(np.transpose(screen_buffer, (1, 0, 2)))
    screen.blit(pygame.transform.scale(surf, (512, 480)), (0, 0))
    pygame.display.flip()

        # ----- Mapping action manuelle -----
    # SIMPLE_MOVEMENT = [
    #     ['NOOP'],               0
    #     ['right'],              1
    #     ['right', 'A'],         2
    #     ['right', 'B'],         3
    #     ['right', 'A', 'B'],    4
    #     ['A'],                  5
    #     ['left'],               6


    keys = pygame.key.get_pressed()

    right = keys[pygame.K_RIGHT]
    left = keys[pygame.K_LEFT]
    jump = keys[pygame.K_SPACE] or keys[pygame.K_UP]
    sprint = keys[pygame.K_DOWN] or keys[pygame.K_LSHIFT]

    # Default action = NOOP
    action = 0

    if right and jump and sprint:
        action = 4  # right + A + B
    elif right and sprint:
        action = 3  # right + B
    elif right and jump:
        action = 2  # right + A
    elif right:
        action = 1  # right only
    elif left and jump:
        action = 7  # left + A
    elif left:
        action = 6  # left only
    elif jump:
        action = 5  # A only
    else:
        action = 0  # NOOP



    obs, reward, done, info = env.step(action)
    total_reward += reward
    steps += 1
    logger.log_step(reward, info["coins"], info["score"])

# ----- Fin de partie -----
logger.log_episode()
logger.record(episode=0, epsilon=0, step=steps)

env.close()
pygame.quit()


