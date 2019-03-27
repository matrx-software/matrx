from time import sleep


# 
# scenario = {
#     'agents': {
#                 'agent1': {
#                     'type': 'random',
#                     'vis': 'yes'
#                 }
# }



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



def updateAgent2(grid):
    agent_grid = grid * 3



if __name__== "__main__":
    main()
