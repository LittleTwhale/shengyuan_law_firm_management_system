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
        # 增大 facet 返回上限（默认 100，不足以覆盖所有法律名称）
        try:
            legal_index.update_settings({
                "faceting": {"maxValuesPerFacet": 10000}
            })
        except Exception:
            pass
        logger.info("Meilisearch 索引 'legal_provisions' 初始化完成")
    except Exception as e:
        logger.warning("Meilisearch 索引 'legal_provisions' 初始化失败: %s", e)