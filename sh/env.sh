#!/bin/bash


##挂载nfs共享磁盘
mount -t nfs 107.1.3.141:/kjtq_data /kjtq_data
mount -t nfs 107.1.3.141:/kjtq_src /kjtq_src
mount -t nfs 107.1.3.141:/kjtq /kjtq

##建立软链接
cp -rf /kjtq_src/code_gendata/lib64/* /usr/lib64
ln -s /usr/lib64/libICE.so.6.3.0 /usr/lib64/libICE.so.6
ln -s /usr/lib64/libX11.so.6.3.0 /usr/lib64/libX11.so.6
ln -s /usr/lib64/libXau.so.6.0.0 /usr/lib64/libXau.so.6
ln -s /usr/lib64/libtirpc.so.1.0.10 /usr/lib64/libtirpc.so.1
ln -s /usr/lib64/libgfortran.so.3.0.0 /usr/lib64/libgfortran.so.3
ln -s /usr/lib64/libquadmath.so.0.0.0 /usr/lib64/libquadmath.so.0

