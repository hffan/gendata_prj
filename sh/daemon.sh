#!/bin/bash
PROC_NAME='apscheduler_gendata.py'
ProNumber=`ps -ef|grep -w $PROC_NAME|grep -v grep|wc -l`
if [ $ProNumber -le 0 ];then
    result=0
else
    result=1
fi
echo "the proc num is :" ${result}

if [ "$result" -eq 1 ] ;then
    echo "the proc is running, no need run it"
    exit 1;
fi


if [ "$result" -eq 0 ] ;then
    echo "the proc is not running, run it now"
    ipcs -q |awk 'NR>3 {print "ipcrm -q", $2}'|sh
    python /home/DQ1044/code_gendata/main_v12.py
    exit 1;
fi

##配置crontab命令：* * * * * sh /home/DQ1044/code_gendata/daemon.sh
##配置方法：crontab -e编辑，wq保存
##最小1分钟检查1次，保证最小任务有1分钟生产一次的
##crontab配置调用的shell脚本，带sh命名执行，保证有可执行权限
##配置格式如下
# .---------------- minute (0 - 59)

# |  .------------- hour (0 - 23)

# |  |  .---------- day of month (1 - 31)

# |  |  |  .------- month (1 - 12) OR jan,feb,mar,apr ...

# |  |  |  |  .---- day of week (0 - 6) (Sunday=0 or 7) OR sun,mon,tue,wed,thu,fri,sat

# |  |  |  |  |

# *  *  *  *  * user-name  command to be executed

