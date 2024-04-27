from copy import deepcopy

class GameState:
    def __init__(self, pacman, powerpellets, score, fruit, ghosts = None, pinky = None, inky = None, clyde = None, blinky = None):
        

        if ghosts is None:
            #self.pellets = pellets
            self.powerpellets = powerpellets
            self.score = score
            self.fruit = fruit
            self.pacman = pacman
            self.pinky = pinky
            self.inky = inky
            self.clyde = clyde
            self.blinky = blinky
        else:
            #self.pellets = deepcopy(pellets)
            self.powerpellets = deepcopy(powerpellets)
            self.score = deepcopy(score)
            self.fruit = deepcopy(fruit)
            self.pacman = deepcopy(pacman.target)
            self.pinky = deepcopy(ghosts.pinky.target)
            self.inky = deepcopy(ghosts.inky.target)
            self.clyde = deepcopy(ghosts.clyde.target)
            self.blinky = deepcopy(ghosts.blinky.target)

    def __hash__(self):
        obj_hash = hash(self.pacman)

        obj_hash += hash(self.score)

        obj_hash += hash(self.pinky)
        obj_hash += hash(self.inky)
        obj_hash += hash(self.clyde)
        obj_hash += hash(self.blinky)

        if self.fruit is not None:
            obj_hash += hash(self.fruit.position)

        #for d in self.pellets:
        #    obj_hash += hash((d.position.x, d.position.y))
        
        for p in self.powerpellets:
            obj_hash += hash((p.position.x, p.position.y))

        return obj_hash
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.pacman == other.pacman and self.score == other.score and self.pinky == other.pinky and self.inky == other.inky and self.clyde == other.clyde and self.blinky == other.blinky and self.fruit == other.fruit and self.powerpellets == other.powerpellets
        return False