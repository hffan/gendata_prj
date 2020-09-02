#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@info:
1. nohup linux后台启动此脚本
2. crontab里添加守护进程脚本，daemon.sh，判断此脚本是否被杀，被杀直接启动
3. crontab里添加守护进程脚本，daemon.sh，保证系统中只有1个生产脚本在启动
4. nohup python -u /home/DQ1044/code/code_gendata/apscheduler_gendata.py >/home/DQ1044/code/code_gendata/debug.log 2>&1 &
5. 输出重定向，可以查看py文件是否执行的日志，也可以查看py文件否具有可执行权限
6. 查找进程， ps -ef|grep main_v12.py
7. 杀进程，kill -9 PID




@modify history:
2020-04-04 19:26:50     1. 修改任务里的despath，需要替换成任务启动时刻的日期
2020-04-07 08:45:52     1. 解决FDS\solar\SRT\数据，文件名时间和文件创建时间不匹配问题
2020-04-07 09:15:59     1. 解决CMA\solar\SRT\数据，文件名时间和文件创建时间不匹配问题
2020-04-15 21:27:19     1. station_info,station_infos里乌鲁木齐站匹配产品生产，将WLZ更改成WLM
2020-04-21 14:23:25     1. apscheduler.log日志，生成到按天命名的文件夹里
2020-04-21 14:25:29     1. 每天晚上12点，启动清理4天前的数据，包括/DATA/TEST/目录和/home/DQ1044/localdatafiles,72小时的文件分散到文件夹中
2020-04-21 17:11:49     1. 每天22点，开始生产下1天的前72小时，IRI数据,放到上午10点启动，cpu使用率太高，任务太多
2020-04-22 09:29:32     1. /home/DQ1044/localdatafiles，每个节点都有，如何用程序去各个节点清理
2020-04-22 11:24:54     1. 修改FDS，ISM，station站信息获取，统一调整为station文件夹下的station_info.txt文件中获取
2020-04-23 09:35:21     1. IRI数据生产，修改添加参数yyyymmddhh的定义和赋值
2020-04-23 10:42:08     1. scheduler._logger，目前只支持写入任务启动时间的文件夹里，不具备根据当前日志动态创建文件夹的功能
2020-04-24 09:23:37     1. 解决gen_IRI函数，在for循环里递归修改iri路径的bug  
2020-04-24 10:04:47     1. gen_FDS_ATMOS_CMA_UPAR/202003/20200331/MIXT/UPAR_CHN_MUL_FTM-2020033100.txt 文件名更改UPAR_CHN_MUL_FTM_2020033100.txt
2020-04-27 10:36:23     1. apsheduler.log日志路径变更，导致mail邮箱接收不到当前路径下的apsheduler.log日志文件
2020-05-19 11:27:49     1. 数据生产按系统时间生产，目前系统时间按UTC+8，真实环境，系统时间更改为UTC+0即可
2020-05-21 09:09:18     1. 增加，每天凌晨0点清理solar太阳的数据
2020-06-15 11:09:53     1. 电离层CET,FDS测试数据产品路径调整，参考如下路径结构XXXJ_ISM/YYYYMM/YYYYMMDD，22所CET站编码M,地基FDS站编码J
                           XXXM_ION
                           XXXM_ISM
                           XXXJ_ION
                           XXXJ_ISM
                        2. 版本号1.0.0.20200615_alpha
2020-06-15 17:04:01
                        1. 目标文件夹，剔除最后的台站文件夹
                        
2020-06-17 17:05:35
                        1. ISM数据,暂停任务,/Data/TEST/FDS/iono/ISM路径下入库真实数据
2020-06-18 14:58:40
                        1. 临时关停,IRI清理数据功能, /home/DQ1044/localplugins/IRI路径下的IRI数据,不清理,20200501-20200510真实数据IRI保留
                        2. 更改main.py为apscheduler_gendata,main.py和其它业务重名,导致杀进程失败
2020-07-21 16:53:43
                        1. 更新数据生产代码,gen_SOLAR_FDS_SRT_oncetime

                        
                        
                        
                        
                        
"""


import os
import glob
import shutil
import sys
sys.path.append('..')
import logging
import re
import platform
import calendar
import datetime
import time
import traceback
import shutil
from cfg import *


from apscheduler.schedulers.background import BackgroundScheduler#非阻塞方式
from apscheduler.schedulers.blocking import BlockingScheduler#阻塞方式
from apscheduler.events import (EVENT_JOB_EXECUTED,EVENT_JOB_ERROR)
from apscheduler.triggers.cron import CronTrigger#制定触发器


import station.station_info
#import station.station_infos
import gen_IONO_FDS_ISM.gen_FDS_ISM
import gen_SOLAR_CMA_SRT.gen_CMA_SRT
import gen_SOLAR_FDS_SRT.gen_FDS_SRT
import gen_IONO_CET_ISM.read_CET_ISM_TEC
import gen_IONO_CET_ISM.read_CET_ISM_SintL
import gen_IONO_CET_ISM.read_CET_ISM_SintU
import gen_IONO_CET_ION.read_CET_ION_fmin
import gen_IONO_CET_ION.read_CET_ION_foF2
import IONO.FDS.ISM.read_FDS_ISM_TEC_krig


def gen_IRI(set_yyyymmdd):
    """
    1. 提前生产下1天的数据，比如20200421，生产20200422日期的IRI
    2. 提前生产1个月，1天24个，1个40秒，1天需要16分钟的生产时间
    3. 生产1个月IRI，需要30*16 = 8小时
    4. 每个晚上22：00：00开始，生产第2天的IRI数据,22点没有太阳的数据，系统压力小
    5. 每天晚上22点，开始生产下1天的前72小时的IRI网格数据，比如2020-04-21 22：00：00 生产2020-04-22 00：00：00 的前72小时的IRI网格数据
    6. 1天16分钟，72小时，3天，3*16=48分钟，22点开始，到23点基本生产完毕
    7. 如果22点开始生产IRI网格数据，刚好产品生产也生产前1小时的IRI网格，有没有冲突，需要做测试看看
    
    
    """
    #today_yyyymmddHHMMSS = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    #tomorrow_yyyymmdd =  (datetime.datetime.now() + datetime.timedelta(days=-expire_day)).strftime('%Y%m%d')
    #yyyymm = tomorrow_yyyymmdd[0:6]
    #yyyymmdd = tomorrow_yyyymmdd[0:8]
    
    ##调用fortran程序，产生iri的网格数据
    iri_inputpath = configs['iri_inputpath']
    #iri_outputrootpath = configs['outputfilepath']
    Fortran_path = configs['Fortran_path']
    ##cmd拼接fortran调用命令，第1个参数年月日小时，第2个参数输出网格数据文件的路径
    ##10s之内产生，TEC地基，22所，共用iri格点数据，是否需要先判断是否存在
    ##根据iri_rootpath创建YYYYMM/YYYYMMDD的文件夹
    ##路径末尾拼接空字符串，或多\\或者/，避免fortran里拼接路径丢失/或者\\
    
    ##方案2，IRI网格数据放到共享目录，提前生产下1天的数据，比如20200421，生产20200422日期的IRI
    iri_rootpath = configs['iri_outputpath']
    
    
    ##导入iri模型背景数据
    ##根据指定的目录结构规则搜索TEC当前小时对应的17个台站的数据
    ##增加iri文件判断，如果存在，直接跳过，不用生产
    ##00-23小时
    #today_yyyymmddHHMMSS = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    #today_yyyymmdd      = datetime.datetime.now().strftime('%Y%m%d') 
    #tomorrow_yyyymmdd   = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y%m%d')
        
    for hour in range(72):
        hour_step = hour + 1#1-72
        yyyymmddHH_72h =  (datetime.datetime.strptime(set_yyyymmdd,'%Y%m%d') + datetime.timedelta(hours=-hour_step)).strftime('%Y%m%d%H')
        # print (yyyymmddHH_72h)
        # input()
        
        year    =   yyyymmddHH_72h[0:4]
        month   =   yyyymmddHH_72h[4:6]
        day     =   yyyymmddHH_72h[6:8]
        hour    =   yyyymmddHH_72h[8:10]
        yyyymm  = yyyymmddHH_72h[0:6]
        yyyymmdd= yyyymmddHH_72h[0:8]
        yyyymmddhh= yyyymmddHH_72h[0:10]
        
        iri_outputpath = os.path.join(iri_rootpath,yyyymm,yyyymmdd,'')#拼接年月，年月日文件夹,''保证路径最后保留斜杠        
        #iri_outputpath = os.path.join(iri_outputpath,yyyymm,yyyymmdd,'')#拼接年月，年月日文件夹,''保证路径最后保留斜杠
        ####需要判断，存在不需要创建，否则报错
        if not os.path.exists(iri_outputpath):
            print('%s do not exist ' % iri_outputpath)
            print('makedirs...')
            os.makedirs(iri_outputpath)
        else:
            pass
        
        iri_fullpath = IONO.FDS.ISM.read_FDS_ISM_TEC_krig.get_iri_fullpath(iri_outputpath, int(year), int(month), int(day), int(hour))
        if ('Windows' == platform.system()):
            filesize = 132130
        if ('Linux' == platform.system()):
            filesize = 131949

        ####路径不存在，或者文件大小有误，需要重新生产
        if not os.path.exists(iri_fullpath) or os.path.getsize(iri_fullpath) < filesize:
            ##如果IRI文件不存在或者IRI文件里得网格不完整，需要重新生产IRI文件
            CMD = Fortran_path + ' ' + yyyymmddhh + ' ' + iri_inputpath + ' ' + iri_outputpath
            print(CMD)
            try:
                # pass
                status = os.system(CMD)
                print("os.system status is %d " % status)
            except Exception as e:
                raise e    
    
    return
    
    
def clean_dirs(srcpath,expire_day):
    """
    1. 不能按文件夹日期比较，按文件的日期比较，因为前72小时的文件在文件夹里
    2. 可以定时删除，删除的时间点，定00：00：00，比如2020-04-22 00：00：00 ，前4天的时间2020-04-18 00：00：00
    3. 删除年月日文件夹，遍历比较即可，然后os.walk，删除年月日文件夹
   
    """
    current_yyyymmdd = datetime.datetime.now().strftime('%Y%m%d')
    expire_yyyymmdd =  (datetime.datetime.now() + datetime.timedelta(days=-expire_day)).strftime('%Y%m%d')
    
    ##遍历文件夹
    for root, dirs, files in os.walk(srcpath):
        #print (root,dirs)
        for dir in dirs:
            ##空文件夹，自动跳出
            ##以下判断有bug,比如*/202004/20200421,202004目录小于20200421，所以会把202004目录下所有的文件夹都删除
            ##字符串按位比较，两个字符串第一位字符的ascii码谁大，字符串就大，不再比较后面的
            ##增加过滤，筛选文件夹
            ##文件夹是数字，文件夹长度为8，文件夹日期小于过期日期
            if (dir.isdigit()) and (8==len(dir)) and (dir <= expire_yyyymmdd ):   
            #if (dir <= expire_yyyymmdd ):
                print ('删除', root,dir)
                shutil.rmtree(os.path.join(root, dir))

    return
    
        
def send_mail_file(mailbox='like19910306@163.com',path=os.path.dirname(os.path.abspath(__file__))):
    """发送apscheduler日志和程序日志到指定邮箱"""
    sys_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    debug_log = os.path.join(path,'debug.log')
    apscheduler_log = os.path.join(path,'apscheduler.log')
    
    cmd_debug = 'mail -s "%s %s" %s< %s'%(sys_time,' debug_log',mailbox,debug_log)
    cmd_apscheduler = 'mail -s "%s %s" %s < %s'%(sys_time,' apscheduler_log',mailbox,apscheduler_log)
    print (cmd_debug)
    print (cmd_apscheduler)
    os.system(cmd_debug)
    os.system(cmd_apscheduler)

    
def send_mail_segment(mailbox='like19910306@163.com',path=os.path.dirname(os.path.abspath(__file__))):
    """
    1.发送apscheduler日志和程序日志到指定邮箱
    2.默认推送定时任务日志的最后500行
    """
    sys_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    debug_log = os.path.join(path,'debug.log')
    apscheduler_log = os.path.join(path,'apscheduler.log')
    
    #cmd_debug = 'tail -n 5 %s | mail -s "%s %s" %s'%(debug_log,sys_time,' debug_log',mailbox)
    cmd_apscheduler = 'tail -n 500 %s |mail -s "%s %s" %s'%(apscheduler_log,sys_time,' apscheduler_log',mailbox)
    #print (cmd_debug)
    print (cmd_apscheduler)
    #os.system(cmd_debug)
    os.system(cmd_apscheduler)

    
def listener(event):
    if event.exception:
        print ('The job crashed :(')
    else:
        print ('The job worked :)')
     

##创建多级目录
def mkdirs(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    else:
        pass
    return


def displayInterpeter():
    import sys
    print(sys.executable)


def displayEncode():
    import sys
    print(sys.getdefaultencoding())


def encoding(s):
    return s.encode('gbk')


def decoding(s):
    return s.decode('gbk')


def getDirSize(dir):
    size = 0
    for root, dirs, files in os.walk(dir):
        size += sum([os.path.getsize(os.path.join(root, name)) for name in files])
    return size


##转换成人类可读的size
def humanReadableSize(size):
    B = 1
    KB = B * 1024
    MB = KB * 1024
    GB = MB * 1024
    TB = GB * 1024
    PB = TB * 1024
    if (size >= PB):
        # return "%.2fTB" % float(size / PB)
        return "%.2fPB" % float(size / PB)
    if (size >= TB):
        return "%.2fTB" % float(size / TB)
    if (size >= GB):
        return "%.2fGB" % float(size / GB)
    if (size >= MB):
        return "%.2fMB" % float(size / MB)
    if (size >= KB):
        return "%.2fKB" % float(size / KB)
    if (size < KB):
        return "%.2fB" % float(size / B)


##统计目录结构，L1,L2级目录占用空间大小
def statics(DATARootPath):
    staticsINFO = []
    for L1dir in os.listdir(DATARootPath):
        # print (DATARootPath)
        L1dirpath = os.path.join(DATARootPath, L1dir)

        ##判断第1级是否为文件夹，不是文件夹跳过
        if os.path.isdir(L1dirpath):
            L1size = 0  ##每次清空
            humanSize = 0
            # print (L1dir)
            L1size = getDirSize(L1dirpath)
            humanSize = humanReadableSize(L1size)
            # print ('%s %s' % (L1dir, humanSize))
            staticsINFO.append(('%s %s' % (L1dir, humanSize)))
            ##判断第2级是否为文件夹，不是文件夹跳过
            for L2dir in os.listdir(L1dirpath):
                L2dirpath = os.path.join(L1dirpath, L2dir)
                ##判断第1级是否为文件夹
                # print (L2dir)
                # print (L1dirpath)
                if os.path.isdir(L2dirpath):
                    L2size = 0  ##每次清空
                    humanSize = 0
                    # print (L2dir)
                    L2size = getDirSize(L2dirpath)
                    humanSize = humanReadableSize(L2size)
                    # print ('%s %s' % (L2dir, humanSize))
                    staticsINFO.append(('%s %s' % (L1dir + L2dir, humanSize)))
                ##如果不是，跳过
                else:
                    continue
        else:
            continue
    # return str(staticsINFO)
    return '   '.join(staticsINFO)  ##把list统一转换成字符串
    
    
def debug_log(logpath, infos):
    ##先创建日志目标文件夹
    #mkdirs(logpath)
    sys_time = datetime.datetime.now().strftime('%Y-%m-%d')
    logpath = os.path.join(logpath,'log',sys_time)
    if not os.path.exists(logpath):
        os.makedirs(logpath)
    logname=os.path.join(logpath,'debug.log')
    
    #logname = logpath + '/debug.log'
    logging.basicConfig(level=logging.INFO,
                        filename=logname,
                        filemode='a',
                        format='%(asctime)s %(message)s',  ##''里的[]是信息输出，加的'[%(asctime)s %(message)s]'可以去掉
                        datefmt='%Y-%m-%d %H:%M:%S'  ##默认输出格式带毫秒'%Y-%m-%d %H:%M:%S%p'
                        )
    logging.info(infos)  ##输出info内容到log文件
    
    
def log_setting(logpath=os.path.dirname(os.path.abspath(__file__))):
    ##先创建日志目标文件夹
    #mkdirs(logpath)
    ##增加log目录，log目录里，增加日期命名文件
    
    #logname = os.path.join(logpath,'log','apscheduler.log')
    sys_time = datetime.datetime.now().strftime('%Y-%m-%d')
    logpath = os.path.join(logpath,'log',sys_time)
    if not os.path.exists(logpath):
        os.makedirs(logpath)
    logname=os.path.join(logpath,'apscheduler.log')
        
    #logname = os.path.join(logpath,'apscheduler.log')
    logging.basicConfig(level=logging.INFO,
                        filename=logname,
                        filemode='a',
                        format='%(asctime)s %(message)s',  ##''里的[]是信息输出，加的'[%(asctime)s %(message)s]'可以去掉
                        datefmt='%Y-%m-%d %H:%M:%S'  ##默认输出格式带毫秒'%Y-%m-%d %H:%M:%S%p'
                        )
    
    return logging
    
    
##对命令行手动输入的日期，进行校验
def check_yyyymmdd(yyyymmdd):
    ##1.判断是否是yyyymmdd,8位格式
    if len(yyyymmdd) != 8:
        exit('请输入正确的年月日，格式yyyymmdd,例如20200313 ')

    ##2.判断输入的年，月，日是否符合格式，比如20201359，13月不存在，59天不存在，比如20210230，2月份不存在30天
    yyyy = int(yyyymmdd[0:4])
    mm = int(yyyymmdd[4:6])
    dd = int(yyyymmdd[6:8])
    try:
        datetime.date(yyyy, mm, dd)
        return True
    except Exception as e:
        # exit('日期不存在,输入正确的年，月，日 %s'% e)
        exit('%s 日期不存在, 请输入正确的年月日.' % e)
    # return False


def search_date_yyyymmddHHMM(s):
    # 2017-11-24 01-05-00
    # pattern=re.search(r"\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}-\d{1,2}-\d{1,2}",s)
    pattern = re.findall(r"_\d{4}\d{1,2}\d{1,2}\d{1,2}\d{1,2}", s)
    # print(pattern)
    return pattern


def search_date_yyyymmddHH(s):
    # 2017-11-24 01-05-00
    # pattern=re.search(r"\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}-\d{1,2}-\d{1,2}",s)
    pattern = re.findall(r"_\d{4}\d{1,2}\d{1,2}\d{1,2}", s)
    # print(pattern)
    return pattern


def search_date_yyyymmdd(s):
    # 2017-11-24 01-05-00
    # pattern=re.search(r"\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}-\d{1,2}-\d{1,2}",s)
    pattern = re.findall(r"_\d{4}\d{1,2}\d{1,2}", s)
    # print(pattern)
    return pattern


def search_pathdate_yyyymmdd(s):
    # 2017-11-24 01-05-00
    # pattern=re.search(r"\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}-\d{1,2}-\d{1,2}",s)
    pattern = re.findall(r"\d{4}\d{1,2}\d{1,2}", s)
    # print(pattern)
    return pattern
    
    
def search_pathdate_yyyymm(s):
    # 2017-11-24 01-05-00
    # pattern=re.search(r"\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}-\d{1,2}-\d{1,2}",s)
    pattern = re.findall(r"\d{4}\d{1,2}", s)
    # print(pattern)
    return pattern


def example3(set_times, current_path, rootpaths):
    # ####产生数据日期设定，用户可以设置，时间精确到年月日
    # set_time = '20200309'
    # ####根目录设置
    # rootpath = 'C:\\Users\\Administrator\\Desktop\\test\\dataaaaa\\'

    ####产生数据日期设定，用户可以设置，时间精确到年月日
    set_time = set_times
    ####设置替换时间的匹配表达式
    repace_yyyymmdd = '_' + set_times

    ####根目录设置
    rootpath = rootpaths

    yyyy = set_times[0:4]
    yyyymm = set_times[0:6]
    yyyymmdd = set_times[0:8]
    ####产品路径，统一由yyyy调整为yyyymm

    if ('Windows' == platform.system()):
        ####根据src路径下的样本数据，来产生设定日期的1天的数据 ,样例数据在当前路径下
        srcpathA = current_path + '\\gen_IONO_CET_ION\\2019\\20190716\\'  ##1小时的样本数据
        srcpathB = current_path + '\\gen_IONO_CET_ISM\\2019\\20190716\\'  ##1小时的样本数据
        srcpathC = current_path + '\\gen_IONO_FDS_ION\\2019\\20191115\\'  ##24小时的样本数据
        srcpathD = current_path + '\\gen_IONO_FDS_ISM\\202001\\20200101\\CDZJ\\CDZJ_ISM01_DBD_L11_01H_20200101000000.txt'  ##24小时的样本数据
        srcpathE = current_path + '\\gen_SOLAR_FDS_SOT\\201910\\20191012\\'
        srcpathF = current_path + '\\gen_SOLAR_CMA_SRT\\201803\\20180328\\SDZM\\YJGC_SDWH_TYSD_20180328_061601_L0_0000_01S.txt'
        srcpathG = current_path + '\\gen_SOLAR_FDS_SRT\\201912\\20191201\\'

        srcpath5 = rootpath + '\\Data\\TEST\\FDS\\geomag\\FGM\\2020\\20200306\\'    ##24小时的样本数据
        srcpath6 = rootpath + '\\Data\\TEST\\FDS\\atmos\\MET\\2020\\20200306\\'     ##24小时的样本数据
        srcpath7 = rootpath + '\\Data\\TEST\\FDS\\atmos\\MST\\2020\\20200306\\'     ##24小时的样本数据

        ####目标路径
        despathA = rootpath + '\\Data\\TEST\\CET\\iono\\ION\\' + yyyymm + '\\' + yyyymmdd + '\\'  ##1小时的样本数据
        despathB = rootpath + '\\Data\\TEST\\CET\\iono\\ISM\\' + yyyymm + '\\' + yyyymmdd + '\\'  ##1小时的样本数据
        despathC = rootpath + '\\Data\\TEST\\FDS\\iono\\ION\\' + yyyymm + '\\' + yyyymmdd + '\\'  ##24小时的样本数据
        despathD = rootpath + '\\Data\\TEST\\FDS\\iono\\ISM\\' + yyyymm + '\\' + yyyymmdd + '\\'  ##24小时的样本数据
        despathE = rootpath + '\\Data\\TEST\\FDS\\solar\\SOT\\' + yyyymm + '\\' + yyyymmdd + '\\'  ##1小时的样本数据
        despathF = rootpath + '\\Data\\TEST\\CMA\\solar\\SRT\\' + yyyymm + '\\' + yyyymmdd + '\\'  ##1小时的样本数据
        despathG = rootpath + '\\Data\\TEST\\FDS\\solar\\SRT\\' + yyyymm + '\\' + yyyymmdd + '\\'  ##1小时的样本数据

        despath5 = rootpath + '\\Data\\TEST\\FDS\\geomag\\FGM\\' + yyyymm + '\\' + yyyymmdd + '\\'  ##24小时的样本数据
        despath6 = rootpath + '\\Data\\TEST\\FDS\\atmos\\MET\\' + yyyymm + '\\' + yyyymmdd + '\\'  ##24小时的样本数据
        despath7 = rootpath + '\\Data\\TEST\\FDS\\atmos\\MST\\' + yyyymm + '\\' + yyyymmdd + '\\'  ##24小时的样本数据

    if ('Linux' == platform.system()):
        ####根据src路径下的样本数据，来产生设定日期的1天的数据,样例数据在当前路径下
        srcpathC = current_path + '/gen_IONO_FDS_ION/2019/20191115/'        ##24小时的样本数据
        srcpathD = current_path + '/gen_IONO_FDS_ISM/202001/20200101/CDZJ/CDZJ_ISM01_DBD_L11_01H_20200101000000.txt'  ##24小时的样本数据
        srcpathE = current_path + '/gen_SOLAR_FDS_SOT/201910/20191012/'     ##24小时的样本数据
        srcpathF = current_path + '/gen_SOLAR_CMA_SRT/202006/20200617/'
        #srcpathG = current_path + '/gen_SOLAR_FDS_SRT/201912/20191201/'
        srcpathG = current_path + '/gen_SOLAR_FDS_SRT/202006/20200617/'

        srcpath1 = current_path + '/gen_FDS_ATMOS_AFD_UPAR/202004/20200401/'     ##24小时的样本数据
        srcpath2 = current_path + '/gen_FDS_ATMOS_CMA_UPAR/202003/20200331/'     ##12小时的样本数据
        srcpath3 = current_path + '/gen_FDS_ATMOS_MET/201201/20120101/'          ##1小时的样本数据
        srcpath4 = current_path + '/gen_FDS_ATMOS_MST/202003/20200330/'          ##30分钟的样本数据
        srcpath5 = current_path + '/gen_FDS_GEOMAG_FGM/202003/20200302/'         ##15分钟、3个小时、1天样本数据
        srcpath6 = current_path + '/gen_MDP_ATMOS_LID/201910/20191022/'          ##1天的样本数据
        srcpath7 = current_path + '/gen_MDP_GEOMAG_FGM/201910/20191021/'        ##1天的样本数据

        #despathA = rootpath + '/Data/TEST/CET/iono/ION/XXXM_ION/' + yyyymm + '/' + yyyymmdd + '/'  ##1小时的样本数据
        #despathB = rootpath + '/Data/TEST/CET/iono/ISM/XXXM_ISM/' + yyyymm + '/' + yyyymmdd + '/'  ##1小时的样本数据
        despathC = rootpath + '/kjtq_data/FDS/iono/ION/XXXJ_ION/' + yyyymm + '/' + yyyymmdd + '/'  ##24小时的样本数据
        despathD = rootpath + '/kjtq_data/FDS/iono/ISM/XXXJ_ISM/' + yyyymm + '/' + yyyymmdd + '/'  ##24小时的样本数据
        despathE = rootpath + '/kjtq_data/FDS/solar/SOT/XXXJ_SOT/' + yyyymm + '/' + yyyymmdd + '/'  ##1小时的样本数据
        despathF = rootpath + '/kjtq_data/CMA/solar/SRT/' + yyyymm + '/' + yyyymmdd + '/'  ##1小时的样本数据
        #despathG = rootpath + '/kjtq_data/FDS/solar/SRT/' + yyyymm + '/' + yyyymmdd + '/'  ##1小时的样本数据
        despathG = rootpath + '/kjtq_data/FDS/solar/SRT/XXXJ_SRT/' + yyyymm + '/' + yyyymmdd + '/'  ##1小时的样本数据        


        
        despath1 = rootpath + '/kjtq_data/CMA/atmos/UPA/' + yyyymm + '/' + yyyymmdd + '/'  ##24小时的样本数据
        despath2 = rootpath + '/kjtq_data/CMA/atmos/UPC/' + yyyymm + '/' + yyyymmdd + '/'  ##12小时的样本数据
        despath3 = rootpath + '/kjtq_data/FDS/atmos/MET/XXXJ_MET/' + yyyymm + '/' + yyyymmdd + '/'  ##1小时的样本数据
        despath4 = rootpath + '/kjtq_data/FDS/atmos/MST/XXXJ_MST/' + yyyymm + '/' + yyyymmdd + '/'  ##30分钟的样本数据
        despath5 = rootpath + '/kjtq_data/FDS/geomag/FGM/XXXJ_FGM/' + yyyymm + '/' + yyyymmdd + '/'  ##15分钟、3个小时、1天样本数据
        despath6 = rootpath + '/kjtq_data/MDP/atmos/LID/' + yyyymm + '/' + yyyymmdd + '/'  ##1天的样本数据
        despath7 = rootpath + '/kjtq_data/MDP/geomag/FGM/' + yyyymm + '/' + yyyymmdd + '/'  ##1天的样本数据

        
    ##创建目标文件目录结构
    ##实际测试发现,创建目标目录的子目录时候，也使用makedirs创建多级目录，所以如下目录创建，可以不调用
    # if not os.path.exists(despathA):
        # os.makedirs(despathA)
    # if not os.path.exists(despathB):
        # os.makedirs(despathB)
    # if not os.path.exists(despathC):
        # os.makedirs(despathC)
    # if not os.path.exists(despathD):
        # os.makedirs(despathD)
    # if not os.path.exists(despathE):
        # os.makedirs(despathE)
    # if not os.path.exists(despathF):
        # os.makedirs(despathF)
    # if not os.path.exists(despathG):
        # os.makedirs(despathG)

    ####需要增加srcpath的合法性，否则后续程序会进入一种无法预知的状态
    # if not os.path.exists(srcpathA):
        # exit('do not exist %s' % srcpathA)
    # if not os.path.exists(srcpathB):
        # exit('do not exist %s' % srcpathB)
    # if not os.path.exists(srcpathC):
        # exit('do not exist %s' % srcpathC)
    # if not os.path.exists(srcpathD):
        # exit('do not exist %s' % srcpathD)
    # if not os.path.exists(srcpathE):
        # exit('do not exist %s' % srcpathE)
    # if not os.path.exists(srcpathF):
        # exit('do not exist %s' % srcpathF)
    # if not os.path.exists(srcpathG):
        # exit('do not exist %s' % srcpathG)




    ####电离层,测试数据生产
    #gen_IONO_FDS_ION_oncetime(set_time, srcpathC, despathC)    
    
    ####太阳,测试数据生产    
    gen_SOLAR_FDS_SOT_oncetime(set_time,srcpathE,despathE, mode='normal', begin_hour=9, end_hour=18)  #12点到14点的数据	
    # gen_SOLAR_CMA_SRT_oncetime(set_time, srcpathF, despathF)
    # gen_SOLAR_FDS_SRT_oncetime(set_time, srcpathG, despathG)
    
    
    # copy_modify_yyyymmdd_mdp(repace_yyyymmdd, srcpath1, despath1)
    # copy_modify_yyyymmdd_mdp(repace_yyyymmdd, srcpath2, despath2)
    # copy_modify_yyyymmdd(repace_yyyymmdd, srcpath3, despath3)
    # copy_modify_yyyymmdd(repace_yyyymmdd, srcpath4, despath4)
    # copy_modify_yyyymmdd(repace_yyyymmdd, srcpath5, despath5)
    # copy_modify_yyyymmdd_mdp(repace_yyyymmdd, srcpath6, despath6)
    # copy_modify_yyyymmdd_mdp(repace_yyyymmdd, srcpath7, despath7)




def example4(current_path, rootpaths):
    print ('into example4......')
    # ####产生数据日期设定，用户可以设置，时间精确到年月日
    # set_time = '20200309'
    # ####根目录设置
    # rootpath = 'C:\\Users\\Administrator\\Desktop\\test\\dataaaaa\\'
    
    set_times=time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    ####产生数据日期设定，用户可以设置，时间精确到年月日
    yyyy = set_times[0:4]
    yyyymm = set_times[0:6]
    yyyymmdd = set_times[0:8]
    yyyymmddhh = set_times[0:10]
    yyyymmddhhmm = set_times[0:12]    
    ####设置替换时间的匹配表达式
    repace_yyyymmdd = '_' + yyyymmdd
    repace_yyyymmddhh = '_' + yyyymmddhh
    repace_yyyymmddhhmm = '_' + yyyymmddhhmm

    ####根目录设置
    rootpath = rootpaths
    ####产品路径，统一由yyyy调整为yyyymm

    if ('Windows' == platform.system()):
        ####根据src路径下的样本数据，来产生设定日期的1天的数据 ,样例数据在当前路径下
        srcpathA = current_path + '\\gen_IONO_CET_ION\\201907\\20190716\\'  ##1小时的样本数据
        srcpathB = current_path + '\\gen_IONO_CET_ISM\\201907\\20190716\\'  ##1小时的样本数据
        srcpathC = current_path + '\\gen_IONO_FDS_ION\\2019\\20191115\\'  ##24小时的样本数据
        srcpathD = current_path + '\\gen_IONO_FDS_ISM\\202001\\20200101\\CDZJ\\CDZJ_ISM01_DBD_L11_01H_20200101000000.txt'  ##24小时的样本数据
        srcpathE = current_path + '\\gen_SOLAR_FDS_SOT\\201910\\20191012\\'
        srcpathF = current_path + '\\gen_SOLAR_CMA_SRT\\201803\\20180328\\SDZM\\YJGC_SDWH_TYSD_20180328_061601_L0_0000_01S.txt'
        srcpathG = current_path + '\\gen_SOLAR_FDS_SRT\\201912\\20191201\\'

        srcpath5 = current_path + '\\Data\\TEST\\FDS\\geomag\\FGM\\2020\\20200306\\'  ##24小时的样本数据
        srcpath6 = current_path + '\\Data\\TEST\\FDS\\atmos\\MET\\2020\\20200306\\'  ##24小时的样本数据
        srcpath7 = current_path + '\\Data\\TEST\\FDS\\atmos\\MST\\2020\\20200306\\'  ##24小时的样本数据
        srcpath8 = ''
        srcpath9 = ''
        srcpath10 = ''
        
        despathA = rootpath + '\\Data\\TEST\\CET\\iono\\ION\\' + yyyymm + '\\' + yyyymmdd + '\\'  ##1小时的样本数据
        despathB = rootpath + '\\Data\\TEST\\CET\\iono\\ISM\\' + yyyymm + '\\' + yyyymmdd + '\\'  ##1小时的样本数据
        despathC = rootpath + '\\Data\\TEST\\FDS\\iono\\ION\\' + yyyymm + '\\' + yyyymmdd + '\\'  ##24小时的样本数据
        despathD = rootpath + '\\Data\\TEST\\FDS\\iono\\ISM\\' + yyyymm + '\\' + yyyymmdd + '\\'  ##24小时的样本数据
        despathE = rootpath + '\\Data\\TEST\\FDS\\solar\\SOT\\' + yyyymm + '\\' + yyyymmdd + '\\'  ##1小时的样本数据
        despathF = rootpath + '\\Data\\TEST\\CMA\\solar\\SRT\\' + yyyymm + '\\' + yyyymmdd + '\\'  ##1小时的样本数据
        despathG = rootpath + '\\Data\\TEST\\FDS\\solar\\SRT\\' + yyyymm + '\\' + yyyymmdd + '\\'  ##1小时的样本数据

        despath5 = rootpath + '\\Data\\TEST\\FDS\\geomag\\FGM\\' + yyyymm + '\\' + yyyymmdd + '\\'  ##24小时的样本数据
        despath6 = rootpath + '\\Data\\TEST\\FDS\\atmos\\MET\\' + yyyymm + '\\' + yyyymmdd + '\\'  ##24小时的样本数据
        despath7 = rootpath + '\\Data\\TEST\\FDS\\atmos\\MST\\' + yyyymm + '\\' + yyyymmdd + '\\'  ##24小时的样本数据
        despath8 = ''
        despath9 = ''
        despath10 = ''
        
    if ('Linux' == platform.system()):
        ####根据src路径下的样本数据，来产生设定日期的1天的数据,样例数据在当前路径下
        srcpathA = current_path + '/gen_IONO_CET_ION/201907/20190716/'  ##1小时的样本数据
        srcpathB = current_path + '/gen_IONO_CET_ISM/201907/20190716/'  ##1小时的样本数据
        srcpathC = current_path + '/gen_IONO_FDS_ION/2019/20191115/'  ##24小时的样本数据
        srcpathD = current_path + '/gen_IONO_FDS_ISM/202001/20200101/CDZJ/CDZJ_ISM01_DBD_L11_01H_20200101000000.txt'  ##24小时的样本数据
        srcpathE = current_path + '/gen_SOLAR_FDS_SOT/201910/20191012/'  ##24小时的样本数据
        srcpathF = current_path + '/gen_SOLAR_CMA_SRT/201803/20180328/SDZM/YJGC_SDWH_TYSD_20180328_061601_L0_0000_01S.txt'
        srcpathG = current_path + '/gen_SOLAR_FDS_SRT/201912/20191201/'

        srcpath5 = current_path + '/gen_FDS_GEOMAG_FGM/202003/20200330/'        ##15分钟的样本数据
        srcpath6 = current_path + '/gen_FDS_ATMOS_MET/201201/20120101/'         ##1小时的样本数据
        srcpath7 = current_path + '/gen_FDS_ATMOS_MST/201911/20191105/'         ##30分钟的样本数据
        srcpath71 = current_path + '/gen_FDS_ATMOS_MST/201911/20191106/'         ##30分钟的样本数据
        srcpath8 = current_path + '/gen_FDS_GEOMAG_FGM/202003/20200329/'        ##3小时的样本数据
        srcpath9 = current_path + '/gen_MDP_ATMOS_LID/201910/20191022/'         ##1天的样本数据
        srcpath10 = current_path + '/gen_MDP_GEOMAG_FGM/201910/20191021/'       ##1天的样本数据
        srcpath11 = current_path + '/gen_FDS_ATMOS_CMA_UPAR/202003/20200331/'   ##12小时的样本数据
        srcpath12 = current_path + '/gen_FDS_GEOMAG_FGM/202003/20200331/'       ##24小时的样本数据
        srcpath13 = current_path + '/gen_FDS_ATMOS_AFD_UPAR/202004/20200401/'   ##24小时的样本数据
        
        
        # despathA = rootpath + '/kjtq_data/CET/iono/ION/' + yyyymm + '/' + yyyymmdd + '/'  ##1小时的样本数据
        # despathB = rootpath + '/kjtq_data/CET/iono/ISM/' + yyyymm + '/' + yyyymmdd + '/'  ##1小时的样本数据
        # despathC = rootpath + '/kjtq_data/FDS/iono/ION/' + yyyymm + '/' + yyyymmdd + '/'  ##24小时的样本数据
        # despathD = rootpath + '/kjtq_data/FDS/iono/ISM/' + yyyymm + '/' + yyyymmdd + '/'  ##24小时的样本数据
        # despathE = rootpath + '/kjtq_data/FDS/solar/SOT/' + yyyymm + '/' + yyyymmdd + '/'  ##1小时的样本数据
        # despathF = rootpath + '/kjtq_data/CMA/solar/SRT/' + yyyymm + '/' + yyyymmdd + '/'  ##1小时的样本数据
        # despathG = rootpath + '/kjtq_data/FDS/solar/SRT/' + yyyymm + '/' + yyyymmdd + '/'  ##1小时的样本数据

        despathA = rootpath + '/kjtq_data/CET/iono/ION/XXXM_ION/' + yyyymm + '/' + yyyymmdd + '/'  ##1小时的样本数据
        despathB = rootpath + '/kjtq_data/CET/iono/ISM/XXXM_ISM/' + yyyymm + '/' + yyyymmdd + '/'  ##1小时的样本数据
        despathC = rootpath + '/kjtq_data/FDS/iono/ION/XXXJ_ION/' + yyyymm + '/' + yyyymmdd + '/'  ##24小时的样本数据
        despathD = rootpath + '/kjtq_data/FDS/iono/ISM/XXXJ_ISM/' + yyyymm + '/' + yyyymmdd + '/'  ##24小时的样本数据
        despathE = rootpath + '/kjtq_data/FDS/solar/SOT/' + yyyymm + '/' + yyyymmdd + '/'  ##1小时的样本数据
        despathF = rootpath + '/kjtq_data/CMA/solar/SRT/' + yyyymm + '/' + yyyymmdd + '/'  ##1小时的样本数据
        despathG = rootpath + '/kjtq_data/FDS/solar/SRT/XXXJ_SRT' + yyyymm + '/' + yyyymmdd + '/'  ##1小时的样本数据
        
        
        despath5 = rootpath + '/kjtq_data/FDS/geomag/FGM/XXXJ_FGM/' + yyyymm + '/' + yyyymmdd + '/'  ##15分钟的样本数据
        despath6 = rootpath + '/kjtq_data/FDS/atmos/MET/XXXJ_MET/' + yyyymm + '/' + yyyymmdd + '/'  ##1小时的样本数据
        despath7 = rootpath + '/kjtq_data/FDS/atmos/MST/XXXM_MST/' + yyyymm + '/' + yyyymmdd + '/'  ##30分钟的样本数据
        despath71 = rootpath + '/kjtq_data/FDS/atmos/MST/XXXJ_MST/' + yyyymm + '/' + yyyymmdd + '/'  ##30分钟的样本数据
        despath8 = rootpath + '/kjtq_data/FDS/geomag/FGM/XXXJ_FGM/' + yyyymm + '/' + yyyymmdd + '/'  ##3小时的样本数据
        despath9 = rootpath + '/kjtq_data/MDP/atmos/LID/' + yyyymm + '/' + yyyymmdd + '/'  ##1天的样本数据
        despath10 = rootpath + '/kjtq_data/MDP/geomag/FGM/' + yyyymm + '/' + yyyymmdd + '/'  ##1天的样本数据
        despath11 = rootpath + '/kjtq_data/CMA/atmos/UPC/' + yyyymm + '/' + yyyymmdd + '/'  ##12小时的样本数据
        despath12 = rootpath + '/kjtq_data/FDS/geomag/FGM/XXXJ_FGM/' + yyyymm + '/' + yyyymmdd + '/'  ##24小时的样本数据
        despath13 = rootpath + '/kjtq_data/CMA/atmos/UPA/' + yyyymm + '/' + yyyymmdd + '/'  ##24小时的样本数据
        
        
        
        
    ####创建目标文件目录结构
    ####实际测试发现,创建目标目录的子目录时候，也使用makedirs创建多级目录，所以如下目录创建，可以不调用
    # if not os.path.exists(despathA):
        # os.makedirs(despathA)
    # if not os.path.exists(despathB):
        # os.makedirs(despathB)
    # if not os.path.exists(despathC):
        # os.makedirs(despathC)
    # if not os.path.exists(despathD):
        # os.makedirs(despathD)
    # if not os.path.exists(despathE):
        # os.makedirs(despathE)
    # if not os.path.exists(despathF):
        # os.makedirs(despathF)
    # if not os.path.exists(despathG):
        # os.makedirs(despathG)

    ####需要增加srcpath的合法性，否则后续程序会进入一种无法预知的状态
    if not os.path.exists(srcpathA):
        exit('do not exist %s' % srcpathA)
    if not os.path.exists(srcpathB):
        exit('do not exist %s' % srcpathB)
    if not os.path.exists(srcpathC):
        exit('do not exist %s' % srcpathC)
    if not os.path.exists(srcpathD):
        exit('do not exist %s' % srcpathD)
    if not os.path.exists(srcpathE):
        exit('do not exist %s' % srcpathE)
    if not os.path.exists(srcpathF):
        exit('do not exist %s' % srcpathF)
    if not os.path.exists(srcpathG):
        exit('do not exist %s' % srcpathG)

    #### 启动定时任务
    scheduler = BlockingScheduler()#阻塞方式
    #sheduler = BackgroundScheduler()#非阻塞方式
    

    #### 用户添加自己的用例add_job
    #### despath,需要根据每天的日期校验替换，否则所有数据都存放到启动任务当天的文件夹下
    
    jobA = scheduler.add_job(func=gen_IONO_CET_ION_scheduler, args=[srcpathA, despathA], trigger='cron', hour='8-18',id='gen_IONO_CET_ION_scheduler')#          #每天的08-18小时开始执行
    #jobB = scheduler.add_job(func=gen_IONO_CET_ISM_scheduler, args=[srcpathB, despathB], trigger='cron', hour='0-23',id='gen_IONO_CET_ISM_scheduler')          ##每天的00-23小时开始执行
    jobC = scheduler.add_job(func=gen_IONO_FDS_ION_scheduler, args=[srcpathC, despathC], trigger='cron', minute='00,15,30,45',id='gen_IONO_FDS_ION_scheduler')  ##每小时的00，15，30，45分开始执行
    #jobD = scheduler.add_job(func=gen_IONO_FDS_ISM_scheduler, args=[srcpathD, despathD], trigger='cron', hour='0-23',id='gen_IONO_FDS_ISM_scheduler')##每隔1个小时1次
    #jobE1 = scheduler.add_job(func=gen_SOLAR_FDS_SOT_scheduler, args=[srcpathE, despathE,'CGC'], trigger='cron', hour='14-14',minute='00,30',id='gen_SOLAR_FDS_SOT_scheduler CGC')##每隔30分钟执行1次
    #jobE2 = scheduler.add_job(func=gen_SOLAR_FDS_SOT_scheduler, args=[srcpathE, despathE,'CGQ'], trigger='cron', hour='14-14',minute='05,10,15,20,25,30,35,40,45,50,55',id='gen_SOLAR_FDS_SOT_scheduler CGQ')##每隔5分钟执行1次
    #jobE3 = scheduler.add_job(func=gen_SOLAR_FDS_SOT_scheduler, args=[srcpathE, despathE,'CGS'], trigger='cron', hour='14-14',minute='05,10,15,20,25,30,35,40,45,50,55',id='gen_SOLAR_FDS_SOT_scheduler CGS')##每隔5分钟执行1次
    #jobE4 = scheduler.add_job(func=gen_SOLAR_FDS_SOT_scheduler, args=[srcpathE, despathE,'CHA'], trigger='cron', hour='14-14',minute='05,10,15,20,25,30,35,40,45,50,55',id='gen_SOLAR_FDS_SOT_scheduler CHA')##每隔5分钟执行1次
    jobF = scheduler.add_job(func=gen_SOLAR_CMA_SRT_scheduler, args=[srcpathF, despathF], trigger='cron', hour='6-18',minute='00,03,06,09,12,15,18,21,24,27,30,33,36,39,42,45,48,51,54,57',id='gen_SOLAR_CMA_SRT_scheduler')##每隔3分钟执行1次，06：00除外
    jobG = scheduler.add_job(func=gen_SOLAR_FDS_SRT_scheduler, args=[srcpathG, despathG], trigger='cron', hour='0-23',minute='00,15,30,45',id='gen_SOLAR_FDS_SRT_scheduler')##每小时的00，15，30，45分钟开始执行，00：00：00除外
    
    
    job5 = scheduler.add_job(func=copy_modify_yyyymmddhhmm_once, args=[srcpath5, despath5], trigger='cron',minute='00,15,30,45', id='FDS_geomag_FGM15M')  ##每小时的00，15，30，45分开始执行
    job6 = scheduler.add_job(func=copy_modify_yyyymmddhhmm_once, args=[srcpath6, despath6], trigger='cron',minute='00', id='FDS_atmos_MET')  ##每小时的00分开始执行
    job7 = scheduler.add_job(func=copy_modify_yyyymmddhhmm_once, args=[srcpath7, despath7], trigger='cron',minute='00,30', id='FDS_atmos_MST')  ##每小时的00,30分开始执行
    job71 = scheduler.add_job(func=copy_modify_yyyymmddhhmm_once, args=[srcpath71, despath71], trigger='cron',minute='00,30', id='FDS_atmos_MST1')  ##每小时的00,30分开始执行
    job8 = scheduler.add_job(func=copy_modify_yyyymmddhhmm_once, args=[srcpath8, despath8], trigger='cron',hour='00,03,06,09,12,15,18,21', id='FDS_geomag_FGM3H')  ##每天的00,03,06,09,12,15,18,21时开始执行
    job9 = scheduler.add_job(func=copy_modify_yyyymmddhhmm_once_mdp, args=[srcpath9, despath9], trigger='cron',hour='00', id='MDP_atmos_LID')  ##每天的00时00分开始执行
    job10 = scheduler.add_job(func=copy_modify_yyyymmddhhmm_once_mdp, args=[srcpath10, despath10],trigger='cron',hour='00', id='MDP_geomag_FGM')  ##每天的00时00分开始执行                             
    #job10 = scheduler.add_job(func=copy_modify_yyyymmddhhmm_once_mdp, args=[srcpath10, despath10],trigger='cron',minute='05,10,15,20,25,30,35,40,45,50,55', id='MDP_geomag_FGM')  ##每天的00时00分开始执行                             
    #job11 = scheduler.add_job(func=copy_modify_yyyymmdd_matchHH_scheduler, args=[srcpath11, despath11],trigger='cron',hour='00,12', id='FDS_atmos_cma_upar')  ##每天的00时、12时开始执行                      
    job11 = scheduler.add_job(func=copy_modify_yyyymmddhhmm_once_mdp, args=[srcpath11, despath11],trigger='cron',hour='00,12', id='FDS_atmos_cma_upar')  ##每天的00时、12时开始执行                      
    job12 = scheduler.add_job(func=copy_modify_yyyymmdd_matchHH_scheduler, args=[srcpath12, despath12],trigger='cron',hour='00', id='FDS_atmos_FGM24H')  ##每天的00时开始执行
    #job13 = scheduler.add_job(func=copy_modify_yyyymmdd_matchHH_scheduler, args=[srcpath13, despath13],trigger='cron',hour='12', id='FDS_atmos_AFD_UPAR')  ##每天的00时开始执行
    job13 = scheduler.add_job(func=copy_modify_yyyymmddhhmm_once_mdp, args=[srcpath13, despath13],trigger='cron',hour='12', id='FDS_atmos_AFD_UPAR')  ##每天的00时开始执行

    #### 任务列表
    #print (scheduler.get_jobs())
    
    #### 日志推送到邮箱
    jobX = scheduler.add_job(func=send_mail_segment, trigger='cron', hour='0,21',id='send_mail_segment')##每天0点，3点，8点，19点, 20点 推送1次
  
    #### 生产IRI网格数据
    jobR = scheduler.add_job(func=gen_IRI,trigger='cron', hour='22', id='gen_IRI')  ##每天的00时开始执行
    
    
    #### 定时清理4天前的数据
    #### 过期天数，设置成4天，保留前72小时的数据即可，多留1天的余量数据
    expire_day= 7
    cleanpath1='/kjtq_data/'
    cleanpath11='/kjtq_data/FDS/solar/'
    cleanpath2='/kjtq_data/localdatafiles/'
    cleanpath3='/kjtq_data/localplugins/IRI'
    
    #jobY1 = scheduler.add_job(func=clean_dirs, args=[cleanpath1,expire_day], trigger='cron', hour='00',id='/Data/TEST/')                    #每天0点开始清理
    jobY11 = scheduler.add_job(func=clean_dirs, args=[cleanpath11,expire_day], trigger='cron', hour='00',id=cleanpath11)    
    jobY2 = scheduler.add_job(func=clean_dirs, args=[cleanpath2,expire_day], trigger='cron', hour='00',id=cleanpath2)   #每天0点开始清理
    #jobY3 = scheduler.add_job(func=clean_dirs, args=[cleanpath3,expire_day], trigger='cron', hour='00',id=cleanpath3)   #每天0点开始清理
    
    
    #### 监听任务
    scheduler.add_listener(listener,EVENT_JOB_EXECUTED|EVENT_JOB_ERROR)
    
    #### 任务日志
    logging = log_setting()
    scheduler._logger = logging
    
    
    #### 启动任务，只能启动1次，不可以重复启动
    try:
        print('begin start......')
        ##start阻塞
        scheduler.start()
        print ('end start......')
    except Exception as e:
        exit(str(e))




if __name__ == '__main__':
    set_time = sys.argv[1]
    print (set_time)
    print (type(set_time))
    gen_IRI(set_time)
    
    
    # if (len(sys.argv) != 2):
        # # print('命令行参数设置错误!')
        # # print('第1个参数： 主程序,名称为 %s'%os.path.basename(__file__))
        # print('第1个参数： 主程序,名称为 %s' % os.path.basename(__file__))
        # print('第2个参数： 日期参数，格式为yyyymmdd, 例如 20200315')
        # exit('请输入正确的命令行调用格式')

    # ####产生数据的日期
    # # set_time = '20200314'
    # exe_name = sys.argv[0]
    # set_time = sys.argv[1]
    # print('脚本名称为: %s' % exe_name)
    # print('设置日期为: %s' % set_time)
    # ##对日期进行非法判断,否则影响子程序的日期格式截取
    # check_yyyymmdd(set_time)

    # ##获取当前的系统时间
    # sys_time=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    # print (sys_time)
    # ##获取当前程序执行路径
    # # current_path = os.getcwd()
    # ##获取当前程序所在路径
    # current_path = os.path.dirname(os.path.abspath(__file__))
    # print('current_path = ', current_path)

    # # input()
    # ####根目录设置
    # if ('Windows' == platform.system()):
        # ####windows
        # data_rootpath = 'C:\\Users\\Administrator\\Desktop\\DQ1044_centos7.7\\code_gendata\\'
    # if ('Linux' == platform.system()):
        # ####linux
        # data_rootpath = '/'

    # ####
    # tic = time.time()
    
    # ####定时定点,启动任务
    # # example4(current_path, data_rootpath)
    
    # ####设置时间,一次任务
    # example3(set_time, current_path, data_rootpath)
    
    # toc = time.time()
    # print('总耗时[秒]：%f' % (toc - tic))
    
    
    
    