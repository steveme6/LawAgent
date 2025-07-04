import requests
import logging
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

class BaseCrawler:
    """
    :param url: 目标网站接口
    :param headers: 自定义请求头
    :param max_retries: 最大重试次数
    :param backoff_factor: 重试延迟因子
    :param timeout: 请求超时时间(秒)
    :param request_delay: 请求间最小延迟(秒)
    :param logger: 自定义日志记录器
    """
    #初始化
    def __init__(self, url=None, headers=None, max_retries=3, backoff_factor=1, timeout=10,request_delay=1.0, logger=None, headless=True, driver_path=None):
        self.session = requests.Session()
        self.url=url.rstrip('/') if url else None
        self.headers = (headers or
                       {
                           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
                           'Accept': '*/*',
                           'Accept-Language': 'zh-CN,zh;q=0.9',
                           'Accept-Encoding': 'gzip, deflate, br, zstd',
                           'Connection': 'keep-alive',
                       })
        # 请求设置
        self.timeout = timeout
        self.request_delay = request_delay
        self.last_request_time = 0
        # 配置重试机制
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
            raise_on_status=False
        )
        # 日志设置
        self.logger = logger or logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # 如果没有配置日志处理器，添加一个默认的
        if not self.logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--window-size=1920,1080')
        if driver_path:
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)

    def get(self, url):
        self.driver.get(url)

    def wait_for_element(self, by, value, timeout=15):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def close(self):
        self.driver.quit()

    """确保请求之间有足够的延迟，避免高频访问"""
    def _enforce_delay(self):
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.request_delay:
            sleep_time = self.request_delay - elapsed
            self.logger.debug(f"强制延迟: {sleep_time:.2f}秒")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def fetch(self, url, method='GET', params=None, data=None, json=None, **kwargs):
        """
        执行HTTP请求，带重试和延迟控制

        :param url: 请求URL（可以是相对路径）
        :param method: HTTP方法
        :param params: 查询参数
        :param data: 表单数据
        :param json: JSON数据
        :return: 响应对象或None
        """
        # 确保请求延迟
        self._enforce_delay()

        try:
            # 执行请求
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json,
                timeout=self.timeout,
                **kwargs
            )

            # 检查响应状态
            response.raise_for_status()

            self.logger.info(f"成功获取: {url} [状态码: {response.status_code}]")
            return response

        except requests.RequestException as e:
            # 处理请求异常
            status_code = e.response.status_code if e.response else "N/A"
            self.logger.error(f"请求失败: {url} [状态码: {status_code}] - {str(e)}")
            return None

    def post(self, url, data=None, json=None, **kwargs):
        """POST请求快捷方法"""
        return self.fetch(url, 'POST', data=data, json=json, **kwargs)

    def __enter__(self):
        """支持with上下文管理"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时自动关闭会话"""
        self.close()
        if exc_type:
            self.logger.error(f"上下文错误: {exc_type} - {exc_val}")
