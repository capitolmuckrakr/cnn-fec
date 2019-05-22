#!/bin/bash
logdir=~/launch
mkdir -p ${logdir}
logfilename="${2#*/}_$(date +%F_%H:%M:%S,%N)"
echo $logfilename
echo "== LAUNCH $@ ==" > ~/launch/${logfilename}_stdout.log
echo "== LAUNCH $@ ==" > ~/launch/${logfilename}_stderr.log
nohup "$@" >>${logdir}/${logfilename}_stdout.log 2>>${logdir}/${logfilename}_stderr.log &
