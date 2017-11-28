#!/bin/bash
clear
pkill -f 'python3 manage.py'
cd /home/rassul/djangoProjects/djangop001/
nohup python3 manage.py runserver > /dev/null 2>&1 & 
cd /home/rassul/djangoProjects/djangop002/ 
nohup python3 manage.py runserver 8001 > /dev/null 2>&1 &
cd ~
