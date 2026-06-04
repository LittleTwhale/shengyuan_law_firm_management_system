"""
法律条文知识库导入脚本
解析 Laws 仓库的 Markdown 文件，以「条」为粒度导入 Meilisearch

使用方式：
    cd back_end/FastAPI
    python -m package.utils.legal_kb_importer

选项：
    --include-dlc   导入地方法规（默认跳过，数据量较大）
    --dry-run       仅解析不写入，打印统计信息
    --limit N       限制导入文件数（测试用）
"""
import os
import re
import sys
import json
import time
import hashlib
import logging

import meilisearch
from dotenv import load_dotenv

# 加载 .env 配置
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger("legal_kb_importer")

# ========================== 配置常量 ==========================

# __file__ 位置: back_end/FastAPI/package/utils/legal_kb_importer.py
# package_dir = back_end/FastAPI/package
_package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 项目根目录 = D:\syls（package 往上三级）
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_package_dir)))

# Laws 仓库根目录（已 clone 到项目根下的 law/Laws）
LAWS_ROOT = os.path.join(_PROJECT_ROOT, "law", "Laws")
if not os.path.isdir(LAWS_ROOT):
    # 降级：尝试环境变量
    LAWS_ROOT = os.environ.get("LAWS_ROOT", "")

# Meilisearch 连接信息（从环境变量读取）
MEILI_URL = os.getenv("MEILI_URL", "http://localhost:7700")
MEILI_MASTER_KEY = os.getenv("MEILI_MASTER_KEY")
INDEX_NAME = "legal_provisions"

# 批量导入每批大小
BATCH_SIZE = 500

# ========================== 文件分类映射 ==========================

# 顶层目录名 → 法律分类标签
CATEGORY_MAP = {
    "宪法": "宪法",
    "宪法相关法": "宪法相关法",
    "刑法": "刑法",
    "民法典": "民法典",
    "民法商法": "民法商法",
    "行政法": "行政法",
    "经济法": "经济法",
    "社会法": "社会法",
    "诉讼与非诉讼程序法": "诉讼与非诉讼程序法",
    "行政法规": "行政法规",
    "司法解释": "司法解释",
    "部门规章": "部门规章",
    "其他": "其他",
}


def normalize_article_number(raw: str) -> str:
    """将条文编号标准化为中文数字格式，便于排序"""
    raw = raw.strip().rstrip("条").strip()
    # 已经是中文数字的保持不变
    if re.match(r'^[一二三四五六七八九十百千万零]+$', raw):
        return f"第{raw}条"
    # 阿拉伯数字转为中文（保留原样以保持与原文一致）
    return f"第{raw}条"


def parse_single_file(filepath: str, category: str) -> list[dict]:
    """
    解析单个法律 Markdown 文件，返回条文文档列表

    返回格式：
    [{
        "id": "刑法_第二百三十二条",
        "law_name": "中华人民共和国刑法",
        "law_category": "刑法",
        "chapter": "第四章 侵犯公民人身权利、民主权利罪",
        "section": "第一节 一般规定",
        "article_number": "第二百三十二条",
        "content": "故意杀人的...",
        "file_path": "刑法/刑法.md",
    }]
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (IOError, UnicodeDecodeError) as e:
        logger.warning("读取文件失败 %s: %s", filepath, e)
        return []

    if not lines:
        return []

    # ---- 解析法律名称 ----
    law_name = ""
    first_line = lines[0].strip()
    if first_line.startswith("# "):
        law_name = first_line[2:].strip()
    else:
        # 文件名作为降级方案
        basename = os.path.splitext(os.path.basename(filepath))[0]
        law_name = re.sub(r'\(\d{4}[-/]\d{2}[-/]\d{2}\)', '', basename).strip()

    # 民法典特殊处理：文件名作为编名追加到法律名称后
    filename = os.path.basename(filepath)
    civil_code_parts = {
        "总则.md": "总则",
        "物权编.md": "物权编",
        "合同编.md": "合同编",
        "人格权编.md": "人格权编",
        "婚姻家庭编.md": "婚姻家庭编",
        "继承编.md": "继承编",
        "侵权责任编.md": "侵权责任编",
        "附则.md": "附则",
    }
    if category == "民法典" and filename in civil_code_parts:
        # 尝试读取第二个 # 标题（编名）
        for ln in lines:
            if ln.strip().startswith("# ") and ln.strip() != first_line.strip():
                part_name = ln.strip()[2:].strip()
                law_name = f"中华人民共和国民法典 · {part_name}"
                break
        else:
            law_name = f"中华人民共和国民法典 · {civil_code_parts[filename]}"

    # ---- 找到正文起始位置（<!-- INFO END --> 之后） ----
    content_start = 0
    for i, ln in enumerate(lines):
        if ln.strip() == "<!-- INFO END -->":
            content_start = i + 1
            break

    if content_start == 0:
        # 没有找到标记，默认从第 2 行开始
        content_start = 1

    # ---- 提取章/节层级和条文 ----
    articles = []
    current_chapter = "总纲"
    current_section = ""
    current_article_num = ""
    current_article_lines = []
    in_article = False

    # 获取文件相对路径
    rel_path = os.path.relpath(filepath, os.path.dirname(LAWS_ROOT) if os.path.isdir(os.path.dirname(LAWS_ROOT)) else LAWS_ROOT)

    def flush_article():
        """将当前累积的条文保存为一个文档"""
        nonlocal current_article_num, current_article_lines, in_article
        if current_article_num and current_article_lines:
            content = "".join(current_article_lines).strip()
            # 过滤掉过短的内容（可能解析错误）
            if len(content) >= 5:
                doc_id = hashlib.md5(f"{law_name}_{current_article_num}".encode('utf-8')).hexdigest()
                articles.append({
                    "id": doc_id,
                    "law_name": law_name,
                    "law_category": category,
                    "chapter": current_chapter,
                    "section": current_section,
                    "article_number": current_article_num,
                    "content": content,
                    "file_path": rel_path.replace("\\", "/"),
                })
        current_article_num = ""
        current_article_lines = []
        in_article = False

    for ln in lines[content_start:]:
        stripped = ln.rstrip("\n").rstrip("\r")

        # 跳过空行和纯空格行
        if not stripped.strip():
            if in_article:
                current_article_lines.append("\n")
            continue

        # 检测编标题（## 第X编）或章标题（##/### 第X章）
        part_match = re.match(r'^##\s+(第[一二三四五六七八九十百千\d]+编\s*.+)', stripped)
        ch_h2_match = re.match(r'^##\s+(第[一二三四五六七八九十百千\d]+章\s*.+)', stripped)
        ch_h3_match = re.match(r'^###\s+(第[一二三四五六七八九十百千\d]+章\s*.+)', stripped)

        if part_match:
            flush_article()
            current_chapter = part_match.group(1).strip()
            current_section = ""  # 进入新编时重置节
            continue
        if ch_h2_match:
            flush_article()
            current_chapter = ch_h2_match.group(1).strip()
            current_section = ""  # 进入新章时重置节
            continue
        if ch_h3_match:
            flush_article()
            current_chapter = ch_h3_match.group(1).strip()
            current_section = ""  # 进入新章时重置节
            continue

        # 检测节标题（### 第X节）
        section_match = re.match(r'^###\s+(第[一二三四五六七八九十百千\d]+节\s*.+)', stripped)
        if section_match:
            flush_article()
            current_section = section_match.group(1).strip()
            continue

        # 检测子节/款项标题（#### 级别）
        sub_match = re.match(r'^####\s+(.+)', stripped)
        if sub_match:
            sub_title = sub_match.group(1).strip()
            if re.match(r'第[一二三四五六七八九十百千\d]+', sub_title):
                flush_article()
                current_section = sub_title
            continue

        # 检测条文开头（"第" 字可选，兼容 "第四百五十二条" 等格式）
        article_match = re.match(r'^(第?[一二三四五六七八九十百千零\d]+条)(\s*)(.*)', stripped)
        if article_match:
            flush_article()
            current_article_num = article_match.group(1).strip()
            rest = article_match.group(3)
            current_article_lines = [rest]
            in_article = True
            continue

        # 正文内容（属于当前条文）
        if in_article:
            current_article_lines.append(stripped)
        # 如果不在任何条文中，跳过（如编标题、目录等）

    # 刷出最后一条
    flush_article()

    return articles


def parse_all_laws(laws_root: str, include_dlc: bool = False, dry_run: bool = False,
                   limit: int = 0) -> tuple[int, list[dict]]:
    """
    遍历 Laws 仓库，解析所有法律 Markdown 文件

    返回：(文件数, 所有条文文档列表)
    """
    all_articles = []
    file_count = 0
    skip_dirs = {"scripts", ".git", ".github", "案例"}

    if not include_dlc:
        skip_dirs.add("DLC")

    for item in sorted(os.listdir(laws_root)):
        item_path = os.path.join(laws_root, item)

        if not os.path.isdir(item_path):
            continue
        if item in skip_dirs:
            logger.info("跳过目录: %s", item)
            continue

        category = CATEGORY_MAP.get(item, item)
        logger.info("正在处理分类: %s", category)

        # 递归查找所有 .md 文件
        md_files = []
        for root, dirs, files in os.walk(item_path):
            # 跳过子目录中的 _index.md 和隐藏文件
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for f in files:
                if f.endswith(".md") and f != "_index.md":
                    md_files.append(os.path.join(root, f))

        for fpath in sorted(md_files):
            articles = parse_single_file(fpath, category)
            all_articles.extend(articles)
            file_count += 1

            if articles:
                logger.debug("  %s → %d 条条文", os.path.basename(fpath), len(articles))

            if limit and file_count >= limit:
                logger.info("已达到限制数 %d，停止解析", limit)
                break

        if limit and file_count >= limit:
            break

    return file_count, all_articles


def import_to_meilisearch(articles: list[dict], dry_run: bool = False):
    """将条文文档批量导入 Meilisearch"""
    if dry_run:
        logger.info("[DRY RUN] 将导入 %d 条法律条文", len(articles))
        # 打印统计
        categories = {}
        for a in articles:
            cat = a["law_category"]
            categories[cat] = categories.get(cat, 0) + 1
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            logger.info("  %s: %d 条", cat, count)
        # 打印样例
        if articles:
            logger.info("\n样例文档:\n%s", json.dumps(articles[0], ensure_ascii=False, indent=2))
        return

    client = meilisearch.Client(MEILI_URL, MEILI_MASTER_KEY)
    index = client.index(INDEX_NAME)

    # 清空旧数据（仅删除非空索引）
    try:
        stats = index.get_stats()
        if stats.number_of_documents > 0:
            logger.info("正在清空旧索引数据（%d 条文档）...", stats.number_of_documents)
            index.delete_all_documents()
    except Exception:
        pass

    # 分批导入
    total = len(articles)
    for i in range(0, total, BATCH_SIZE):
        batch = articles[i:i + BATCH_SIZE]
        try:
            index.add_documents(batch, primary_key='id')
            logger.info("导入进度: %d/%d (%.1f%%)", min(i + BATCH_SIZE, total), total,
                        min(i + BATCH_SIZE, total) / total * 100)
        except Exception as e:
            logger.error("批量导入失败 (offset=%d): %s", i, e)
            # 逐条重试
            for doc in batch:
                try:
                    index.add_documents([doc], primary_key='id')
                except Exception as e2:
                    logger.error("单条导入失败 id=%s: %s", doc.get("id"), e2)

    logger.info("导入完成！共导入 %d 条法律条文", total)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="法律条文知识库导入工具")
    parser.add_argument("--include-dlc", action="store_true", help="包含地方法规（DLC）")
    parser.add_argument("--dry-run", action="store_true", help="仅解析不导入，打印统计信息")
    parser.add_argument("--limit", type=int, default=0, help="限制解析文件数（测试用）")
    parser.add_argument("--laws-root", type=str, default=LAWS_ROOT, help="Laws 仓库根目录")
    args = parser.parse_args()

    laws_root = args.laws_root
    if not os.path.isdir(laws_root):
        logger.error("Laws 仓库目录不存在: %s", laws_root)
        logger.error("请使用 --laws-root 指定路径，或设置 LAWS_ROOT 环境变量")
        sys.exit(1)

    logger.info("=== 法律条文知识库导入工具 ===")
    logger.info("数据源: %s", laws_root)
    logger.info("Meilisearch: %s", MEILI_URL)
    logger.info("包含 DLC: %s", "是" if args.include_dlc else "否")
    logger.info("")

    t0 = time.time()

    file_count, articles = parse_all_laws(
        laws_root,
        include_dlc=args.include_dlc,
        dry_run=args.dry_run,
        limit=args.limit,
    )

    t1 = time.time()
    logger.info("解析完成：%d 个文件，%d 条法律条文，耗时 %.1f 秒",
                file_count, len(articles), t1 - t0)

    import_to_meilisearch(articles, dry_run=args.dry_run)

    t2 = time.time()
    logger.info("总耗时: %.1f 秒", t2 - t0)


if __name__ == "__main__":
    main()
