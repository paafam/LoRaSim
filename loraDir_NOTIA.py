#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
 LoRaSim 0.2.1: simulate collisions in LoRa
 Copyright © 2016 Thiemo Voigt <thiemo@sics.se> and Martin Bor <m.bor@lancaster.ac.uk>

 This work is licensed under the Creative Commons Attribution 4.0
 International License. To view a copy of this license,
 visit http://creativecommons.org/licenses/by/4.0/.


 Do LoRa Low-Power Wide-Area Networks Scale? Martin Bor, Utz Roedig, Thiemo Voigt
 and Juan Alonso, MSWiM '16, http://dx.doi.org/10.1145/2988287.2989163

 $Date: 2017-05-12 19:16:16 +0100 (Fri, 12 May 2017) $
 $Revision: 334 $


"""

"""
 SYNOPSIS:
   ./loraDir.py <nodes> <avgsend> <experiment> <simtime> [collision]
 DESCRIPTION:
 
    nodes
        number of nodes to simulate
    avgsend
        average sending interval in milliseconds
    experiment
        experiment is an integer that determines with what radio settings the
        simulation is run. All nodes are configured with a fixed transmit power
        and a single transmit frequency, unless stated otherwise.
        0   use the settings with the the slowest datarate (SF12, BW125, CR4/8).
        1   similair to experiment 0, but use a random choice of 3 transmit
            frequencies.
        2   use the settings with the fastest data rate (SF6, BW500, CR4/5).
        3   optimise the setting per node based on the distance to the gateway.
        4   use the settings as defined in LoRaWAN (SF12, BW125, CR4/5).
        5   similair to experiment 3, but also optimises the transmit power.
    simtime
        total running time in milliseconds
    sim_scenario
        sim_scenario determines the scenario used for simulation purposes. 
        Default value is 0
        0   all frames are unconfirmed frame
        1   all frames are confirmed frame, a 13 bytes ACK frame is sent on the first RX1 window
        2   all frames are confirmed frame, a 13 bytes ACK frame is sent on the second RX2 window
    collision
        set to 1 to enable the full collision check, 0 to use a simplified check.
        With the simplified check, two messages collide when they arrive at the
        same time, on the same frequency and spreading factor. The full collision
        check considers the 'capture effect', whereby a collision of one or the
 OUTPUT
    The result of every simulation run will be appended to a file named expX.dat,
    whereby X is the experiment number. The file contains a space separated table
    of values for nodes, collisions, transmissions and total energy spent. The
    data file can be easily plotted using e.g. gnuplot.
    
 EXAMPLE
    > python loraDir.py 100 1000000 1 0 5011200000

"""

import math
import os
import random
import sys

import matplotlib.pyplot as plt
import numpy as np
import simpy
from datetime import datetime

# Verbose:
# 0 : SILENT mode
# 1 : INFO mode  : only information type of messages are printed
# 2 : ERROR mode : only error messages are printed
# 3 : DEBUG mode : all messages are printed
# Default mode is SILENT mode
verbose = 0
Tpream = 0

# Get runtime
now = datetime.now()

# detect the current working directory
path = os.getcwd()
if verbose >=1:
    print ("[INFO] - current working directory is %s " % path)


data_path   = path + "/data"
# Create results directory
results_path = path + "/results"
try:
    os.mkdir(results_path)
except OSError:
    if verbose >=2:
        print ("[ERROR] - Creation of the directory %s failed" % results_path)
    if os.path.isdir(results_path):
        if verbose >= 2:
            print('[ERROR] - Directory already exist')
else:
    if verbose >= 1:
        print ("[INFO] - Successfully created the directory %s " % results_path)

# Create sim directory in results directory
dt_string = now.strftime("%Y%m%d-%H%M%S")
sim_results_path = results_path + "/sim_"+dt_string


# Simulation scenario
# 0 : all frame are unconfirmed frame
# 1 : all frame are confirmed frame, a 13 bytes ACK frame is sent on the first RX1 window
# 2 : all frame are confirmed frame, a 13 bytes ACK frame is sent on the second RX2 window
sim_scenario = 0   # This is the default value

# MAC protocol selection
# 0 : Pure Aloha
# 1 : Slotted Aloha
# 2 : ToDo
mac_protocol = 0

# Load nodes location from file
loadNodesLocation = 0

# turn on/off graphics
graphics = 0

# do the full collision check
full_collision = False

# experiments:
# 0: packet with longest airtime, aloha-style experiment
# 1: one with 3 frequencies, 1 with 1 frequency
# 2: with shortest packets, still aloha-style
# 3: with shortest possible packets depending on distance

# Store frequency channels usage for freq: 860000000, 864000000, 868000000
global_freq_usage = [0, 0, 0]

# this is an array with measured values for sensitivity
# see paper, Table 3
sf7 = np.array([7, -126.5, -124.25, -120.75])
sf8 = np.array([8, -127.25, -126.75, -124.0])
sf9 = np.array([9, -131.25, -128.25, -127.5])
sf10 = np.array([10, -132.75, -130.25, -128.75])
sf11 = np.array([11, -134.5, -132.75, -128.75])
sf12 = np.array([12, -133.25, -132.25, -132.25])

LORAWAN_DR = np.array([[0, 12, 125],
                      [1, 11, 125],
                      [2, 10, 125],
                      [3, 9, 125],
                      [4, 8, 125],
                      [5, 7, 125],
                      [6, 7, 250]])

#
# check for collisions at base station
# Note: called before a packet (or rather node) is inserted into the list
def checkcollision(packet):
    col = 0  # flag needed since there might be several collisions for packet
    processing = 0
    for i in range(0, len(packetsAtBS)):
        if packetsAtBS[i].packet.processed == 1:
            processing = processing + 1
    if (processing > maxBSReceives):
        if (verbose >= 3):
            print("[DEBUG] -  too long:", len(packetsAtBS))
        packet.processed = 0
    else:
        packet.processed = 1

    if packetsAtBS:
        if (verbose >= 3):
            print("[DEBUG] - CHECK node {} (sf:{} bw:{} freq:{:.6e}) others: {}".format(packet.nodeid, packet.sf, packet.bw,
                                                                                    packet.freq, len(packetsAtBS)))
        for other in packetsAtBS:
            if other.nodeid != packet.nodeid:
                if (verbose >= 3):
                    print("[DEBUG] - >> node {} (sf:{} bw:{} freq:{:.6e})".format(other.nodeid, other.packet.sf,
                                                                              other.packet.bw, other.packet.freq))
                # simple collision
                if frequencyCollision(packet, other.packet) and sfCollision(packet, other.packet):
                    if full_collision:
                        if timingCollision(packet, other.packet):
                            # check who collides in the power domain
                            c = powerCollision(packet, other.packet)
                            # mark all the collided packets
                            # either this one, the other one, or both
                            for p in c:
                                p.collided = 1
                                if p == packet:
                                    col = 1
                        else:
                            # no timing collision, all fine
                            pass
                    else:
                        packet.collided = 1
                        other.packet.collided = 1  # other also got lost, if it wasn't lost already
                        col = 1
        return col
    return 0


#
# frequencyCollision, conditions
#
#        |f1-f2| <= 120 kHz if f1 or f2 has bw 500
#        |f1-f2| <= 60 kHz if f1 or f2 has bw 250
#        |f1-f2| <= 30 kHz if f1 or f2 has bw 125
def frequencyCollision(p1, p2):
    if (abs(p1.freq - p2.freq) <= 120 and (p1.bw == 500 or p2.freq == 500)):
        if (verbose >= 3):
            print("[DEBUG] -  frequency coll 500")
        return True
    elif (abs(p1.freq - p2.freq) <= 60 and (p1.bw == 250 or p2.freq == 250)):
        if (verbose >= 3):
            print("[DEBUG] -  frequency coll 250")
        return True
    else:
        if (abs(p1.freq - p2.freq) <= 30):
            if (verbose >= 3):
                print("[DEBUG] -  frequency coll 125")
            return True
            # else:
            if (verbose >= 3):
                print("[DEBUG] -  no frequency coll")
    return False


def sfCollision(p1, p2):
    if p1.sf == p2.sf:
        if (verbose >= 3):
            print("[DEBUG] -  collision sf node {} and node {}".format(p1.nodeid, p2.nodeid))
        # p2 may have been lost too, will be marked by other checks
        return True
    if (verbose >= 3):
        print("[DEBUG] -  no sf collision")
    return False


def powerCollision(p1, p2):
    powerThreshold = 6  # dB
    if (verbose >= 3):
        print(
            "[DEBUG] -  pwr: node {0.nodeid} {0.rssi:3.2f} dBm node {1.nodeid} {1.rssi:3.2f} dBm; diff {2:3.2f} dBm".format(
                p1, p2, round(p1.rssi - p2.rssi, 2)))
    if abs(p1.rssi - p2.rssi) < powerThreshold:
        if (verbose >= 3):
            print("[DEBUG] -  collision pwr both node {} and node {}".format(p1.nodeid, p2.nodeid))
        # packets are too close to each other, both collide
        # return both packets as casualties
        return (p1, p2)
    elif p1.rssi - p2.rssi < powerThreshold:
        # p2 overpowered p1, return p1 as casualty
        if verbose >= 3:
            print("[DEBUG] -  collision pwr node {} overpowered node {}".format(p2.nodeid, p1.nodeid))
        return (p1,)
    if verbose >= 3:
        print("[DEBUG] -  p1 wins, p2 lost")
    # p2 was the weaker packet, return it as a casualty
    return (p2,)


def timingCollision(p1, p2):
    # assuming p1 is the freshly arrived packet and this is the last check
    # we've already determined that p1 is a weak packet, so the only
    # way we can win is by being late enough (only the first n - 5 preamble symbols overlap)

    # assuming 8 preamble symbols
    Npream = 8

    # we can lose at most (Npream - 5) * Tsym of our preamble
    Tpreamb = 2 ** p1.sf / (1.0 * p1.bw) * (Npream - 5)

    # check whether p2 ends in p1's critical section
    p2_end = p2.addTime + p2.rectime
    p1_cs = env.now + Tpreamb
    if (verbose >= 3):
        print("[DEBUG] -  collision timing node {} ({},{},{}) node {} ({},{})".format(p1.nodeid, env.now - env.now,
                                                                                 p1_cs - env.now, p1.rectime, p2.nodeid,
                                                                                 p2.addTime - env.now,
                                                                                 p2_end - env.now))
    if p1_cs < p2_end:
        # p1 collided with p2 and lost
        if (verbose >= 3):
            print("[DEBUG] -  not late enough")
        return True
    if (verbose >= 3):
        print("[DEBUG] -  saved by the preamble")
    return False


# this function computes the airtime of a packet
# according to LoraDesignGuide_STD.pdf
#
def airtime(sf, cr, pl, bw):
    global Tpream
    H = 0  # implicit header disabled (H=0) or not (H=1)
    DE = 0  # low data rate optimization enabled (=1) or not (=0)
    Npream = 8  # number of preamble symbol (12.25  from Utz paper)

    if bw == 125 and sf in [11, 12]:
        # low data rate optimization mandated for BW125 with SF11 and SF12
        DE = 1
    if sf == 6:
        # can only have implicit header with SF6
        H = 1

    Tsym = (2.0 ** sf) / bw
    Tpream = (Npream + 4.25) * Tsym
    if (verbose >= 3):
        print("[DEBUG] -  sf", sf, " cr", cr, "pl", pl, "bw", bw)
    payloadSymbNB = 8 + max(math.ceil((8.0 * pl - 4.0 * sf + 28 + 16 - 20 * H) / (4.0 * (sf - 2 * DE))) * (cr + 4), 0)
    Tpayload = payloadSymbNB * Tsym

    return Tpream + Tpayload


#
# this function creates a node
#
class myNode():
    def __init__(self, nodeid, bs, period, packetlen):
        self.nodeid = nodeid
        self.period = period
        self.bs = bs
        self.x = 0
        self.y = 0
        self.Q_matrix = np.zeros((6, 3))  # Matrice Q de taille 6x3 (6 DRs, 3 colonnes pour F1, F2, F3)
        # this is very complex prodecure for placing nodes
        # and ensure minimum distance between each pair of nodes
        found = 0
        rounds = 0
        global nodes
        global nodesPosition
        global loadNodesLocation

        if loadNodesLocation:
            self.x = nodesPosition[nodeid][0]
            self.y = nodesPosition[nodeid][1]
        else:
            while (found == 0 and rounds < 100):
                a = random.random()
                b = random.random()
                if b < a:
                    a, b = b, a
                posx = b * maxDist * math.cos(2 * math.pi * a / b) + bsx
                posy = b * maxDist * math.sin(2 * math.pi * a / b) + bsy
                if len(nodes) > 0:
                    for index, n in enumerate(nodes):
                        dist = np.sqrt(((abs(n.x - posx)) ** 2) + ((abs(n.y - posy)) ** 2))
                        if dist >= 10:
                            found = 1
                            self.x = posx
                            self.y = posy
                        else:
                            rounds = rounds + 1
                            if rounds == 100:
                                if (verbose >= 1):
                                    print("INFO: could not place new node, giving up")
                                exit(-1)
                else:
                    if (verbose >= 3):
                        print("[DEBUG] -  first node")
                    self.x = posx
                    self.y = posy
                    found = 1

        self.dist = np.sqrt((self.x - bsx) * (self.x - bsx) + (self.y - bsy) * (self.y - bsy))
        if (verbose >= 3):
            print('[DEBUG] -  node %d' % nodeid, "x", self.x, "y", self.y, "dist: ", self.dist)
        if sim_scenario == 0:
            self.packet = myPacket(self.nodeid, packetlen, self.dist,'unconfirmed')
        elif sim_scenario == 1:
            self.packet = myPacket(self.nodeid, packetlen, self.dist,'confirmed')
        elif sim_scenario == 2:
            self.packet = myPacket(self.nodeid, packetlen, self.dist,'confirmed')
        self.sent = 0
        # number of DL ACK received by the node
        # This is required for confirmed frame only
        self.ack_received = 0
        self.reward = 0
        # This is required for confirmed frame which are in collison
        self.nack_received = 0
        self.nreward = 0

        # Node frequency usage. Incremented each time a packet is sent using one of these frequency channels
        # freq_usage[0] = 860000000,
        # freq_usage[1] = 864000000,
        # freq_usage[2] = 868000000
        self.freq_usage = [0, 0, 0]
        self.freq_usage_ack_received = [0, 0, 0]

        # graphics for node
        global graphics
        if (graphics == 1):
            global ax
            ax.add_artist(plt.Circle((self.x, self.y), 2, fill=True, color='blue'))


#
# this function creates a packet (associated with a node)
# it also sets all parameters, currently random
#
class myPacket():
    def __init__(self, nodeid, plen, distance, frame_type):
        global experiment
        global Ptx
        global gamma
        global d0
        global var
        global Lpld0
        global GL

        self.nodeid = nodeid
        self.txpow = Ptx

        self.MType = frame_type

        # randomize configuration values
        self.sf = random.randint(6, 12)
        self.cr = random.randint(1, 4)
        self.bw = random.choice([125, 250, 500])

        # for certain experiments override these
        if experiment == 1 or experiment == 0:
            self.sf = 12
            self.cr = 4
            self.bw = 125

        # for certain experiments override these
        if experiment == 2:
            self.sf = 6
            self.cr = 1
            self.bw = 500
        # lorawan
        if experiment == 4:
            self.sf = 12
            self.cr = 1
            self.bw = 125

        if experiment == 6:
            # Exploration phase
            DR = random.randint(0, 6)
            # ToDO: Exploitation phase
            # Chose DR according to Q matrice

            self.sf = LORAWAN_DR[DR,1]
            self.bw = LORAWAN_DR[DR,2]
            self.cr = 1
            


        # for experiment 3 find the best setting
        # OBS, some hardcoded values
        Prx = self.txpow  ## zero path loss by default

        # log-shadow
        Lpl = Lpld0 + 10 * gamma * math.log10(distance / d0)
        if (verbose >= 3):
            print("[DEBUG] -  Lpl:", Lpl)
        Prx = self.txpow - GL - Lpl

        if (experiment == 3) or (experiment == 5):
            minairtime = 9999
            minsf = 0
            minbw = 0

            if (verbose >= 3):
                print("[DEBUG] -  Prx:", Prx)

            for i in range(0, 6):
                for j in range(1, 4):
                    if (sensi[i, j] < Prx):
                        self.sf = int(sensi[i, 0])
                        if j == 1:
                            self.bw = 125
                        elif j == 2:
                            self.bw = 250
                        else:
                            self.bw = 500
                        at = airtime(self.sf, 1, plen, self.bw)
                        if at < minairtime:
                            minairtime = at
                            minsf = self.sf
                            minbw = self.bw
                            minsensi = sensi[i, j]
            if (minairtime == 9999):
                if (verbose >= 3):
                    print("[DEBUG] -  does not reach base station")
                exit(-1)
            if (verbose >= 3):
                print("[DEBUG] -  best sf:", minsf, " best bw: ", minbw, "best airtime:", minairtime)
            self.rectime = minairtime
            self.sf = minsf
            self.bw = minbw
            self.cr = 1

            if experiment == 5:
                # reduce the txpower if there's room left
                self.txpow = max(2, self.txpow - math.floor(Prx - minsensi))
                Prx = self.txpow - GL - Lpl
                if (verbose >= 3):
                    print('[DEBUG] -  minsesi {} best txpow {}'.format(minsensi, self.txpow))



        # transmission range, needs update XXX
        self.transRange = 150
        self.pl = plen
        self.symTime = (2.0 ** self.sf) / self.bw
        self.arriveTime = 0
        self.rssi = Prx
        # frequencies: lower bound + number of 61 Hz steps
        self.freq = 860000000 + random.randint(0, 2622950)

        # for certain experiments override these and
        # choose some random frequencies
        if experiment == 1:
            self.freq = random.choice([860000000, 864000000, 868000000])
        elif experiment == 6:
            # Exploration phase
            self.freq = random.choice([860000000, 864000000, 868000000])
            # ToDo : Exploitation phase
            # Chose the frequency according to the Q learning matrice

        else:
            self.freq = 860000000

        if (verbose >= 3):
            print("[DEBUG] -  frequency", self.freq, "symTime ", self.symTime)
            print("[DEBUG] -  bw", self.bw, "sf", self.sf, "cr", self.cr, "rssi", self.rssi)
        self.rectime = airtime(self.sf, self.cr, self.pl, self.bw)
        if (verbose >= 3):
            print("[DEBUG] -  rectime node ", self.nodeid, "  ", self.rectime)
        # denote if packet is collided
        self.collided = 0
        self.processed = 0


#
# main discrete event loop, runs for each node
# a global list of packet being processed at the gateway
# is maintained
#
# modification fonction transmit pour faire du Alloha sloté by IKF
def transmit(env, node):
    while True:
        # Pure Aloha
        # A = random.expovariate(1.0/float(node.period))
        # yield env.timeout(A)

        # Aloha slotted
        # uncomment the following line to use Aloha slotted medium access protocol
        # if A == random.randint(1,10):
        #    yield env.timeout(A)
        # else if A!= random.randint(1,10):
        #    B = random.randint(1,10)
        #    yield env.timeout(B)
        global txInstantVector
        global slot_time
        global verbose
        # A = random.expovariate(1.0 / float(node.period))
        if verbose >= 3:
            print("[DEBUG] - " + str(env.now) + ' --- Node ' + str(node.nodeid) + ' --> tx_starting')
        if mac_protocol == 0:
            # Pure Aloha protocol
            nextTxInstant = random.expovariate(1.0 / float(node.period))
            if verbose >= 3:
                print('[DEBUG] - ' + str(env.now) + ' --- Node ' + str(node.nodeid) + ' --> transmission is scheduled at ', env.now + nextTxInstant)

            yield env.timeout(nextTxInstant)
        elif mac_protocol == 1:
            # Slotted Aloha proocol
            nextTxInstant = random.expovariate(1.0 / float(node.period))
            if nextTxInstant in txInstantVector:
                if (verbose >= 1):
                    print("INFO: transmission is scheduled at ", env.now + nextTxInstant)

                yield env.timeout(nextTxInstant)
            else:
                delayTime = slot_time - (nextTxInstant % slot_time)
                nextTxInstant = nextTxInstant + delayTime
                if (verbose >= 1):
                    print("INFO: transmission of the packet is delayed of ", delayTime, "[ s]")
                    print("INFO: new transmission is scheduled at ", env.now + nextTxInstant)
                yield env.timeout(nextTxInstant)
        else:
            # Default MAC protocol : Pure Aloha
            # Pure Aloha protocol
            nextTxInstant = random.expovariate(1.0 / float(node.period))
            if (verbose >= 1):
                print("INFO: transmission is scheduled at ", env.now + nextTxInstant)
            yield env.timeout(nextTxInstant)

        # time sending and receiving
        # packet arrives -> add to base station

        node.sent = node.sent + 1
        if verbose >= 3:
            print("[DEBUG] - " + str(env.now) + ' --- Node ' + str(node.nodeid) + ' --> tx_done, packet is sent')

        # save frequency channels usage freq: 860000000, 864000000, 868000000
        if node.packet.freq == 860000000:
            node.freq_usage[0] += 1
            global_freq_usage[0] += 1
        elif node.packet.freq == 864000000:
            node.freq_usage[1] += 1
            global_freq_usage[1] += 1
        elif node.packet.freq == 868000000:
            node.freq_usage[2] += 1
            global_freq_usage[2] += 1

        if node in packetsAtBS:
            if verbose >= 2:
                print("[ERROR] - packet already in")
        else:
            sensitivity = sensi[node.packet.sf - 7, [125, 250, 500].index(node.packet.bw) + 1]
            if node.packet.rssi < sensitivity:
                if verbose >= 1:
                    print("[INFO] - node {}: packet will be lost").format(node.nodeid)
                node.packet.lost = True
            else:
                node.packet.lost = False
                # adding packet if no collision
                if checkcollision(node.packet) == 1:
                    node.packet.collided = 1
                else:
                    node.packet.collided = 0
                packetsAtBS.append(node)
                node.packet.addTime = env.now
                if verbose >= 3:
                    print("[DEBUG] - " + str(env.now) + ' --- Node ' + str(node.nodeid) + ' --> packet in BS queue')

        yield env.timeout(node.packet.rectime)

        if node.packet.lost:
            global nrLost
            nrLost += 1
        if node.packet.collided == 1:
            global nrCollisions
            nrCollisions = nrCollisions + 1
        if node.packet.collided == 0 and not node.packet.lost:
            global nrReceived
            nrReceived = nrReceived + 1
        if node.packet.processed == 1:
            global nrProcessed
            nrProcessed = \
                nrProcessed + 1

        # complete packet has been received by base station
        # can remove it
        if node in packetsAtBS:
            packetsAtBS.remove(node)
            if verbose >= 3:
                print("[DEBUG] - " + str(env.now) + ' --- Node ' + str(node.nodeid) + '--> packet removed from BS '
                                                                                      'queue')
                print("[DEBUG] - " + str(env.now) + ' --- Node ' + str(
                    node.nodeid) + '--> packet successfully received by BS')


        # Check if an ack frame is needed
        if node.packet.MType == 'confirmed' and node.packet.collided == 0 and not node.packet.lost:
            node.ack_received += 1
            node.reward +=1


        else:
            node.nack_received += 1
            node.nreward += 1


            if verbose >= 3:
              print("[DEBUG] - " + str(env.now) + ' --- Node ' + str(
                node.nodeid) + '--> ACK successfully received by Node')

        # reset the packet
        node.packet.collided = 0
        node.packet.processed = 0
        node.packet.lost = False




#
# "main" program
#

# get arguments
if len(sys.argv) >= 5:
    nrNodes = int(sys.argv[1])
    avgSendTime = int(sys.argv[2])
    experiment = int(sys.argv[3])
    simtime = int(sys.argv[4])

    if len(sys.argv) >= 6:
        sim_scenario = int(sys.argv[5])

    # Create sim results directory
    if len(sys.argv) >= 7:
        # Directory is already created
        sim_results_path = results_path + '/' + str(sys.argv[6])
    else:
        # We need to create the directory
        try:
            os.mkdir(sim_results_path)
        except OSError:
            print("[ERROR] - Creation of the directory %s failed" % sim_results_path)
            if os.path.isdir(sim_results_path):
                print('[ERROR] - Directory already exist')
        else:
            print("[INFO] - Successfully created the directory %s " % sim_results_path)


    # instant de transmission et durée d'un slot pour le Aloha sloté
    if (mac_protocol == 1):
        slot_time = 100
        txInstantVector = np.arange(0, simtime, slot_time)

    if len(sys.argv) > 7:
        full_collision = bool(int(sys.argv[7]))

    if (verbose >= 1):
        print("[INFO] - Nodes:", nrNodes)
        print("[INFO] - AvgSendTime (exp. distributed):", avgSendTime)
        print("[INFO] - Experiment: ", experiment)
        print("[INFO] - Simtime: ", simtime)
        print("[INFO] - Sim_scenario: ", sim_scenario)
        print("[INFO] - Sim_result_path: ", sim_results_path)
        print("[INFO] - Full Collision: ", full_collision)

else:
    print("usage: ./loraDir <nodes> <avgsend> <experi"
          "ment> <simtime> <sim_scenario> [collision]")
    print("experiment 0 and 1 use 1 frequency only")
    exit(-1)

# global stuff
# Rnd = random.seed(12345)
nodes = []
packetsAtBS = []
env = simpy.Environment()

# maximum number of packets the BS can receive at the same time
maxBSReceives = 8

# max distance: 300m in city, 3000 m outside (5 km Utz experiment)
# also more unit-disc like according to Utz
bsId = 1
nrCollisions = 0
nrReceived = 0
nrProcessed = 0
nrLost = 0

Ptx = 14
gamma = 2.08
d0 = 40.0
var = 0  # variance ignored for now
Lpld0 = 127.41
GL = 0

sensi = np.array([sf7, sf8, sf9, sf10, sf11, sf12])
if experiment in [0, 1, 4]:
    minsensi = sensi[5, 2]  # 5th row is SF12, 2nd column is BW125
elif experiment == 2:
    minsensi = -112.0  # no experiments, so value from datasheet
elif experiment in [3, 5]:
    minsensi = np.amin(sensi)  ## Experiment 3 can use any setting, so take minimum
elif experiment == 6:
    minsensi = np.amin(sensi[:,1:2])


print("experiment = ", minsensi)
Lpl = Ptx - minsensi
if (verbose >= 1):
    print("[INFO] - amin", minsensi, "Lpl", Lpl)
maxDist = d0 * (math.e ** ((Lpl - Lpld0) / (10.0 * gamma)))
if (verbose >= 1):
    print("[INFO] - maxDist:", maxDist)

# base station placement
bsx = maxDist + 10
bsy = maxDist + 10
xmax = bsx + maxDist + 20
ymax = bsy + maxDist + 20

# prepare graphics and add sink
if (graphics == 1):
    plt.ion()
    plt.figure()
    ax = plt.gcf().gca()
    # XXX should be base station position
    ax.add_artist(plt.Circle((bsx, bsy), 3, fill=True, color='green'))
    ax.add_artist(plt.Circle((bsx, bsy), maxDist, fill=False, color='green'))

# load node location from "nodes.txt" file if present and selected
if loadNodesLocation:
    if os.path.isfile('data/nodes.txt'):
        nodesPosition = np.loadtxt('data/nodes.txt')
        nrNodes = nodesPosition.shape[0]
        print(str(nodesPosition[1][1]) + "\n")

for i in range(0, nrNodes):
    # myNode takes period (in ms), base station id packetlen (in Bytes)
    # 1000000 = 16 min
    node = myNode(i, bsId, avgSendTime, 20)
    print ()
    print("matrice Q du noeud", i, "est", node.Q_matrix)  # Chaque noeud a sa matrice Q
    print ("récompense du noeud", i, "est", node.reward)
    print("sanction du noeud", i, "est", node.nreward)
    nodes.append(node)
    env.process(transmit(env, node))

# prepare show
if (graphics == 1):
    plt.xlim([0, xmax])
    plt.ylim([0, ymax])
    plt.draw()
    plt.show()

# start simulation
env.run(until=simtime)

# print stats and save into file
if (verbose >= 1):
    print("[INFO] - nrCollisions ", nrCollisions)

# compute energy
# Transmit consumption in mA from -2 to +17 dBm
TX = [22, 22, 22, 23,  # RFO/PA0: -2..1
      24, 24, 24, 25, 25, 25, 25, 26, 31, 32, 34, 35, 44,  # PA_BOOST/PA1: 2..14
      82, 85, 90,  # PA_BOOST/PA1: 15..17
      105, 115, 125]  # PA_BOOST/PA1+PA2: 18..20
# mA = 90    # current draw for TX = 17 dBm

V = 3.0     # voltage XXX
if (sim_scenario == 0):
 Iidle = 1.5 #according to the datasheet this is the supply current in the idle mode in mA
 idletime = 2000 # time in idle mode in ms
 Istb = 1.6 #according to the datasheet this is the supply current in standby mode in mA
 Isleep = 0.0002 #according to the datasheet this is the supply current in sleep mode in mA
 Nstb= 2 # number of stanby mode, nodes go two time in standby mode
 sent = sum(n.sent for n in nodes)
 energy_TxUL = sum(node.packet.rectime * TX[int(node.packet.txpow)+2] * V * node.sent for node in nodes)
 energy_idle = sum(idletime* Iidle * V * node.sent for node in nodes)
 energy_stb = sum(Tpream * Nstb *Istb * V * node.sent for node in nodes)
 energy_sleep = sum((avgSendTime- node.packet.rectime-idletime-Nstb*Tpream)*Isleep*V * node.sent for node in nodes)
 energy1 = energy_TxUL/1e6
 energyT = (energy_TxUL + energy_idle + energy_stb + energy_sleep)/1e6
elif (sim_scenario == 1):
   Iidle = 1.5  # according to the datasheet this is the supply current in the idle mode in mA
   idletime1 = 1000  # time in idle mode in ms
   idletime2 = 2000  # time in idle mode in ms
   Istb = 1.6  # according to the datasheet this is the supply current in standby mode in mA
   Ir = 11.5  # according to the datasheet this is the supply current in receive mode, LnaBoost ON,band 1 in mA
   Isleep = 0.0002  # according to the datasheet this is the supply current in sleep mode in mA
   Nstb = 2  # number of stanby mode, nodes go two time in standby mode
   Tr = airtime(12,4,13,125)
   sent = sum(n.sent for n in nodes)
   ack_received = sum(n.ack_received for n in nodes)
   energy_TxUL = sum(node.packet.rectime * TX[int(node.packet.txpow) + 2] * V * node.sent for node in nodes)
   energy_idle1 = sum(idletime1 * Iidle * V * node.ack_received for node in nodes)
   energy_idle2 = sum(idletime2 * Iidle * V * node.nack_received for node in nodes)
   energy_Rx1DL = sum(Tr* Ir * V * node.ack_received for node in nodes)
   energy_stb = sum(Tpream * Nstb * Istb * V * node.nack_received for node in nodes)
   energy_sleep1 = sum((avgSendTime - node.packet.rectime - idletime1 - Tr) * Isleep * V * node.ack_received for node in nodes)
   energy_sleep2 = sum((avgSendTime - node.packet.rectime - idletime2 - Nstb * Tpream) * Isleep * V * node.nack_received for node in nodes)
   energy1 = energy_TxUL / 1e6
   energy2 = (energy_idle1 + energy_Rx1DL + energy_sleep1 ) / 1e6
   energy3 = (energy_idle2 + energy_sleep2 + energy_stb) / 1e6
   energyT = energy1 + energy2 + energy3
elif (sim_scenario == 2):
    Iidle = 1.5  # according to the datasheet this is the supply current in the idle mode in mA
    idletime = 2000  # time in idle mode in ms
    Istb = 1.6  # according to the datasheet this is the supply current in standby mode in mA
    Ir = 11.5  # according to the datasheet this is the supply current in receive mode, LnaBoost ON,band 1 in mA
    Isleep = 0.0002  # according to the datasheet this is the supply current in sleep mode in mA
    Nstb1 = 1  # number of stanby mode, nodes go two time in standby mode
    Nstb2 = 2  # number of stanby mode, nodes go two time in standby mode
    Tr = airtime(12, 4, 13, 125)
    sent = sum(n.sent for n in nodes)
    ack_received = sum(n.ack_received for n in nodes)
    energy_TxUL = sum(node.packet.rectime * TX[int(node.packet.txpow) + 2] * V * node.sent for node in nodes)
    energy_idle1 = sum(idletime * Iidle * V *node.ack_received for node in nodes )
    energy_idle2 = sum(idletime * Iidle * V * node.nack_received for node in nodes)
    energy_Rx2DL = sum(Tr * Ir * V * node.ack_received for node in nodes)
    energy_stb1 = sum(Tpream * Nstb1 * Istb * V * node.ack_received for node in nodes)
    energy_stb2 = sum(Tpream * Nstb2 * Istb * V * node.nack_received for node in nodes)
    energy_sleep1 = sum((avgSendTime - node.packet.rectime - Nstb1 * Tpream - idletime - Tr) * Isleep * V * node.ack_received for node in nodes )
    energy_sleep2 = sum((avgSendTime - node.packet.rectime - idletime - Nstb2 * Tpream) * Isleep * V * node.nack_received for node in nodes)
    energy1 = energy_TxUL / 1e6
    energy2 = (energy_idle1 + energy_Rx2DL + energy_sleep1 + energy_stb1) / 1e6
    energy3 = (energy_idle2 + energy_sleep2 + energy_stb2) / 1e6
    energyT = energy1 + energy2 + energy3
if (verbose>=1):
    print ("[INFO] - energy (in J) in tx only: ", energy1)
    print ("[INFO] -  total energy (in J): ", energyT)
    print ("[INFO] - sent packets: ", sent)
    print ("[INFO] - collisions: ", nrCollisions)
    print ("[INFO] - received packets: ", nrReceived)
    print ("[INFO] - processed packets: ", nrProcessed)
    print ("[INFO] - lost packets: ", nrLost)
    print ("[INFO] - Tpream: ", Tpream)


# data extraction rate
der1 = (sent - nrCollisions) / float(sent)
if (verbose >= 1):
    print("[INFO] - DER method 1:", der1)
der2 = (nrReceived) / float(sent)
if (verbose >= 1):
    print("[INFO] - DER method 2:", der2)

# this can be done to keep graphics visible
if (graphics == 1):
    input('Press Enter to continue ...')

# save experiment data into a dat file that can be read by e.g. gnuplot
# name of file would be:  exp0.dat for experiment 0




fname = sim_results_path +"/sim_results_exp" + str(experiment) + "_mac" + str(mac_protocol) + "_scenario"+ str(sim_scenario) + ".dat"

if (verbose >= 1):
    print(fname)
if os.path.isfile(fname):
    res1 = "\n" + str(simtime) + " " + str(avgSendTime) + " " + str(nrNodes) + " " + str(nrCollisions) + " " + str(
        nrReceived) + " " + str(nrProcessed) + " " + str(nrLost) + " " + str(sent) + " " + str(energy1) + " " + str(
        energyT) + " " + str(der1) + " " + str(der2)
    # res2 = "\n" + str(nrNodes) + " " + str(nrCollisions) + " " + str(sent) + " " + str(energy2)

else:
    res1 = "#simtime avgSendTime nrNodes nrCollisions nrReceived nrProcessed nrLost nrTransmissions OverallEnergy1 OverallEnergyT der1 der2 \n" + str(
        simtime) + " " + str(avgSendTime) + " " + str(nrNodes) + " " + str(nrCollisions) + " " + str(
        nrReceived) + " " + str(nrProcessed) + " " + str(nrLost) + " " + str(sent) + " " + str(energy1) + " " + str(
        energyT) + " " + str(der1) + " " + str(der2)
    # res2 = "#simtime avgSendTime nrNodes nrCollisions nrReceived nrProcessed nrLost nrTransmissions OverallEnergy\n" + str(nrNodes) + " " + str(nrCollisions) + " " + str(sent) + " " + str(energy2)
with open(fname, "a") as myfile:
    myfile.write(res1)
    # myfile.write(res2)

myfile.close()

with open('nodes.txt', 'w') as nfile:
    for n in nodes:
        nfile.write("{} {} {}\n".format(n.x, n.y, n.nodeid))
with open('basestation.txt', 'w') as bfile:
    bfile.write("{} {} {}\n".format(bsx, bsy, 0))