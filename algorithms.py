import sys

def heuristic(node1, node2):
    # manhattan distance
    return abs(node1[0] - node2[0]) + abs(node1[1] - node2[1])

def dijkstra(nodes, start_node, depth):
    unvisited_nodes = list(nodes.costs)
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

        if shortest_path[current_min_node] > depth:
            break

        neighbors = nodes.getNeighbors(current_min_node)
        for neighbor in neighbors:
            if neighbor not in unvisited_nodes:
                continue
            tentative_value = shortest_path[current_min_node] + heuristic(current_min_node, neighbor)
            if tentative_value < shortest_path[neighbor]:
                shortest_path[neighbor] = tentative_value
                previous_nodes[neighbor] = current_min_node

        unvisited_nodes.remove(current_min_node)
    
    return previous_nodes, shortest_path