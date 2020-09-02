#!/bin/sh

#########################################################
# 1. 查找父进程及其子进程
# 2. 杀掉父进程及其子进程
# 3. 重启进程
#########################################################


####公司环境
# python_path=/root/anaconda3/bin/python
# code_path=/home/DQ1044/code/code_gendata/


####真实环境
# python_path=/kjtq_src/anaconda3/bin/python
# code_path=/kjtq_src/code_gendata/


####直接将配置信息加载到session的环境变量中
####config.txt必须为linux格式,如果是windows格式,变量末尾有^M,导致字符串比较失败
source ./config.txt
echo $real_enviroment


####公司环境
if [ "$real_enviroment" == "False" ];then
    python_path=/root/anaconda3/bin/python
    code_path=/home/DQ1044/code/code_gendata/
    echo $python_path
    echo $code_path
fi

####真实环境
if [ "$real_enviroment" == "True" ];then
    python_path=/kjtq_src/anaconda3/bin/python
    code_path=/kjtq_src/code_gendata/
    echo $python_path
    echo $code_path  
fi




##查找automatically_apsheduler.py任务，杀掉
processname='apscheduler_gendata.py'
program_logname='apscheduler_gendata.log'

##查找automatically_apsheduler.py任务，杀掉
pid=$(ps x | grep $processname | grep -v grep | awk '{print $1}')
echo $pid
echo '根据父进程的pid,查询父进程及其子进程......'


if [ -z $pid ]; then
    echo $processname '没有启动,不需要杀进程.'
else
    echo $processname '有启动,需要杀掉进程.'
    ##杀死父进程及其所有的子进程
    kill -9 `pstree -p $pid | awk -F"[()]" '{for(i=0;i<=NF;i++)if($i~/^[0-9]+$/)print $i}'`  
fi


echo ''
echo '准备启动进程' $processname


####启动automatically_apsheduler.py任务
#cd /kjtq_src/code_gendata; nohup python -u $processname >$program_logname 2>&1 &
cd $code_path; nohup $python_path -u $processname >$program_logname 2>&1 &
ps -ef |grep $processname

