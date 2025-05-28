#!/bin/sh

# 设置根文件系统目录为当前目录
ROOTFS_DIR=$(pwd)
# 添加路径
export PATH=$PATH:~/.local/usr/bin
# 设置最大重试次数和超时时间
max_retries=50
timeout=1
# 获取系统架构
ARCH=$(uname -m)
# 获取当前用户名
CURRENT_USER=$(whoami)

# 根据CPU架构设置对应的架构名称
if [ "$ARCH" = "x86_64" ]; then
  ARCH_ALT=amd64
elif [ "$ARCH" = "aarch64" ]; then
  ARCH_ALT=arm64
else
  printf "不支持的CPU架构: ${ARCH}"
  exit 1
fi

# 检查是否已安装
if [ ! -e $ROOTFS_DIR/.installed ]; then
  echo "#######################################################################################"
  echo "#"
  echo "#                                      Foxytoux 安装程序"
  echo "#"
  echo "#                           Copyright (C) 2024, RecodeStudios.Cloud"
  echo "#"
  echo "#"
  echo "#######################################################################################"

  read -p "是否安装Ubuntu? (YES/no): " install_ubuntu
fi

# 根据用户输入决定是否安装Ubuntu
case $install_ubuntu in
  [yY][eE][sS])
    # 下载Ubuntu基础系统
    wget --tries=$max_retries --timeout=$timeout -O /tmp/rootfs.tar.gz \
      "http://cdimage.ubuntu.com/ubuntu-base/releases/20.04/release/ubuntu-base-20.04.4-base-${ARCH_ALT}.tar.gz"
    # 解压到根文件系统目录
    tar -xf /tmp/rootfs.tar.gz -C $ROOTFS_DIR
    ;;
  *)
    echo "跳过Ubuntu安装。"
    ;;
esac

# 安装proot
if [ ! -e $ROOTFS_DIR/.installed ]; then
  # 创建目录
  mkdir $ROOTFS_DIR/usr/local/bin -p
  # 下载proot - 使用用户提供的GitHub地址
  wget --tries=$max_retries --timeout=$timeout -O $ROOTFS_DIR/usr/local/bin/proot "https://raw.githubusercontent.com/zhumengkang/agsb/main/proot-${ARCH}"

  # 确保proot下载成功
  while [ ! -s "$ROOTFS_DIR/usr/local/bin/proot" ]; do
    rm $ROOTFS_DIR/usr/local/bin/proot -rf
    wget --tries=$max_retries --timeout=$timeout -O $ROOTFS_DIR/usr/local/bin/proot "https://raw.githubusercontent.com/zhumengkang/agsb/main/proot-${ARCH}"

    if [ -s "$ROOTFS_DIR/usr/local/bin/proot" ]; then
      chmod 755 $ROOTFS_DIR/usr/local/bin/proot
      break
    fi

    chmod 755 $ROOTFS_DIR/usr/local/bin/proot
    sleep 1
  done

  # 设置proot执行权限
  chmod 755 $ROOTFS_DIR/usr/local/bin/proot
fi

# 完成安装配置
if [ ! -e $ROOTFS_DIR/.installed ]; then
  # 设置DNS服务器
  printf "nameserver 1.1.1.1\nnameserver 1.0.0.1" > ${ROOTFS_DIR}/etc/resolv.conf
  # 清理临时文件
  rm -rf /tmp/rootfs.tar.xz /tmp/sbin
  # 创建安装标记文件
  touch $ROOTFS_DIR/.installed
fi

# 定义颜色
CYAN='\e[0;36m'
WHITE='\e[0;37m'
RESET_COLOR='\e[0m'

# 显示安装完成信息
display_gg() {
  echo -e "${WHITE}___________________________________________________${RESET_COLOR}"
  echo -e ""
  echo -e "           ${CYAN}-----> 任务完成! <----${RESET_COLOR}"
}

# 创建用户目录
mkdir -p $ROOTFS_DIR/home/$CURRENT_USER

# 创建正常的.bashrc文件
cat > $ROOTFS_DIR/root/.bashrc << EOF
# 默认.bashrc内容
if [ -f /etc/bash.bashrc ]; then
  . /etc/bash.bashrc
fi
EOF

# 创建初始化脚本，并传递当前用户名作为变量
cat > $ROOTFS_DIR/root/init.sh << EOF
#!/bin/bash

# 使用传入的物理机用户名
HOST_USER="$CURRENT_USER"

# 创建物理机用户目录
mkdir -p /home/\$HOST_USER 2>/dev/null
echo -e "\033[1;32m已创建用户目录: /home/\$HOST_USER\033[0m"

# 备份原始软件源
cp /etc/apt/sources.list /etc/apt/sources.list.bak 2>/dev/null

# 设置新的软件源
tee /etc/apt/sources.list <<SOURCES
deb http://archive.ubuntu.com/ubuntu jammy main universe restricted multiverse
deb http://archive.ubuntu.com/ubuntu jammy-updates main universe restricted multiverse
deb http://archive.ubuntu.com/ubuntu jammy-backports main universe restricted multiverse
deb http://security.ubuntu.com/ubuntu jammy-security main universe restricted multiverse
SOURCES

# 显示提示信息
echo -e "\033[1;32m软件源已更新为Ubuntu 22.04 (Jammy)源\033[0m"
echo -e "\033[1;33m正在更新系统并安装必要软件包，请稍候...\033[0m"

# 更新系统并安装软件包
apt -y update && apt -y upgrade && apt install -y curl wget git vim nano htop tmux python3 python3-pip nodejs npm build-essential net-tools zip unzip sudo locales tree ca-certificates gnupg lsb-release iproute2 cron podman

echo -e "\033[1;32m系统更新和软件安装完成!\033[0m"

# 显示欢迎信息
printf "\n\033[1;36m################################################################################\033[0m\n"
printf "\033[1;33m#                                                                              #\033[0m\n"
printf "\033[1;33m#   \033[1;35m作者: 康康\033[1;33m                                                            #\033[0m\n"
printf "\033[1;33m#   \033[1;34mGithub: https://github.com/zhumengkang/\033[1;33m                              #\033[0m\n"
printf "\033[1;33m#   \033[1;31mYouTube: https://www.youtube.com/@康康的V2Ray与Clash\033[1;33m                  #\033[0m\n"
printf "\033[1;33m#   \033[1;36mTelegram: https://t.me/+WibQp7Mww1k5MmZl\033[1;33m                           #\033[0m\n"
printf "\033[1;33m#                                                                              #\033[0m\n"
printf "\033[1;33m################################################################################\033[0m\n"
printf "\033[1;32m\n★ YouTube请点击关注!\033[0m\n"
printf "\033[1;32m★ Github请点个Star支持!\033[0m\n\n"
printf "\033[1;36m欢迎进入Ubuntu 20.04环境!\033[0m\n\n"

# 启动bash
/bin/bash
EOF

# 设置初始化脚本执行权限
chmod +x $ROOTFS_DIR/root/init.sh

# 清屏并显示完成信息
clear
display_gg

# 启动proot环境并执行初始化脚本
$ROOTFS_DIR/usr/local/bin/proot \
  --rootfs="${ROOTFS_DIR}" \
  -0 -w "/root" -b /dev -b /sys -b /proc -b /etc/resolv.conf --kill-on-exit \
  /bin/bash /root/init.sh
