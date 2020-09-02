#!/bin/bash
##########################################################
#1. 生成特定时间的CMA,SRT数据
##########################################################


####公司环境
# python_path=/root/anaconda3/bin/python
# code_path=/home/DQ1044/code/code_gendata/


####真实环境
# python_path=/kjtq_src/anaconda3/bin/python
# code_path=/kjtq_src/code_gendata/


####直接将配置信息加载到session的环境变量中
####config.txt必须为linux格式,如果是windows格式,变量末尾有^M,导致字符串比较失败
source ../config.txt
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



####方法1：
# $python_path $code_path/apscheduler_gendata.py 20200401
# $python_path $code_path/apscheduler_gendata.py 20200402
# $python_path $code_path/apscheduler_gendata.py 20200403
# $python_path $code_path/apscheduler_gendata.py 20200404
# $python_path $code_path/apscheduler_gendata.py 20200405
# $python_path $code_path/apscheduler_gendata.py 20200406
# $python_path $code_path/apscheduler_gendata.py 20200407
# $python_path $code_path/apscheduler_gendata.py 20200408
# $python_path $code_path/apscheduler_gendata.py 20200409
# $python_path $code_path/apscheduler_gendata.py 20200410
# $python_path $code_path/apscheduler_gendata.py 20200411
# $python_path $code_path/apscheduler_gendata.py 20200412
# $python_path $code_path/apscheduler_gendata.py 20200413
# $python_path $code_path/apscheduler_gendata.py 20200414
# $python_path $code_path/apscheduler_gendata.py 20200415


####方法2：
startdate=20200401
enddate=20200415
while [[ $startdate -le $enddate ]]
do
echo ${startdate} 
$python_path $code_path/apscheduler_gendata.py $startdate
####日期加1天
startdate=`date -d "+1 day $startdate" +%Y%m%d`
done 





