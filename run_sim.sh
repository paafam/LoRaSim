#!/bin/bash

# script that lists all the items in the current folder
nodes=`seq 10 10 1000`			#number of nodes to simulate
avgsend=180000						#average sending interval in ms
experiments=(0 1 6)					#simulation radio settings 0 --> SF12 - BW125 - CR4/8
simdays=1	
simtime=$((($simdays)*24*60*60*1000))	#total running time in ms
scenario=1
full_colision_check=1
for experiment in ${experiments[@]}
do
	echo =====================================================
	echo "Experiment - $experiment"
	echo =====================================================
	for node in $nodes
	do	
		echo Simulation : Nodes: $node  --- $((($node)*100/(1000)))%
		for i in `seq 1 100`
		do
			#echo Simulation : Nodes: $node - Sim: $i --- $((($node)*($i)/(1*100)))%
			#echo ----------------------------------------------
			python loraDir.py $node $avgsend $experiment $simtime $scenario $full_colision_check
		done
		
	done
done
echo =====================================================
echo Plot figures and save it to figures directory
python plot_figures.py
echo =====================================================