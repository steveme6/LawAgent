from crawler.pkulaw_crawler import PKULawCrawler
from crawler.utils import save_json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
import pyperclip  # 用于访问剪贴板
import re
import os  # 新增导入os模块

# 指定 chromedriver 路径（请根据实际情况修改）
CHROMEDRIVER_PATH = r"D:\chromedriver-win64\chromedriver.exe"  # 使用原始字符串避免转义问题

def crawl_law_details(crawler, law_link):
    """
    爬取单个法案的详细信息
    """
    # 获取法案标题和链接
    title = law_link.text.strip()
    href = law_link.get_attribute('href')

    print(f"正在爬取法案: {title}")

    # 打开新窗口访问法案详情页
    crawler.driver.execute_script("window.open(arguments[0]);", href)
    crawler.driver.switch_to.window(crawler.driver.window_handles[-1])

    time.sleep(2)

    # 获取法案详情
    law_detail = {
        'title': title,
        'url': href,
        'content': '',
        'metadata': {}
    }

    try:
        # 清空剪贴板
        pyperclip.copy('')

        # 尝试点击"复制全文"按钮获取内容
        copy_button = WebDriverWait(crawler.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@logfunc='复制全文' and @name='linkCopyFulltext']"))
        )
        copy_button.click()
        print("已点击'复制全文'按钮")
        time.sleep(2)

        # 从剪贴板获取内容
        clipboard_content = pyperclip.paste()
        if clipboard_content and clipboard_content.strip():
            law_detail['content'] = clipboard_content.strip()

        # 获取元数据（发布时间、生效时间等）
        metadata_elems = crawler.driver.find_elements(By.CSS_SELECTOR, '.law-info span, .meta-info span, .MTitle')
        for elem in metadata_elems:
            text = elem.text.strip()
            if elem.get_attribute('class') == 'MTitle':
                # 获取标题信息
                law_detail['metadata']['完整标题'] = text

    except Exception as e:
        print(f"获取法案详情失败: {e}")

    # 关闭当前标签页，返回主页面
    crawler.driver.close()
    crawler.driver.switch_to.window(crawler.driver.window_handles[0])

    return law_detail



def extract_total_laws_from_category(category_text):
    """
    从分类文本中提取法案总数，如 "宪法 (2552)" -> 2552
    """
    match = re.search(r'\((\d+)\)', category_text)
    if match:
        return int(match.group(1))
    return 0

def crawl_category_laws(crawler, category_name, total_laws_count, max_pages=10):
    """
    爬取指定分类下的所有法案，按浏览量排序并筛选前1/20
    """
    all_laws = []
    current_page = 1

    # 计算需要爬取的法案数量（总数的1/20）
    target_laws_count = min(200, total_laws_count // 20)  # 至少爬取1个法案
    print(f"\n开始爬取分类: {category_name}（总共{total_laws_count}个法案，目标爬取{target_laws_count}个）")

    # 只在第一次进入分类时点击时效性、浏览量、更多按钮
    # 1. 点击时效性按钮
    effectiveness_button = WebDriverWait(crawler.driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//span[text()='时效性']"))
    )
    effectiveness_button.click()
    print("已点击时效性按钮")
    time.sleep(2)

    # 2. 点击浏览量按钮进行排序（从大到小）
    browse_count_button = WebDriverWait(crawler.driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//span[text()='浏览量']"))
    )
    browse_count_button.click()
    print("已点击浏览量按钮进行排序")
    time.sleep(3)  # 等待排序完成

    # 3. 最后点击"现行有效"同一行的"更多"按钮
    more_button = WebDriverWait(crawler.driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[@logfunc='分组栏目-右上角更多' and @class='more' and text()='更多']"))
    )
    more_button.click()
    print("已点击'现行有效'的'更多'按钮")
    time.sleep(2)

    crawled_count = 0
    while current_page <= max_pages and crawled_count < target_laws_count:
        print(f"\n=== 第 {current_page} 页 ===")


        # 等待页面加载完成
        WebDriverWait(crawler.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[flink="true"]'))
        )

        # 获取当前页面的所有法案链接，排除朗读链接
        law_links = crawler.driver.find_elements(
            By.XPATH,
            '//a[@flink="true" and @logfunc="文章点击" and contains(@href, "/chl/") and contains(@href, ".html")]'
        )
        print(f"找到 {len(law_links)} 个法案链接")

        if not law_links:
            print("未找到法案链接，结束爬取")
            break

        # 爬取每个法案的详情，但不超过目标数量
        page_laws = []
        remaining_needed = target_laws_count - crawled_count
        laws_to_process = min(len(law_links), remaining_needed)

        for i, law_link in enumerate(law_links[:laws_to_process], 1):
            print(f"处理第 {i}/{laws_to_process} 个法案（总进度: {crawled_count + 1}/{target_laws_count}）")
            law_detail = crawl_law_details(crawler, law_link)
            if law_detail:
                page_laws.append(law_detail)
                crawled_count += 1

            # 避免请求过于频繁
            time.sleep(1)

            # 如果已达到目标数量，停止爬取
            if crawled_count >= target_laws_count:
                break

        all_laws.extend(page_laws)
        print(f"第 {current_page} 页完成，爬取了 {len(page_laws)} 个法案")

        # 如果已达到目标数量，停止爬取
        if crawled_count >= target_laws_count:
            print(f"已达到目标数量 {target_laws_count}，停止爬取")
            break

        # 尝试点击下一页
        try:
            next_page_button = WebDriverWait(crawler.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '下一页') and @href='javascript:void(0);']"))
            )
            next_page_button.click()
            print("已点击下一页")
            time.sleep(3)
            current_page += 1
        except TimeoutException:
            print("未找到下一页按钮或已到最后一页")
            break

    print(f"分类 '{category_name}' 爬取完成，共爬取 {len(all_laws)} 个法案")
    return all_laws

if __name__ == '__main__':
    # 计算正确的data/raw目录路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_raw_dir = os.path.join(os.path.dirname(script_dir), "data", "raw")

    crawler = PKULawCrawler(output_dir=data_raw_dir, headless=False, driver_path=CHROMEDRIVER_PATH)
    try:
        print(f"正在访问页面: {crawler.base_url}")
        crawler.get(crawler.base_url)

        # 等待页面加载完成，检查是否出现安全提示
        time.sleep(2)

        print(f"页面标题: {crawler.driver.title}")
        print(f"当前URL: {crawler.driver.current_url}")

        # 专门获取法规类别标签下显示的分类
        print("获取法规类别标签下的所有分类...")
        law_categories = []
        time.sleep(2)


        # 点击法规类别下的"查看更多"按钮
        more_button = crawler.driver.find_element(
            By.XPATH,
            "//a[@logfunc='法规类别-查看更多' and contains(text(), '查看更多')]"
        )
        more_button.click()
        time.sleep(3)
        print("已点击'查看更多'")


        # 查找法规类别内容区域
        category_section = crawler.driver.find_element(By.XPATH,"//a[@searchname='Category' and contains(@logother, '法规类别')]/../following-sibling::div[1]")
        # 查找span.node_name元素（真正的分类标题）
        node_name_elements = category_section.find_elements(By.XPATH, ".//span[@class='node_name']")

        for elem in node_name_elements:
            text = elem.text.strip()
            if text not in ['查看更多', '更多', '展开', '收起']:
                law_categories.append(text)
            else:
                continue


        if law_categories:
            print(f"找到 {len(law_categories)} 个法规分类")

        # 保存分类信息
        all_categories_info = {
            "source": "法规类别标签",
            "total_count": len(law_categories),
            "categories": law_categories,
        }

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(project_root, "data")
        os.makedirs(data_dir, exist_ok=True)
        categories_file_path = os.path.join(data_dir, "law_categories_from_regulation_tab.json")
        save_json([all_categories_info], categories_file_path)
        print(f"分类信息已保存到: {categories_file_path}")

        print(f"\n=== 开始爬取各分类下的法案 ===")

        # 为每个分类爬取法案
        all_category_data = {}
        for i, category in enumerate(law_categories[:], 1):
            print(f"\n处理分类 {i}/{len(law_categories)}: {category}")

            # 提取该分类的法案总数
            total_laws_count = extract_total_laws_from_category(category)


            # 确保返回主页面（如果不在主页面的话）
            if crawler.driver.current_url != crawler.base_url:
                print("返回主页面...")
                crawler.get(crawler.base_url)
                time.sleep(3)

                # 重新点击法规类别的"查看更多"按钮
                more_button = crawler.driver.find_element(
                    By.XPATH,
                    "//a[@logfunc='法规类别-查看更多' and contains(text(), '查看更多')]"
                )
                more_button.click()
                time.sleep(3)
                print("重新点击'查看更多'")


            # 点击分类
            category_link = crawler.driver.find_element(
                By.XPATH,
                f"//span[@class='node_name' and text()='{category}']/.."
            )
            category_link.click()
            time.sleep(2)

            # 爬取该分类下的法案，传入总数用于计算目标爬取数量
            category_laws = crawl_category_laws(crawler, category, total_laws_count, max_pages=10)

            all_category_data[category] = {
                'category_name': category,
                'total_laws_in_category': total_laws_count,
                'target_laws_count': min(200, total_laws_count // 20),
                'actual_crawled_count': len(category_laws),
                'laws': category_laws
            }

            print(f"分类 '{category}' 完成，共爬取 {len(category_laws)} 个法案")

            # 保存当前分类的数据
            safe_filename = category.replace('/', '_').replace('(', '').replace(')', '').replace(' ', '_')
            # 确保保存到正确的data/raw目录（与crawler同级的data/raw目录）
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_raw_dir = os.path.join(project_root, "data", "raw")
            os.makedirs(data_raw_dir, exist_ok=True)
            output_path = os.path.join(data_raw_dir, f"laws_{safe_filename}.json")
            save_json([all_category_data[category]], output_path)
            print(f"分类 '{category}' 数据已保存到: {output_path}")


        print(f"\n=== 爬取完成 ===")
        print(f"处理了 {len(all_category_data)} 个分类")

    except Exception as e:
        print(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("按回车键关闭浏览器...")  # 暂停以便观察
        crawler.close()