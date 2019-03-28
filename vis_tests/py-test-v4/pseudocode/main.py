

# main testbed Python loop




def main():

    grid = 1
    while True:
        grid += 1

        updateAgent1(grid)

        updateAgent2(grid)

        sleep(1)



# send the agent grid to the GUI
def updateAgent1(grid):
    agent_grid = grid * 2
    user_inputs = server.update_client(self.id, agent_grid)

    # http request ?
    # r = requests.post('localhost/update/' + str(self.id), data = {'key':'value'})

def updateAgent2(grid):
    agent_grid = grid * 3
    user_inputs = server.update_client(self.id, agent_grid)

if __name__== "__main__":
    main()
