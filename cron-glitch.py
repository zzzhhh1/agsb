import time
import random
import requests
import logging
from datetime import datetime
import uuid
import platform
import json
import os
import argparse
import sys
import shutil
import subprocess
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("requests.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 默认目标URL
DEFAULT_URL = "https://seemly-organized-thing.glitch.me/"

# 解析命令行参数
def parse_arguments():
    parser = argparse.ArgumentParser(description='模拟真人访问网站，防止Glitch休眠')
    parser.add_argument('-u', '--url', type=str, default=DEFAULT_URL,
                        help=f'要访问的目标URL (默认: {DEFAULT_URL})')
    parser.add_argument('-i', '--interval', type=str, default="60-240",
                        help='请求间隔范围(秒)，格式为"最小值-最大值" (默认: "60-240")')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='显示详细日志')
    parser.add_argument('-d', '--delete', action='store_true',
                        help='删除指定URL的会话记录和Cookie')
    parser.add_argument('-c', '--clear-all', action='store_true',
                        help='清除所有会话记录和Cookie')
    parser.add_argument('-b', '--background', action='store_true',
                        help='在后台运行脚本(使用nohup)')
    parser.add_argument('-s', '--stop', action='store_true',
                        help='停止所有后台运行的脚本实例')
    parser.add_argument('-l', '--list', action='store_true',
                        help='列出所有正在运行的脚本实例')
    
    return parser.parse_args()

# 创建cookies目录
COOKIES_DIR = "cookies"
os.makedirs(COOKIES_DIR, exist_ok=True)

# 创建会话管理器
class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.url_sessions = {}  # 用于存储URL和会话ID的映射
        self.load_cookies()
        
    def load_cookies(self):
        """从文件加载已保存的cookie"""
        if not os.path.exists(COOKIES_DIR):
            return
            
        for file in os.listdir(COOKIES_DIR):
            if file.endswith('.json'):
                session_id = file.split('.')[0]
                try:
                    with open(os.path.join(COOKIES_DIR, file), 'r') as f:
                        data = json.load(f)
                        cookies = data.get('cookies', [])
                        url = data.get('url', '')
                        
                        session = requests.Session()
                        for cookie in cookies:
                            session.cookies.set(cookie['name'], cookie['value'])
                            
                        self.sessions[session_id] = {
                            'session': session,
                            'user_agent': '',
                            'last_used': datetime.now(),
                            'visit_count': 0,
                            'url': url
                        }
                        
                        # 添加URL到会话ID的映射
                        if url:
                            if url not in self.url_sessions:
                                self.url_sessions[url] = []
                            self.url_sessions[url].append(session_id)
                            
                        logger.info(f"已加载会话: {session_id} (URL: {url})")
                except Exception as e:
                    logger.error(f"加载cookie文件出错: {e}")
    
    def save_cookies(self, session_id, url=''):
        """保存会话cookie到文件"""
        if session_id not in self.sessions:
            return
            
        session = self.sessions[session_id]['session']
        cookies = []
        for cookie in session.cookies:
            cookies.append({
                'name': cookie.name,
                'value': cookie.value,
                'domain': cookie.domain,
                'path': cookie.path
            })
        
        # 保存会话数据，包括URL    
        data = {
            'cookies': cookies,
            'url': url
        }
            
        try:
            with open(os.path.join(COOKIES_DIR, f"{session_id}.json"), 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"保存cookie出错: {e}")
    
    def get_session(self, user_agent, headers, url=''):
        """获取或创建会话"""
        # 70%概率复用已有会话，30%概率创建新会话
        existing_sessions = []
        
        # 如果有URL对应的会话，优先使用
        if url in self.url_sessions:
            for session_id in self.url_sessions[url]:
                if session_id in self.sessions:
                    session_data = self.sessions[session_id]
                    if (datetime.now() - session_data['last_used']).total_seconds() < 86400:  # 24小时内的会话
                        existing_sessions.append((session_id, session_data))
        
        # 如果没有找到URL对应的会话，尝试使用任何可用会话
        if not existing_sessions:
            existing_sessions = [s for s in self.sessions.items() 
                                if (datetime.now() - s[1]['last_used']).total_seconds() < 86400]  # 24小时内的会话
        
        if existing_sessions and random.random() < 0.7:
            # 选择一个现有会话
            session_id, session_data = random.choice(existing_sessions)
            session_data['last_used'] = datetime.now()
            session_data['visit_count'] += 1
            session_data['url'] = url  # 更新URL
            
            # 更新User-Agent以保持一致性
            headers['user-agent'] = session_data['user_agent'] if session_data['user_agent'] else headers['user-agent']
            
            # 更新URL到会话ID的映射
            if url:
                if url not in self.url_sessions:
                    self.url_sessions[url] = []
                if session_id not in self.url_sessions[url]:
                    self.url_sessions[url].append(session_id)
                    
            logger.info(f"复用会话: {session_id} (访问次数: {session_data['visit_count']})")
            return session_id, session_data['session']
        else:
            # 创建新会话
            session_id = str(uuid.uuid4())[:8]
            session = requests.Session()
            
            # 配置重试策略
            retry_strategy = Retry(
                total=3,
                backoff_factor=0.3,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET", "POST"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            self.sessions[session_id] = {
                'session': session,
                'user_agent': headers['user-agent'],
                'last_used': datetime.now(),
                'visit_count': 1,
                'url': url
            }
            
            # 添加URL到会话ID的映射
            if url:
                if url not in self.url_sessions:
                    self.url_sessions[url] = []
                self.url_sessions[url].append(session_id)
                
            logger.info(f"创建新会话: {session_id}")
            return session_id, session
            
    def delete_url_sessions(self, url):
        """删除指定URL的所有会话"""
        if url not in self.url_sessions:
            logger.info(f"没有找到URL {url} 的会话")
            return 0
            
        count = 0
        for session_id in self.url_sessions[url][:]:  # 使用副本进行迭代
            if session_id in self.sessions:
                del self.sessions[session_id]
                
                # 删除对应的cookie文件
                cookie_file = os.path.join(COOKIES_DIR, f"{session_id}.json")
                if os.path.exists(cookie_file):
                    os.remove(cookie_file)
                    count += 1
                    
        # 清除URL映射
        del self.url_sessions[url]
        logger.info(f"已删除URL {url} 的 {count} 个会话")
        return count
        
    def clear_all_sessions(self):
        """清除所有会话和cookie"""
        # 清空会话字典
        self.sessions.clear()
        self.url_sessions.clear()
        
        # 删除cookies目录下的所有文件
        if os.path.exists(COOKIES_DIR):
            for file in os.listdir(COOKIES_DIR):
                if file.endswith('.json'):
                    os.remove(os.path.join(COOKIES_DIR, file))
                    
        logger.info("已清除所有会话和Cookie")

# 初始化会话管理器
session_manager = SessionManager()

# 预定义的真实User-Agent列表
REAL_USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    # Chrome macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    # Chrome Android
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    # Firefox macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0",
    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",
    # Safari macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    # Safari iOS
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
]

# 模拟真人的请求头
def get_headers():
    # 从预定义列表中随机选择User-Agent
    user_agent = random.choice(REAL_USER_AGENTS)
    
    # 从UA检测浏览器类型
    browser_info = detect_browser_from_ua(user_agent)
    browser_name = browser_info["browser"]
    platform_name = browser_info["platform"]
    browser_version = extract_version_from_ua(user_agent)
    
    # 生成sec-ch-ua值
    sec_ch_ua = generate_sec_ch_ua(browser_name, browser_version)
    
    # 根据平台设置移动标识
    is_mobile = platform_name in ["Android", "iPhone", "iPad"] or "Mobile" in user_agent or "Android" in user_agent
    mobile_flag = "?1" if is_mobile else "?0"
    
    # 构建请求头
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": random.choice(["zh-CN,zh;q=0.9", "en-US,en;q=0.9", "en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4", "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3"]),
        "cache-control": random.choice(["max-age=0", "no-cache", "max-age=0, private"]),
        "sec-ch-ua": sec_ch_ua,
        "sec-ch-ua-mobile": mobile_flag,
        "sec-ch-ua-platform": f'"{platform_name}"',
        "sec-fetch-dest": random.choice(["document", "empty"]),
        "sec-fetch-mode": random.choice(["navigate", "cors", "no-cors"]),
        "sec-fetch-site": random.choice(["none", "same-origin", "same-site"]),
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": user_agent
    }
    
    # 随机添加额外头信息
    if random.random() < 0.3:
        headers["referer"] = random.choice([
            "https://www.google.com/",
            "https://www.bing.com/",
            "https://search.yahoo.com/",
            "https://duckduckgo.com/"
        ])
    
    if random.random() < 0.2:
        headers["dnt"] = "1"  # Do Not Track
        
    if random.random() < 0.1:
        headers["pragma"] = "no-cache"
        
    if random.random() < 0.05:
        headers["x-requested-with"] = "XMLHttpRequest"
    
    # 随机添加客户端提示
    if random.random() < 0.3:
        viewport_width = random.choice([1280, 1366, 1440, 1536, 1600, 1920, 2560, 3440, 3840])
        viewport_height = int(viewport_width * random.uniform(0.5, 0.7))
        headers["viewport-width"] = str(viewport_width)
        headers["viewport-height"] = str(viewport_height)
        headers["device-memory"] = random.choice(["4", "8", "16"])
        headers["sec-ch-device-memory"] = random.choice(["4", "8", "16"])
        headers["sec-ch-viewport-width"] = str(viewport_width)
        headers["sec-ch-viewport-height"] = str(viewport_height)
        
    return headers

def extract_version_from_ua(user_agent):
    """从User-Agent提取版本号"""
    ua = user_agent.lower()
    version = "120"  # 默认版本
    
    # 尝试提取Chrome版本
    if "chrome/" in ua:
        try:
            chrome_part = ua.split("chrome/")[1]
            version = chrome_part.split(".")[0]
        except:
            pass
    # 尝试提取Firefox版本
    elif "firefox/" in ua:
        try:
            ff_part = ua.split("firefox/")[1]
            version = ff_part.split(".")[0]
        except:
            pass
    # 尝试提取Edge版本
    elif "edg/" in ua:
        try:
            edge_part = ua.split("edg/")[1]
            version = edge_part.split(".")[0]
        except:
            pass
    # 尝试提取Safari版本
    elif "version/" in ua and "safari" in ua:
        try:
            safari_part = ua.split("version/")[1]
            version = safari_part.split(".")[0]
        except:
            pass
            
    return version

def detect_browser_from_ua(user_agent):
    """从User-Agent检测浏览器类型和平台"""
    ua = user_agent.lower()
    browser = "Chrome"
    platform = "Windows"
    
    if "firefox" in ua:
        browser = "Firefox"
    elif "edg/" in ua:
        browser = "Edge"
    elif "safari" in ua and "chrome" not in ua:
        browser = "Safari"
    
    if "windows" in ua:
        platform = "Windows"
    elif "macintosh" in ua or "mac os" in ua:
        platform = "Macintosh"
    elif "linux" in ua and "android" not in ua:
        platform = "Linux"
    elif "android" in ua:
        platform = "Android"
    elif "iphone" in ua:
        platform = "iPhone"
    elif "ipad" in ua:
        platform = "iPad"
        
    return {"browser": browser, "platform": platform}

def generate_sec_ch_ua(browser, version):
    """生成适合浏览器的sec-ch-ua值"""
    if browser == "Chrome":
        return f'"Google Chrome";v="{version}", "Chromium";v="{version}", "Not/A)Brand";v="{random.randint(8, 99)}"'
    elif browser == "Firefox":
        return f'"Firefox";v="{version}", "Not)A;Brand";v="8"'
    elif browser == "Edge":
        return f'"Microsoft Edge";v="{version}", "Chromium";v="{int(version)-10}", "Not/A)Brand";v="{random.randint(8, 99)}"'
    elif browser == "Safari":
        return f'"Safari";v="{version}", "Not)A;Brand";v="8"'
    else:
        return f'"Google Chrome";v="{version}", "Chromium";v="{version}", "Not/A)Brand";v="{random.randint(8, 99)}"'

# 存储ETag以模拟浏览器缓存行为
etag = None

def simulate_human_behavior():
    """模拟人类浏览行为"""
    # 模拟页面加载后的行为
    behaviors = [
        {"action": "scroll_down", "probability": 0.7},
        {"action": "click_element", "probability": 0.3},
        {"action": "move_mouse", "probability": 0.5},
        {"action": "idle", "probability": 0.2}
    ]
    
    # 随机选择1-3个行为执行
    num_actions = random.randint(1, 3)
    selected_behaviors = random.sample(behaviors, num_actions)
    
    for behavior in selected_behaviors:
        if random.random() <= behavior["probability"]:
            action = behavior["action"]
            duration = random.uniform(0.5, 3.0)
            
            if action == "scroll_down":
                scroll_amount = random.randint(300, 1500)
                logger.info(f"模拟行为: 向下滚动 {scroll_amount}px ({duration:.1f}秒)")
            elif action == "click_element":
                logger.info(f"模拟行为: 点击页面元素 ({duration:.1f}秒)")
            elif action == "move_mouse":
                logger.info(f"模拟行为: 移动鼠标 ({duration:.1f}秒)")
            elif action == "idle":
                idle_time = random.uniform(2.0, 10.0)
                logger.info(f"模拟行为: 停留页面 ({idle_time:.1f}秒)")
                duration = idle_time
                
            time.sleep(duration)

def send_request(url):
    """发送请求并模拟真人行为"""
    global etag
    headers = get_headers()
    
    # 获取会话
    session_id, session = session_manager.get_session(headers['user-agent'], headers, url)
    
    # 如果有ETag，添加到请求头中
    if etag and random.random() < 0.9:  # 90%的概率使用缓存
        headers["if-none-match"] = etag
    
    # 随机添加指纹特征
    if random.random() < 0.1:
        # 模拟不同的网络条件
        headers["downlink"] = str(random.randint(5, 50))
        headers["rtt"] = str(random.randint(50, 250))
        headers["ect"] = random.choice(["4g", "3g"])
    
    try:
        # 模拟网络延迟
        network_delay = random.uniform(0.05, 0.3)  # 50-300ms的网络延迟
        time.sleep(network_delay)
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 发送请求
        response = session.get(url, headers=headers, timeout=10)
        
        # 计算请求时间
        request_time = time.time() - start_time
        
        # 记录ETag以便下次请求使用
        if 'etag' in response.headers:
            etag = response.headers['etag']
        
        # 保存会话cookies
        session_manager.save_cookies(session_id, url)
        
        # 记录请求信息
        logger.info(f"请求发送到 {url}")
        logger.info(f"会话ID: {session_id}")
        logger.info(f"状态码: {response.status_code}")
        logger.info(f"响应时间: {request_time:.2f}秒")
        logger.info(f"User-Agent: {headers['user-agent']}")
        logger.info(f"Platform: {headers['sec-ch-ua-platform']}")
        logger.info(f"Cookie数量: {len(session.cookies)}")
        
        # 只在状态码变化或非304状态时打印详细信息
        if response.status_code != 304:
            logger.info(f"响应头: {dict(response.headers)}")
            logger.info(f"响应内容: {response.text[:100]}..." if len(response.text) > 100 else f"响应内容: {response.text}")
        else:
            logger.info("内容未修改 (304 Not Modified)")
        
        # 模拟人类浏览行为
        if response.status_code == 200:
            simulate_human_behavior()
            
    except requests.exceptions.Timeout:
        logger.warning("请求超时")
    except requests.exceptions.ConnectionError:
        logger.warning("连接错误")
    except Exception as e:
        logger.error(f"发送请求时出错: {e}")

def run_in_background(args):
    """在后台运行脚本"""
    # 构建命令行参数，排除--background选项
    cmd = [sys.executable, sys.argv[0]]
    
    if args.url != DEFAULT_URL:
        cmd.extend(['--url', args.url])
    
    if args.interval != "60-240":
        cmd.extend(['--interval', args.interval])
    
    if args.verbose:
        cmd.append('--verbose')
    
    # 使用nohup在后台运行
    log_file = "glitch.log"
    nohup_cmd = ['nohup'] + cmd + ['>', log_file, '2>&1', '&']
    
    try:
        # 使用shell=True来执行命令，因为我们需要使用重定向符号
        subprocess.run(' '.join(nohup_cmd), shell=True)
        print(f"脚本已在后台启动，日志输出到 {log_file}")
        print("可以使用以下命令查看日志:")
        print(f"tail -f {log_file}")
        print("\n要停止脚本，请运行:")
        print(f"{sys.executable} {sys.argv[0]} --stop")
    except Exception as e:
        print(f"启动后台进程时出错: {e}")

def stop_background_processes():
    """停止所有后台运行的脚本实例"""
    try:
        # 获取脚本名称
        script_name = os.path.basename(sys.argv[0])
        
        # 使用ps和grep查找运行中的实例
        ps_cmd = f"ps aux | grep '{script_name}' | grep -v grep | grep -v stop"
        ps_output = subprocess.check_output(ps_cmd, shell=True, text=True)
        
        if not ps_output.strip():
            print("没有找到正在运行的脚本实例")
            return
        
        # 提取进程ID
        pids = []
        for line in ps_output.splitlines():
            parts = line.split()
            if len(parts) > 1:
                pids.append(parts[1])
        
        if not pids:
            print("没有找到正在运行的脚本实例")
            return
        
        # 终止进程
        for pid in pids:
            try:
                subprocess.run(['kill', pid])
                print(f"已终止进程ID: {pid}")
            except Exception as e:
                print(f"终止进程 {pid} 时出错: {e}")
        
        print(f"已停止 {len(pids)} 个脚本实例")
    except Exception as e:
        print(f"停止后台进程时出错: {e}")

def list_background_processes():
    """列出所有正在运行的脚本实例"""
    try:
        # 获取脚本名称
        script_name = os.path.basename(sys.argv[0])
        
        # 使用ps和grep查找运行中的实例
        ps_cmd = f"ps aux | grep '{script_name}' | grep -v grep | grep -v list"
        ps_output = subprocess.check_output(ps_cmd, shell=True, text=True)
        
        if not ps_output.strip():
            print("没有找到正在运行的脚本实例")
            return
        
        print("正在运行的脚本实例:")
        print("PID\t用户\t启动时间\t\t命令")
        print("-" * 80)
        
        for line in ps_output.splitlines():
            parts = line.split()
            if len(parts) > 9:
                pid = parts[1]
                user = parts[0]
                start_time = f"{parts[9]}"
                cmd = ' '.join(parts[10:])
                print(f"{pid}\t{user}\t{start_time}\t{cmd}")
    except Exception as e:
        print(f"列出后台进程时出错: {e}")

# 主循环，以随机间隔发送请求
def main():
    # 解析命令行参数
    args = parse_arguments()
    
    # 处理停止命令
    if args.stop:
        stop_background_processes()
        return
        
    # 处理列出进程命令
    if args.list:
        list_background_processes()
        return
    
    # 处理后台运行命令
    if args.background:
        run_in_background(args)
        return
    
    # 设置目标URL
    target_url = args.url
    
    # 处理删除操作
    if args.delete:
        count = session_manager.delete_url_sessions(target_url)
        logger.info(f"已删除URL {target_url} 的 {count} 个会话记录")
        return
        
    # 处理清除所有操作
    if args.clear_all:
        session_manager.clear_all_sessions()
        logger.info("已清除所有会话记录")
        return
    
    # 解析时间间隔
    try:
        min_interval, max_interval = map(int, args.interval.split('-'))
        if min_interval < 1:
            min_interval = 1
        if max_interval < min_interval:
            max_interval = min_interval + 60
    except:
        logger.warning("间隔格式无效，使用默认值 60-240 秒")
        min_interval, max_interval = 60, 240
    
    # 设置日志级别
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.info(f"开始运行脚本，模拟真人访问...")
    logger.info(f"目标URL: {target_url}")
    logger.info(f"请求间隔: {min_interval}-{max_interval} 秒")
    
    try:
        while True:
            # 确保每1-4分钟发送一次请求，防止Glitch休眠
            # 60%的概率在较短时间内请求
            # 40%的概率在较长时间内请求
            rand = random.random()
            if rand < 0.6:  # 60%的概率
                wait_time = random.randint(min_interval, (min_interval + max_interval) // 2)
            else:  # 40%的概率
                wait_time = random.randint((min_interval + max_interval) // 2, max_interval)
                
            current_time = datetime.now().strftime("%H:%M:%S")
            logger.info(f"当前时间: {current_time}, 等待 {wait_time} 秒...")
            
            # 不是精确等待，而是在目标时间上下浮动一点
            jitter = random.uniform(-3, 3)
            actual_wait = max(1, wait_time + jitter)
            time.sleep(actual_wait)
            
            send_request(target_url)
            
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序出错: {e}")
        
if __name__ == "__main__":
    main()
