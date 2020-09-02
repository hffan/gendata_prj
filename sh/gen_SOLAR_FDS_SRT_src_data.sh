#!/bin/bash
##########################################################
#1. 根据喀什站的数据,产生HEBJ站的样例数据
##########################################################


####公司节点
#code_path=/home/DQ1044/code/code_gendata/

####真实环境
#code_path=/kjtq_src/code_gendata/


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





mkdir -p $code_path/gen_SOLAR_FDS_SRT/202006/20200617/HEBJ
echo 'mkdir ...'

cp -rp $code_path/gen_SOLAR_FDS_SRT/202006/20200617/KSZJ/* $code_path/gen_SOLAR_FDS_SRT/202006/20200617/HEBJ/
echo 'cp ...'

find $code_path/gen_SOLAR_FDS_SRT/202006/20200617/HEBJ/ -name '*KSZJ*' | xargs -i echo mv \"{}\" \"{}\" | sed 's/KSZJ/HEBJ/2g' | sh
echo 'find ...'



