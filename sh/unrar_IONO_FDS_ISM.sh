#!/bin/bash
##########################################################
#1. 遍历目录解压rar文件,要求带全路径解压
##########################################################

#unrar_path=/kjtq_data/FDS/iono/ISM/      ##真实环境路径
#unrar_path=/Data/TEST/FDS/iono/ISM/      ##公司环境路径




####直接将配置信息加载到session的环境变量中
####config.txt必须为linux格式,如果是windows格式,变量末尾有^M,导致字符串比较失败
source ../config.txt
echo $real_enviroment


####公司环境
if [ "$real_enviroment" == "False" ];then
    unrar_path=/Data/TEST/FDS/iono/ISM/
    echo $unrar_path
fi


####真实环境
if [ "$real_enviroment" == "True" ];then
    unrar_path=/kjtq_data/FDS/iono/ISM/
    echo $unrar_path
fi



for rarfile in `cd $unrar_path;ls *.rar`;
do
    echo $rarfile
    pwd
    cd $unrar_path
    pwd
    ##解压
    unrar x -o+ $rarfile
    ##删除rar文件
    rm -rf $rarfile
    ##开启权限
    #chmod 777 $rarfile
    
    ##解压文件夹名称    
    filename=`basename $rarfile .rar`
    ##查找L2,替换为L1
    
    #find /kjtq_data/FDS/iono/ISM/$filename -name '*L2*' | xargs -i echo mv \"{}\" \"{}\" | sed 's/L2/L1/2g' | sh
    find $unrar_path$filename -name '*L2*' | xargs -i echo mv \"{}\" \"{}\" | sed 's/L2/L1/2g' | sh
    
done



