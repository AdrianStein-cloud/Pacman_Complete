from random import choice
import pygame
from pygame.locals import *
from vector import Vector2
from constants import *
from entity import Entity
from sprites import PacmanSprites
from algorithms import dijkstra, print_result, dijkstra_or_a_star

class Pacman(Entity):
    def __init__(self, node, nodes):
        Entity.__init__(self, node )
        self.name = PACMAN    
        self.color = YELLOW
        self.direction = LEFT
        self.setBetweenNodes(LEFT)
        self.alive = True
        self.sprites = PacmanSprites(self)
        self.directionMethod = self.goalDirectionDij
        self.nodes = nodes
        self.unvisitedNodes = list(nodes.costs)
        self.goal = self.unvisitedNodes[0]

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

    def update(self, dt):	
        self.sprites.update(dt)
        self.position += self.directions[self.direction]*self.speed*dt
        directions = self.validDirections()
        direction = self.directionMethod(directions)
        if self.overshotTarget():
            self.node = self.target
            if self.node.neighbors[PORTAL] is not None:
                self.node = self.node.neighbors[PORTAL]
            self.target = self.getNewTarget(direction)
            if self.target is not self.node:
                self.direction = direction
            else:
                self.target = self.getNewTarget(self.direction)

            if self.target is self.node:
                self.direction = STOP
            self.setPosition()
        else: 
            if self.oppositeDirection(direction):
                self.reverseDirection()

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
    def getDijkstraPath(self):
        pacmanTarget = self.target
        pacmanTarget = self.nodes.getVectorFromLUTNode(pacmanTarget)

        if self.goal == pacmanTarget and len(self.unvisitedNodes) > 1:
            self.unvisitedNodes.remove(self.goal)
            self.goal = self.unvisitedNodes[0]

        if pacmanTarget in self.unvisitedNodes:
            self.unvisitedNodes.remove(pacmanTarget)

        if pacmanTarget == self.goal:
            return [pacmanTarget]  # Pacman is already at the goal, return the current position

        previous_nodes, shortest_path = dijkstra_or_a_star(self.nodes, pacmanTarget, a_star=False)
        path = []
        node = self.goal
        while node != pacmanTarget:
            if node not in previous_nodes:  # Pacman cannot reach the goal, return empty path
                return []
            path.append(node)
            node = previous_nodes[node]
        path.append(pacmanTarget)
        path.reverse()
        return path



    # Chooses direction in which to turn based on the dijkstra
    # returned path
    def goalDirectionDij(self, directions):
        path = self.getDijkstraPath()  # Assuming self.getDijkstraPath() returns a list of nodes
        self.path = path

        print("path: ", path)

        if len(path) < 2:
            return choice(directions)  # No more path to follow, return a random direction

        nextNode = path[1]
        pacmanPosition = self.nodes.getVectorFromLUTNode(self.target)  # Get Pacman's current position
        pacmanX, pacmanY = pacmanPosition[0], pacmanPosition[1]
        nextNodeX, nextNodeY = nextNode[0], nextNode[1]

        dx = nextNodeX - pacmanX
        dy = nextNodeY - pacmanY

        if dx < 0 and 2 in directions:  # move left
            return 2
        if dx > 0 and -2 in directions:  # move right
            return -2
        if dy < 0 and 1 in directions:  # move up
            return 1
        if dy > 0 and -1 in directions:  # move down
            return -1

        return choice(directions)



