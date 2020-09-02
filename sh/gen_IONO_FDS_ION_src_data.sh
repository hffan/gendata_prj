#!/bin/bash
##########################################################
#1. 根据三亚站的数据,产生其它4个站的样例数据
##########################################################



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




# mkdir -p /kjtq_src/code_gendata/gen_IONO_FDS_ION/2019/20191115/KSZJ
# mkdir -p /kjtq_src/code_gendata/gen_IONO_FDS_ION/2019/20191115/HEBJ
# mkdir -p /kjtq_src/code_gendata/gen_IONO_FDS_ION/2019/20191115/GYZJ
# mkdir -p /kjtq_src/code_gendata/gen_IONO_FDS_ION/2019/20191115/BJZJ
# echo 'mkdir ...'

# cp -rp /kjtq_src/code_gendata/gen_IONO_FDS_ION/2019/20191115/SYZJ/* /kjtq_src/code_gendata/gen_IONO_FDS_ION/2019/20191115/KSZJ/
# cp -rp /kjtq_src/code_gendata/gen_IONO_FDS_ION/2019/20191115/SYZJ/* /kjtq_src/code_gendata/gen_IONO_FDS_ION/2019/20191115/HEBJ/
# cp -rp /kjtq_src/code_gendata/gen_IONO_FDS_ION/2019/20191115/SYZJ/* /kjtq_src/code_gendata/gen_IONO_FDS_ION/2019/20191115/GYZJ/
# cp -rp /kjtq_src/code_gendata/gen_IONO_FDS_ION/2019/20191115/SYZJ/* /kjtq_src/code_gendata/gen_IONO_FDS_ION/2019/20191115/BJZJ/
# echo 'cp ...'


# find /kjtq_src/code_gendata/gen_IONO_FDS_ION/2019/20191115/KSZJ/ -name '*SYZJ*' | xargs -i echo mv \"{}\" \"{}\" | sed 's/SYZJ/KSZJ/2g' | sh
# find /kjtq_src/code_gendata/gen_IONO_FDS_ION/2019/20191115/HEBJ/ -name '*SYZJ*' | xargs -i echo mv \"{}\" \"{}\" | sed 's/SYZJ/HEBJ/2g' | sh
# find /kjtq_src/code_gendata/gen_IONO_FDS_ION/2019/20191115/GYZJ/ -name '*SYZJ*' | xargs -i echo mv \"{}\" \"{}\" | sed 's/SYZJ/GYZJ/2g' | sh
# find /kjtq_src/code_gendata/gen_IONO_FDS_ION/2019/20191115/BJZJ/ -name '*SYZJ*' | xargs -i echo mv \"{}\" \"{}\" | sed 's/SYZJ/BJZJ/2g' | sh
# echo 'find ...'



mkdir -p $code_path/gen_IONO_FDS_ION/2019/20191115/KSZJ
mkdir -p $code_path/gen_IONO_FDS_ION/2019/20191115/HEBJ
mkdir -p $code_path/gen_IONO_FDS_ION/2019/20191115/GYZJ
mkdir -p $code_path/gen_IONO_FDS_ION/2019/20191115/BJZJ
echo 'mkdir ...'

cp -rp /$code_path/gen_IONO_FDS_ION/2019/20191115/SYZJ/* /$code_path/gen_IONO_FDS_ION/2019/20191115/KSZJ/
cp -rp /$code_path/gen_IONO_FDS_ION/2019/20191115/SYZJ/* /$code_path/gen_IONO_FDS_ION/2019/20191115/HEBJ/
cp -rp /$code_path/gen_IONO_FDS_ION/2019/20191115/SYZJ/* /$code_path/gen_IONO_FDS_ION/2019/20191115/GYZJ/
cp -rp /$code_path/gen_IONO_FDS_ION/2019/20191115/SYZJ/* /$code_path/gen_IONO_FDS_ION/2019/20191115/BJZJ/
echo 'cp ...'

find /$code_path/gen_IONO_FDS_ION/2019/20191115/KSZJ/ -name '*SYZJ*' | xargs -i echo mv \"{}\" \"{}\" | sed 's/SYZJ/KSZJ/2g' | sh
find /$code_path/gen_IONO_FDS_ION/2019/20191115/HEBJ/ -name '*SYZJ*' | xargs -i echo mv \"{}\" \"{}\" | sed 's/SYZJ/HEBJ/2g' | sh
find /$code_path/gen_IONO_FDS_ION/2019/20191115/GYZJ/ -name '*SYZJ*' | xargs -i echo mv \"{}\" \"{}\" | sed 's/SYZJ/GYZJ/2g' | sh
find /$code_path/gen_IONO_FDS_ION/2019/20191115/BJZJ/ -name '*SYZJ*' | xargs -i echo mv \"{}\" \"{}\" | sed 's/SYZJ/BJZJ/2g' | sh
echo 'find ...'



