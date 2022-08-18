'''
Test to send note and duration for controling the metro in Max/MSP
This code use OSC Client and Server at the same code
This code use Multithreading between Server and Client
This code use EEG information for controling the music parameters
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

Cminor_pentatonic = [36, 38, 40, 43, 45, 48, 50, 52, 55, 57, 60, 62, 64, 67, 69, 72, 74, 76,
                     79, 81, 84, 86, 88, 91, 93, 96, 98, 100, 103, 105, 108, 110, 112, 115, 117]

Cminor_pentatonic = [36, 39, 41, 43, 46, 48, 51, 53, 55, 58, 60, 63, 65, 67, 70, 72, 75,
                     77, 79, 82, 84, 87, 89, 91, 94, 96, 99, 101, 103, 106, 108, 111, 113, 115, 118]

durations = [2, 4, 8, 16, 32]

velocities = [0, 127, 107, 87]

colors = ['red', 'blue', 'green']

total_iteration = 3


def initiate_max(client):
    client.send_message('initiation', 'bang')


def bang_handler(unused_addr, args, volume):
    args[0].value = 1


# def eeg_handler(unused_addr, args, alpha):
#     args[0].value = alpha
#     print("Alpha Ratio: ", args[0].value)


def server_func(toggle, eeg):
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
    # dispatcher.map("/eeg", eeg_handler, eeg)

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
    pitch_stack = []
    midiout = []
    play = [1, 0, 0, 0]
    currentDuration = 1
    currentPitch = 5
    currentVelocity = 1
    currentPlay = 0
    initialPitch = 0

    for idx in range(0, total_iteration):
        i = 0
        client.send_message("record"+str(idx+1), 1)
        client.send_message("channel", idx)
        client.send_message("play", play)
        initialPitch = currentPitch
        print("Play loop:", idx)

        SYSTEM_RULES = model[idx][-1]
        turtle.color(colors[idx])

        for command in SYSTEM_RULES:
            turtle.pd()

            if command in ["F", "G", "R", "L"]:
                while toggle.value == 0:
                    # print("UDP doesn't work")
                    continue
                toggle.value = 0

                if i+1 == len(SYSTEM_RULES):
                    break

                elif SYSTEM_RULES[i+1] is not 'F':
                    currentVelocity = idx+1
                    # print("note on(", duration, ", ", velocity, ")")

                elif SYSTEM_RULES[i+1] is 'F':
                    currentVelocity = 0
                    # print("note off(", duration, ", ", velocity, ")")

                midiout = [Cminor_pentatonic[currentPitch],
                           durations[currentDuration], velocities[currentVelocity]]
                client.send_message("midiout", midiout)

                # print("command[", i, "]: "+SYSTEM_RULES[i] +
                #       ", command[", i+1, "]: " + SYSTEM_RULES[i+1])

                turtle.forward(seg_length)

            elif command == "f":
                turtle.pu()  # pen up - not drawing
                turtle.forward(seg_length)
            elif command == "+":
                turtle.right(angle)

                currentPitch += 1
                if currentPitch+1 > len(Cminor_pentatonic):
                    currentPitch = initialPitch

            elif command == "-":
                turtle.left(angle)

                currentPitch -= 1
                if currentPitch < 0:
                    currentPitch = initialPitch

            elif command == "[":
                stack.append((turtle.position(), turtle.heading()))
                pitch_stack.append(currentPitch)
            elif command == "]":
                turtle.pu()  # pen up - not drawing
                position, heading = stack.pop()
                currentPitch = pitch_stack.pop()
                turtle.goto(position)
                turtle.setheading(heading)

            # print("command: ", i+1, "/", len(SYSTEM_RULES))
            i += 1

        currentPitch += 10
        currentDuration += 1
        currentVelocity += 1
        currentPlay += 1
        play[currentPlay] = 1

        client.send_message("mainplay", 'bang')
        client.send_message("loopset", 'bang')
        time.sleep(1)
        client.send_message("record"+str(idx+1), 0)

    client.send_message("play", play)
    return


def set_turtle(alpha_zero):
    r_turtle = turtle.Turtle()  # recursive turtle
    r_turtle.screen.title("L-System Music Playing")
    r_turtle.speed(0)  # adjust as needed (0 = fastest)
    r_turtle.setheading(alpha_zero)  # initial heading
    return r_turtle


def drawing_macro(toggle, client):
    # rule = "F->F-F+F+FF-F-F+F"
    # key, value = rule.split("->")
    # SYSTEM_RULES[key] = value

    # axiom = "F-F-F-F"
    # segment_length = 5
    # alpha_zero = 0.0
    # angle = 90.0

    #------------------------------#

    # rule = "L->L+R++R-L--LL-R+"
    # key, value = rule.split("->")
    # SYSTEM_RULES[key] = value
    # rule = "R->-L+RR++R+L--L-R"
    # key, value = rule.split("->")
    # SYSTEM_RULES[key] = value

    # axiom = "L"
    # segment_length = 5
    # alpha_zero = 60.0
    # angle = 60.0

    #------------------------------#

    rule = "X->F-[[X]+X]+F[+FX]-X"
    key, value = rule.split("->")
    SYSTEM_RULES[key] = value
    rule = "F->FF"
    key, value = rule.split("->")
    SYSTEM_RULES[key] = value

    axiom = "X"
    segment_length = 5
    alpha_zero = 90.0
    angle = 22.5

    #------------------------------#

    # rule = "X->F[+X][-X]FX"
    # key, value = rule.split("->")
    # SYSTEM_RULES[key] = value
    # rule = "F->FF"
    # key, value = rule.split("->")
    # SYSTEM_RULES[key] = value

    # axiom = "X"
    # segment_length = 5
    # alpha_zero = 90.0
    # angle = 45.0

    #------------------------------#

    # rule = "F->F+F-F-F+F"
    # key, value = rule.split("->")
    # SYSTEM_RULES[key] = value

    # axiom = "-F"
    # segment_length = 5
    # alpha_zero = 90.0
    # angle = 90.0

    #------------------------------#

    model = []
    for i in range(0, total_iteration):
        model.append(derivation(axiom, i+1))

    # Set turtle parameters and draw L-System
    r_turtle = set_turtle(alpha_zero)  # create turtle object
    turtle_screen = turtle.Screen()  # create graphics window
    turtle_screen.screensize(1500, 1500)
    turtle_screen.bgcolor('black')
    draw_l_system(r_turtle, model,
                  segment_length, angle, toggle, client)  # draw model
    client.send_message("mainplay", 'bang')
    turtle_screen.exitonclick()
    return


def main(toggle):
    # OSC Client Setting
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1",
                        help="The ip of the OSC server")
    parser.add_argument("--port", type=int, default=7402,
                        help="The port the OSC server is listening on")
    args = parser.parse_args()

    client = udp_client.SimpleUDPClient(args.ip, args.port)

    initiate_max(client)
    drawing_macro(toggle, client)
    return


if __name__ == "__main__":
    try:
        toggle = Value('i', 0)
        eeg = Value('d', 0.0)
        p = Process(target=server_func, args=(toggle, eeg,))
        c = Process(target=main, args=(toggle,))
        p.start()
        c.start()
        c.join()
        c.kill()
        p.kill()
        sys.exit(0)
    except BaseException:
        sys.exit(0)
