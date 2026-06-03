"""
法律知识库 API 路由
提供法律条文的全文搜索、分类浏览、按法律查阅等功能
底层使用 Meilisearch 检索引擎
"""
import logging
import re
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..models.user import User
from ..api.deps import get_current_active_user
from ..utils.search_engine import meili_client

logger = logging.getLogger("shengyuan_app.legal_kb")

router = APIRouter(
    prefix="/legal",
    tags=["legal_knowledge_base"],
)

INDEX_NAME = "legal_provisions"

# 中文数字 → 阿拉伯数字映射
_CN_NUM_MAP = {
    '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '百': 100, '千': 1000, '万': 10000, '零': 0,
}


def _cn_num_to_int(cn: str) -> int:
    """将中文数字字符串转为整数，如 '第二百三十二' → 232"""
    cn = cn.strip().lstrip('第').rstrip('条').strip()
    # 如果已经是纯阿拉伯数字
    if cn.isdigit():
        return int(cn)
    # 处理混合格式如 "三百零六"
    total = 0
    section = 0
    for ch in cn:
        val = _CN_NUM_MAP.get(ch)
        if val is None:
            continue
        if val >= 10:
            if section == 0:
                section = 1
            total += section * val
            section = 0
        else:
            section = val
    total += section
    return total


def _article_sort_key(article: dict) -> int:
    """提取条文编号的排序键"""
    num = article.get("article_number", "")
    try:
        return _cn_num_to_int(num)
    except Exception:
        return 0


@router.get("/categories")
def list_categories(
    current_user: User = Depends(get_current_active_user),
):
    """获取所有法律分类及各自条文数量（从 Meilisearch 动态获取，自动包含 DLC 分类）"""
    try:
        index = meili_client.index(INDEX_NAME)
        result = index.search("", {
            "facets": ["law_category"],
            "limit": 0,
        })
        facet_dist = result.get("facetDistribution", {})
        cat_counts = facet_dist.get("law_category", {})
        categories = [
            {"name": name, "count": count}
            for name, count in sorted(cat_counts.items(), key=lambda x: -x[1])
        ]
        return {"categories": categories}
    except Exception as e:
        logger.error("获取分类列表失败: %s", e)
        return {"categories": []}


@router.get("/stats")
def get_stats(
    current_user: User = Depends(get_current_active_user),
):
    """获取法律知识库总体统计信息"""
    try:
        index = meili_client.index(INDEX_NAME)
        stats = index.get_stats()
        # 获取法律数量（去重）
        result = index.search("", {
            "facets": ["law_name"],
            "limit": 0,
        })
        facet_dist = result.get("facetDistribution", {})
        law_count = len(facet_dist.get("law_name", {}))
        return {
            "total_articles": stats.number_of_documents,
            "total_laws": law_count,
        }
    except Exception as e:
        logger.error("获取统计信息失败: %s", e)
        return {"total_articles": 0, "total_laws": 0}


@router.get("/structure")
def get_law_structure(
    law_name: str = Query(..., description="法律名称"),
    current_user: User = Depends(get_current_active_user),
):
    """获取某部法律的章节目录树结构"""
    try:
        index = meili_client.index(INDEX_NAME)
        # 拉取该法律的所有条文
        result = index.search("", {
            "filter": f'law_name = "{law_name}"',
            "limit": 1000,
        })
        hits = sorted(result.get("hits", []), key=_article_sort_key)
        # 构建章节树
        chapters = []
        chapter_map = {}
        for hit in hits:
            ch_title = hit.get("chapter", "总纲")
            sec_title = hit.get("section", "")
            article_num = hit.get("article_number", "")
            article_id = hit.get("id", "")

            if ch_title not in chapter_map:
                chapter = {
                    "title": ch_title,
                    "sections": [],
                    "articles": [],
                }
                chapters.append(chapter)
                chapter_map[ch_title] = chapter

            chapter = chapter_map[ch_title]

            article = {
                "id": article_id,
                "article_number": article_num,
            }

            if sec_title:
                # 查找或创建节
                sec_found = None
                for s in chapter["sections"]:
                    if s["title"] == sec_title:
                        sec_found = s
                        break
                if sec_found is None:
                    sec_found = {"title": sec_title, "articles": []}
                    chapter["sections"].append(sec_found)
                sec_found["articles"].append(article)
            else:
                chapter["articles"].append(article)

        return {
            "law_name": law_name,
            "total_articles": len(hits),
            "chapters": chapters,
        }
    except Exception as e:
        logger.error("获取法律结构失败: %s", e)
        return {"law_name": law_name, "total_articles": 0, "chapters": []}


@router.get("/laws")
def list_laws_by_category(
    category: str = Query(..., description="法律分类（多个用逗号分隔）"),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取一个或多个分类下所有法律的名称及条文数量
    用于前端"按法律浏览"模式
    """
    try:
        categories = [c.strip() for c in category.split(",") if c.strip()]
        index = meili_client.index(INDEX_NAME)
        # 多分类用 IN 过滤
        if len(categories) == 1:
            filter_str = f'law_category = "{categories[0]}"'
        else:
            values = ", ".join(f'"{c}"' for c in categories)
            filter_str = f"law_category IN [{values}]"
        result = index.search("", {
            "filter": filter_str,
            "facets": ["law_name"],
            "limit": 0,
        })
        facet_dist = result.get("facetDistribution", {})
        law_names = list(facet_dist.get("law_name", {}).keys()) if facet_dist else []
        return {"category": category, "laws": sorted(law_names)}
    except Exception as e:
        logger.error("获取法律列表失败: %s", e)
        return {"category": category, "laws": []}


@router.get("/articles")
def list_articles_by_law(
    law_name: str = Query(..., description="法律名称"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取某部法律的完整条文列表（按条号排序）
    用于"按法律浏览"模式，展示完整法律结构
    """
    try:
        index = meili_client.index(INDEX_NAME)
        result = index.search("", {
            "filter": f'law_name = "{law_name}"',
            "limit": 1000,
        })
        hits = sorted(result.get("hits", []), key=_article_sort_key)
        # 分页截取
        paged_hits = hits[(page - 1) * page_size : page * page_size]
        items = []
        for hit in paged_hits:
            items.append({
                "id": hit.get("id"),
                "article_number": hit.get("article_number"),
                "chapter": hit.get("chapter"),
                "section": hit.get("section"),
                "content": hit.get("content"),
            })
        return {
            "law_name": law_name,
            "total": result.get("estimatedTotalHits", 0),
            "page": page,
            "page_size": page_size,
            "articles": items,
        }
    except Exception as e:
        logger.error("获取法律条文失败: %s", e)
        return {"law_name": law_name, "total": 0, "articles": []}


@router.get("/search")
def search_provisions(
    keyword: str = Query(default="", description="搜索关键词"),
    law_category: Optional[str] = Query(default=None, description="按法律分类筛选"),
    law_name: Optional[str] = Query(default=None, description="按法律名称筛选"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
):
    """
    全文搜索法律条文

    支持按分类和法律名称筛选，返回高亮命中结果
    """
    if not keyword.strip():
        return {"total": 0, "items": []}

    try:
        index = meili_client.index(INDEX_NAME)

        # 构建过滤条件
        filters = []
        if law_category:
            cats = [c.strip() for c in law_category.split(",") if c.strip()]
            if len(cats) == 1:
                filters.append(f'law_category = "{cats[0]}"')
            else:
                values = ", ".join(f'"{c}"' for c in cats)
                filters.append(f"law_category IN [{values}]")
        if law_name:
            filters.append(f'law_name = "{law_name}"')

        search_params = {
            "offset": (page - 1) * page_size,
            "limit": page_size,
            "attributesToHighlight": ["content", "article_number", "chapter"],
            "highlightPreTag": "<mark>",
            "highlightPostTag": "</mark>",
            "attributesToCrop": ["content"],
            "cropLength": 200,
        }
        if filters:
            search_params["filter"] = " AND ".join(filters)

        result = index.search(keyword.strip(), search_params)

        items = []
        for hit in result.get("hits", []):
            formatted = hit.get("_formatted", {})
            items.append({
                "id": hit.get("id"),
                "law_name": hit.get("law_name"),
                "law_category": hit.get("law_category"),
                "chapter": hit.get("chapter"),
                "section": hit.get("section"),
                "article_number": hit.get("article_number"),
                "content": hit.get("content"),
                # 高亮字段供前端渲染
                "content_highlighted": formatted.get("content", hit.get("content", "")),
                "article_number_highlighted": formatted.get("article_number", hit.get("article_number", "")),
            })

        return {
            "total": result.get("estimatedTotalHits", 0),
            "page": page,
            "page_size": page_size,
            "items": items,
        }
    except Exception as e:
        logger.error("搜索法律条文失败: %s", e)
        return {"total": 0, "items": []}


@router.get("/search/rag")
def search_for_rag(
    query: str = Query(..., description="检索查询（通常为案由+案件类别）"),
    top_k: int = Query(default=5, ge=1, le=20),
    current_user: User = Depends(get_current_active_user),
):
    """
    为 RAG 提供精简检索接口
    返回 top-k 条最相关的法律条文原文（不含高亮）
    """
    if not query.strip():
        return {"provisions": []}

    try:
        index = meili_client.index(INDEX_NAME)
        result = index.search(query.strip(), {
            "limit": top_k,
            "attributesToRetrieve": ["law_name", "article_number", "chapter", "content", "law_category"],
        })

        provisions = []
        for hit in result.get("hits", []):
            provisions.append({
                "law_name": hit.get("law_name"),
                "article_number": hit.get("article_number"),
                "chapter": hit.get("chapter"),
                "content": hit.get("content"),
                "law_category": hit.get("law_category"),
            })
        return {"provisions": provisions}
    except Exception as e:
        logger.error("RAG 检索失败: %s", e)
        return {"provisions": []}
