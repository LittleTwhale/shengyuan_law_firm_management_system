# utils/search_engine.py
import meilisearch
import logging

from ..core.config import MEILI_URL, MEILI_MASTER_KEY

logger = logging.getLogger("shengyuan_app.search_engine")

meili_client = meilisearch.Client(MEILI_URL, MEILI_MASTER_KEY)


def init_meilisearch():
    """初始化所有 Meilisearch 索引配置（应用启动时调用）"""

    # ---- volume_files 索引：卷宗 OCR 文件搜索 ----
    vol_index = meili_client.index('volume_files')
    vol_index.update(primary_key='id')
    vol_index.update_filterable_attributes(['volume_id', 'case_id', 'category'])
    vol_index.update_searchable_attributes(['file_name', 'summary', 'ocr_content', 'tags'])

    # ---- legal_provisions 索引：法律知识库 ----
    try:
        legal_index = meili_client.index('legal_provisions')
        legal_index.update(primary_key='id')
        legal_index.update_filterable_attributes(['law_category', 'law_name', 'chapter'])
        legal_index.update_searchable_attributes([
            'content', 'article_number', 'law_name', 'chapter', 'section'
        ])
        legal_index.update_sortable_attributes(['law_name', 'article_number'])
        # 配置搜索设置（排序规则 + facet 上限）
        try:
            legal_index.update_settings({
                "rankingRules": [
                    "words",       # 匹配词数越多越靠前
                    "typo",        # 容错少越靠前
                    "proximity",   # 匹配词间距越近越靠前
                    "attribute",   # 字段权重（searchableAttributes 顺序决定）
                    "sort",        # 允许自定义排序
                    "exactness",   # 精确匹配加分
                ],
                "faceting": {"maxValuesPerFacet": 10000},
            })
        except Exception as e:
            logger.warning("Meilisearch 搜索设置配置失败: %s", e)

        # 配置法律领域同义词（让"借款"也能搜到"贷款"等变体）
        try:
            legal_index.update_synonyms({
                "借款": ["贷款", "借贷"],
                "贷款": ["借款", "借贷"],
                "借贷": ["借款", "贷款"],
                "时效": ["期限", "期间", "有效期"],
                "担保": ["保证", "抵押", "质押"],
                "保证": ["担保"],
                "抵押": ["担保", "质押"],
                "违约": ["逾期", "欠款"],
                "逾期": ["违约"],
                "利息": ["利率", "罚息"],
                "合同": ["合约", "协议"],
                "解除": ["终止", "撤销"],
                "赔偿": ["补偿", "损失"],
                "执行": ["强制执行"],
                "诉讼": ["起诉"],
                "仲裁": ["商事仲裁"],
                "物权": ["所有权", "担保物权", "用益物权"],
                "侵权": ["侵害", "损害"],
                "债权": ["债务", "欠款"],
            })
        except Exception as e:
            logger.warning("法律领域同义词配置失败（不影响使用）: %s", e)

        logger.info("Meilisearch 索引 'legal_provisions' 初始化完成")
    except Exception as e:
        logger.warning("Meilisearch 索引 'legal_provisions' 初始化失败: %s", e)