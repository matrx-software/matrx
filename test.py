import numpy as np
import collections

seen = None

def bfs(grid, start, goal):
    queue = collections.deque([[start]])
    global seen
    seen = set([start])

    width = grid.shape[0]
    height = grid.shape[1]

    while queue:
        path = queue.popleft()
        x, y = path[-1]
        if (x,y) == goal:
            return path
        for x2, y2 in ((x+1,y), (x-1,y), (x,y+1), (x,y-1)):
            if 0 <= x2 < width and 0 <= y2 < height and (x2, y2) not in seen:
                queue.append(path + [(x2, y2)])
                seen.add((x2, y2))
                print("Adding", [x2, y2])


# [x, y]
grid = np.zeros([10,9])
curr_loc = (4,4)
goal = (7,4)

bfs(grid, curr_loc, goal)

print(seen)
