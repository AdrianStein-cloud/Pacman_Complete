import sys

from constants import FREIGHT
#########
# A*
def heuristic(node1, node2):
    # manhattan distance
    return abs(node1[0] - node2[0]) + abs(node1[1] - node2[1])

def a_star(nodes, start_node, ghosts=[]):

    unvisited_nodes = dict(nodes.costs)

    for ghost in ghosts:
        if ghost.mode.current != FREIGHT:
            try:
                del unvisited_nodes[(ghost.target.position.x, ghost.target.position.y)]
            except:
                pass

    unvisited_nodes = list(unvisited_nodes)

    shortest_path = {}
    previous_nodes = {}

    max_value = sys.maxsize
    for node in unvisited_nodes:
        shortest_path[node] = max_value
    shortest_path[start_node] = 0

    while unvisited_nodes:
        current_min_node = None
        for node in unvisited_nodes:
            if current_min_node == None:
                current_min_node = node
            elif shortest_path[node] < shortest_path[current_min_node]:
                current_min_node = node

        neighbors = nodes.getNeighbors(current_min_node)
        for neighbor in neighbors:
            if neighbor in unvisited_nodes:
                tentative_value = shortest_path[current_min_node] + heuristic(current_min_node, neighbor)
                if tentative_value < shortest_path[neighbor]:
                    shortest_path[neighbor] = tentative_value
                    # We also update the best path to the current node
                    previous_nodes[neighbor] = current_min_node
 
        # After visiting its neighbors, we mark the node as "visited"
        unvisited_nodes.remove(current_min_node)
    return previous_nodes, shortest_path