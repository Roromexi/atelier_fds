import gym
import pygame
import numpy as np
import time
from pathlib import Path
from datetime import datetime
from gym_super_mario_bros.actions import COMPLEX_MOVEMENT
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
env = JoypadSpace(env, COMPLEX_MOVEMENT)

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

    action = 0  # NOOP par défaut

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            done = True
    
    keys = pygame.key.get_pressed()

    if keys[pygame.K_RIGHT]:
        action = 1 # avancer
    elif keys[pygame.K_SPACE]:
        action = 2 # sauter et avancer
    elif keys[pygame.K_DOWN]:
        action = 3 # sprint
    elif keys[pygame.K_UP]:
        action = 5 # sauter 
    elif keys[pygame.K_LEFT]:
        action = 6

            
    else:
        action = 0 #ne rien faire  

    obs, reward, done, info = env.step(action)
    total_reward += reward
    steps += 1
    logger.log_step(reward, info["coins"], info["score"])

# ----- Fin de partie -----
logger.log_episode()
logger.record(episode=0, epsilon=0, step=steps)

env.close()
pygame.quit()


  