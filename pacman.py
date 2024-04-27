from gamestate import GameState
import pygame
from pygame.locals import *
from vector import Vector2
from constants import *
from entity import Entity
from sprites import PacmanSprites
from random import choice, randint
from utils.file_utils import save_pickle, load_pickle
from copy import deepcopy

class Pacman(Entity): #https://github.com/knowit/ml-pacman  (Some inspiration from this github repo, but it's very different from this pacman framework.)
    def __init__(self, node):
        Entity.__init__(self, node )
        self.name = PACMAN    
        self.color = YELLOW
        self.direction = LEFT
        self.setBetweenNodes(LEFT)
        self.alive = True
        self.sprites = PacmanSprites(self)
        self.q_table = {}
        self.loadModel()
        self.directionMethod = self.goalDirectionQLearning
        self.oldGameState = None
        self.oldAction = None
        self.gameStateElements = None
        self.numberOfActions = 1
        self.lives = None

        self.discount = 0.8
        self.alpha = 0.2

    def setGameStateElements(self, gameStateElements):
        self.gameStateElements = gameStateElements

    def setLives(self, lives):
        self.lives = lives

    def compute_max_q_value(self, directions, state):
        if state not in self.q_table:
            self.q_table[state] = {key: 0.0 for key in directions}

        return max(self.q_table[state].values())

    def goalDirectionQLearning(self, directions, game_state, old_game_state):
        action = self.pick_action(directions, game_state)

        reward = self.calculate_reward_for_move(game_state, old_game_state)

        if game_state not in self.q_table:
            self.q_table[game_state] = {key: 0.0 for key in directions}

        if self.oldAction is not None and old_game_state is not None:
            self.q_table[old_game_state][self.oldAction] = self.q_table[old_game_state][self.oldAction] + self.alpha * (reward + (self.discount * self.compute_max_q_value(directions, game_state)) - self.q_table[old_game_state][self.oldAction])

        self.oldGameState = GameState(game_state.pacman, game_state.powerpellets, game_state.score, game_state.fruit, pinky=game_state.pinky, inky=game_state.inky, clyde=game_state.clyde, blinky=game_state.blinky)
        self.oldAction = action


        # if self.numberOfActions % 50 == 0:
        #     self.numberOfActions += 1
        #     print('Saving model')
        #     save_pickle('./q_table_nopellets', self.q_table, True)
        # else:
        #     self.numberOfActions += 1

        

        return action
    
    def pick_action(self, directions, game_state): 
        exploration_prob = 0
        if exploration_prob >= randint(1, 100):
            # Explore
            print("Exploring!")
            return choice(directions)
        else:
            # Exploit
            return self.pick_optimal_action(directions, game_state)
        
    def pick_optimal_action(self, directions, state):
        if state not in self.q_table:
            self.q_table[state] = {key: 0.0 for key in directions}

        max_value = max(self.q_table[state].values())
        numberOfActions = [key for key in self.q_table[state] if self.q_table[state][key] == max_value]

        return choice(numberOfActions)

    def reset(self):
        Entity.reset(self)
        self.direction = LEFT
        self.setBetweenNodes(LEFT)
        self.alive = True
        self.image = self.sprites.getStartImage()
        self.sprites.reset()
        self.oldGameState = None
        self.oldAction = None

    def die(self):
        print('Pacman died')
        if self.oldGameState is not None and self.oldAction is not None:
            reward = -100
            directions = self.validDirections()
            self.q_table[self.oldGameState][self.oldAction] = self.q_table[self.oldGameState][self.oldAction] + self.alpha * (reward + (self.discount * self.compute_max_q_value(directions, self.oldGameState)) - self.q_table[self.oldGameState][self.oldAction])
            self.oldGameState = None
            self.oldAction = None
        print('Saving model')
        save_pickle('./q_table_nopellets', self.q_table, True)
        self.alive = False
        self.direction = STOP

    def validDirections(self): # Returns a list of valid directions, opposite direction is included.
        directions = []
        for key in [UP, DOWN, LEFT, RIGHT]:
            if self.validDirection(key):
                directions.append(key)
        return directions
    
    def loadModel(self, model_path='./q_table_nopellets.pkl'):
        try:
            self.q_table = load_pickle(model_path)
        except:
            self.q_table = {}

    def calculate_reward_for_move(self, game_state, old_game_state):
        if old_game_state is None:
            return game_state.score - 0
        
        new_score = game_state.score - old_game_state.score
        if new_score > 0:
            return new_score
        else:
            return -2

    def update(self, dt):
        self.sprites.update(dt)
        self.position += self.directions[self.direction]*self.speed*dt

        if self.overshotTarget(): # The direction method is only called when pacman has reached a node
            self.node = self.target
            directions = self.validDirections()
            direction = self.directionMethod(directions, GameState(self, self.gameStateElements[0], self.gameStateElements[1], self.gameStateElements[2], ghosts=self.gameStateElements[3]), self.oldGameState)
            self.target = self.getNewTarget(direction)
            if self.target is not self.node:
                self.direction = direction
            else:
                self.target = self.getNewTarget(self.direction)

            self.setPosition()

    def getValidKey(self):
        key_pressed = pygame.key.get_pressed()
        if key_pressed[K_UP]:
            return UP
        if key_pressed[K_DOWN]:
            return DOWN
        if key_pressed[K_LEFT]:
            return LEFT
        if key_pressed[K_RIGHT]:
            return RIGHT
        return STOP  

    def eatPellets(self, pelletList):
        for pellet in pelletList:
            if self.collideCheck(pellet):
                return pellet
        return None    
    
    def collideGhost(self, ghost):
        return self.collideCheck(ghost)

    def collideCheck(self, other):
        d = self.position - other.position
        dSquared = d.magnitudeSquared()
        rSquared = (self.collideRadius + other.collideRadius)**2
        if dSquared <= rSquared:
            return True
        return False
