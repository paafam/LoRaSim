# -*- coding: utf-8 -*-
"""
This python code allows us to plot some figures from the generated simulation results file

@author: Pafam
"""
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Verbose:
# 0 : SILENT mode
# 1 : INFO mode  : only information type of messages are printed
# 2 : ERROR mode : only error messages are printed
# 3 : DEBUG mode : all messages are printed
# Default mode is SILENT mode
verbose = 0

# detect the current working directory
path = os.getcwd()
if verbose >= 1:
    print ("[INFO] - current working directory is %s " % path)


data_path   = path + "/data"
# Create results directory
results_path = path + "/results"
try:
    os.mkdir(results_path)
except OSError:
    if verbose >= 2:
        print ("[ERROR] - Creation of the directory %s failed" % results_path)
    if os.path.isdir(results_path):
        if verbose >= 2:
            print('[ERROR] - Directory already exist')
else:
    if verbose >= 1:
        print ("[INFO] - Successfully created the directory %s " % results_path)

#
# "main" program
#

# get arguments
if len(sys.argv) >= 3:
    sim_results_path = results_path + '/'+ str(sys.argv[1])
    files = os.listdir(sim_results_path)

    nrRealization = int(sys.argv[2])

    # Create figure directory to save figures
    figures_path = sim_results_path + "/figures"
    if os.path.isdir(figures_path) == False:
        os.mkdir(figures_path)

    if (verbose >= 1):
        print("[INFO] - Sim_result_path: ", sim_results_path)
        print("[INFO] - Sim_figures_path: ", figures_path)

else:
    print("usage: ./plot_figures <sim_results_path> <Nr_sim_realization>")
    exit(-1)


# results filename to load
i = 2
for f in files:
    result_filepath = sim_results_path + "/" + f
    names = f.split(".")
    names = names[0].split("_")
    # we perform 100 simulation realization for each number of nodes from 100 to 1600
    # the number of realization should be updated according to the simulation results in the result file
    # Read data from sim_results_file
    simtime, avgSendTime, nrNodes, nrCollisions, nrReceived, nrProcessed, nrLost, nrTransmissions, OverallEnergy1, OverallEnergyT, der1, der2 = np.loadtxt(result_filepath, unpack=True)
    # plot raw data
    plt.figure(i)
    plt.grid(True)
    plt.plot(nrNodes, OverallEnergy1/1e3, 'r--+', nrNodes, OverallEnergyT/1e3, 'b-x')
    plt.legend(['Tx only energy','Node global energy'])
    plt.xlabel('Number of nodes')
    plt.ylabel('Network Energy Consumption [kJ]')
    plt.title(names[4] + ' - Raw Data')
    plt.savefig(figures_path + "/" + names[4] + "_OverallEnergy_consumption_raw.png")
    # plt.show()
    i=i+1
    # plot mean data
    nodes = np.unique(nrNodes)
    m_energy1 = np.mean(np.reshape(OverallEnergy1/1e3, [nodes.size,nrRealization]),1)
    m_energyT = np.mean(np.reshape(OverallEnergyT/1e3, [nodes.size,nrRealization]),1)
    m_der1 = np.mean(np.reshape(der1, [nodes.size,nrRealization]),1)
    m_der2 = np.mean(np.reshape(der2, [nodes.size,nrRealization]),1)

    plt.figure(1)
    plt.grid(True)
    plt.plot(nodes, m_energy1, 'r--+', nodes, m_energyT, 'b-x')
    plt.legend(['Tx only energy', 'Node global energy'])
    plt.xlabel('Number of nodes')
    plt.ylabel('Network Energy Consumption [kJ]')
    plt.title(names[4] + ' - NEC')
    plt.savefig(figures_path + "/_OverallEnergy_consumption_mean.png")

    plt.figure(i)
    plt.grid(True)
    plt.plot(nodes, m_energy1, 'r--+', nodes, m_energyT, 'b-x')
    plt.legend(['Tx only energy', 'Node global energy'])
    plt.xlabel('Number of nodes')
    plt.ylabel('Network Energy Consumption [kJ]')
    plt.title(names[4] + ' - NEC')
    plt.savefig(figures_path + "/" + names[4] + "_OverallEnergy_consumption_mean.png")
    #plt.show()
    i = i + 1

    plt.figure(i)
    plt.plot(nodes, m_der1, 'r--', nodes, m_der2, 'b*')
    plt.xlabel('Nodes')
    plt.ylabel('Data Extraction Rate')
    plt.title('DER - Mean Data')
    plt.savefig(figures_path + "/" + names[4] + "_data_extraction_rate_mean.png")
    #plt.show()
    i = i + 1