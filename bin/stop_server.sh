#!/bin/bash

export PROXY_HOME="/home/splunk/redisproxy-server" 

date_front=`date |awk '{print$1$2$3}'`
log_dir=$PROXY_HOME"/logs"
log_file="flask_"
file_type="log.txt"
log_file_with_date=$log_dir/$log_file$date_front$file_type


echo "###############" >> $log_file_with_date
echo "Stopping now..." >> $log_file_with_date
echo "###############" >> $log_file_with_date
echo "[INFO] Stopping now..."

arr_stop_target_list_full_info=$(ps -ef |grep "$PROXY_HOME/app.py" |grep -v "grep $PROXY_HOME/app.py")
arr_stop_target_list=$(ps -ef |grep "$PROXY_HOME/app.py" |grep -v "grep $PROXY_HOME/app.py" |awk '{print $2}')
for target_stop in ${arr_stop_target_list};do
    kill -9 $target_stop
done

echo "###############" >> $log_file_with_date
echo "Success to stop" >> $log_file_with_date
echo "###############" >> $log_file_with_date
echo "[INFO] Success to stop!"
