from crawler.pkulaw_crawler import PKULawCrawler
from crawler.utils import save_json
from selenium.webdriver.common.by import By
import time

# 指定 chromedriver 路径（请根据实际情况修改）
CHROMEDRIVER_PATH = "/home/admin/chromedriver/chromedriver"

if __name__ == '__main__':
    crawler = PKULawCrawler(headless=True, driver_path=CHROMEDRIVER_PATH)
    try:
        crawler.get(crawler.base_url)
        time.sleep(2)
        # 获取所有一级分类
        first_level_elems = crawler.driver.find_elements(By.CSS_SELECTOR, 'a.level0 > span.node_name')
        first_level_names = [elem.text.strip() for elem in first_level_elems if elem.text.strip()]
        print('所有一级分类:', first_level_names)

        # 遍历每个一级分类
        for first_name in first_level_names:
            # 重新加载页面，防止元素失效
            crawler.get(crawler.base_url)
            time.sleep(2)
            # 展开所有一级分类
            switches = crawler.driver.find_elements(By.CSS_SELECTOR, "span.switch.root_close")
            for sw in switches:
                try:
                    sw.click()
                    time.sleep(0.1)
                except Exception:
                    pass
            # 点击当前一级分类，展开二级
            try:
                a_elem = crawler.driver.find_element(
                    By.XPATH,
                    f"//a[contains(@class, 'level0')][span[@class='node_name' and contains(text(), '{first_name}')]]"
                )
                crawler.driver.execute_script("arguments[0].scrollIntoView();", a_elem)
                a_elem.click()
                time.sleep(1)
            except Exception as e:
                print(f"无法点击一级分类 {first_name}: {e}")
                continue

            # 获取所有二级分类
            second_level_elems = crawler.driver.find_elements(By.CSS_SELECTOR, 'a.level1 > span.node_name')
            second_level_names = [elem.text.strip() for elem in second_level_elems if elem.text.strip()]
            print(f'一级分类【{first_name}】下的二级分类:', second_level_names)

            # 如果有二级分类，遍历二级
            if second_level_names:
                for second_name in second_level_names:
                    category_path = [first_name, second_name]
                    print(f'正在爬取分类路径: {category_path}')
                    laws = crawler.crawl(category_name=category_path, max_pages=2)
                    save_json(laws, f"laws_{'_'.join(category_path)}.json")
                    print(f"已保存 {len(laws)} 条法规到 laws_{'_'.join(category_path)}.json")
            else:
                # 只爬一级分类
                category_path = [first_name]
                print(f'正在爬取分类路径: {category_path}')
                laws = crawler.crawl(category_name=category_path, max_pages=2)
                save_json(laws, f"laws_{'_'.join(category_path)}.json")
                print(f"已保存 {len(laws)} 条法规到 laws_{'_'.join(category_path)}.json")
    finally:
        crawler.close()
