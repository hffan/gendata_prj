#!/usr/bin/python
# -*- coding: UTF-8 -*-
import platform
import os
from io_stat.iostat import is_executable


real_enviroment=False

if False==real_enviroment:
    rootpath='/home/DQ1044/code/code_prj/'
    iri_rootpath='/home/DQ1044/'
    data_rootpath='/Data/TEST/'
if True==real_enviroment:
    rootpath = '/kjtq_src/code_prj/'
    iri_rootpath='/kjtq/'
    data_rootpath='/kjtq_data/'
    
    


####真实环境节点
# rootpath = '/kjtq_src/code_prj/'
# iri_rootpath='/kjtq/'
# data_rootpath='/kjtq_data/'

####公司节点
# rootpath='/home/DQ1044/code/code_prj/' 
# iri_rootpath='/home/'
# data_rootpath='/Data/TEST/'



# ####直接将配置信息加载到session的环境变量中
# ####config.txt必须为linux格式,如果是windows格式,变量末尾有^M,导致字符串比较失败
# source ./config.txt
# echo $real_enviroment


# ####公司环境
# if [ "$real_enviroment" == "False" ];then
    # rootpath=/home/DQ1044/code/code_prj/
    # iri_rootpath=/home/
    # data_rootpath=/Data/TEST/
    # echo $rootpath
    # echo $iri_rootpath
    # echo $data_rootpath
# fi

# ####真实环境
# if [ "$real_enviroment" == "True" ];then
    # rootpath=/kjtq_src/code_prj/
    # iri_rootpath=/kjtq/
    # data_rootpath=/kjtq_data/
    # echo $rootpath
    # echo $iri_rootpath
    # echo $data_rootpath
# fi




##用户可以根据不同的操作系统，修改如下参数，配置代码存放的根路径,不能使用os.path.join
#print (os.path.dirname(os.path.abspath(__file__)))
current_path = os.path.dirname(os.path.abspath(__file__))


# rootpath = "/home/DQ1044/code_prj/"
# rootpath = "C:\\Users\\Administrator\\Desktop\\DQ1044_centos7.1\\code_prj\\"
# print (rootpath)


##station_txt使用current_path下的station文件夹，保证代码里可以找到station文件夹路径
##iri_inputpath使用/home/DQ1044/code/code_prj/代码路径下的IRI

if ('Linux' == platform.system()):            
    iri_inputpath =  rootpath + '/IRI_2016/input/'
    iri_outputpath = iri_rootpath + '/localplugins/IRI/'
    #iri_outputpath =  rootpath + '/home/DQ1044/localplugins/IRI/'
    Fortran_path =  rootpath + '/IRI_2016/IRI_2016_linux.exe'
    station_txt = current_path + '/station/station_info.txt' 
    ##需要增加exe可执行权限判断，否则拷贝之后没有可执行权限，导致程序调用失败
    is_executable(Fortran_path)

    
configs = { 
            'iri_inputpath':iri_inputpath,
            'iri_outputpath':iri_outputpath,
            'Fortran_path':Fortran_path,
            'station_txt':station_txt,
            'data_rootpath':data_rootpath}
            
print (configs)
