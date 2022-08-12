'''
Test to send note and duration for controling the metro in Max/MSP
This code use OSC Client and Server at the same code
This code use Multithreading between Server and Client
'''
import sys
import turtle
import argparse
import math
import random
import time

from pythonosc import dispatcher
from pythonosc import osc_server

from pythonosc import udp_client
from multiprocessing import Process, Value

SYSTEM_RULES = {}  # generator system rules for l-system

notes = [36, 38, 40, 43, 45, 48, 50, 52, 55, 57, 60, 62, 64, 67, 69, 72, 74, 76,
         79, 81, 84, 86, 88, 91, 93, 96, 98, 100, 103, 105, 108, 110, 112, 115, 117]
durations = [2, 4, 8, 16]

velocities = [127, 97, 67]


def bang_handler(unused_addr, args, volume):
    args[0].value = 1


def server_func(toggle):
    # OSC Server Setting
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
                        default="127.0.0.1", help="The ip to listen on")
    parser.add_argument("--port",
                        type=int, default=5005, help="The port to listen on")
    args = parser.parse_args()

    # Server dispatcher
    global dispatcher
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/filter", bang_handler, toggle)

    server = osc_server.ThreadingOSCUDPServer(
        (args.ip, args.port), dispatcher)
    print("Serving on {}".format(server.server_address))

    server.serve_forever()


def derivation(axiom, steps):
    derived = [axiom]  # seed
    for _ in range(steps):
        next_seq = derived[-1]
        next_axiom = [rule(char) for char in next_seq]
        derived.append(''.join(next_axiom))
    return derived


def rule(sequence):
    if sequence in SYSTEM_RULES:
        return SYSTEM_RULES[sequence]
    return sequence


def draw_l_system(turtle, model, seg_length, angle, toggle, client):
    stack = []
    message = []
    currentDuration = 2
    currentPitch = 5
    velocity = 127
    play = [1, 0]
    i = 0

    for idx in range(0, 3):

        client.send_message("play", play)
        print("Play loop:", idx)

        SYSTEM_RULES = model[idx][-1]
        currentPitch += idx*10
        currentDuration += idx

        for command in SYSTEM_RULES:
            turtle.pd()

            if command in ["F", "G", "R", "L"]:
                while toggle.value == 0:
                    continue
                toggle.value = 0

                if i+1 == len(SYSTEM_RULES):
                    print("out of range")
                    client.send_message("bang", 'bang')
                    client.send_message("bang2", 'bang')
                    time.sleep(1)
                    play[1] = 1
                    break

                elif SYSTEM_RULES[i+1] is not 'F':
                    velocity = 127
                    # print("note on(", duration, ", ", velocity, ")")

                elif SYSTEM_RULES[i+1] is 'F':
                    velocity = 0
                    # print("note off(", duration, ", ", velocity, ")")

                message = [notes[currentPitch],
                           durations[currentDuration], velocity]
                client.send_message("message", message)
                # print("command[", i, "]: "+SYSTEM_RULES[i] +
                #       ", command[", i+1, "]: " + SYSTEM_RULES[i+1])

                turtle.forward(seg_length)

            elif command == "f":
                turtle.pu()  # pen up - not drawing
                turtle.forward(seg_length)
            elif command == "+":
                turtle.right(angle)
                # max
                currentPitch += 1
                # max
            elif command == "-":
                turtle.left(angle)
                # max
                currentPitch -= 1
                # max
            elif command == "[":
                stack.append((turtle.position(), turtle.heading()))
            elif command == "]":
                turtle.pu()  # pen up - not drawing
                position, heading = stack.pop()
                turtle.goto(position)
                turtle.setheading(heading)

            print("command: ", i+1, "/", len(SYSTEM_RULES))
            i += 1
        i = 0
    return


def set_turtle(alpha_zero):
    r_turtle = turtle.Turtle()  # recursive turtle
    r_turtle.screen.title("L-System Derivation")
    r_turtle.speed(0)  # adjust as needed (0 = fastest)
    r_turtle.setheading(alpha_zero)  # initial heading
    return r_turtle


def drawing_macro(toggle, client):
    rule = "F->F-F+F+FF-F-F+F"
    key, value = rule.split("->")
    SYSTEM_RULES[key] = value

    axiom = "F-F-F-F"
    model = []
    for i in range(0, 3):
        # iterations = 1
        model.append(derivation(axiom, i+1))
    # print(model)

    segment_length = 5
    alpha_zero = 90.0
    angle = 90.0

    # Set turtle parameters and draw L-System
    r_turtle = set_turtle(alpha_zero)  # create turtle object
    turtle_screen = turtle.Screen()  # create graphics window
    turtle_screen.screensize(1500, 1500)
    draw_l_system(r_turtle, model,
                  segment_length, angle, toggle, client)  # draw model
    client.send_message("bang", 'bang')
    turtle_screen.exitonclick()


def main(toggle):
    # OSC Client Setting
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1",
                        help="The ip of the OSC server")
    parser.add_argument("--port", type=int, default=7402,
                        help="The port the OSC server is listening on")
    args = parser.parse_args()

    client = udp_client.SimpleUDPClient(args.ip, args.port)

    drawing_macro(toggle, client)


if __name__ == "__main__":
    try:
        toggle = Value('i', 0)
        p = Process(target=server_func, args=(toggle,))
        c = Process(target=main, args=(toggle,))
        p.start()
        c.start()
        c.join()
        c.kill()
        p.kill()
        sys.exit(0)
    except BaseException:
        sys.exit(0)