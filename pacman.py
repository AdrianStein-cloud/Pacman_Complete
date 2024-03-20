from random import choice
from FSM import StateMachine
import pygame
from pygame.locals import *
from vector import Vector2
from constants import *
from entity import Entity
from sprites import PacmanSprites
from algorithms import a_star, heuristic

class Pacman(Entity):
    def __init__(self, node, nodes):
        Entity.__init__(self, node )
        self.name = PACMAN    
        self.color = YELLOW
        self.direction = LEFT
        self.setBetweenNodes(LEFT)
        self.alive = True
        self.sprites = PacmanSprites(self)
        self.directionMethod = self.goalDirectionAStar
        self.nodes = nodes # All nodes
        self.unvisitedNodes = self.getImportantNodes() # Important nodes that have not been visited yet
        self.goal = self.unvisitedNodes[44] # Initial goal is a point right next to pacman
        self.debugMode = True # set to True to see debug info
        self.ghosts = None # all ghosts
        self.path = None # path to follow
        self.oldTarget = None # Pacman's previous target

        # FSM   
        self.states = [FLEE, SEEK] # Possible states
        self.myState = SEEK # Initial state
        self.FSM = StateMachine(self.myState)

        self.FSM_decision() # Decide directionMethod based on state

        self.a_star_failed = False # True if A* failed to find a path

    def getImportantNodes(self): # Returns a list of important nodes, removes a bunch of nodes without pellets
        temp_list = list(self.nodes.costs)
        del temp_list[22]
        del temp_list[22]
        del temp_list[22]
        del temp_list[22]
        del temp_list[22]
        del temp_list[23]
        del temp_list[23]
        del temp_list[24]
        del temp_list[24]
        del temp_list[24]
        return temp_list

    def setGhosts(self, ghosts): # Set all ghosts from run.py
        self.ghosts = ghosts

    def reset(self):
        Entity.reset(self)
        self.direction = LEFT
        self.setBetweenNodes(LEFT)
        self.alive = True
        self.image = self.sprites.getStartImage()
        self.sprites.reset()

    def die(self):
        self.alive = False
        self.direction = STOP

    def validDirections(self): # Returns a list of valid directions, opposite direction is included.
        directions = []
        for key in [UP, DOWN, LEFT, RIGHT]:
            if self.validDirection(key):
                directions.append(key)
        return directions

    def update(self, dt):	
        self.advancedFSM() # Update state every frame
        self.sprites.update(dt)
        self.position += self.directions[self.direction]*self.speed*dt

        self.path = self.getAStarPath() # The path is checked every frame, so that flee_2_seek can check if there is a path to the goal
         
        if self.overshotTarget(): # The direction method is only called when pacman has reached a node
            self.node = self.target
            directions = self.validDirections()
            direction = self.directionMethod(directions)
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
    
    def setPelletList(self, pelletList):
        self.pelletList = pelletList
    
    def collideGhost(self, ghost):
        return self.collideCheck(ghost)

    def collideCheck(self, other):
        d = self.position - other.position
        dSquared = d.magnitudeSquared()
        rSquared = (self.collideRadius + other.collideRadius)**2
        if dSquared <= rSquared:
            return True
        return False
    
    #############
    def getAStarPath(self):
        pacmanTarget = self.target
        pacmanTarget = self.nodes.getVectorFromLUTNode(pacmanTarget)

        if len(self.unvisitedNodes) <= 0: # If all nodes have been visited, start over.
            self.unvisitedNodes = self.getImportantNodes()

        self.unvisitedNodes.sort(key=lambda node: heuristic(node, pacmanTarget)) # Sort unvisited nodes by distance from pacman
        self.goal = self.unvisitedNodes[0] # Set the goal to the closest unvisited node
            

        if pacmanTarget != self.oldTarget: # If pacman has moved, remove the old target from unvisited nodes
            if self.oldTarget is not None and self.oldTarget in self.unvisitedNodes:
                self.unvisitedNodes.remove(self.oldTarget)
            self.oldTarget = pacmanTarget

        if self.goal == pacmanTarget and len(self.unvisitedNodes) > 1: # If the goal is the same as pacman's target, set the goal to the next closest node
            self.unvisitedNodes.remove(self.goal)

        if (self.position.x, self.position.y) in self.unvisitedNodes: # If pacman is on a node, remove it from unvisited nodes
            self.unvisitedNodes.remove((self.position.x, self.position.y))

        if pacmanTarget == self.goal:
            return [pacmanTarget]  # Pacman is already at the goal, return the current position

        previous_nodes, shortest_path = a_star(self.nodes, pacmanTarget, ghosts=self.ghosts) # Get the shortest path to the goal
        path = []
        node = self.goal # Start from the goal
        while node != pacmanTarget: # Follow the path back to pacman's current position
            if node not in previous_nodes:  # Pacman cannot reach the goal
                # Sort unvisited nodes by distance from Pacman's current position
                self.unvisitedNodes.sort(key=lambda node: heuristic(node, pacmanTarget))
                for unvisited in self.unvisitedNodes:  # Try all other unvisited nodes
                    previous_nodes, shortest_path = a_star(self.nodes, unvisited, ghosts=self.ghosts)
                    if unvisited in previous_nodes:  # Found a reachable unvisited node
                        self.goal = unvisited
                        break
                else:  # No reachable unvisited nodes found
                    self.a_star_failed = True # A* failed
                    return []
            path.append(node) # Add the node to the path
            node = previous_nodes[node] # Move to the next node
        path.append(pacmanTarget) # Add Pacman's current position to the path
        path.reverse() # Reverse the path so that it goes from Pacman's current position to the goal
        self.a_star_failed = False # A* succeeded
        return path
    
    # Chooses direction in which to turn based on a star
    def goalDirectionAStar(self, directions):
            
            path = self.path # Get the path to follow

            if len(path) < 2:
                print("Random")
                return choice(directions)  # No more path to follow, return a random direction

            nextNode = path[1] # Get the next node in the path
            pacmanPosition = self.nodes.getVectorFromLUTNode(self.target)  # Get Pacman's current position
            pacmanX, pacmanY = pacmanPosition[0], pacmanPosition[1] # Get Pacman's current x and y coordinates
            nextNodeX, nextNodeY = nextNode[0], nextNode[1] # Get the next node's x and y coordinates

            dx = nextNodeX - pacmanX # Calculate the difference in x coordinates
            dy = nextNodeY - pacmanY # Calculate the difference in y coordinates

            if dx < 0 and LEFT in directions: # if difference in x coordinates is negative, move left
                return LEFT
            if dx > 0 and RIGHT in directions: # if difference in x coordinates is positive, move right
                return RIGHT
            if dy < 0 and UP in directions: # if difference in y coordinates is negative, move up
                return UP
            if dy > 0 and DOWN in directions: # if difference in y coordinates is positive, move down
                return DOWN
            
            print("directions: ", directions) # If no direction was chosen, print directions and return a random direction

            return choice(directions)
    
    def distancesToGhosts(self, node): # Returns a list of distances to all ghosts that are not in freight mode or spawn mode
        distances = []
        for ghost in self.ghosts:
            if ghost.mode.current == FREIGHT or ghost.mode.current == SPAWN :
                continue
            vec = node.position - ghost.target.position
            distances.append(vec.magnitudeSquared())
        return distances
    
    def closestGhost(self): # Returns the closest ghost that is not in freight mode or spawn mode
        distances = self.distancesToGhosts(self.node)
        if len(distances) == 0:
            return None
        index = distances.index(min(distances))
        return list(self.ghosts)[index]
    
    def goalDirectionFlee(self, directions): # Returns the direction in which to flee from the closest ghost. Identical to ghosts' chase, but with the closest ghost as target, and max instead of min.
        distances = []
        for direction in directions:
            try:
                vec = self.node.position + self.directions[direction]*TILEWIDTH - self.closestGhost().position
            except:
                return choice(directions)
            distances.append(vec.magnitudeSquared())
        index = distances.index(max(distances)) # Choose the direction that maximizes the distance to the closest ghost
        return directions[index]

    

    def FSM_decision(self): # Decides which direction method to use based on the current state
        if self.myState == FLEE:
            self.directionMethod = self.goalDirectionFlee
        elif self.myState == SEEK:
            self.directionMethod = self.goalDirectionAStar
        else:
            self.myState = choice(self.states)

    def advancedFSM(self): # Updates the state and direction method every frame
        distances_to_ghosts = self.distancesToGhosts(self.node)

        # If there are no ghosts in the game that are not in freight mode or spawn mode, the distance is set really high.
        if len(distances_to_ghosts) != 0: 
            distance_to_ghost = min(distances_to_ghosts)
        else:
            distance_to_ghost = 1000000000
        new_state = self.FSM.updateState(distance_to_ghost, self.a_star_failed) # Update the state

        self.FSM_decision() # Decide which direction method to use based on the new state

        self.old_state = new_state








