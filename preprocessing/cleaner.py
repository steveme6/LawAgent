"""
法律文本数据清洗模块

该模块实现了针对法律文本的专业化数据清洗流水线，包括：
- 文本标准化和格式清理
- 法律特有结构的处理（条文、章节等）
- 内容去重和质量检测
- 可配置的清洗策略
- 完整的日志记录和错误处理

Author: LawQASys Team
Date: 2024
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path
import unicodedata
from collections import Counter
import hashlib


@dataclass
class CleaningConfig:
    """数据清洗配置类"""
    
    # 基本清洗选项
    remove_extra_whitespace: bool = True
    normalize_unicode: bool = True
    remove_control_chars: bool = True
    standardize_punctuation: bool = True
    
    # 法律文本特定清洗
    normalize_legal_references: bool = True
    clean_article_numbers: bool = True
    remove_redundant_headers: bool = True
    standardize_legal_terms: bool = True
    
    # 内容过滤
    min_content_length: int = 10
    max_content_length: int = 50000
    remove_duplicates: bool = True
    duplicate_threshold: float = 0.95
    
    # 质量检测
    check_encoding_issues: bool = True
    detect_incomplete_sentences: bool = True
    validate_legal_structure: bool = True
    
    # 输出选项
    preserve_original: bool = True
    add_cleaning_metadata: bool = True
    
    # 自定义过滤规则
    custom_remove_patterns: List[str] = field(default_factory=list)
    custom_replace_patterns: List[Tuple[str, str]] = field(default_factory=list)


class LegalTextCleaner:
    """法律文本清洗器"""
    
    def __init__(self, config: Optional[CleaningConfig] = None):
        """
        初始化清洗器
        
        Args:
            config: 清洗配置，如果为None则使用默认配置
        """
        self.config = config or CleaningConfig()
        self.logger = self._setup_logger()
        self.stats = {
            'processed': 0,
            'cleaned': 0,
            'duplicates_removed': 0,
            'quality_issues': 0,
            'errors': 0
        }
        
        # 初始化清洗模式
        self._init_cleaning_patterns()
        
        # 用于去重的哈希集合
        self.seen_hashes: Set[str] = set()
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('LegalTextCleaner')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _init_cleaning_patterns(self):
        """初始化清洗正则表达式模式"""
        
        # 基本清理模式
        self.whitespace_pattern = re.compile(r'\s+')
        self.control_chars_pattern = re.compile(r'[\x00-\x1f\x7f-\x9f]')
        self.extra_newlines_pattern = re.compile(r'\n{3,}')
        
        # 标点符号标准化
        self.punctuation_mapping = {
            '，': '，',  # 全角逗号
            '。': '。',  # 全角句号
            '；': '；',  # 全角分号
            '：': '：',  # 全角冒号
            '！': '！',  # 全角感叹号
            '？': '？',  # 全角问号
            '"': '"',   # 左双引号
            '"': '"',   # 右双引号
            '\u2018': '\u2019',   # 左单引号转右单引号
            '\u2019': '\u2019',   # 右单引号
            '（': '（', # 全角左括号
            '）': '）', # 全角右括号
        }
        
        # 法律文本特有模式
        self.article_number_pattern = re.compile(
            r'第[一二三四五六七八九十百千万\d]+条|第[一二三四五六七八九十百千万\d]+章|第[一二三四五六七八九十百千万\d]+节'
        )
        
        self.legal_reference_pattern = re.compile(
            r'《[^》]+》|〈[^〉]+〉|\[[^\]]+\]'
        )
        
        # 常见法律术语标准化
        self.legal_terms_mapping = {
            '法人': '法人',
            '自然人': '自然人',
            '民事主体': '民事主体',
            '民事权利': '民事权利',
            '民事义务': '民事义务',
            '民事责任': '民事责任',
        }
        
        # 需要移除的冗余模式
        self.redundant_patterns = [
            re.compile(r'^\s*目\s*录\s*$', re.MULTILINE),
            re.compile(r'^\s*第[一二三四五六七八九十]+编\s*$', re.MULTILINE),
            re.compile(r'^\s*附\s*则\s*$', re.MULTILINE),
            re.compile(r'^\s*说\s*明\s*$', re.MULTILINE),
        ]
    
    def clean_single_document(self, document: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        清洗单个文档
        
        Args:
            document: 原始文档字典
            
        Returns:
            清洗后的文档字典，如果文档无效则返回None
        """
        try:
            self.stats['processed'] += 1
            
            # 创建清洗后的文档副本
            cleaned_doc = document.copy() if self.config.preserve_original else {}
            
            # 提取需要清洗的文本字段
            text_fields = self._extract_text_fields(document)
            
            if not text_fields:
                self.logger.warning(f"文档 {document.get('title', 'Unknown')} 中未找到文本内容")
                return None
            
            # 执行清洗流水线
            cleaned_fields = {}
            has_valid_content = False
            
            for field_name, text_content in text_fields.items():
                cleaned_text, metadata = self._clean_text_pipeline(text_content)
                
                if cleaned_text and self._validate_content_quality(cleaned_text):
                    cleaned_fields[field_name] = cleaned_text
                    has_valid_content = True
                    
                    if self.config.add_cleaning_metadata:
                        cleaned_fields[f"{field_name}_cleaning_metadata"] = metadata
                
            if not has_valid_content:
                self.logger.warning(f"文档 {document.get('title', 'Unknown')} 清洗后无有效内容")
                return None
            
            # 检查重复
            if self.config.remove_duplicates:
                content_hash = self._calculate_content_hash(cleaned_fields)
                if content_hash in self.seen_hashes:
                    self.stats['duplicates_removed'] += 1
                    self.logger.debug(f"发现重复文档: {document.get('title', 'Unknown')}")
                    return None
                self.seen_hashes.add(content_hash)
            
            # 更新清洗后的文档
            cleaned_doc.update(cleaned_fields)
            
            # 添加清洗元数据
            if self.config.add_cleaning_metadata:
                cleaned_doc['cleaning_info'] = {
                    'cleaned_at': self._get_timestamp(),
                    'cleaner_version': '1.0.0',
                    'config_hash': self._get_config_hash()
                }
            
            self.stats['cleaned'] += 1
            return cleaned_doc
            
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"清洗文档时发生错误: {str(e)}")
            return None
    
    def _extract_text_fields(self, document: Dict[str, Any]) -> Dict[str, str]:
        """提取文档中的文本字段"""
        text_fields = {}
        
        # 常见的文本字段名
        common_text_fields = ['content', 'text', 'body', 'fulltext', 'article_content']
        
        for field in common_text_fields:
            if field in document and isinstance(document[field], str):
                text_fields[field] = document[field]
        
        # 如果没有找到标准字段，尝试查找其他可能的文本字段
        if not text_fields:
            for key, value in document.items():
                if isinstance(value, str) and len(value) > 50:  # 假设有意义的文本至少50字符
                    text_fields[key] = value
        
        return text_fields
    
    def _clean_text_pipeline(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        文本清洗流水线
        
        Args:
            text: 原始文本
            
        Returns:
            (清洗后的文本, 清洗元数据)
        """
        metadata = {
            'original_length': len(text),
            'operations_applied': []
        }
        
        # 1. Unicode标准化
        if self.config.normalize_unicode:
            text = unicodedata.normalize('NFKC', text)
            metadata['operations_applied'].append('unicode_normalization')
        
        # 2. 移除控制字符
        if self.config.remove_control_chars:
            text = self.control_chars_pattern.sub('', text)
            metadata['operations_applied'].append('control_chars_removal')
        
        # 3. 处理编码问题
        if self.config.check_encoding_issues:
            text = self._fix_encoding_issues(text)
            metadata['operations_applied'].append('encoding_fix')
        
        # 4. 标准化标点符号
        if self.config.standardize_punctuation:
            text = self._standardize_punctuation(text)
            metadata['operations_applied'].append('punctuation_standardization')
        
        # 5. 清理空白字符
        if self.config.remove_extra_whitespace:
            text = self._clean_whitespace(text)
            metadata['operations_applied'].append('whitespace_cleaning')
        
        # 6. 处理法律文本特有结构
        if self.config.normalize_legal_references:
            text = self._normalize_legal_references(text)
            metadata['operations_applied'].append('legal_references_normalization')
        
        if self.config.clean_article_numbers:
            text = self._clean_article_numbers(text)
            metadata['operations_applied'].append('article_numbers_cleaning')
        
        if self.config.remove_redundant_headers:
            text = self._remove_redundant_headers(text)
            metadata['operations_applied'].append('redundant_headers_removal')
        
        # 7. 标准化法律术语
        if self.config.standardize_legal_terms:
            text = self._standardize_legal_terms(text)
            metadata['operations_applied'].append('legal_terms_standardization')
        
        # 8. 应用自定义规则
        text = self._apply_custom_rules(text)
        metadata['operations_applied'].append('custom_rules_application')
        
        # 9. 最终清理
        text = text.strip()
        
        metadata['final_length'] = len(text)
        metadata['compression_ratio'] = metadata['final_length'] / metadata['original_length'] if metadata['original_length'] > 0 else 0
        
        return text, metadata
    
    def _fix_encoding_issues(self, text: str) -> str:
        """修复常见的编码问题"""
        # 修复常见的编码错误
        encoding_fixes = [
            ('â€œ', '"'),
            ('â€', '"'),
            ('â€™', '''),
            ('â€˜', '''),
            ('â€¢', '•'),
            ('Â', ''),
            ('â', ''),
        ]
        
        for wrong, correct in encoding_fixes:
            text = text.replace(wrong, correct)
        
        return text
    
    def _standardize_punctuation(self, text: str) -> str:
        """标准化标点符号"""
        for old_punct, new_punct in self.punctuation_mapping.items():
            text = text.replace(old_punct, new_punct)
        return text
    
    def _clean_whitespace(self, text: str) -> str:
        """清理空白字符"""
        # 标准化空白字符
        text = self.whitespace_pattern.sub(' ', text)
        
        # 清理多余的换行符
        text = self.extra_newlines_pattern.sub('\n\n', text)
        
        # 清理行首行尾空白
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines]
        text = '\n'.join(line for line in cleaned_lines if line)
        
        return text
    
    def _normalize_legal_references(self, text: str) -> str:
        """标准化法律引用格式"""
        def normalize_reference(match):
            ref = match.group(0)
            # 确保法律名称使用标准书名号
            if ref.startswith('[') and ref.endswith(']'):
                ref = '《' + ref[1:-1] + '》'
            elif ref.startswith('〈') and ref.endswith('〉'):
                ref = '《' + ref[1:-1] + '》'
            return ref
        
        return self.legal_reference_pattern.sub(normalize_reference, text)
    
    def _clean_article_numbers(self, text: str) -> str:
        """清理和标准化条文编号"""
        def normalize_article(match):
            article = match.group(0)
            # 确保条文编号格式一致
            article = re.sub(r'\s+', '', article)  # 移除内部空白
            return article
        
        return self.article_number_pattern.sub(normalize_article, text)
    
    def _remove_redundant_headers(self, text: str) -> str:
        """移除冗余的标题和分隔符"""
        for pattern in self.redundant_patterns:
            text = pattern.sub('', text)
        return text
    
    def _standardize_legal_terms(self, text: str) -> str:
        """标准化法律术语"""
        for old_term, new_term in self.legal_terms_mapping.items():
            text = re.sub(rf'\b{re.escape(old_term)}\b', new_term, text)
        return text
    
    def _apply_custom_rules(self, text: str) -> str:
        """应用自定义清洗规则"""
        # 应用自定义移除模式
        for pattern in self.config.custom_remove_patterns:
            text = re.sub(pattern, '', text)
        
        # 应用自定义替换模式
        for old_pattern, new_pattern in self.config.custom_replace_patterns:
            text = re.sub(old_pattern, new_pattern, text)
        
        return text
    
    def _validate_content_quality(self, text: str) -> bool:
        """验证内容质量"""
        # 检查长度
        if len(text) < self.config.min_content_length:
            self.stats['quality_issues'] += 1
            return False
        
        if len(text) > self.config.max_content_length:
            self.stats['quality_issues'] += 1
            return False
        
        # 检查是否为纯符号或数字
        if re.match(r'^[\s\d\W]+$', text):
            self.stats['quality_issues'] += 1
            return False
        
        # 检查是否包含基本的法律文本特征
        if self.config.validate_legal_structure:
            if not self._has_legal_structure(text):
                self.stats['quality_issues'] += 1
                return False
        
        # 检查不完整句子
        if self.config.detect_incomplete_sentences:
            if self._has_incomplete_sentences(text):
                self.stats['quality_issues'] += 1
                return False
        
        return True
    
    def _has_legal_structure(self, text: str) -> bool:
        """检查是否具有法律文本结构"""
        legal_indicators = [
            r'第[一二三四五六七八九十百千万\d]+条',
            r'第[一二三四五六七八九十百千万\d]+章',
            r'第[一二三四五六七八九十百千万\d]+节',
            r'《[^》]+》',
            r'法律|法规|条例|办法|规定|通知|意见',
            r'应当|必须|禁止|不得|可以|有权',
            r'责任|义务|权利|权力|处罚|处分'
        ]
        
        matches = 0
        for pattern in legal_indicators:
            if re.search(pattern, text):
                matches += 1
        
        # 至少匹配2个法律特征才认为是有效的法律文本
        return matches >= 2
    
    def _has_incomplete_sentences(self, text: str) -> bool:
        """检查是否有不完整的句子"""
        # 简单启发式：检查是否以标点符号结尾
        text = text.strip()
        if not text:
            return True
        
        ending_punctuation = ['。', '！', '？', '；', '：', '.', '!', '?', ';', ':']
        return text[-1] not in ending_punctuation
    
    def _calculate_content_hash(self, content_dict: Dict[str, str]) -> str:
        """计算内容哈希用于去重"""
        content_str = ''.join(sorted(content_dict.values()))
        return hashlib.md5(content_str.encode('utf-8')).hexdigest()
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _get_config_hash(self) -> str:
        """获取配置哈希"""
        import json
        config_str = json.dumps(self.config.__dict__, sort_keys=True)
        return hashlib.md5(config_str.encode('utf-8')).hexdigest()[:8]
    
    def clean_batch(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量清洗文档
        
        Args:
            documents: 文档列表
            
        Returns:
            清洗后的文档列表
        """
        self.logger.info(f"开始批量清洗 {len(documents)} 个文档")
        
        cleaned_documents = []
        for i, doc in enumerate(documents):
            if i > 0 and i % 100 == 0:
                self.logger.info(f"已处理 {i}/{len(documents)} 个文档")
            
            cleaned_doc = self.clean_single_document(doc)
            if cleaned_doc:
                cleaned_documents.append(cleaned_doc)
        
        self.logger.info(f"批量清洗完成，成功清洗 {len(cleaned_documents)}/{len(documents)} 个文档")
        self.print_stats()
        
        return cleaned_documents
    
    def clean_json_file(self, input_path: str, output_path: str) -> bool:
        """
        清洗JSON文件
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            
        Returns:
            是否成功
        """
        try:
            self.logger.info(f"开始清洗文件: {input_path}")
            
            # 读取文件
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 处理不同的数据格式
            if isinstance(data, list):
                cleaned_data = self.clean_batch(data)
            elif isinstance(data, dict):
                cleaned_doc = self.clean_single_document(data)
                cleaned_data = [cleaned_doc] if cleaned_doc else []
            else:
                self.logger.error(f"不支持的数据格式: {type(data)}")
                return False
            
            # 保存清洗后的数据
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"清洗完成，结果保存到: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"清洗文件时发生错误: {str(e)}")
            return False
    
    def print_stats(self):
        """打印清洗统计信息"""
        print("\n" + "="*50)
        print("数据清洗统计报告")
        print("="*50)
        print(f"处理文档总数: {self.stats['processed']}")
        print(f"成功清洗文档: {self.stats['cleaned']}")
        print(f"移除重复文档: {self.stats['duplicates_removed']}")
        print(f"质量问题文档: {self.stats['quality_issues']}")
        print(f"处理错误数量: {self.stats['errors']}")
        
        if self.stats['processed'] > 0:
            success_rate = (self.stats['cleaned'] / self.stats['processed']) * 100
            print(f"成功率: {success_rate:.2f}%")
        
        print("="*50)
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'processed': 0,
            'cleaned': 0,
            'duplicates_removed': 0,
            'quality_issues': 0,
            'errors': 0
        }
        self.seen_hashes.clear()


def create_default_cleaner() -> LegalTextCleaner:
    """创建默认配置的清洗器"""
    config = CleaningConfig()
    return LegalTextCleaner(config)


def create_strict_cleaner() -> LegalTextCleaner:
    """创建严格模式的清洗器"""
    config = CleaningConfig(
        min_content_length=50,
        duplicate_threshold=0.98,
        check_encoding_issues=True,
        detect_incomplete_sentences=True,
        validate_legal_structure=True
    )
    return LegalTextCleaner(config)


def create_lenient_cleaner() -> LegalTextCleaner:
    """创建宽松模式的清洗器"""
    config = CleaningConfig(
        min_content_length=5,
        duplicate_threshold=0.90,
        check_encoding_issues=False,
        detect_incomplete_sentences=False,
        validate_legal_structure=False
    )
    return LegalTextCleaner(config)


if __name__ == "__main__":
    # 示例用法
    cleaner = create_default_cleaner()
    
    # 测试单个文档清洗
    test_doc = {
        "title": "测试法律文档",
        "content": "第一条   本法为规范   民事关系，保护民事主体的合法权益。。。   第二条  民事主体在民事活动中的法律地位一律平等。"
    }
    
    cleaned = cleaner.clean_single_document(test_doc)
    if cleaned:
        print("清洗结果:")
        print(json.dumps(cleaned, ensure_ascii=False, indent=2))
    
    cleaner.print_stats()
