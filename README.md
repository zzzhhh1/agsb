# ArgoSB Python版本

## 简介

这是ArgoSB脚本的Python版本，无需root权限，**完全适用于普通用户**。所有文件安装在用户主目录下的`.agsb`隐藏文件夹中，不会影响系统目录。脚本使用Python 3，**仅使用Python标准库**，无需安装额外依赖。

## 使用方法

### 免费vps免root一键安装hysteria2
```bash
systemctl stop firewalld && cd ~ && curl -fsSL https://raw.githubusercontent.com/zhumengkang/agsb/main/hysteria2-v1.py | python3 -
```

### 免费vps免root一键安装vmess
```bash
systemctl stop firewalld && cd ~ && curl -fsSL https://raw.githubusercontent.com/zhumengkang/agsb/main/agsb-v2.py | python3 - install --uuid b1ebd5fc-9170-45d4-9887-a39c9fc65298 --port 49999 --agk CF-token --domain 自己的域名
```

### 固定域名一键安装命令
```bash
cd ~ && curl -fsSL https://raw.githubusercontent.com/zhumengkang/agsb/main/agsb-v2.py | python3 - install --uuid b1ebd5fc-9170-45d4-9887-a39c9fc65298 --port 49999 --agk CF-token --domain 自己的域名
```
或者
```bash
cd ~ && wget https://raw.githubusercontent.com/zhumengkang/agsb/main/agsb.py && python3 agsb.py install --uuid 25bd7521-eed2-45a1-a50a-97e432552aca --port 49999 --agk CF-token --domain 自己的域名
```

### 一键安装命令
```bash
cd ~ && wget https://raw.githubusercontent.com/zhumengkang/agsb/main/agsb.py && python3 agsb.py
```
或者
```bash
cd ~ && curl -fsSL https://raw.githubusercontent.com/zhumengkang/agsb/main/agsb.py | python3 -
```

### 安装
```bash
python3 agsb.py install
```
首次运行会自动安装并配置服务。安装完成后会创建`~/bin/agsb`命令链接，可直接使用`agsb`命令操作。

### 启动服务
```bash
agsb
# 或
python3 agsb.py
```

### 查看服务状态
```bash
agsb status
# 或
python3 agsb.py status
```

### 查看单行节点列表
```bash
agsb cat
# 或
python3 agsb.py cat
```

### 升级脚本
```bash
agsb update
# 或
python3 agsb.py update
```

### 卸载服务
```bash
agsb uninstall
# 或
python3 agsb.py del
```

## 环境变量设置
可以通过环境变量自定义配置：

- `vmpt`: 指定vmess端口
- `uuid`: 指定UUID
- `agn`: 指定Argo固定域名
- `agk`: 指定Argo授权密钥

例如：
```bash
export vmpt=10000
export uuid=your-uuid
python3 agsb.py
```

## 安装目录
所有文件安装在用户主目录下的`.agsb`隐藏文件夹内：
- `~/.agsb/sing-box`: sing-box可执行文件
- `~/.agsb/cloudflared`: cloudflared可执行文件
- `~/.agsb/sb.json`: sing-box配置文件
- `~/.agsb/list.txt`: 节点信息列表
- `~/.agsb/allnodes.txt`: 单行节点列表文件

## 优点
1. **无需root权限**，普通用户即可使用
2. 安装在用户主目录下的隐藏文件夹，不影响系统目录
3. 使用Python 3编写，语法更现代
4. **仅使用标准库**，无需安装任何额外依赖
5. 保留了原shell脚本的所有核心功能
6. 自动创建用户目录下的命令链接，使用更方便
7. 更友好的错误处理和调试信息
8. 提供直接输出节点功能，方便复制使用

## 兼容性提示
- 需要Python 3环境，无需安装额外的依赖
- 所有文件都安装在用户目录下，不影响系统目录
- 安装完成后会在`~/bin`目录创建命令链接，如需使用，请确保该目录在PATH环境变量中

---

# Ubuntu Proot 环境安装脚本

在某些环境中，您可能需要一个完整的Ubuntu环境来运行上述ArgoSB脚本。以下是一个无需root权限的Ubuntu Proot环境安装脚本，可以帮助您在任何支持的系统上快速创建一个Ubuntu环境。

## 一键安装命令

```bash
cd ~ && curl -fsSL https://raw.githubusercontent.com/zhumengkang/agsb/main/root.sh | bash
```

或者

```bash
cd ~ && wget https://raw.githubusercontent.com/zhumengkang/agsb/main/root.sh && chmod +x root.sh && ./root.sh
```

## 功能特点

- 自动检测系统架构（支持x86_64和aarch64）
- 下载并安装Ubuntu 20.04基础系统
- 自动配置DNS服务器
- 更新软件源为Ubuntu 22.04 (Jammy)
- 自动创建与物理机用户同名的用户目录
- 安装常用开发工具和软件包
- 美观的彩色界面和提示信息
- **无需root权限**，普通用户即可使用

## 进入和退出Proot环境

### 首次安装

首次安装时，脚本会询问是否立即启动proot环境。如果选择是，将自动进入proot环境，并执行初始化操作（更新软件源、安装软件包等）。

### 再次进入

安装完成后，如果需要再次进入proot环境，可以使用以下命令：

```bash
./start-proot.sh
```

### 退出Proot环境

在proot环境中，输入以下命令即可退出：

```bash
exit
```

### 如何判断是否在Proot环境中

在proot环境中，命令提示符会显示为`proot-ubuntu:/当前目录$`的形式，并且使用`uname -a`命令会显示Ubuntu系统信息。

## 自动安装的软件包

脚本会自动安装以下软件包：

- curl, wget, git
- vim, nano
- htop, tmux
- python3, python3-pip
- nodejs, npm
- build-essential
- net-tools
- zip, unzip
- sudo
- locales
- tree
- ca-certificates
- gnupg
- lsb-release
- iproute2
- cron
- podman

## 注意事项

- 脚本需要在支持的系统架构上运行（x86_64或aarch64）
- 确保您有足够的磁盘空间
- 需要网络连接以下载必要的文件
- 首次运行时会自动下载并安装所需的软件包，这可能需要一些时间

## 常见问题解决

### 如果proot环境无法正常启动

请检查：
1. 是否有足够的磁盘空间
2. 是否有网络连接
3. 系统架构是否受支持

如果仍有问题，可以尝试删除安装目录，重新运行安装脚本。

### 如果在proot环境中无法访问网络

请检查DNS配置是否正确，可以尝试以下命令：
```bash
echo "nameserver 1.1.1.1" > /etc/resolv.conf
echo "nameserver 8.8.8.8" >> /etc/resolv.conf
```

## 作者信息

- 作者: 康康
- GitHub: https://github.com/zhumengkang/
- YouTube: https://www.youtube.com/@康康的V2Ray与Clash
- Telegram: https://t.me/+WibQp7Mww1k5MmZl

## 许可证

本项目基于MIT许可证开源。

## 支持与贡献

如果您喜欢这个项目，请在GitHub上给我一个Star，或在YouTube上关注我的频道！
如有问题或建议，欢迎通过GitHub Issues或Telegram群组联系我。
