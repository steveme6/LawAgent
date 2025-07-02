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
        time.sleep(4)

        print(f"页面标题: {crawler.driver.title}")
        print(f"当前URL: {crawler.driver.current_url}")

        # 等待分类列表加载
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        # 等待页面完全加载
        try:
            WebDriverWait(crawler.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            WebDriverWait(crawler.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.list.overflow'))
            )
            print("页面加载完成")
        except Exception as e:
            print(f"等待页面加载失败: {e}")

        # 专门获取法规类别标签下显示的分类
        print("获取法规类别标签下的所有分类...")
        law_categories = []
        time.sleep(3)

        try:
            # 点击法规类别下的"查看更多"按钮
            try:
                more_button = crawler.driver.find_element(
                    By.XPATH,
                    "//a[@logfunc='法规类别-查看更多' and contains(text(), '查看更多')]"
                )
                more_button.click()
                time.sleep(3)
                print("已点击'查看更多'")
            except Exception as e:
                print(f"未找到'查看更多'按钮: {e}")

            # 查找法规类别内容区域
            category_section = None
            xpath_patterns = [
                "//a[@searchname='Category' and contains(@logother, '法规类别')]/following-sibling::div[1]",
                "//a[@searchname='Category' and contains(@logother, '法规类别')]/../following-sibling::div[1]"
            ]

            for xpath in xpath_patterns:
                try:
                    category_section = crawler.driver.find_element(By.XPATH, xpath)
                    break
                except:
                    continue

            if category_section:
                # 查找span.node_name元素（真正的分类标题）
                node_name_elements = category_section.find_elements(By.XPATH, ".//span[@class='node_name']")

                seen_texts = set()
                for elem in node_name_elements:
                    try:
                        text = elem.text.strip()
                        if text and len(text) > 1 and text not in seen_texts:
                            seen_texts.add(text)
                            if text not in ['查看更多', '更多', '展开', '收起']:
                                law_categories.append(text)
                    except:
                        continue
            else:
                print("未找到法规类别内容区域")

        except Exception as e:
            print(f"获取法规分类失败: {e}")

        if law_categories:
            print(f"找到 {len(law_categories)} 个法规分类")
        else:
            print("未找到任何法规分类")
            law_categories = []

        # 保存分类信息
        all_categories_info = {
            "source": "法规类别标签",
            "total_count": len(law_categories),
            "categories": law_categories,
        }
        save_json([all_categories_info], "law_categories_from_regulation_tab.json")
        print("分类信息已保存")

        print(f"\n=== 处理完成 ===")
        print(f"成功识别法规类别标签下的 {len(law_categories)} 个分类：")
        for i, category in enumerate(law_categories, 1):
            print(f"{i}. {category}")
    except Exception as e:
        print(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("按回车键关闭浏览器...")  # 暂停以便观察
        crawler.close()
