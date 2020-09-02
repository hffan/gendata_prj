#!/bin/sh


########################################################################################################################
#1. 备份代码操作
########################################################################################################################


##脚本上一级目录
code_path=$(dirname "$PWD")
echo $code_path


systime=$(date "+%Y%m%d%H%M%S")
echo $systime
cd $code_path
zipname=code_gendata_v$systime
echo $zipname
pwd
zip -r $zipname code_gendata



