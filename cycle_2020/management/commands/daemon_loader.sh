#!/bin/bash
#https://ss64.com/bash/nohup.html
logdir=~/launch
mkdir -p ${logdir}
logfilename="${2#*/}_$(date +%F_%H:%M:%S,%N)"
echo $logfilename
echo "== LAUNCH $@ ==" > ~/launch/${logfilename}_stdout.log
echo "== LAUNCH $@ ==" > ~/launch/${logfilename}_stderr.log
#nohup "$@" | tee -a -i ${logdir}/${logfilename}_stdout.log 2>>${logdir}/${logfilename}_stderr.log &
nohup "$@" 1> >(tee -a -i ${logdir}/${logfilename}_stdout.log) 2> >(tee -a -i ${logdir}/${logfilename}_stderr.log) &
