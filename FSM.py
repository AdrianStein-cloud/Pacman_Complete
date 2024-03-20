from xml.etree.ElementTree import TreeBuilder
from constants import *
from entity import *

class Transition(object):
    def __init__(self, start_state, target_state):
        self.start_state = start_state
        self.target_state = target_state

    # Tests for checking if state has to change
    def isTriggered(self, distance_to_ghost, a_star_failed):
        # SEEK
        if self.start_state == SEEK:
            if self.target_state.state == FLEE:
                return self.seek_2_flee(distance_to_ghost, a_star_failed)
        # FLEE
        if self.start_state == FLEE:
            if self.target_state.state == SEEK:
                return self.flee_2_seek(distance_to_ghost, a_star_failed)

    def seek_2_flee(self, distance_to_ghost, a_star_failed):
        if distance_to_ghost < 1500 or a_star_failed: # If the ghost is too close or the A* algorithm failed, change from seek to flee
            print("seek -> flee")
            return True
        else:
            return False
        
    def flee_2_seek(self, distance_to_ghost, a_star_failed):
        if distance_to_ghost > 2000 and not a_star_failed: # If the ghost is far enough away and the A* algorithm didn't fail, change from flee to seek
            print("flee -> seek")
            return True
        else:
            return False
            

class State(object):
    def __init__(self, state):
        self.state = state 
        
    def getOtherStates(self, state1):
        # SEEK
        if self.state == SEEK:
            self.flee = state1
            self.seek_2_flee = Transition(self.state, self.flee) # Transition from seek to flee
        # FLEE
        if self.state == FLEE:
            self.seek = state1
            self.flee_2_seek = Transition(self.state, self.seek) # Transition from flee to seek

    # Return which transitions are possible from each state
    def getTransitions(self):
        if self.state == SEEK:
            return [self.seek_2_flee]
        if self.state == FLEE:
            return [self.flee_2_seek]
        


class StateMachine(object):
    def __init__(self, initial_state):
        # Holds a list of states for the machine
        self.seek = State(SEEK)
        self.flee = State(FLEE)
        
        self.seek.getOtherStates(self.flee)
        self.flee.getOtherStates(self.seek)

        # Holds the initial state
        if initial_state == SEEK:
            self.initialState = self.seek
        elif initial_state == FLEE:
            self.initialState = self.flee
        # Holds the current state
        self.currentState = self.initialState
        
        
    # Checks and applies transitions, returning a list of actions.
    def updateState(self, distance_to_ghost, a_star_failed): # distance_to_ghost is the distance to the closest ghost, a_star_failed is a boolean that is True if the A* algorithm failed
        # Assume no transition is triggered 
        triggeredTransition = None

        # Check through each transition and 
        # store the first one that triggers.
        for transition in self.currentState.getTransitions():
            if transition.isTriggered(distance_to_ghost, a_star_failed):
                triggeredTransition = transition
                break
        
        # Check if we have a transition to fire
        if triggeredTransition:
            # Find the triggered state
            targetState = triggeredTransition.target_state

            # Complete transition and return action list
            self.currentState = targetState
            return self.currentState.state

        else:
            return self.currentState.state