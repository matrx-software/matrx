import requests
from time import sleep
import datetime
import numpy as np
import random
import json

# main testbed Python loop
def main():

    grid2 = np.array([[round(random.random() * 100) for x in range(100)] for y in range(100)])

    print(grid2)

    grid = 1
    while True:
        grid += 1

        updateAgent1(grid2)

        # updateAgent2(grid)

        sleep(1)



# send the agent grid to the GUI
def updateAgent1(grid):
    id = 0
    agent_grid = grid * 2
    # user_inputs = server.update_client(self.id, agent_grid)

    # GET request
    # print("Sending get request")
    # r = requests.get('http://localhost:3000/example/' + str(id), params = {'gw':agent_grid})
    # if r.status_code == requests.codes.ok:
    #     print("Received :", r.text)
    # else:
    #     print("Error in contacting GUI API")

    # POST request
    # print("Sending get request")
    # r = requests.post('http://localhost:3000/example/' + str(id), params = {'gw':agent_grid})
    # print("post url:", r.url)
    # if r.status_code == requests.codes.ok:
    #     print("Received :", r.text)
    # else:
    #     print("Error in contacting GUI API")

    # grid = np.array([1,2,3])


    # POST request with grid
    data = {'params': {'arg1': 2}, 'arr': grid.tolist()}

    print("Sending get request")
    tick_start_time = datetime.datetime.now()
    r = requests.post('http://localhost:3000/update/agent/' + str(id), json=data)
    tick_end_time = datetime.datetime.now()
    print("post url:", r.url)

    if r.status_code == requests.codes.ok:
        print("Received : %s" % r.text)
    else:
        print("Error in contacting GUI API")

    print("JSON response:")
    print(r.json())



    tick_duration = tick_end_time - tick_start_time
    print("Request + reply took:", tick_duration.total_seconds())


# def updateAgent2(grid):
#     agent_grid = grid * 3
#     user_inputs = server.update_client(self.id, agent_grid)


if __name__== "__main__":
    main()
