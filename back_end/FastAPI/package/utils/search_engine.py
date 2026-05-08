# utils/search_engine.py
import meilisearch

# 使用你在部署时设置的密钥和地址
MEILI_URL = "http://localhost:7700"
MEILI_MASTER_KEY = "syls88888888"

meili_client = meilisearch.Client(MEILI_URL, MEILI_MASTER_KEY)

# 初始化索引配置（可以在服务启动时运行一次）
def init_meilisearch():
    index = meili_client.index('volume_files')
    # 强制指定主键为 'id'，防止多个 id 后缀字段引发冲突
    index.update(primary_key='id')
    # 设置主键
    index.update_filterable_attributes(['volume_id', 'case_id', 'category'])
    # 设置哪些字段可以被搜索（去除不需要搜索的字段提升性能）
    index.update_searchable_attributes(['file_name', 'summary', 'ocr_content', 'tags'])