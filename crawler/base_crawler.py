class BaseCrawler:
    """基础爬虫类"""

    def __init__(self, headless=True, driver_path=None, logger=None):
        """
        初始化浏览器驱动

        :param headless: 是否使用无头模式
        :param driver_path: chromedriver路径
        :param logger: 日志记录器（可选）
        """
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.support.ui import WebDriverWait

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
        """访问指定URL"""
        self.driver.get(url)

    def close(self):
        """关闭浏览器"""
        self.driver.quit()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
