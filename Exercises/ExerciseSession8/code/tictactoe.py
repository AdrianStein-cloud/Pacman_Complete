import numpy as np
import pickle
import random

# Size of our board.
BOARD_ROWS = 3
BOARD_COLS = 3

# Data structure for holding information about the current state
# of the game, as well as for progressing the learning.
class State:
    def __init__(self, p1, p2):
        # Generate a tictactoe board full of 0s.
        self.board = np.zeros((BOARD_ROWS, BOARD_COLS))
        # Initialise the two players that will play against each other.
        self.p1 = p1
        self.p2 = p2
        # Variable for whether game is finished and needs restarting or not.
        self.isEnd = False
        # A "compacted" way to represent our board. 
        self.boardHash = None
        # Initialise p1 to have the first move. 
        # P1 will have symbol 1, P2 will have -1.
        self.playerSymbol = 1

    # Get unique hash of current board state.
    # A hash is simply the current board, represented as a single row.
    def getHash(self):
        self.boardHash = str(self.board.reshape(BOARD_COLS * BOARD_ROWS))
        return self.boardHash

    # Function for checking whether there is a winner in the current state of the board.
    # This will be checked at the beginning of every turn.
    # To check for a winner, check if the numbers sum up to 3 or -3 in any of the directions.
    def winner(self):
        # row
        for i in range(BOARD_ROWS):
            if sum(self.board[i, :]) == 3:
                self.isEnd = True
                return 1
            if sum(self.board[i, :]) == -3:
                self.isEnd = True
                return -1
        # col
        for i in range(BOARD_COLS):
            if sum(self.board[:, i]) == 3:
                self.isEnd = True
                return 1
            if sum(self.board[:, i]) == -3:
                self.isEnd = True
                return -1
        # diagonal
        diag_sum1 = sum([self.board[i, i] for i in range(BOARD_COLS)])
        diag_sum2 = sum([self.board[i, BOARD_COLS - i - 1] for i in range(BOARD_COLS)])
        diag_sum = max(abs(diag_sum1), abs(diag_sum2))
        if diag_sum == 3:
            self.isEnd = True
            if diag_sum1 == 3 or diag_sum2 == 3:
                return 1
            else:
                return -1

        # tie
        # No more available positions --> game ends.
        if len(self.availablePositions()) == 0:
            self.isEnd = True
            return 0
        # Not end
        self.isEnd = False
        return None

    # Compute the available positions by checking which positions have 0s.
    def availablePositions(self):
        positions = []
        for i in range(BOARD_ROWS):
            for j in range(BOARD_COLS):
                if self.board[i, j] == 0:
                    positions.append((i, j))  # need to be tuple
        return positions

    # Given the current board, and the position where the player
    # wants to put his symbol, updates the board to the new state.
    def updateState(self, position):
        self.board[position] = self.playerSymbol
        # switch to another player
        self.playerSymbol = -1 if self.playerSymbol == 1 else 1

    # Give rewards to the players depending on who won.
    # Called only when game ends.
    def giveReward(self):
        result = self.winner()
        # backpropagate reward
        if result == 1:
            self.p1.feedReward(1)
            self.p2.feedReward(0)
        elif result == -1:
            self.p1.feedReward(0)
            self.p2.feedReward(1)
        # Since P1 started (thus had an advantage) but the game
        # still ended in tie, P2 should have more points.
        else:
            self.p1.feedReward(0.1)
            self.p2.feedReward(0.5)

    # Reset the board to 0s.
    def reset(self):
        self.board = np.zeros((BOARD_ROWS, BOARD_COLS))
        self.boardHash = None
        self.isEnd = False
        self.playerSymbol = 1

    # Generate a totally random board.
    def generateRandBoard(self):
        board = np.zeros((BOARD_ROWS, BOARD_COLS))
        for row in range(1,BOARD_ROWS):
            for col in range(BOARD_COLS):
                if random.uniform(0,1) > 0.5:
                    if random.uniform(0,1) > 0.5:
                        board[row,col] = 1
                    else:
                        board[row,col] = -1
        return board

    # Function that is called to actually play the games and learn.
    def play(self, iterations=100):
        for i in range(iterations):
            if i % 1000 == 0:
                print("Iterations {}".format(i))
            while not self.isEnd:
                # We interrupt the current sequence and generate a totally
                # random board, with a probability of rand_nu.
                # This is one of the learning parameter of Q-learning (see book)
                rand_nu = random.uniform(0,1)
                if rand_nu < self.p1.walk_len_nu: 
                    self.board = self.generateRandBoard()
                
                # Player 1's turn
                positions = self.availablePositions()
                # EXPLOIT VS EXPLORE:
                # Explore: select a random action with a probability of rand_rho...
                rand_rho = random.uniform(0,1)
                if rand_rho < self.p1.exploration_rho:
                    # take random action
                    idx = np.random.choice(len(positions))
                    p1_action = positions[idx]
                # Exploit: else, take the best action for the current state-action pair.
                else:
                    p1_action = self.p1.chooseAction(positions, self.board, self.playerSymbol)
                # Apply the action and update board state.
                self.updateState(p1_action)
                board_hash = self.getHash()
                self.p1.addState(board_hash)
                # Check board status if it is end
                win = self.winner()
                # IF YES: end the game
                if win is not None:
                    # self.showBoard()
                    # ended with p1 either win or draw
                    self.giveReward()
                    self.p1.reset()
                    self.p2.reset()
                    self.reset()
                    break
                # IF NO: player 2's turn
                else:
                    # Player 2
                    positions = self.availablePositions()
                    p2_action = self.p2.chooseAction(positions, self.board, self.playerSymbol)
                    self.updateState(p2_action)
                    board_hash = self.getHash()
                    self.p2.addState(board_hash)

                    win = self.winner()
                    if win is not None:
                        # self.showBoard()
                        # ended with p2 either win or draw
                        self.giveReward()
                        self.p1.reset()
                        self.p2.reset()
                        self.reset()
                        break


    # Function to be called for demo, when play with human.
    # Same as "play()" but without the Player 2's turn.
    # Instead, takes input from the terminal.
    def play2(self):
        while not self.isEnd:
            # Player 1
            positions = self.availablePositions()
            p1_action = self.p1.chooseAction(positions, self.board, self.playerSymbol)
            # take action and update board state
            self.updateState(p1_action)
            self.showBoard()
            # check board status if it is end
            win = self.winner()
            if win is not None:
                if win == 1:
                    print(self.p1.name, "wins!")
                else:
                    print("tie!")
                self.reset()
                break

            else:
                # Player 2
                positions = self.availablePositions()
                p2_action = self.p2.chooseAction(positions)

                self.updateState(p2_action)
                self.showBoard()
                win = self.winner()
                if win is not None:
                    if win == -1:
                        print(self.p2.name, "wins!")
                    else:
                        print("tie!")
                    self.reset()
                    break

    # Show the current state of the board in an easy-to-read format.
    def showBoard(self):
        # p1: x  p2: o
        for i in range(0, BOARD_ROWS):
            print('-------------')
            out = '| '
            for j in range(0, BOARD_COLS):
                if self.board[i, j] == 1:
                    token = 'x'
                if self.board[i, j] == -1:
                    token = 'o'
                if self.board[i, j] == 0:
                    token = ' '
                out += token + ' | '
            print(out)
        print('-------------')


# Data structure for defining the functions and actions 
# that each player (aka the controller) should take.
class Player:
    def __init__(self, name, exploration_rho=0.3, lr_alpha=0.2, discount_rate_gamma=0.9, walk_len_nu=0.2):
        self.name = name
        self.states = []  # record all positions taken
        self.states_value = {}  # state -> value
        # Q-Learning parameters
        self.exploration_rho = exploration_rho
        self.lr_alpha = lr_alpha
        self.discount_rate_gamma = discount_rate_gamma
        self.walk_len_nu = walk_len_nu

    # Same as before. It is needed in the next function.
    def getHash(self, board):
        boardHash = str(board.reshape(BOARD_COLS * BOARD_ROWS))
        return boardHash

    # Chooses an action to be taken based on the learnt information.
    def chooseAction(self, positions, current_board, symbol):
        value_max = -999
        duplicates = []
        # Find the position that will give the best value by
        # iteratively checking each available position's value
        # if the player was to take that position.
        for position in positions:
            next_board = current_board.copy()
            next_board[position] = symbol
            next_boardHash = self.getHash(next_board)
            if self.states_value.get(next_boardHash) is None:
                value = 0 
            else: 
                value = self.states_value.get(next_boardHash)
            # print("value", value)
            if value > value_max:
                value_max = value
                action = position
                duplicates = []
                duplicates.append(action) 
            if value == value_max:
                duplicates.append(position)
        # if there are multiple max values, pick one randomly
        if len(duplicates)> 1:
            return random.choice(duplicates)
        # else, just pick the highest action
        else:
            return action

    # Append a hash state to the list of all states
    def addState(self, state):
        self.states.append(state)

    # At the end of game, backpropagate and update states value
    def feedReward(self, reward):
        # Reverse the list of s tates, so that we start from the last state
        # and propagate back to the first state.
        for st in reversed(self.states):
            if self.states_value.get(st) is None:
                self.states_value[st] = 0
            Q = self.states_value[st]
            maxQ = self.states_value[st]
            self.states_value[st] = Q * (1 - self.lr_alpha) + self.lr_alpha * (self.discount_rate_gamma * reward + maxQ)
            reward = self.states_value[st]

    # Resets the list of states taken.
    def reset(self):
        self.states = []

    # Saves Q-table, for later reuse.
    def savePolicy(self):
        fw = open('policy_' + str(self.name), 'wb')
        pickle.dump(self.states_value, fw)
        fw.close()

    # Load a trained Q-table, for demo purposes or for 
    # resuming training.
    def loadPolicy(self, file):
        fr = open(file, 'rb')
        self.states_value = pickle.load(fr)
        fr.close()

# Structure for when playing against human.
class HumanPlayer:
    def __init__(self, name):
        self.name = name

    def chooseAction(self, positions):
        while True:
            row = int(input("Input your action row:"))
            col = int(input("Input your action col:"))
            action = (row, col)
            if action in positions:
                return action

    # append a hash state
    def addState(self, state):
        pass

    # at the end of game, backpropagate and update states value
    def feedReward(self, reward):
        pass

    def reset(self):
        pass


if __name__ == "__main__":
    #### PARAMETERS:
    # ALPHA -> Learning Rate
    # controls how much influence the current feedback value has over the stored Q-value.

    # GAMMA -> Discount Rate
    # how much an action’s Q-value depends on the Q-value at the state (or states) it leads to.

    # RHO -> Randomness of Exploration
    # how often the algorithm will take a random action, rather than the best action it knows so far.

    # NU: The Length of Walk
    # number of iterations that will be carried out in a sequence of connected actions.
    
    # INITIALISE PARAMETERS
    exploration_rho=0.3
    lr_alpha=0.2
    discount_rate_gamma=0.9
    walk_len_nu = 0.2
    
    # training
    p1 = Player("p1", exploration_rho, lr_alpha, discount_rate_gamma, walk_len_nu)
    p2 = Player("p2", exploration_rho, lr_alpha, discount_rate_gamma, walk_len_nu)

    st = State(p1, p2)
    print("training...")
    st.play(100000)

    #play with human
    p1 = Player("computer", exploration_rho=0)
    p1.loadPolicy("D:\Data\Data - Dokumenter\GitProjects\Pacman_Complete\Exercises\ExerciseSession8\code/policy_computer")
    # p1.savePolicy()
#
    p3 = Player("computer", exploration_rho=0.2)
    p3.loadPolicy("D:\Data\Data - Dokumenter\GitProjects\Pacman_Complete\Exercises\ExerciseSession8\code/policy_computer")


    p2 = HumanPlayer("human")

    st = State(p1, p2)
    st.play2()