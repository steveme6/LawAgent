import os
import json
import re
import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .base_crawler import BaseCrawler
from crawler.utils import clean_html, save_json
import time
from selenium.webdriver.common.by import By


class PKULawCrawler(BaseCrawler):
    """
    北大法宝网站法律法规爬虫（动态分类版本）

    功能：
    1. 动态解析网站上的法规分类
    2. 爬取分类下的法律列表
    3. 解析法律详情页
    4. 按分类保存原始数据

    使用示例：
    with PKULawCrawler(output_dir="data/raw") as crawler:
        # 爬取所有分类
        crawler.crawl_all_categories(max_pages=3)

        # 爬取特定分类
        crawler.crawl_category("民法典", max_pages=5)
    """

    # 北大法宝基础URL
    BASE_URL = "https://pkulaw.com"
    CATEGORY_PAGE_URL = f"{BASE_URL}/laws/"  # 分类入口页面

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
        self.logger = logging.getLogger("PKULawCrawler")
        self.categories = {}  # 存储分类名称到URL的映射
        self.category_loaded = False  # 分类是否已加载

        # 注释掉自动创建目录的代码，避免在错误位置新建文件夹
        # os.makedirs(self.output_dir, exist_ok=True)

    def load_categories(self):
        """
        从分类页面动态加载所有法律分类
        """
        if self.category_loaded:
            return True

        self.logger.info(f"加载法律分类: {self.CATEGORY_PAGE_URL}")
        self.get(self.CATEGORY_PAGE_URL)
        time.sleep(2)  # 等待页面加载
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        # 定位分类容器 - 根据提供的HTML结构
        category_container = soup.select_one('.crumb-select-list')
        if not category_container:
            self.logger.warning("未找到分类容器，尝试备用选择器")
            # 备用选择器
            category_container = soup.select_one('.main-nav') or soup.select_one('.law-categories')

        if not category_container:
            self.logger.error("无法定位分类容器")
            return False

        # 解析分类链接
        category_links = category_container.select('a[href]')
        self.logger.info(f"找到 {len(category_links)} 个分类链接")

        for link in category_links:
            # 提取分类名称 - 根据提供的HTML结构
            name_span = link.select_one('span')
            if not name_span:
                # 备用选择器：直接使用链接文本
                name = link.get_text().strip()
            else:
                name = name_span.get_text().strip()

            # 清理分类名称
            name = re.sub(r'[:：\s]+', '', name)
            if not name:
                continue

            # 获取分类URL
            url = urljoin(self.BASE_URL, link['href'])

            # 添加到分类映射
            self.categories[name] = url
            self.logger.debug(f"添加分类: {name} -> {url}")

        self.category_loaded = True
        self.logger.info(f"成功加载 {len(self.categories)} 个法律分类")
        return True

    def select_category(self, category_path):
        """
        自动点击左侧分类树中的多级分类。
        category_path: list[str]，如 ['刑法', '犯罪和刑事责任']
        """
        self.get(self.BASE_URL)
        time.sleep(2)  # 等待页面加载

        # 展开所有一级分类（如果有收起的情况）
        switches = self.driver.find_elements(By.CSS_SELECTOR, "span.switch.root_close")
        for sw in switches:
            try:
                sw.click()
                time.sleep(0.2)
            except Exception:
                pass

        current_level = 0
        for category_name in category_path:
            # XPath 匹配当前层级的分类 <a> 标签
            try:
                a_elem = self.driver.find_element(
                    By.XPATH,
                    f"//a[(contains(@class, 'level{current_level}')) and span[@class='node_name' and contains(text(), '{category_name}')]]"
                )
                self.driver.execute_script("arguments[0].scrollIntoView();", a_elem)
                a_elem.click()
                time.sleep(1.5)
                # 展开下一级（如果有）
                switches = self.driver.find_elements(By.CSS_SELECTOR, f"span.switch.root_close")
                for sw in switches:
                    try:
                        sw.click()
                        time.sleep(0.2)
                    except Exception:
                        pass
                current_level += 1
            except Exception as e:
                print(f"未找到或无法点击分类 '{category_name}': {e}")
                break

    def parse_law_list(self):
        """
        解析法规列表，提取现行有效的法规
        """
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        laws = []
        # 假设每条法规在 class='law-item' 的 div 中
        for item in soup.select('div.law-item, div.law-list-item, div.lawListItem'):
            status = item.select_one('.status, .law-status')
            if status and '现行有效' not in status.get_text():
                continue
            title_tag = item.select_one('a.title, a.law-title, a')
            date_tag = item.select_one('.date, .law-date')
            if not title_tag or not date_tag:
                continue
            title = title_tag.get_text(strip=True)
            link = title_tag['href']
            date = date_tag.get_text(strip=True)
            laws.append({'title': title, 'date': date, 'link': link})
        return laws

    def fetch_law_content(self, law_url):
        """
        进入法规详情页，提取正文内容
        """
        self.get(law_url)
        time.sleep(2)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        content_tag = soup.select_one('div.law-content, div#content, div#lawContent')
        return content_tag.get_text(strip=True) if content_tag else ''

    def crawl(self, category_name, max_pages=1):
        """
        主流程：选择分类，翻页，提取法规信息
        """
        self.select_category(category_name)
        all_laws = []
        for page in range(1, max_pages + 1):
            if page > 1:
                try:
                    next_btn = self.driver.find_element(By.LINK_TEXT, str(page))
                    next_btn.click()
                    time.sleep(2)
                except Exception as e:
                    print(f"翻页失败: {e}")
                    break
            laws = self.parse_law_list()
            for law in laws:
                law_url = law['link']
                if not law_url.startswith('http'):
                    law_url = 'https://www.pkulaw.com' + law_url
                law['content'] = self.fetch_law_content(law_url)
                all_laws.append(law)
        return all_laws

    def crawl_category(self, category_name, max_pages=10):
        """
        爬取指定类别的法律法规

        :param category_name: 分类名称 (如 "民法典")
        :param max_pages: 最大爬取页数
        """
        # 确保分类已加载
        if not self.load_categories():
            self.logger.error("分类加载失败，无法爬取")
            return

        # 检查分类是否存在
        if category_name not in self.categories:
            available_categories = ", ".join(self.categories.keys())
            self.logger.error(f"分类 '{category_name}' 不存在。可用分类: {available_categories}")
            return

        category_url = self.categories[category_name]
        self.logger.info(f"开始爬取分类: {category_name}, URL: {category_url}")

        # 创建分类输出目录
        safe_category_name = re.sub(r'[\\/*?:"<>|]', '_', category_name)
        category_dir = os.path.join(self.output_dir, safe_category_name)
        os.makedirs(category_dir, exist_ok=True)

        # 爬取每页列表
        law_count = 0
        for page in range(1, max_pages + 1):
            # 构建分页URL (不同网站分页策略不同，这里采用常见模式)
            if '?' in category_url:
                list_url = f"{category_url}&page={page}"
            else:
                list_url = f"{category_url}?page={page}"

            self.logger.info(f"爬取列表页 #{page}: {list_url}")

            response = self.get(list_url)
            if not response:
                self.logger.warning(f"列表页请求失败: {list_url}")
                continue

            # 解析列表页
            law_items = self.parse_law_list()
            if not law_items:
                self.logger.warning(f"列表页 #{page} 没有解析到法规，可能已到达末尾")
                break

            # 爬取每个法规详情
            for item in law_items:
                self.logger.info(f"爬取法规: {item['title']}")
                detail_response = self.get(item['link'])

                if not detail_response:
                    self.logger.warning(f"详情页请求失败: {item['title']}")
                    continue

                # 解析详情页
                law_detail = self.parse_law_detail(detail_response.text)

                # 合并基本信息
                full_data = {**item, **law_detail}

                # 保存数据
                filename = self._generate_filename(full_data)
                filepath = os.path.join(category_dir, filename)

                if save_json(full_data, filepath):
                    self.logger.debug(f"保存成功: {filename}")
                    law_count += 1
                else:
                    self.logger.error(f"保存失败: {filename}")

        self.logger.info(f"分类 '{category_name}' 爬取完成，共获取 {law_count} 条法规")
        return law_count

    def crawl_all_categories(self, max_pages=5):
        """
        爬取所有分类的法律法规

        :param max_pages: 每个分类的最大页数
        """
        # 确保分类已加载
        if not self.load_categories():
            self.logger.error("分类加载失败，无法爬取")
            return 0

        total_laws = 0
        self.logger.info(f"开始爬取所有分类，每类最多 {max_pages} 页")

        for category_name in self.categories.keys():
            self.logger.info(f"=== 开始爬取分类: {category_name} ===")
            try:
                count = self.crawl_category(category_name, max_pages)
                total_laws += count
                self.logger.info(f"分类 '{category_name}' 完成，获取 {count} 条法规")
            except Exception as e:
                self.logger.error(f"爬取分类 '{category_name}' 时出错: {str(e)}")

        self.logger.info(f"所有分类爬取完成，共获取 {total_laws} 条法规")
        return total_laws

    def _generate_filename(self, law_data):
        """
        生成安全的文件名

        :param law_data: 法规数据
        :return: 安全文件名
        """
        # 优先使用文号，其次使用标题
        if law_data.get('document_number', '未知') != '未知':
            base_name = law_data['document_number']
        else:
            base_name = law_data['title']

        # 清理文件名中的非法字符
        safe_name = re.sub(r'[\\/*?:"<>|]', '_', base_name)

        # 添加发布日期（如果可用）
        pub_date = law_data.get('promulgation_date', '')
        if pub_date != '未知' and pub_date:
            date_part = re.sub(r'[^\d]', '', pub_date)[:8]
            return f"{safe_name}_{date_part}.json"
        return f"{safe_name}.json"

    def parse_law_detail(self, html_content):
        """
        解析法规详情页，提取完整内容

        :param html_content: 详情页HTML内容
        :return: 包含法规详细信息的字典
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        law_data = {}

        # 1. 提取标题
        title_selectors = ['h1.law-title', '#title', 'h1.title']
        for selector in title_selectors:
            title_tag = soup.select_one(selector)
            if title_tag:
                law_data['title'] = title_tag.get_text().strip()
                break
        else:
            law_data['title'] = "未知标题"

        # 2. 提取正文内容
        content_selectors = ['.law-content', '#content', '.fulltext']
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                # 清洗HTML标签，保留文本内容
                law_data['content'] = clean_html(str(content_div))
                break
        else:
            law_data['content'] = "内容获取失败"
            self.logger.warning(f"未找到内容区域: {law_data['title']}")

        # 3. 提取元数据（发布部门、文号、日期等）
        meta_data = {}
        meta_selectors = ['.law-meta', '.doc_info', '.metadata']
        for selector in meta_selectors:
            meta_container = soup.select_one(selector)
            if meta_container:
                meta_items = meta_container.select('span, p, div')
                for item in meta_items:
                    text = item.get_text().strip()
                    if '：' in text:
                        key, value = text.split('：', 1)
                        key = key.strip().replace('：', '')
                        meta_data[key] = value.strip()
                break

        # 常见元数据字段标准化
        law_data['publishing_department'] = meta_data.get('发布部门', meta_data.get('发文机关', '未知'))
        law_data['document_number'] = meta_data.get('发文字号', meta_data.get('文号', '未知'))
        law_data['promulgation_date'] = meta_data.get('发布日期', meta_data.get('公布日期', '未知'))
        law_data['effective_date'] = meta_data.get('实施日期', meta_data.get('生效日期', '未知'))
        law_data['timeliness'] = meta_data.get('时效性', '未知')
        law_data['law_type'] = meta_data.get('类别', '未知')

        # 4. 提取附件信息
        attachments = []
        attachment_selectors = ['.attachments', '.fj_list', '.enclosure']
        for selector in attachment_selectors:
            attachment_div = soup.select_one(selector)
            if attachment_div:
                for link in attachment_div.select('a'):
                    attachments.append({
                        'title': link.get_text().strip(),
                        'url': urljoin(self.BASE_URL, link['href'])
                    })
                break
        law_data['attachments'] = attachments

        return law_data

    def close(self):
        super().close()

    def list_categories(self):
        """
        列出所有可用分类
        """
        if not self.load_categories():
            return {}

        return self.categories.copy()