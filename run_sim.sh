#!/bin/bash

# script that lists all the items in the current folder
nodes=100 			#number of nodes to simulate
avgsend=1000			#average sending interval in ms
experiment=0 			#simulation radio settings 0 --> SF12 - BW125 - CR4/8
simtime=10000			#total running time in ms
for i in `seq 1 10`;
do
	echo =========================================
	echo Simulation : $i
	echo -----------------------------------------
	python loraDir.py $nodes $avgsend $experiment $simtime
done


