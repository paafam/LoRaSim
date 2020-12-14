#!/bin/bash

# script that run the LoRa simulator
echo ===========================================================
# Check weather results directory exist
path=`pwd`
results_dir=$path'/results'
now=$(date +'%Y''%m''%d'_'%H''%M''%S')    #getcurrent date and time
if [[ ! -e $results_dir ]]; then
    mkdir $results_dir
    #echo "$results_dir directory is created" 1>&2
elif [[ ! -d $results_dir ]]; then
    echo "$results_dir already exists but is not a directory" 1>&2
fi
# create sim_directory
sim_dir='sim_'$now
#echo "$results_dir'/'$sim_dir"
if [[ ! -e $results_dir'/'$sim_dir ]]; then
    mkdir $results_dir'/'$sim_dir
    #echo "$results_dir'/'$sim_dir directory is created" 1>&2
elif [[ ! -d $results_dir'/'$sim_dir ]]; then
    echo "$results_dir'/'$sim_dir already exists but is not a directory" 1>&2
fi
echo "Sim ID : $now"


nodes=(`seq 100 100 1600`)		  #number of nodes to simulate
avgsend=1000000						      #average sending interval in ms
experiment=1 						        #simulation radio settings 0 --> SF12 - BW125 - CR4/8
simdays=1
simtime=$((simdays*24*60*60*1000))	#total running time in ms
scenario=(`seq 0 2`)
Nr=1                             # Number of realization
progress=0
echo ===========================================================
for s in ${scenario[@]}
do

  for node in ${nodes[@]}
  do
    for i in `seq 1 $Nr`
    do
      progress=$(( progress + 1))
      echo Simulation : Scenario $s - Nodes: $node - Sim: $i --- $((progress*100/((Nr*${#nodes[@]})*${#scenario[@]})))%
      echo -----------------------------------------------------------
      python loraDir.py $node $avgsend $experiment $simtime $s $sim_dir
    done
  done
done
echo ===========================================================
echo Plot figures and save it to figures directory
python plot_figures.py $sim_dir $Nr
echo ===========================================================
#echo "${nodes[-1]}"
