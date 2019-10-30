import requests
import datetime
import sys
import os
import numpy as np

def send_data(data, print_response=False):
    """ Sends some data to the Flask server """

    url = 'http://localhost:3000/get_states/1'
    tick_start_time = datetime.datetime.now()

    # send the data as json to the url with a max timeout of 5 seconds
    try:
        r = requests.post(url, json=data, timeout=5)
        # r = requests.get(url)
    except requests.exceptions.ConnectionError:
        raise requests.exceptions.ConnectionError("Connection error. Is the server still running?")

    tick_end_time = datetime.datetime.now()
    tick_duration = tick_end_time - tick_start_time

    if print_response:
        print(f"Connecting to {url} with data {data}. Received response: {r.content}")

    # check for errors in the response
    if r.status_code != requests.codes.ok:
        raise Exception("Error received from server", r.status_code)

    return tick_duration.total_seconds()


def spam_server(data, n):
    """ spam the server x times, and calc the averages etcetera"""

    t = []
    for i in range(n):
        t.append(send_data(data))

    # calc worst 1%, with a lower bound of 1
    worst_1perc_n = int(np.ceil(0.01*n))
    worst_1perc = np.sort(t)
    worst_1perc = worst_1perc[len(worst_1perc) - worst_1perc_n:]

    print(f"{len(data)} \t\t\t {n} \t\t\t {round(np.mean(t),4)}s \t\t\t {round(1.0/np.mean(t))} fps \t\t\t\t {round(np.std(t),4)}s \t\t\t\t\t\t {round(np.mean(worst_1perc), 4)}s \t\t\t\t {round(1.0/np.mean(worst_1perc))}fps")


def stress_test_server():
    print("#" * 150)
    print("Benchmarking Flask API connection (request + reply)")
    print("#" * 150)
    print(f"Dict size \t Connections \t Con time Mean (s) \t Con time Mean (fps) \t Standard Deviation (s) \t\t Mean worst 1\% (s) \t Mean worst 1\% (fps) ")


    string = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."


    for i in range(1, 500, 30):
        # fill in some data in a variable
        data = [string] * i * i

        # send API request
        spam_server(data, 500)

def main():
    time = send_data("hoi", print_response=True)
    print("Time elapsed:", time)


if __name__ == "__main__":
    main()
