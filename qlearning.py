from __future__ import annotations

# avoiding circular dependency
from genericpath import exists
import os
import time
from typing import TYPE_CHECKING, Any
from enum import IntEnum
import pickle
import random
from filelock import FileLock
from algorithms import dijkstra

import pygame


from vector import Vector2
from run import GameController
from constants import UP, DOWN, RIGHT, LEFT


class State:
    def __init__(self, nodes, pacman, ghosts, pellets) -> None:
        
        self.nodes = nodes
        self.path = self.dijkstra(nodes, pacman, 100)
        self.pacman = pacman
        self.ghosts = ghosts
        self.closestPellet = self.findClosestPellet(pacman.target.position, pellets).asTuple()


    def __str__(self) -> str:
        ghostPositions = []
        pacmanTarget = self.pacman.target
        pacmanTarget = self.nodes.getVectorFromLUTNode(pacmanTarget)

        for ghost in self.ghosts:
            if ghost.mode.current != 2:
                ghostTarget = ghost.target
                ghostTarget = self.nodes.getVectorFromLUTNode(ghostTarget)
                ghostPositions.append(((ghostTarget[0] - pacmanTarget[0]), (ghostTarget[1] - pacmanTarget[1])))

        result = "p{}.{}".format(self.closestPellet[0], self.closestPellet[1])
        for node in self.path:
            if node not in ghostPositions:
                result += ",{}.{}".format(node[0], node[1])
            else:
                result += ",g{}.{}".format(node[0], node[1])
        
        return result
    
    def findClosestPellet(self, playerPosition, pellets):
        closestPellet = None
        minDistance = float('inf')
        for pellet in pellets.pelletList:
            distance = pellet.position.distance(playerPosition)
            if distance < minDistance:
                minDistance = distance
                closestPellet = pellet
        closestPellet = closestPellet.position - playerPosition
        return closestPellet
    
    def dijkstra (self, nodes, pacman, depth):
        pacmanTarget = pacman.target
        pacmanTarget = nodes.getVectorFromLUTNode(pacmanTarget)
        previous_nodes, shortest_path = dijkstra(nodes, pacmanTarget, depth)

        path = []

        for node in previous_nodes:
            path.append(((node[0] - pacmanTarget[0]), (node[1] - pacmanTarget[1])))

        pacman.setPath(previous_nodes)

        return path


class Action(IntEnum):
    UP = UP
    DOWN = DOWN
    LEFT = LEFT
    RIGHT = RIGHT

    def __str__(self) -> str:
        return str(self)


def hash(state: State, action: Action) -> str:
    return "{}.{}".format(str(state), str(action))


class QValueStore:
    def __init__(self, filePath: str) -> None:
        self.filePath = filePath
        self.storage: dict[str, float] = {}
        self.load(self.filePath)

    def getQValue(self, state: State, action: Action) -> float:
        h = hash(state, action)
        value = self.storage.get(h)
        if value:
            return value
        else:
            return 0.0
        
    def mergeAndSave(self):
        lock = FileLock("lockfile.lock")

        print("Requesting lock...")

        with lock:
            try:
                if os.path.exists(self.filePath):
                    with open(self.filePath, "rb") as fr:
                        fileStorage = pickle.load(fr)
                        for key, value in fileStorage.items():
                            if key in self.storage:
                                self.storage[key] = max(self.storage[key], value)
                            else:
                                self.storage[key] = value
                with open(self.filePath, "wb") as fw:
                    pickle.dump(self.storage, fw)
            except Exception as e:
                print(f"An error occurred while merging and saving: {e}")

        print("Saving: dictionary size", len(self.storage))

    def getBestAction(self, state: State, possibleActions: list[Action]) -> Action:
        return max(possibleActions, key=lambda action: self.getQValue(state, action))

    def storeQValue(self, state: State, action: Action, value: float):
        h = hash(state, action)
        self.storage[h] = value

    def save(self):
        print("Saving: dictionary size", len(self.storage))
        fw = open(self.filePath, "wb")
        pickle.dump(self.storage, fw)
        fw.close()

    # Loads a Q-table.
    def load(self, file: str):
        if os.path.exists(file):
            fr = open(file, "rb")
            self.storage = pickle.load(fr)
            print("Loading: dictionary size", len(self.storage))
            fr.close()
        else:
            self.save()


class ReinforcementProblem:

    def __init__(self) -> None:
        self.game = GameController()
        self.game.restartGameRandom()

    def getCurrentState(self) -> State:
        return State(self.game.nodes, self.game.pacman, self.game.ghosts.ghosts, self.game.pellets)

    # Choose a random starting state for the problem.
    def getRandomState(self) -> State:
        #self.game.setPacmanInRandomPosition()
        return self.getCurrentState()

    # Get the available actions for the given state.
    def getAvailableActions(self, state: State) -> list[Action]:
        directions = self.game.pacman.validDirections()

        def intDirectionToString(dir: Action) -> str:
            match dir:
                case Action.UP:
                    return "UP"
                case Action.DOWN:
                    return "DOWN"
                case Action.LEFT:
                    return "LEFT"
                case Action.RIGHT:
                    return "RIGHT"
                case _:
                    return "INV"

        # print(list(map(intDirectionToString, directions)))
        return directions

    def updateGameNTimes(self, frames: int):
        for i in range(frames):
            self.game.update()

    def updateGameForSeconds(self, seconds: float):
        durationMills: float = seconds * 1000
        currentTime = pygame.time.get_ticks()
        endTime = currentTime + durationMills
        while currentTime < endTime:
            self.game.update()
            currentTime = pygame.time.get_ticks()

    # Take the given action and state, and return
    # a pair consisting of the reward and the new state.
    def takeAction(self, state: State, action: Action) -> tuple[float, State]:
        previousScore = self.game.score
        previousLives = self.game.pacman.lives
        previousNumberOfPellets = len(self.game.pellets.pelletList)
        self.game.pacman.learntDirection = action
        self.updateGameForSeconds(0.1)
        reward = 0
        score = self.game.score - previousScore
        if score == 0:
            reward = -1
        else:
            reward = previousNumberOfPellets - len(self.game.pellets.pelletList) * 20
        if previousLives is not None and self.game.pacman.lives < previousLives:
            reward = -500

        if self.game.pellets.isEmpty():
            reward = 10000

        newState = self.getCurrentState()
        return reward, newState

    # PARAMETERS:
    # Learning Rate
    # controls how much influence the current feedback value has over the stored Q-value.

    # Discount Rate
    # how much an action’s Q-value depends on the Q-value at the state (or states) it leads to.

    #  Randomness of Exploration
    # how often the algorithm will take a random action, rather than the best action it knows so far.

    # The Length of Walk
    # number of iterations that will be carried out in a sequence of connected actions.


# Updates the store by investigating the problem.
def QLearning(
    problem: ReinforcementProblem,
    iterations,
    initialLearningRate,
    discountRate,
    explorationRandomness,
    walkLength,
):
    # Get a starting state.
    state = problem.getRandomState()
    saveIterations = 500
    # Repeat a number of times.
    for i in range(iterations + 1):
        # Decay the learning rate over time
        # learningRate = initialLearningRate * (1 - i / iterations)
        learningRate = initialLearningRate

        if i % saveIterations == 0 and i > 0:
            print("Saving at iteration:", i)
            store.mergeAndSave()
        # Pick a new state every once in a while.
        if random.uniform(0, 1) < walkLength:
            state = problem.getRandomState()

        # Get the list of available actions.
        actions = problem.getAvailableActions(state)

        # Should we use a random action this time?
        if random.uniform(0, 1) < explorationRandomness:
            action = random.choice(actions)
        # Otherwise pick the best action.
        else:
            action = store.getBestAction(state, problem.getAvailableActions(state))

        # Carry out the action and retrieve the reward and new state.
        reward, newState = problem.takeAction(state, action)

        # Get the current q from the store.
        q = store.getQValue(state, action)

        # Get the q of the best action from the new state
        maxQ = store.getQValue(
            newState,
            store.getBestAction(newState, problem.getAvailableActions(newState)),
        )

        # Perform the q learning.
        q = (1 - learningRate) * q + learningRate * (reward + discountRate * maxQ)

        # Store the new Q-value.
        store.storeQValue(state, action, q)

        # And update the state.
        state = newState

if __name__ == "__main__":
    # The store for Q-values, we use this to make decisions based on
    # the learning.
    store = QValueStore("training_dijkstra_100")
    problem = ReinforcementProblem()

    # Train the model
    # QLearning(problem, 30000, 0.7, 0.75, 0.1, 0.00)

    # Test the model
    QLearning(problem, 10000, 0.7, 0.75, 0.2, 0.00)

