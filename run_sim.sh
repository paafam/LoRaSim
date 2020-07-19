#!/bin/bash

# script that lists all the items in the current folder
nodes=(`seq 100 100 1600`)		  #number of nodes to simulate
avgsend=1000000						      #average sending interval in ms
experiment=1 						        #simulation radio settings 0 --> SF12 - BW125 - CR4/8
simdays=58
simtime=$((simdays*24*60*60*1000))	#total running time in ms
Nr=10                             # Number of realization
progress=0
echo =====================================================
for node in ${nodes[@]}
do	
	for i in `seq 1 $Nr`
	do
	  progress=$(( progress + 1))
		echo Simulation : Nodes: $node - Sim: $i --- $((progress*100/(Nr*${#nodes[@]})))%
		echo ----------------------------------------------
		python loraDir.py $node $avgsend $experiment $simtime
	done
done
echo =====================================================
echo Plot figures and save it to figures directory
python plot_figures.py
echo =====================================================
#echo "${nodes[-1]}"