import multiprocessing, Queue, time, signal, sys
from time import sleep

def writer1(queue):
    name = multiprocessing.current_process().name
    print (name, " Starting")
    i = 100
    while True:
        print (name, " sending ", i)
        queue.put(i)
        i += 1
        time.sleep(2)
    print (name, " Exiting")



def reader(queue1):
    name = multiprocessing.current_process().name
    time_out = 0.1
    print (name, " Starting")
    msg1 = None
    while True:

        print (name, " Checking")


        try:
            # get any items
            task = q.get(False)
        except Queue.Empty:
            # Handle empty queue here
            pass
        else:
            # Handle task here and call q.task_done()


        sleep(0.5)
    print (name, " Exiting")

if __name__ == "__main__":
    print ("Starting")
    try:

        q1 = multiprocessing.Queue()
        writer1 = multiprocessing.Process(name = "writer1-proc", target=writer1, args=(q1,))
        reader = multiprocessing.Process(name = "reader-proc", target=reader, args=(q1,))

        writer1.start()
        reader.start()

        t=1
        while t < 4:
            time.sleep(1)
            print ("sleeping")
            t += 1

        # wait untill done and then exit
        # writer1.join()
        # writer2.join()
        # reader.join()

        # Just exit
        writer1.terminate()
        reader.terminate()

        print ("----------")
        print ("Exiting")

        while True:
            print ("----------")
            print  ("Is wr1 alive?", writer1.is_alive())
            print ("Is r alive?", reader.is_alive())
            time.sleep(0.5)

    except KeyboardInterrupt:
        print ("Caught KeyboardInterrupt, terminating processes")
        writer1.terminate()
        reader.terminate()
