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

# 指定 chromedriver 路径（请根据实际情况修改）
CHROMEDRIVER_PATH = r"D:\chromedriver-win64\chromedriver.exe"  # 使用原始字符串避免转义问题

def crawl_law_details(crawler, law_link):
    """
    爬取单个法案的详细信息
    """
    try:
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
            try:
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
                    print("成功从剪贴板获取法案内容")
                else:
                    print("剪贴板为空，尝试其他方法获取内容")
                    # 如果剪贴板为空，使用原来的方法获取内容
                    content_selectors = [
                        '#divFullText',  # 主要的正文内容容器
                        '.fulltext',     # 备用选择器
                        '.law-content',
                        '.article-content',
                        '.content-body',
                        '#lawcontent',
                        '.main-content'
                    ]

                    for selector in content_selectors:
                        try:
                            content_elem = crawler.driver.find_element(By.CSS_SELECTOR, selector)
                            law_detail['content'] = content_elem.text.strip()
                            print(f"成功获取正文内容，使用选择器: {selector}")
                            break
                        except NoSuchElementException:
                            continue

            except TimeoutException:
                print("未找到'复制全文'按钮，使用备用方法获取内容")
                # 使用原来的方法获取内容
                content_selectors = [
                    '#divFullText',  # 主要的正文内容容器
                    '.fulltext',     # 备用选择器
                    '.law-content',
                    '.article-content',
                    '.content-body',
                    '#lawcontent',
                    '.main-content'
                ]

                for selector in content_selectors:
                    try:
                        content_elem = crawler.driver.find_element(By.CSS_SELECTOR, selector)
                        law_detail['content'] = content_elem.text.strip()
                        print(f"成功获取正文内容，使用选择器: {selector}")
                        break
                    except NoSuchElementException:
                        continue

            # 如果仍然没有获取到内容，尝试获取整个页面的文本作为备用
            if not law_detail['content']:
                try:
                    body_elem = crawler.driver.find_element(By.TAG_NAME, 'body')
                    law_detail['content'] = body_elem.text.strip()
                    print("使用整个页面内容作为备用")
                except:
                    pass

            # 获取元数据（发布时间、生效时间等）
            try:
                metadata_elems = crawler.driver.find_elements(By.CSS_SELECTOR, '.law-info span, .meta-info span, .MTitle')
                for elem in metadata_elems:
                    text = elem.text.strip()
                    if '发布时间' in text or '生效时间' in text or '失效时间' in text:
                        key_value = text.split('：', 1)
                        if len(key_value) == 2:
                            law_detail['metadata'][key_value[0]] = key_value[1]
                    elif elem.get_attribute('class') == 'MTitle':
                        # 获取标题信息
                        law_detail['metadata']['完整标题'] = text
            except:
                pass

        except Exception as e:
            print(f"获取法案详情失败: {e}")

        # 关闭当前标签页，返回主页面
        crawler.driver.close()
        crawler.driver.switch_to.window(crawler.driver.window_handles[0])

        return law_detail

    except Exception as e:
        print(f"爬取法案详情出错: {e}")
        # 确保返回主窗口
        try:
            if len(crawler.driver.window_handles) > 1:
                crawler.driver.close()
                crawler.driver.switch_to.window(crawler.driver.window_handles[0])
        except:
            pass
        return None

def extract_total_laws_from_category(category_text):
    """
    从分类文本中提取法案总数，如 "宪法 (2552)" -> 2552
    """
    match = re.search(r'\((\d+)\)', category_text)
    if match:
        return int(match.group(1))
    return 0

def crawl_category_laws(crawler, category_name, total_laws_count, max_pages=5):
    """
    爬取指定分类下的所有法案，按浏览量排序并筛选前1/20
    """
    all_laws = []
    current_page = 1

    # 计算需要爬取的法案数量（总数的1/20）
    target_laws_count = max(1, total_laws_count // 20)  # 至少爬取1个法案
    print(f"\n开始爬取分类: {category_name}（总共{total_laws_count}个法案，目标爬取{target_laws_count}个）")

    # 只在第一次进入分类时点击时效性、浏览量、更多按钮
    try:
        # 1. 点击时效性按钮
        try:
            effectiveness_button = WebDriverWait(crawler.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='时效性']"))
            )
            effectiveness_button.click()
            print("已点击时效性按钮")
            time.sleep(2)
        except TimeoutException:
            print("未找到时效性按钮，继续执行...")

        # 2. 点击浏览量按钮进行排序（从大到小）
        try:
            browse_count_button = WebDriverWait(crawler.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='浏览量']"))
            )
            browse_count_button.click()
            print("已点击浏览量按钮进行排序")
            time.sleep(3)  # 等待排序完成

            # 如果需要，再次点击确保是从大到小排序
            # 检查是否有排序指示器，如果是升序则再点击一次
            try:
                # 检查排序状态，如果需要可以再次点击
                browse_count_button.click()
                print("再次点击浏览量按钮确保从大到小排序")
                time.sleep(2)
            except:
                pass

        except TimeoutException:
            print("未找到浏览量按钮，继续执行...")

        # 3. 最后点击"现行有效"同一行的"更多"按钮
        try:
            more_button = WebDriverWait(crawler.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@logfunc='分组栏目-右上角更多' and @class='more' and text()='更多']"))
            )
            more_button.click()
            print("已点击'现行有效'的'更多'按钮")
            time.sleep(2)
        except TimeoutException:
            print("未找到'现行有效'的'更多'按钮，继续执行...")

    except Exception as e:
        print(f"点击时效性、浏览量或更多按钮时出错: {e}")

    crawled_count = 0
    while current_page <= max_pages and crawled_count < target_laws_count:
        print(f"\n=== 第 {current_page} 页 ===")

        try:
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

        except Exception as e:
            print(f"爬取第 {current_page} 页时出错: {e}")
            break

    print(f"分类 '{category_name}' 爬取完成，共爬取 {len(all_laws)} 个法案")
    return all_laws

if __name__ == '__main__':
    crawler = PKULawCrawler(headless=False, driver_path=CHROMEDRIVER_PATH)  # 先用非无头模式测试
    try:
        print(f"正在访问页面: {crawler.base_url}")
        crawler.get(crawler.base_url)

        # 等待页面加载完成，检查是否出现安全提示
        time.sleep(3)

        print(f"页面标题: {crawler.driver.title}")
        print(f"当前URL: {crawler.driver.current_url}")

        # 等待分类列表加载
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
        time.sleep(2)

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

        print(f"\n=== 开始爬取各分类下的法案 ===")

        # 为每个分类爬取法案
        all_category_data = {}
        for i, category in enumerate(law_categories[82:], 83):
            print(f"\n处理分类 {i}/{len(law_categories)}: {category}")

            # 提取该分类的法案总数
            total_laws_count = extract_total_laws_from_category(category)
            if total_laws_count == 0:
                print(f"警告: 无法从分类名称 '{category}' 中提取法案总数，使用默认值100")
                total_laws_count = 100  # 默认值

            try:
                # 确保返回主页面（如果不在主页面的话）
                if crawler.driver.current_url != crawler.base_url:
                    print("返回主页面...")
                    crawler.get(crawler.base_url)
                    time.sleep(3)

                    # 重新点击法规类别的"查看更多"按钮
                    try:
                        more_button = crawler.driver.find_element(
                            By.XPATH,
                            "//a[@logfunc='法规类别-查看更多' and contains(text(), '查看更多')]"
                        )
                        more_button.click()
                        time.sleep(3)
                        print("重新点击'查看更多'")
                    except Exception as e:
                        print(f"重新点击'查看更多'失败: {e}")

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
                    'target_laws_count': max(1, total_laws_count // 20),
                    'actual_crawled_count': len(category_laws),
                    'laws': category_laws
                }

                print(f"分类 '{category}' 完成，共爬取 {len(category_laws)} 个法案")

                # 保存当前分类的数据
                safe_filename = category.replace('/', '_').replace('(', '').replace(')', '').replace(' ', '_')
                save_json([all_category_data[category]], f"laws_{safe_filename}.json")

            except Exception as e:
                print(f"处理分类 '{category}' 时出错: {e}")
                # 发生错误时，尝试返回主页面
                try:
                    print("发生错误，尝试返回主页面...")
                    crawler.get(crawler.base_url)
                    time.sleep(3)
                except:
                    print("返回主页面失败")
                continue


        print(f"\n=== 爬取完成 ===")
        print(f"处理了 {len(all_category_data)} 个分类")

    except Exception as e:
        print(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("按回车键关闭浏览器...")  # 暂停以便观察
        crawler.close()
