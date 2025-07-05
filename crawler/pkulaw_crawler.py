from .base_crawler import BaseCrawler


class PKULawCrawler(BaseCrawler):
    """
    北大法宝网站法律法规爬虫
    """

    # 北大法宝基础URL
    BASE_URL = "https://pkulaw.com"

    def __init__(self, output_dir="data/raw", headless=True, driver_path=None, logger=None):
        """
        初始化北大法宝爬虫

        :param output_dir: 数据输出目录
        :param headless: 是否使用无头浏览器
        :param driver_path: 浏览器驱动路径
        :param logger: 日志记录器
        """
        super().__init__(
            headless=headless,
            driver_path=driver_path,
            logger=logger
        )
        self.base_url = self.BASE_URL
        self.output_dir = output_dir

    def close(self):
        """关闭浏览器"""
        super().close()
