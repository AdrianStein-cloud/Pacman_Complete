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
        self.nodes = nodes
        self.unvisitedNodes = self.getImportantNodes()
        self.goal = self.unvisitedNodes[44]
        self.debugMode = True
        self.ghosts = None
        self.path = None
        self.oldTarget = None

        # FSM   
        self.states = [FLEE, SEEK]
        self.myState = SEEK
        self.FSM = StateMachine(self.myState)

        self.FSM_decision()

        self.a_star_failed = False

    def getImportantNodes(self):
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
        self.advancedFSM()
        self.sprites.update(dt)
        self.position += self.directions[self.direction]*self.speed*dt

        self.path = self.getAStarPath()
         
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

        if len(self.unvisitedNodes) <= 0:
            self.unvisitedNodes = self.getImportantNodes()

        self.unvisitedNodes.sort(key=lambda node: heuristic(node, pacmanTarget))
        self.goal = self.unvisitedNodes[0]
            

        if pacmanTarget != self.oldTarget:
            if self.oldTarget is not None and self.oldTarget in self.unvisitedNodes:
                self.unvisitedNodes.remove(self.oldTarget)
            self.oldTarget = pacmanTarget

        if self.goal == pacmanTarget and len(self.unvisitedNodes) > 1:
            self.unvisitedNodes.remove(self.goal)
            

        if (self.position.x, self.position.y) in self.unvisitedNodes:
            self.unvisitedNodes.remove((self.position.x, self.position.y))

        if pacmanTarget == self.goal:
            return [pacmanTarget]  # Pacman is already at the goal, return the current position

        previous_nodes, shortest_path = a_star(self.nodes, pacmanTarget, ghosts=self.ghosts)
        path = []
        node = self.goal
        while node != pacmanTarget:
            if node not in previous_nodes:  # Pacman cannot reach the goal
                # Sort unvisited nodes by distance from Pacman's current position
                self.unvisitedNodes.sort(key=lambda node: heuristic(node, pacmanTarget))
                for unvisited in self.unvisitedNodes:  # Try all other unvisited nodes
                    previous_nodes, shortest_path = a_star(self.nodes, unvisited, ghosts=self.ghosts)
                    if unvisited in previous_nodes:  # Found a reachable unvisited node
                        self.goal = unvisited
                        break
                else:  # No reachable unvisited nodes found
                    self.a_star_failed = True
                    return []
            path.append(node)
            node = previous_nodes[node]
        path.append(pacmanTarget)
        path.reverse()
        self.a_star_failed = False
        return path
    
    # Chooses direction in which to turn based on a star
    def goalDirectionAStar(self, directions):
            
            path = self.path

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
            if ghost.mode.current == FREIGHT or ghost.mode.current == SPAWN :
                continue
            vec = node.position - ghost.target.position
            distances.append(vec.magnitudeSquared())
        return distances
    
    def closestGhost(self):
        distances = self.distancesToGhosts(self.node)
        if len(distances) == 0:
            return None
        index = distances.index(min(distances))
        return list(self.ghosts)[index]
    
    def goalDirectionFlee(self, directions):
        distances = []
        for direction in directions:
            try:
                vec = self.node.position + self.directions[direction]*TILEWIDTH - self.closestGhost().position
            except:
                return choice(directions)
            distances.append(vec.magnitudeSquared())
        index = distances.index(max(distances))
        return directions[index]

    

    def FSM_decision(self):
        if self.myState == FLEE:
            self.directionMethod = self.goalDirectionFlee
        elif self.myState == SEEK:
            self.directionMethod = self.goalDirectionAStar
        else:
            self.myState = choice(self.states)

    def advancedFSM(self):
        distances_to_ghosts = self.distancesToGhosts(self.node)
        if len(distances_to_ghosts) != 0:
            distance_to_ghost = min(distances_to_ghosts)
        else:
            distance_to_ghost = 1000000000
        new_state = self.FSM.updateState(distance_to_ghost, self.a_star_failed)

        # print(new_state)
        if new_state == SEEK: 
            self.directionMethod = self.goalDirectionAStar
        elif new_state == FLEE:
            self.directionMethod = self.goalDirectionFlee

        self.old_state = new_state








