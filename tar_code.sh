#!/bin/bash
# 功能：打包代码
# 脚本名称：tar_code.sh
# 作者：zy
# 版本：V 0.1
# 联系方式：xx

# 1.0 命令罗列
cd /data/codes
# 确保当前目录下没有django,tar.gz文件
[ -f django.tar.gz ]  && rm -f django.tar.gz	

tar zcf django.tar.gz django

# 下两行非脚本内容
sed -i 's#1.1#1.2#' /data/codes/django/views.py
bash /data.scripts/tar_code.sh

# 1.1 固定内容变量化
# 定义变量
FILE='django.tar.gz'
CODE_DIR='/data/codes'
PRO_DIR='django'

cd "${CODE_DIR}"
[ -f "${FILE}" ]  && rm -f "${FILE}"
tar zcf "${FILE}" "${PRO_DIR}"

# 1.2 功能函数化
FILE='django.tar.gz'
CODE_DIR='/data/codes'
PRO_DIR='django'

code_tar(){
	cd "${CODE_DIR}"
	[ -f "${FILE}" ]  && rm -f "${FILE}"
	tar zcf "${FILE}" "${PRO_DIR}"
}
code_tar

# 1.3 远程执行
# 远程更新	ssh root@114.116.247.86	"sed -i /'s#1.4#1.5#' /data/codes/django/views.py"
# 远程执行	ssh root@114.116.247.86 "/bin/bash /data/scripts/code_tar.sh"
# 远程查看	ssh root@114.116.247.86 "zcat /data/codes/code_tar.views"	# 查看zcat	ls

# 1.4 命令填充
# 获取代码-因为是手工方式，所以不需要

LOG_FILE='/data/logs/deploy.log'
PID_FILE='/tmp/deploy.pid'

# 增加锁文件	，同一时间段只能有1个人操作
add_lock(){
	echo "增加锁文件"
	touch "${PID_FILE}"
	write_log "增加锁文件"
}
del_lock(){
	echo "是演出锁文件"
	rm -rf "${PID_FILE}"
	write_log "删除锁文件"
}
err_msg(){
	echo "脚本 $0 正在运行，请稍后..."
}


# 增加日志功能
write_log(){
	DATE=$(date +%F)  	# 日期
	TIME=$(date +%T)	# 时间
	buzhou="$1"			# 脚本
	echo "$[DATE] $[TIME] $0 : $(buzhou)" >> "$(LOG_FILE)"
}

get_code(){
	echo "获取代码"
	write_log "获取代码"
}
# 打包代码
tar_code(){
	echo "打包代码"
	ssh root@114.116.247.86 "/bin/bash /data/scripts/tar_code.sh"
	write_log "打包代码"
}
# 传输代码
scp_code(){
	echo "传输代码"
	cd /data/codes
	[ -f django.tar.gz ] && rm -rf django.tar.gz
	scp root@114.116.247.86:/data/codes/django.tar.gz ./
	write_log "传输代码"
}
#关闭应用
stop_serv(){
	echo "关闭应用"
	write_log "关闭应用"

	echo "关闭nginx应用"
	nginx -s stop
	write_log "关闭nginx应用"

	echo "关闭django应用"
	kill $(lsof -Pti :8000)
	write_log "关闭django应用"
}

# 解压代码
untar_code(){
	echo "解压代码"
	cd /data/codes
	tar xf django.tar.gz
	write_log "关闭应用"
}

# 放置代码
fangzhi_code(){
	echo "放置代码"
	echo "备份老文件"
	mv /data/server/itcast/test1/views.py /data/backup/views.py-$(date +%Y%m%d%H%M%S)
	write_log "备份老文件"
	echo "放置新文件"
	mv /data/codes/django/views.py /data/server/itcast/test1
	write_log "放置新文件"
}

# 开启应用
start_serv(){
	echo "开启应用"
	echo "开启django应用"
	source /data/virtuals/venv/bin/activate
	cd /data/server/itcast/
	python manage.py runserver >> /dev/null 2>&1 &
	deactivate
	write_log "开启django应用"
	echo "开启nginx应用"
	nginx
	write_log "开启nginx应用"
}

# 检查
check(){
	echo "检查项目"
	netstat -tnulp | grep ':80'
	write_log "检查项目"
}

# 部署函数
pro_deploy(){
	add_lock
	get_code
	tar_code
	scp_code
	stop_serv
	untar_code
	fangzhi_code
	start_serv
	check
	del_lock
}

# 帮助信息
usage(){
	echo "脚本 $0 的使用方式是：$0 [ deploy ]"
}
# 主函数
main(){
	case "$1" in
		deploy)
			if [ -f "${PID_FILE}" ]
			then
				err_msg
			else
				pro_deploy
			fi
			;;
		*)
			usage
			;;
	esac
}

# 调用主函数
main $1





