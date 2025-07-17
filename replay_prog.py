#-------Importations---------
import random, datetime
from pathlib import Path

import gym
import gym_super_mario_bros
from gym.wrappers import FrameStack, GrayScaleObservation, TransformObservation
from nes_py.wrappers import JoypadSpace

from metrics_prog import MetricLogger
from agent import Mario
from wrappers import ResizeObservation, SkipFrame
import cv2


#-------Initialisations--------------
env = gym_super_mario_bros.make('SuperMarioBros-v0')
env = JoypadSpace(
    env,
    [['right'],
    ['right', 'A']]
)
env = SkipFrame(env, skip=4)
env = GrayScaleObservation(env, keep_dim=False)
env = ResizeObservation(env, shape=84)
env = TransformObservation(env, f=lambda x: x / 255.)
env = FrameStack(env, num_stack=4)

# Patch pour désactiver l'affichage et éviter pyglet
env.render = lambda *args, **kwargs: None

env.reset()


save_dir = Path('checkpoints') / datetime.datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
save_dir.mkdir(parents=True)

# Peut commencer l'entrainement de zéro ou à partir d'un checkpoint
checkpoint = Path('trained_mario.chkpt')
mario = Mario(state_dim=(4, 84, 84), action_dim=env.action_space.n, save_dir=save_dir, checkpoint=checkpoint)
mario.exploration_rate = mario.exploration_rate_min

logger = MetricLogger(save_dir)

episodes = 14000 #Normalement le mario finit le niveau quasiment tout le temps à ce niveau là

# -------Boucle principale------
for e in range(episodes):
    state = env.reset()
    scale_factor = 3  # ajuste la taille ici
    level_finished = 0
    avancee = 0
    position = 0 

    while True:
        frame = env.unwrapped.screen
        if frame is not None:
            frame_bgr = frame[..., ::-1]
            height, width = frame_bgr.shape[:2]
            frame_resized = cv2.resize(frame_bgr, (width * scale_factor, height * scale_factor), interpolation=cv2.INTER_NEAREST)

            cv2.imshow("Mario", frame_resized)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        action = mario.act(state)
        next_state, reward, done, info = env.step(action)

        mario.cache(state, next_state, action, reward, done)
        logger.log_step(reward, None, None)
        state = next_state

        # Calcul de la progression 
        distance = info.get("x_pos", 0)
        percent_done = min(distance / 3155, 1.0) * 100  

        #Condition d'arret si le mario atteind le drapeau 
        if info['flag_get']:
            level_finished += 1
            print(f"Time = {400 - info['time']} secondes")
            print("flag!")
            env.reset()
            break

        elif done:
            print(f"Time = {400 - info['time']} secondes")
            print("done!")
            print(f"{percent_done} % de fini") # Rajouter pour la progression
            break

    logger.log_episode()

# Affichage tout les 50 épisodes 
    if e % 50 == 0:
        logger.record(
            episode=e,
            epsilon=mario.exploration_rate,
            step=mario.curr_step,
            progression = percent_done , # Rajouter pour la progression
            flag_get = level_finished
        )

cv2.destroyAllWindows()
