#!/bin/bash

export PROXY_HOME="/home/splunk/redisproxy-server" 
port="5000"        

date_front=`date |awk '{print$1$2$3}'`
log_dir=$PROXY_HOME"/logs"
log_file="flask_"
file_type="log.txt"
log_file_with_date=$log_dir/$log_file$date_front$file_type

if [ ! -f $PROXY_HOME/app.py ];then
    echo "[Warning] You have to change this script with your setting!"
else
    source $PROXY_HOME/bin/activate
    if [ ! -d $log_dir ];then
        mkdir $log_dir
        echo "[INFO] Success to make dir : logs" >> $log_file_with_date
    fi
    echo "#####################################" >> $log_file_with_date
    echo "########## Starting now... ##########" >> $log_file_with_date
    echo "#####################################" >> $log_file_with_date
    nohup python $PROXY_HOME/app.py >> $log_file_with_date &
    echo "#########################################################" >> $log_file_with_date
    echo "Success to start! You can check logs in ./logs/$log_file" >> $log_file_with_date
    echo "#########################################################" >> $log_file_with_date
    echo "########## Starting now... ##########"
    echo "[INFO] Success to start! You can check logs in ./logs/$log_file"
    echo "[INFO] Please press Enter Key and Do your job."
fi
