from random import choice
import pygame
from pygame.locals import *
from vector import Vector2
from constants import *
from entity import Entity
from sprites import PacmanSprites
from algorithms import a_star

class Pacman(Entity):
    def __init__(self, node, nodes):
        Entity.__init__(self, node )
        self.name = PACMAN    
        self.color = YELLOW
        self.direction = LEFT
        self.setBetweenNodes(LEFT)
        self.alive = True
        self.sprites = PacmanSprites(self)
        self.directionMethod = self.goalDirectionFlee
        self.nodes = nodes
        self.unvisitedNodes = list(nodes.costs)
        self.goal = self.unvisitedNodes[0]
        self.debugMode = True
        self.ghosts = None
        self.path = None
        self.oldTarget = None

    def setGhosts(self, ghosts):
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

    def validDirections(self):
        directions = []
        for key in [UP, DOWN, LEFT, RIGHT]:
            if self.validDirection(key):
                directions.append(key)
        return directions

    def update(self, dt):	
        self.sprites.update(dt)
        self.position += self.directions[self.direction]*self.speed*dt
         
        if self.overshotTarget():
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

        if pacmanTarget != self.oldTarget:
            if self.oldTarget is not None and self.oldTarget in self.unvisitedNodes:
                self.unvisitedNodes.remove(self.oldTarget)
            self.oldTarget = pacmanTarget

        if self.goal == pacmanTarget and len(self.unvisitedNodes) > 1:
            self.unvisitedNodes.remove(self.goal)
            self.goal = self.unvisitedNodes[0]

        if (self.position.x, self.position.y) in self.unvisitedNodes:
            self.unvisitedNodes.remove((self.position.x, self.position.y))

        if pacmanTarget == self.goal:
            return [pacmanTarget]  # Pacman is already at the goal, return the current position

        previous_nodes, shortest_path = a_star(self.nodes, pacmanTarget, ghosts=self.ghosts)
        path = []
        node = self.goal
        while node != pacmanTarget:
            if node not in previous_nodes:  # Pacman cannot reach the goal
                for unvisited in self.unvisitedNodes:  # Try all other unvisited nodes
                    previous_nodes, shortest_path = a_star(self.nodes, unvisited, ghosts=self.ghosts)
                    if unvisited in previous_nodes:  # Found a reachable unvisited node
                        self.goal = unvisited
                        break
                else:  # No reachable unvisited nodes found
                    print("Failed")
                    return []
            path.append(node)
            node = previous_nodes[node]
        path.append(pacmanTarget)
        path.reverse()
        return path
    
    # Chooses direction in which to turn based on a star
    def goalDirectionAStar(self, directions):
            path = self.getAStarPath()
            self.path = path

            if len(path) < 2:
                print("Random")
                return choice(directions)  # No more path to follow, return a random direction

            nextNode = path[1]
            pacmanPosition = self.nodes.getVectorFromLUTNode(self.target)  # Get Pacman's current position
            pacmanX, pacmanY = pacmanPosition[0], pacmanPosition[1]
            nextNodeX, nextNodeY = nextNode[0], nextNode[1]

            dx = nextNodeX - pacmanX
            dy = nextNodeY - pacmanY

            if dx < 0 and LEFT in directions:  # move left
                return LEFT
            if dx > 0 and RIGHT in directions:  # move right
                return RIGHT
            if dy < 0 and UP in directions:  # move up
                return UP
            if dy > 0 and DOWN in directions:  # move down
                return DOWN
            
            print("directions: ", directions)

            return choice(directions)
    
    def distancesToGhosts(self, node):
        distances = []
        for ghost in self.ghosts:
            vec = node.position - ghost.target.position
            distances.append(vec.magnitudeSquared())
        return distances
    
    def goalDirectionFlee(self, directions):
        # Find the direction that moves Pacman farthest away from the nearest ghost
        max_distance = 0
        flee_direction = None
        for direction in directions:
            node = self.node.neighbors[direction]  # Get the neighbor node in the specified direction

            # Calculate the distance to the nearest ghost from the neighbor node
            nearest_ghost_distance = min(self.distancesToGhosts(node))

            # Check if moving in this direction increases the distance from the nearest ghost
            if nearest_ghost_distance > max_distance:
                max_distance = nearest_ghost_distance
                flee_direction = direction

        # Return the flee direction
        return flee_direction








