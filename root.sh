#!/bin/bash

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

# 定义颜色
CYAN='\e[0;36m'
WHITE='\e[0;37m'
RED='\e[0;31m'
GREEN='\e[0;32m'
YELLOW='\e[0;33m'
RESET_COLOR='\e[0m'

# 显示安装完成信息
display_gg() {
  echo -e "${WHITE}___________________________________________________${RESET_COLOR}"
  echo -e ""
  echo -e "           ${CYAN}-----> 任务完成! <----${RESET_COLOR}"
}

# 显示帮助信息
display_help() {
  echo -e "${CYAN}Ubuntu Proot 环境安装脚本${RESET_COLOR}"
  echo -e "${WHITE}使用方法:${RESET_COLOR}"
  echo -e "  ${GREEN}./root.sh${RESET_COLOR}         - 安装Ubuntu Proot环境"
  echo -e "  ${GREEN}./root.sh del${RESET_COLOR}     - 删除所有配置和文件"
  echo -e "  ${GREEN}./root.sh help${RESET_COLOR}    - 显示此帮助信息"
  echo -e ""
  echo -e "${WHITE}更多信息请查看 README.md 文件${RESET_COLOR}"
}

# 删除所有配置和文件
delete_all() {
  echo -e "${YELLOW}正在删除所有配置和文件...${RESET_COLOR}"
  
  # 删除proot目录下的所有文件，但保留root.sh和README.md
  find "$ROOTFS_DIR" -mindepth 1 -not -name "root.sh" -not -name "README.md" -not -name ".git" -not -path "*/.git/*" -exec rm -rf {} \; 2>/dev/null
  
  echo -e "${GREEN}所有配置和文件已删除!${RESET_COLOR}"
  echo -e "${WHITE}如果需要重新安装，请运行:${RESET_COLOR} ${GREEN}./root.sh${RESET_COLOR}"
  exit 0
}

# 处理命令行参数
if [ "$1" = "del" ]; then
  delete_all
elif [ "$1" = "help" ]; then
  display_help
  exit 0
fi

echo "当前用户: $CURRENT_USER"
echo "系统架构: $ARCH"
echo "工作目录: $ROOTFS_DIR"

# 根据CPU架构设置对应的架构名称
if [ "$ARCH" = "x86_64" ]; then
  ARCH_ALT=amd64
elif [ "$ARCH" = "aarch64" ]; then
  ARCH_ALT=arm64
else
  printf "不支持的CPU架构: ${ARCH}"
  exit 1
fi

echo "架构别名: $ARCH_ALT"

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
    echo "开始下载Ubuntu基础系统..."
    # 下载Ubuntu基础系统
    curl --retry $max_retries --connect-timeout $timeout -o /tmp/rootfs.tar.gz \
      "http://cdimage.ubuntu.com/ubuntu-base/releases/20.04/release/ubuntu-base-20.04.4-base-${ARCH_ALT}.tar.gz"
    
    echo "解压Ubuntu基础系统到 $ROOTFS_DIR..."
    # 解压到根文件系统目录
    tar -xf /tmp/rootfs.tar.gz -C $ROOTFS_DIR
    ;;
  *)
    echo "跳过Ubuntu安装。"
    ;;
esac

# 安装proot
if [ ! -e $ROOTFS_DIR/.installed ]; then
  echo "创建目录: $ROOTFS_DIR/usr/local/bin"
  # 创建目录
  mkdir $ROOTFS_DIR/usr/local/bin -p
  
  echo "下载proot..."
  # 下载proot - 使用用户提供的GitHub地址
  curl --retry $max_retries --connect-timeout $timeout -o $ROOTFS_DIR/usr/local/bin/proot \
    "https://raw.githubusercontent.com/zhumengkang/agsb/main/proot-${ARCH}"

  # 确保proot下载成功
  while [ ! -s "$ROOTFS_DIR/usr/local/bin/proot" ]; do
    echo "proot下载失败，重试..."
    rm $ROOTFS_DIR/usr/local/bin/proot -rf
    curl --retry $max_retries --connect-timeout $timeout -o $ROOTFS_DIR/usr/local/bin/proot \
      "https://raw.githubusercontent.com/zhumengkang/agsb/main/proot-${ARCH}"

    if [ -s "$ROOTFS_DIR/usr/local/bin/proot" ]; then
      chmod 755 $ROOTFS_DIR/usr/local/bin/proot
      echo "proot下载成功"
      break
    fi

    sleep 1
  done

  echo "设置proot执行权限"
  # 设置proot执行权限
  chmod 755 $ROOTFS_DIR/usr/local/bin/proot
fi

# 完成安装配置
if [ ! -e $ROOTFS_DIR/.installed ]; then
  echo "配置DNS服务器..."
  # 设置DNS服务器
  printf "nameserver 1.1.1.1\nnameserver 1.0.0.1" > ${ROOTFS_DIR}/etc/resolv.conf
  
  echo "清理临时文件..."
  # 清理临时文件
  rm -rf /tmp/rootfs.tar.xz /tmp/sbin
  
  echo "创建安装标记文件..."
  # 创建安装标记文件
  touch $ROOTFS_DIR/.installed
fi

echo "创建用户目录: $ROOTFS_DIR/home/$CURRENT_USER"
# 创建用户目录
mkdir -p $ROOTFS_DIR/home/$CURRENT_USER

echo "创建.bashrc文件..."
# 创建正常的.bashrc文件
cat > $ROOTFS_DIR/root/.bashrc << EOF
# 默认.bashrc内容
if [ -f /etc/bash.bashrc ]; then
  . /etc/bash.bashrc
fi

# 显示提示信息
PS1='\[\033[1;32m\]proot-ubuntu\[\033[0m\]:\[\033[1;34m\]\w\[\033[0m\]\\$ '
EOF

echo "创建初始化脚本..."
# 创建初始化脚本
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
printf "\033[1;33m提示: 输入 'exit' 可以退出proot环境\033[0m\n\n"
EOF

echo "设置初始化脚本执行权限..."
# 设置初始化脚本执行权限
chmod +x $ROOTFS_DIR/root/init.sh

echo "创建启动脚本..."
# 创建启动脚本
cat > $ROOTFS_DIR/start-proot.sh << EOF
#!/bin/bash
# 启动proot环境
echo "正在启动proot环境..."
cd $ROOTFS_DIR
$ROOTFS_DIR/usr/local/bin/proot \\
  --rootfs="$ROOTFS_DIR" \\
  -0 -w "/root" -b /dev -b /sys -b /proc -b /etc/resolv.conf --kill-on-exit \\
  /bin/bash -c "cd /root && /bin/bash /root/init.sh && /bin/bash"
EOF

chmod +x $ROOTFS_DIR/start-proot.sh

# 清屏并显示完成信息
clear
display_gg
echo -e "\n${CYAN}Ubuntu proot环境已安装完成!${RESET_COLOR}"
echo -e "${CYAN}使用以下命令启动proot环境:${RESET_COLOR}"
echo -e "${WHITE}    ./start-proot.sh${RESET_COLOR}"
echo -e "${CYAN}在proot环境中输入 'exit' 可以退出${RESET_COLOR}"
echo -e "${CYAN}如需删除所有配置和文件，请执行:${RESET_COLOR}"
echo -e "${WHITE}    ./root.sh del${RESET_COLOR}\n"

echo "是否立即启动proot环境? (y/n): "
read start_now

if [[ "$start_now" == "y" || "$start_now" == "Y" ]]; then
  echo "正在启动proot环境..."
  # 启动proot环境并执行初始化脚本
  cd $ROOTFS_DIR
  $ROOTFS_DIR/usr/local/bin/proot \
    --rootfs="${ROOTFS_DIR}" \
    -0 -w "/root" -b /dev -b /sys -b /proc -b /etc/resolv.conf --kill-on-exit \
    /bin/bash -c "cd /root && /bin/bash /root/init.sh && /bin/bash"
else
  echo "您可以稍后使用 ./start-proot.sh 命令启动proot环境"
fi
