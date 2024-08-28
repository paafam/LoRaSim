# -*- coding: utf-8 -*-
"""
This python code allows us to plot some figures from the generated simulation results file

@author: Pafam
"""
import numpy as np
import matplotlib.pyplot as plt
import os
exp_color = ['r','b','g']
exp_marker = ['--','-+','-x']
idx = 0
fig1,ax1 = plt.subplots(figsize=(5, 4), layout='constrained')
fig2,ax2 = plt.subplots(figsize=(5, 4), layout='constrained')
for i in [1,6]:
    # results filename to load
    result_filepath = './results/AFRICOMM1/sim_results_exp'+str(i)+'.dat'
    # we perform 100 simulation realization for each number of nodes from 100 to 1600
    # the number of realization should be updated according to the simulation results in the result file
    nrRealization = 100

    # Read data from sim_results_file
    simtime, avgSendTime, nrNodes, nrCollisions, nrReceived, nrProcessed, nrLost, nrTransmissions, OverallEnergy1, OverallEnergy2, OverallEnergy3, der1, der2 = np.loadtxt(result_filepath, unpack=True)

    # Create figure directory to save figures
    dirname = "figures"
    path = "./"+dirname

    if os.path.isdir(path)==False:
        os.mkdir(path)

    # plot raw data
    #plt.figure(1)
    #plt.plot(nrNodes, OverallEnergy1, 'r--', nrNodes, OverallEnergy2, 'b-o', nrNodes, OverallEnergy3, 'g-.')
    #plt.xlabel('Nodes')
    #plt.ylabel('Overall Energy')
    #plt.title('Raw Data')
    #plt.savefig(path+"/OverallEnergy_consumption_raw_"+str(i)+".png")
    #plt.show()

    # plot mean data 
    nodes = np.unique(nrNodes)
    m_energy1 = np.mean(np.reshape(OverallEnergy1, [nodes.size,nrRealization]),1)
    m_energy2 = np.mean(np.reshape(OverallEnergy2, [nodes.size,nrRealization]),1)
    m_energy3 = np.mean(np.reshape(OverallEnergy3, [nodes.size,nrRealization]),1)
    m_der1 = np.mean(np.reshape(der1, [nodes.size,nrRealization]),1)
    m_der2 = np.mean(np.reshape(der2, [nodes.size,nrRealization]),1)

    #plt.figure(1)
    
    #plt.plot(nodes, m_energy1, exp_color[idx]+exp_marker[idx], nodes, m_energy2, exp_color[idx]+exp_marker[idx], nodes, m_energy3, exp_color[idx]+exp_marker[idx])
    ax1.plot(nodes, m_energy1, color=exp_color[idx],marker='',label='TX only-Experiment-'+str(i) )
    ax1.plot(nodes, m_energy3, color=exp_color[idx],marker='+',label='all state-Experiment-'+str(i))
    ax1.set_xlabel('Nodes')
    ax1.set_ylabel('Network Energy Consumed (NEC) [J]')
    ax1.set_title('NEC as a function of the number of IoT devices')
    ax1.grid(True)
    ax1.legend()  # Add a legend.
    #plt.savefig(path+"/OverallEnergy_consumption_mean_"+str(i)+".png")
    plt.show()

    #plt.figure(2)

    #plt.plot(nodes, m_der1, exp_color[idx]+exp_marker[idx], nodes, m_der2, exp_color[idx]+exp_marker[idx])
    #plt.plot(nodes, m_der1, exp_color[idx]+exp_marker[idx])
    ax2.plot(nodes, m_der1, exp_color[idx]+exp_marker[idx],label='Experiment-'+str(i))
    ax2.set_xlabel('Nodes')
    ax2.set_ylabel('Data Extraction Rate (DER) [%]')
    ax2.set_title('DER as a function of the number of IoT devices')
    ax2.grid(True)
    ax2.legend()  # Add a legend.
    #plt.savefig(path+"/data_extraction_rate_mean_"+str(i)+".png")
    plt.show()
    idx = idx+1