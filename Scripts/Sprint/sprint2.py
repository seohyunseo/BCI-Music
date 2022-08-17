'''
title: sound model test 3
data: meditation / electrode
controlled component: duration of the note / note
description: the duration of a note will be increased when meditation is high and decreased when vice versa. The range is from 16 to 2.
And the raw data will decide the note in certain scale which is made by harmony rule.
openvibe server settings: check 'Esence' in 'Driver properties' / downsampling 512 -> 128
resource: soundModel3.maxpat / soundModel3.xml
'''
import numpy as np
import argparse
import random
import time

from pythonosc import udp_client

global epoch
global meditation
global electrode
global duration
global noteNum

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # parser.add_argument("--ip", default="127.0.0.1",
    #                     help="The ip of the OSC server")
    parser.add_argument("--ip", default="172.17.217.255",
                        help="The ip of the OSC server")
    parser.add_argument("--port", type=int, default=7402,
                        help="The port the OSC server is listening on")
    args = parser.parse_args()

    client = udp_client.SimpleUDPClient(args.ip, args.port)


def list_chunk(lst, n):
    return [lst[i:i+n] for i in range(0, len(lst), n)]


class MyOVBox(OVBox):
    def __init__(self):
        OVBox.__init__(self)
        self.signalHeader = None

    def process(self):
        # initialize variables
        epoch = 8
        electrode = 0
        note = 0
        attention = 1
        meditation = 2

        for chunkIdx in range(len(self.input[0])):
            if (type(self.input[0][chunkIdx]) == OVSignalHeader):
                self.signalHeader = self.input[0].pop()

                outputHeader = OVSignalHeader(self.signalHeader.startTime, self.signalHeader.endTime, [1, self.signalHeader.dimensionSizes[1]], [
                                              'Mean']+self.signalHeader.dimensionSizes[1]*[''], self.signalHeader.samplingRate)

            elif(type(self.input[0][chunkIdx]) == OVSignalBuffer):
                chunk = self.input[0].pop()

                list_chunked = list_chunk(chunk, epoch)
                atten = np.mean(list_chunked[attention])
                client.send_message("Brightness", atten)
                # print("atten: ", atten)

                medi = np.mean(list_chunked[meditation])
                client.send_message("Dynamics", medi)
                # print("medi: ", medi)

            elif(type(self.input[0][chunkIdx]) == OVSignalEnd):
                print(self.input[0].pop())


box = MyOVBox()
