"""
宪法类别法律数据分析和清洗脚本

该脚本专门用于分析和清洗 laws_宪法_2552.json 文件，提供：
- 数据结构分析
- 内容质量评估
- 字段统计和分布
- 清洗建议和实施
- 清洗后数据导出

Author: LawQASys Team
Date: 2024
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from collections import Counter, defaultdict
from datetime import datetime
import logging

# 导入现有的清洗器
from cleaner import LegalTextCleaner, CleaningConfig


class ConstitutionDataAnalyzer:
    """宪法类别数据分析器"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.data = None
        self.laws_data = None
        self.analysis_results = {}
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def load_data(self) -> bool:
        """加载JSON数据"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            # 提取laws数组
            if isinstance(self.data, list) and len(self.data) > 0:
                category_data = self.data[0]
                self.laws_data = category_data.get('laws', [])
                
                self.logger.info(f"成功加载数据，包含 {len(self.laws_data)} 条法律条目")
                return True
            else:
                self.logger.error("数据格式不符合预期")
                return False
                
        except Exception as e:
            self.logger.error(f"加载数据失败: {str(e)}")
            return False
    
    def analyze_structure(self) -> Dict[str, Any]:
        """分析数据结构"""
        if not self.data:
            return {}
        
        structure_info = {}
        
        # 分析顶层结构
        if isinstance(self.data, list) and len(self.data) > 0:
            category_data = self.data[0]
            structure_info['top_level'] = {
                'type': 'array',
                'length': len(self.data),
                'first_item_keys': list(category_data.keys()) if isinstance(category_data, dict) else []
            }
            
            # 分析类别信息
            structure_info['category_info'] = {
                'category_name': category_data.get('category_name'),
                'total_laws_in_category': category_data.get('total_laws_in_category'),
                'target_laws_count': category_data.get('target_laws_count'),
                'actual_crawled_count': category_data.get('actual_crawled_count')
            }
            
            # 分析laws数组结构
            laws = category_data.get('laws', [])
            if laws:
                first_law = laws[0]
                structure_info['law_item_structure'] = {
                    'total_laws': len(laws),
                    'fields': list(first_law.keys()) if isinstance(first_law, dict) else [],
                    'sample_law': {k: str(v)[:100] + '...' if len(str(v)) > 100 else v 
                                 for k, v in first_law.items()} if isinstance(first_law, dict) else {}
                }
        
        self.analysis_results['structure'] = structure_info
        return structure_info
    
    def analyze_content_quality(self) -> Dict[str, Any]:
        """分析内容质量"""
        if not self.laws_data:
            return {}
        
        quality_info = {
            'total_laws': len(self.laws_data),
            'field_coverage': {},
            'content_length_stats': {},
            'duplicate_analysis': {},
            'encoding_issues': [],
            'content_quality': {}
        }
        
        # 分析字段覆盖率
        field_counts = Counter()
        content_lengths = []
        titles = []
        urls = []
        contents = []
        
        for law in self.laws_data:
            if isinstance(law, dict):
                for field in law.keys():
                    field_counts[field] += 1
                
                # 收集内容用于分析
                title = law.get('title', '')
                content = law.get('content', '')
                url = law.get('url', '')
                
                titles.append(title)
                contents.append(content)
                urls.append(url)
                
                if content:
                    content_lengths.append(len(content))
        
        # 字段覆盖率
        total_laws = len(self.laws_data)
        for field, count in field_counts.items():
            quality_info['field_coverage'][field] = {
                'count': count,
                'percentage': (count / total_laws) * 100
            }
        
        # 内容长度统计
        if content_lengths:
            quality_info['content_length_stats'] = {
                'min': min(content_lengths),
                'max': max(content_lengths),
                'avg': sum(content_lengths) / len(content_lengths),
                'median': sorted(content_lengths)[len(content_lengths)//2],
                'empty_content_count': contents.count(''),
                'very_short_content_count': sum(1 for length in content_lengths if length < 100),
                'very_long_content_count': sum(1 for length in content_lengths if length > 50000)
            }
        
        # 重复分析
        title_duplicates = [title for title, count in Counter(titles).items() if count > 1]
        url_duplicates = [url for url, count in Counter(urls).items() if count > 1 and url]
        
        quality_info['duplicate_analysis'] = {
            'duplicate_titles': len(title_duplicates),
            'duplicate_urls': len(url_duplicates),
            'sample_duplicate_titles': title_duplicates[:5],
            'sample_duplicate_urls': url_duplicates[:5]
        }
        
        # 编码问题检测
        encoding_issues = []
        for i, law in enumerate(self.laws_data[:100]):  # 检查前100条
            content = law.get('content', '')
            if self._has_encoding_issues(content):
                encoding_issues.append({
                    'index': i,
                    'title': law.get('title', ''),
                    'issue_sample': content[:200]
                })
        
        quality_info['encoding_issues'] = encoding_issues[:10]  # 只保留前10个示例
        
        # 内容质量分析
        quality_info['content_quality'] = self._analyze_content_patterns(contents[:100])
        
        self.analysis_results['quality'] = quality_info
        return quality_info
    
    def _has_encoding_issues(self, text: str) -> bool:
        """检测编码问题"""
        encoding_indicators = [
            'â€œ', 'â€', 'â€™', 'â€˜', 'â€¢', 'Â', 'â',
            '\ufffd',  # 替换字符
            '\x00', '\x01', '\x02'  # 控制字符
        ]
        return any(indicator in text for indicator in encoding_indicators)
    
    def _analyze_content_patterns(self, contents: List[str]) -> Dict[str, Any]:
        """分析内容模式"""
        patterns = {
            'has_articles': 0,  # 包含条文
            'has_chapters': 0,  # 包含章节
            'has_legal_refs': 0,  # 包含法律引用
            'has_dates': 0,     # 包含日期
            'has_numbers': 0,   # 包含编号
            'avg_paragraph_count': 0,
            'common_phrases': Counter()
        }
        
        total_paragraphs = 0
        
        for content in contents:
            if not content:
                continue
            
            # 检测条文
            if re.search(r'第[一二三四五六七八九十百千万\d]+条', content):
                patterns['has_articles'] += 1
            
            # 检测章节
            if re.search(r'第[一二三四五六七八九十百千万\d]+章', content):
                patterns['has_chapters'] += 1
            
            # 检测法律引用
            if re.search(r'《[^》]+》', content):
                patterns['has_legal_refs'] += 1
            
            # 检测日期
            if re.search(r'\d{4}年|\d{1,2}月|\d{1,2}日', content):
                patterns['has_dates'] += 1
            
            # 检测编号
            if re.search(r'\d+\.\d+|\(\d+\)|（\d+）', content):
                patterns['has_numbers'] += 1
            
            # 段落计数
            paragraphs = content.split('\n')
            total_paragraphs += len([p for p in paragraphs if p.strip()])
            
            # 常见短语
            phrases = re.findall(r'[\u4e00-\u9fff]{3,8}', content)
            patterns['common_phrases'].update(phrases[:20])  # 只取前20个
        
        if contents:
            patterns['avg_paragraph_count'] = total_paragraphs / len(contents)
            patterns['common_phrases'] = dict(patterns['common_phrases'].most_common(10))
        
        return patterns
    
    def analyze_metadata(self) -> Dict[str, Any]:
        """分析元数据"""
        if not self.laws_data:
            return {}
        
        metadata_info = {
            'metadata_fields': Counter(),
            'source_analysis': {},
            'date_analysis': {},
            'category_analysis': {}
        }
        
        sources = []
        dates = []
        categories = []
        
        for law in self.laws_data:
            metadata = law.get('metadata', {})
            if isinstance(metadata, dict):
                for field in metadata.keys():
                    metadata_info['metadata_fields'][field] += 1
                
                # 收集特定字段
                if 'source' in metadata:
                    sources.append(metadata['source'])
                if 'date' in metadata:
                    dates.append(metadata['date'])
                if 'category' in metadata:
                    categories.append(metadata['category'])
        
        # 分析来源
        if sources:
            metadata_info['source_analysis'] = dict(Counter(sources).most_common(10))
        
        # 分析日期
        if dates:
            metadata_info['date_analysis'] = {
                'total_dates': len(dates),
                'unique_dates': len(set(dates)),
                'sample_dates': list(set(dates))[:10]
            }
        
        # 分析类别
        if categories:
            metadata_info['category_analysis'] = dict(Counter(categories).most_common(10))
        
        self.analysis_results['metadata'] = metadata_info
        return metadata_info
    
    def generate_cleaning_recommendations(self) -> List[str]:
        """生成清洗建议"""
        recommendations = []
        
        quality_info = self.analysis_results.get('quality', {})
        
        # 基于分析结果生成建议
        if quality_info.get('encoding_issues'):
            recommendations.append("发现编码问题，建议进行编码修复")
        
        content_stats = quality_info.get('content_length_stats', {})
        if content_stats.get('empty_content_count', 0) > 0:
            recommendations.append(f"发现 {content_stats['empty_content_count']} 条空内容记录，建议移除")
        
        if content_stats.get('very_short_content_count', 0) > 0:
            recommendations.append(f"发现 {content_stats['very_short_content_count']} 条内容过短的记录，建议审查")
        
        duplicate_info = quality_info.get('duplicate_analysis', {})
        if duplicate_info.get('duplicate_titles', 0) > 0:
            recommendations.append(f"发现 {duplicate_info['duplicate_titles']} 个重复标题，建议去重")
        
        if duplicate_info.get('duplicate_urls', 0) > 0:
            recommendations.append(f"发现 {duplicate_info['duplicate_urls']} 个重复URL，建议去重")
        
        # 内容质量建议
        content_quality = quality_info.get('content_quality', {})
        if content_quality.get('has_articles', 0) / len(self.laws_data) < 0.5:
            recommendations.append("较少记录包含条文结构，可能需要内容验证")
        
        return recommendations
    
    def clean_data(self, output_path: Optional[str] = None) -> bool:
        """清洗数据"""
        if not self.laws_data:
            self.logger.error("没有数据可供清洗")
            return False
        
        # 创建专门的宪法数据清洗配置
        config = CleaningConfig(
            min_content_length=20,  # 宪法相关内容最小长度
            max_content_length=100000,  # 增加最大长度限制
            remove_duplicates=True,
            duplicate_threshold=0.95,
            normalize_legal_references=True,
            clean_article_numbers=True,
            standardize_legal_terms=True,
            check_encoding_issues=True,
            validate_legal_structure=True,
            add_cleaning_metadata=True
        )
        
        # 创建清洗器
        cleaner = LegalTextCleaner(config)
        
        # 执行清洗
        self.logger.info("开始清洗宪法数据...")
        cleaned_laws = cleaner.clean_batch(self.laws_data)
        
        # 构建清洗后的完整数据结构
        cleaned_data = self.data.copy()
        if isinstance(cleaned_data, list) and len(cleaned_data) > 0:
            cleaned_data[0]['laws'] = cleaned_laws
            cleaned_data[0]['actual_crawled_count'] = len(cleaned_laws)
            
            # 添加清洗信息
            cleaned_data[0]['cleaning_info'] = {
                'cleaned_at': datetime.now().isoformat(),
                'original_count': len(self.laws_data),
                'cleaned_count': len(cleaned_laws),
                'removal_count': len(self.laws_data) - len(cleaned_laws)
            }
        
        # 保存清洗后的数据
        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
                self.logger.info(f"清洗后的数据已保存到: {output_path}")
                return True
            except Exception as e:
                self.logger.error(f"保存清洗数据失败: {str(e)}")
                return False
        
        return True
    
    def export_analysis_report(self, output_path: str):
        """导出分析报告"""
        report = {
            'analysis_time': datetime.now().isoformat(),
            'file_path': str(self.file_path),
            'structure_analysis': self.analysis_results.get('structure', {}),
            'quality_analysis': self.analysis_results.get('quality', {}),
            'metadata_analysis': self.analysis_results.get('metadata', {}),
            'cleaning_recommendations': self.generate_cleaning_recommendations()
        }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            self.logger.info(f"分析报告已保存到: {output_path}")
        except Exception as e:
            self.logger.error(f"保存分析报告失败: {str(e)}")
    
    def print_analysis_summary(self):
        """打印分析摘要"""
        print("\n" + "="*60)
        print("宪法类别数据分析报告")
        print("="*60)
        
        # 结构信息
        structure = self.analysis_results.get('structure', {})
        if structure:
            category_info = structure.get('category_info', {})
            print(f"类别名称: {category_info.get('category_name', 'N/A')}")
            print(f"目标抓取数量: {category_info.get('target_laws_count', 'N/A')}")
            print(f"实际抓取数量: {category_info.get('actual_crawled_count', 'N/A')}")
            
            law_structure = structure.get('law_item_structure', {})
            print(f"法律条目总数: {law_structure.get('total_laws', 'N/A')}")
            print(f"条目字段: {', '.join(law_structure.get('fields', []))}")
        
        # 质量信息
        quality = self.analysis_results.get('quality', {})
        if quality:
            print(f"\n内容质量分析:")
            
            content_stats = quality.get('content_length_stats', {})
            if content_stats:
                print(f"  平均内容长度: {content_stats.get('avg', 0):.0f} 字符")
                print(f"  空内容数量: {content_stats.get('empty_content_count', 0)}")
                print(f"  过短内容数量: {content_stats.get('very_short_content_count', 0)}")
            
            duplicate_info = quality.get('duplicate_analysis', {})
            print(f"  重复标题数量: {duplicate_info.get('duplicate_titles', 0)}")
            print(f"  重复URL数量: {duplicate_info.get('duplicate_urls', 0)}")
            
            encoding_issues = quality.get('encoding_issues', [])
            print(f"  编码问题数量: {len(encoding_issues)}")
        
        # 清洗建议
        recommendations = self.generate_cleaning_recommendations()
        if recommendations:
            print(f"\n清洗建议:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        print("="*60)


def main():
    """主函数"""
    # 文件路径
    input_file = r"d:\LawQASys\LawAgent\preprocessing\laws_宪法_2552.json"
    
    # 创建分析器
    analyzer = ConstitutionDataAnalyzer(input_file)
    
    # 加载数据
    if not analyzer.load_data():
        print("数据加载失败，退出程序")
        return
    
    # 执行分析
    print("正在进行数据结构分析...")
    analyzer.analyze_structure()
    
    print("正在进行内容质量分析...")
    analyzer.analyze_content_quality()
    
    print("正在进行元数据分析...")
    analyzer.analyze_metadata()
    
    # 打印分析摘要
    analyzer.print_analysis_summary()
    
    # 导出分析报告
    report_path = input_file.replace('.json', '_analysis_report.json')
    analyzer.export_analysis_report(report_path)
    
    # 询问是否进行清洗
    user_input = input("\n是否要进行数据清洗？(y/n): ").strip().lower()
    if user_input == 'y':
        cleaned_file = input_file.replace('.json', '_cleaned.json')
        if analyzer.clean_data(cleaned_file):
            print(f"数据清洗完成，清洗后文件保存到: {cleaned_file}")
        else:
            print("数据清洗失败")


if __name__ == "__main__":
    main()
