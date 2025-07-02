from crawler.pkulaw_crawler import PKULawCrawler
from crawler.utils import save_json
from selenium.webdriver.common.by import By
import time

# 指定 chromedriver 路径（请根据实际情况修改）
CHROMEDRIVER_PATH = r"D:\chromedriver-win64\chromedriver.exe"  # 使用原始字符串避免转义问题

if __name__ == '__main__':
    crawler = PKULawCrawler(headless=False, driver_path=CHROMEDRIVER_PATH)  # 先用非无头模式测试
    try:
        print(f"正在访问页面: {crawler.base_url}")
        crawler.get(crawler.base_url)

        # 等待页面加载完成，检查是否出现安全提示
        time.sleep(4)  # 增加等待时间

        print(f"页面标题: {crawler.driver.title}")
        print(f"当前URL: {crawler.driver.current_url}")


        # 等待分类列表加载
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        # 等待页面完全加载，但不要点击法规类别标签
        try:
            print("等待页面完全加载...")

            # 等待页面完全加载 - 使用更宽松的条件
            try:
                WebDriverWait(crawler.driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                print("页面body已加载")
            except Exception as e:
                print(f"等待body失败: {e}，继续尝试...")

            # 等待分类列表出现 - 使用多个可能的选择器
            list_loaded = False
            selectors_to_try = [
                'ul.list.overflow',
                '.classify-list',
                '.category-list',
                'ul',
                '.list',
                'li.level0'
            ]

            for selector in selectors_to_try:
                try:
                    WebDriverWait(crawler.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"找到分类列表: {selector}")
                    list_loaded = True
                    break
                except:
                    continue

            if list_loaded:
                print("页面加载完成，分类列表已显示")
            else:
                print("未找到预期的分类列表，但继续尝试处理")

        except Exception as e:
            print(f"等待页面加载出现问题: {e}")
            print("跳过等待，直接尝试处理页面内容")

        # 专门获取法规类别标签下显示的分类（不点击标签本身）
        print("获取法规类别标签下的所有分类...")
        law_categories = []

        # 先简单等待一下让页面稳定
        time.sleep(3)

        try:
            # 首先查找并点击法规类别下的"查看更多"按钮
            try:
                print("查找法规类别下的'查看更多'按钮...")
                more_button = crawler.driver.find_element(
                    By.XPATH,
                    "//a[@logfunc='法规类别-查看更多' and contains(text(), '查看更多')]"
                )

                print("找到法规类别的'查看更多'按钮，点击展开...")
                more_button.click()
                time.sleep(3)  # 等待内容加载
                print("已点击'查看更多'，等待内容加载完成")

            except Exception as e:
                print(f"未找到或无法点击'查看更多'按钮: {e}")
                print("继续尝试获取当前可见的分类")

            # 查找法规类别标签对应的内容区域
            try:
                print("查找法规类别标签后的内容区域...")

                # 尝试多种XPath来查找法规类别相关的内容
                category_section = None
                xpath_patterns = [
                    "//a[@searchname='Category' and contains(@logother, '法规类别')]/following-sibling::div[1]",
                    "//a[@searchname='Category' and contains(@logother, '法规类别')]/../following-sibling::div[1]",
                    "//a[contains(@logother, '法规类别')]/following-sibling::*[1]",
                    "//a[contains(text(), '法规类别')]/following-sibling::div",
                    "//*[contains(@logother, '法规类别')]/following-sibling::div"
                ]

                for xpath in xpath_patterns:
                    try:
                        category_section = crawler.driver.find_element(By.XPATH, xpath)
                        print(f"找到法规类别内容区域: {xpath}")
                        break
                    except:
                        continue

                if category_section:
                    print("找到法规类别内容区域，获取其中的分类...")

                    # 首先尝试获取整个区域的文本，然后解析
                    section_text = category_section.text.strip()
                    print(f"法规类别区域文本内容: {section_text}")

                    # 在该区域内查找所有分类链接或文本
                    category_items = []

                    # 专门查找span.node_name元素（这是真正的分类标题）
                    print("查找span.node_name元素...")
                    try:
                        node_name_elements = category_section.find_elements(By.XPATH, ".//span[@class='node_name']")
                        print(f"找到 {len(node_name_elements)} 个 node_name 元素")

                        for i, elem in enumerate(node_name_elements):
                            try:
                                elem_text = elem.text.strip()
                                if elem_text:
                                    print(f"  分类 {i+1}: {elem_text}")
                                    category_items.append(elem)
                            except:
                                print(f"  分类 {i+1}: 无法获取文本")

                    except Exception as e:
                        print(f"查找node_name元素失败: {e}")

                    # 如果没找到node_name元素，尝试其他方式
                    if not category_items:
                        print("未找到node_name元素，尝试其他选择器...")
                        # 尝试查找其他可能的分类元素
                        backup_selectors = [
                            ".//span[contains(@class, 'node_name')]",  # 包含node_name类的span
                            ".//span[contains(@id, '_span')]",  # id包含_span的span元素
                            ".//a[contains(@class, 'level')]/span",  # level类链接下的span
                        ]

                        for i, selector in enumerate(backup_selectors):
                            try:
                                elements = category_section.find_elements(By.XPATH, selector)
                                print(f"备用选择器 {i+1} ({selector}): 找到 {len(elements)} 个元素")

                                if elements:
                                    category_items.extend(elements)
                                    # 显示前几个元素的文本
                                    for j, elem in enumerate(elements[:3]):
                                        try:
                                            elem_text = elem.text.strip()
                                            if elem_text:
                                                print(f"  元素 {j+1}: {elem_text}")
                                        except:
                                            print(f"  元素 {j+1}: 无法获取文本")
                                    break  # 找到元素就停止尝试其他选择器
                            except Exception as e:
                                print(f"备用选择器 {i+1} 失败: {e}")

                    print(f"总共找到 {len(category_items)} 个候选元素")

                    # 如果还是没找到元素，直接解析区域文本
                    if not category_items and section_text:
                        print("直接解析区域文本内容...")
                        # 按行分割文本，尝试提取分类名称
                        text_lines = [line.strip() for line in section_text.split('\n') if line.strip()]
                        for line in text_lines:
                            if line and len(line) > 1:
                                # 创建模拟的文本项
                                class TextItem:
                                    def __init__(self, text):
                                        self.text = text
                                category_items.append(TextItem(line))
                        print(f"从文本中解析出 {len(category_items)} 个候选项")

                    # 处理找到的分类项
                    seen_texts = set()
                    for item in category_items:
                        try:
                            text = item.text.strip()
                            if text and len(text) > 1 and text not in seen_texts:
                                seen_texts.add(text)
                                # 过滤掉"查看更多"等非分类文本
                                if text not in ['查看更多', '更多', '展开', '收起']:
                                    law_categories.append(text)
                                    print(f"找到法规类别: {text}")
                        except:
                            continue

                else:
                    print("未找到法规类别内容区域")

            except Exception as e:
                print(f"查找法规类别内容失败: {e}")

        except Exception as e:
            print(f"获取法规类别标签下的分类时出现错误: {e}")
            print("尝试使用其他方式获取分类")

        if law_categories:
            print(f"\n=== 法规类别标签下找到的所有分类 ===")
            for i, category in enumerate(law_categories, 1):
                print(f"{i}. {category}")
            print(f"总计: {len(law_categories)} 个法规分类\n")

            # 将找到的法规分类设为处理目标
            first_level_names = law_categories
        else:
            print("未找到任何法规分类")

        # 保存所有法规分类到一个JSON文件
        all_categories_info = {
            "source": "法规类别标签",
            "total_count": len(first_level_names),
            "categories": first_level_names,
        }
        save_json([all_categories_info], "law_categories_from_regulation_tab.json")
        print("分类信息已保存到 law_categories_from_regulation_tab.json")

        print(f"\n=== 处理完成 ===")
        print(f"成功识别法规类别标签下的 {len(first_level_names)} 个分类：")
        for i, category in enumerate(first_level_names, 1):
            print(f"{i}. {category}")
    except Exception as e:
        print(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("按回车键关闭浏览器...")  # 暂停以便观察
        crawler.close()
