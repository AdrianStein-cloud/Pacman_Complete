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

import pygame


from vector import Vector2
from run import GameController
from constants import UP, DOWN, RIGHT, LEFT


class State:
    def __init__(self, playerPosition: Vector2, inkyPosition: Vector2, blinkyPosition: Vector2, clydePosition: Vector2, pinkyPosition: Vector2, fruit, pellets) -> None:
        # TODO: Add more variables in the state so that the agent can account for more things in its environment
        # examples: (ghosts,)
        # warning: The more variables you add, the more space it will have search and it will take more time to train
        self.playerPosition = playerPosition.asTuple()
        self.inkyPosition = inkyPosition.asTuple()
        self.blinkyPosition = blinkyPosition.asTuple()
        self.clydePosition = clydePosition.asTuple()
        self.pinkyPosition = pinkyPosition.asTuple()
        self.powerpellets = pellets.powerpellets
        if fruit is not None:
            self.fruit = fruit.position.asTuple()
        else:
            self.fruit = None
        self.closestPellet = self.findClosestPellet(playerPosition, pellets).position.asTuple()

    def __str__(self) -> str:
        result = "{}.{}".format(self.playerPosition[0], self.playerPosition[1]) + "," + "{}.{}".format(self.inkyPosition[0], self.inkyPosition[1]) + "," + "{}.{}".format(self.blinkyPosition[0], self.blinkyPosition[1]) + "," + "{}.{}".format(self.clydePosition[0], self.clydePosition[1]) + "," + "{}.{}".format(self.pinkyPosition[0], self.pinkyPosition[1])
        for powerpellet in self.powerpellets:
            powerpelletPosition = powerpellet.position.asTuple()
            result += "," + "{}.{}".format(powerpelletPosition[0], powerpelletPosition[1])
        if self.fruit is not None:
            result += "," + "{}.{}".format(self.fruit[0], self.fruit[1])
        result += "," + "{}.{}".format(self.closestPellet[0], self.closestPellet[1])
        
        return result
    
    def findClosestPellet(self, playerPosition, pellets):
        closestPellet = None
        minDistance = float('inf')
        for pellet in pellets.pelletList:
            distance = pellet.position.distance(playerPosition)
            if distance < minDistance:
                minDistance = distance
                closestPellet = pellet
        return closestPellet


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
                                self.storage[key] = (self.storage[key] + value) / 2
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
        return State(self.game.pacman.target.position, self.game.ghosts.inky.target.position, self.game.ghosts.blinky.target.position, self.game.ghosts.clyde.target.position, self.game.ghosts.pinky.target.position, self.game.fruit, self.game.pellets)

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
            reward = -2
        else:
            reward = (self.game.score - previousScore) / 3
            reward += previousNumberOfPellets - len(self.game.pellets.pelletList) * 30
        if previousLives is not None and self.game.pacman.lives < previousLives:
            reward = -10000

        if self.game.pellets.isEmpty():
            reward = 100000

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
    store = QValueStore("training_high_pellet_reward")
    problem = ReinforcementProblem()

    # Train the model
    # QLearning(problem, 30000, 0.7, 0.75, 0.1, 0.00)

    # Test the model
    QLearning(problem, 10000, 0.7, 0.75, 0.2, 0.00)

