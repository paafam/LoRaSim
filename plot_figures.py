# -*- coding: utf-8 -*-
"""
This python code allows us to plot some figures from the generated simulation results file

@author: Pafam
"""
import numpy as np
import matplotlib.pyplot as plt
import os

# results filename to load
result_filepath = './sim_results_exp1.dat'
# we perform 100 simulation realization for each number of nodes from 100 to 1600
# the number of realization should be updated according to the simulation results in the result file
nrRealization = 10

# Read data from sim_results_file
simtime, avgSendTime, nrNodes, nrCollisions, nrReceived, nrProcessed, nrLost, nrTransmissions, OverallEnergy1, OverallEnergyT, der1, der2 = np.loadtxt(result_filepath, unpack=True)

# Create figure directory to save figures
dirname = "figures"
path = "./"+dirname

if os.path.isdir(path)==False:
    os.mkdir(path)

# plot raw data
plt.figure(1)
plt.plot(nrNodes, OverallEnergy1, 'r--', nrNodes, OverallEnergyT, 'b')
plt.xlabel('Nodes')
plt.ylabel('Overall Energy')
plt.title('Raw Data')
plt.savefig(path+"/OverallEnergy_consumption_raw.png")
# plt.show()

# plot mean data 
nodes = np.unique(nrNodes)
m_energy1 = np.mean(np.reshape(OverallEnergy1, [nodes.size,nrRealization]),1)
m_energyT = np.mean(np.reshape(OverallEnergyT, [nodes.size,nrRealization]),1)
m_der1 = np.mean(np.reshape(der1, [nodes.size,nrRealization]),1)
m_der2 = np.mean(np.reshape(der2, [nodes.size,nrRealization]),1)

plt.figure(2)
plt.plot(nodes, m_energy1, 'r--', nodes, m_energyT, 'b')
plt.xlabel('Nodes')
plt.ylabel('Overall Energy')
plt.title('Mean Data')
plt.savefig(path+"/OverallEnergy_consumption_mean.png")
#plt.show()

plt.figure(3)
plt.plot(nodes, m_der1, 'r--', nodes, m_der2, 'b*')
plt.xlabel('Nodes')
plt.ylabel('Overall Energy')
plt.title('Mean Data')
plt.savefig(path+"/data_extraction_rate_mean.png")
#plt.show()