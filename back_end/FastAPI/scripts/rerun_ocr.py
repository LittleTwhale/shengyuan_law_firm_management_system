"""
重新对 OCR 失败的 PDF 文件执行智能提取

使用方式（在 back_end/FastAPI/ 目录下执行）：
    python -m scripts.rerun_ocr

或在项目根目录执行：
    python back_end/FastAPI/scripts/rerun_ocr.py
"""
import sys
import os
import time

# 将项目根目录加入 sys.path，使其能找到 package 模块
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)  # back_end/FastAPI/
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("OCR_RERUN", "1")  # 标记运行环境，避免意外触发其他初始化

from package.database.database import SessionLocal
from package.models.electronic_volume_model import VolumeFile, CaseVolume
from package.models.case import Case
from package.models.user import User
from package.models.finance import CaseFinance
from package.utils.ocr_helper import perform_smart_extraction
from package.utils.search_engine import meili_client
from package.core.config import ELECTRONIC_VOLUME_ROOT


def main():
    db = SessionLocal()
    try:
        # 1. 查询所有 OCR 提取失败的记录
        target_error = "PDF处理错误: Failed to load page."
        files = (
            db.query(VolumeFile)
            .filter(VolumeFile.ocr_content == target_error)
            .all()
        )
        total = len(files)
        print(f"找到 {total} 个需要重新 OCR 的文件\n")

        for idx, f in enumerate(files, 1):
            file_id = f.id
            file_name = f.file_name
            file_type = f.file_type or ""
            relative_path = f.file_path

            # 2. 拼接完整磁盘路径
            full_path = os.path.join(ELECTRONIC_VOLUME_ROOT, relative_path)

            print(f"[{idx}/{total}] file_id={file_id}, name={file_name}")

            if not os.path.exists(full_path):
                print(f"  ⚠ 文件不存在，跳过: {full_path}")
                # 写入占位标记
                f.ocr_content = "OCR失效(文件已丢失)"
                db.commit()
                continue

            # 3. 执行智能提取
            try:
                content = perform_smart_extraction(full_path, file_type)
            except Exception as e:
                print(f"  ⚠ 提取异常: {e}")
                content = ""

            # 4. 空值处理
            if not content or not content.strip():
                print(f"  ⚠ 未提取到内容，写入 OCR失效")
                content = "OCR失效"

            # 5. 截断保护
            if len(content) > 500000:
                content = content[:500000]

            # 6. 更新数据库
            f.ocr_content = content
            db.commit()
            print(f"  ✓ 数据库更新成功, 字数={len(content)}")

            # 7. 同步 Meilisearch
            try:
                volume = db.query(CaseVolume).filter(CaseVolume.id == f.volume_id).first()
                case_id = volume.case_id if (volume and volume.case_id) else 0

                document = {
                    "id": f.id,
                    "volume_id": f.volume_id,
                    "case_id": case_id,
                    "file_name": f.file_name,
                    "category": f.category,
                    "summary": f.summary or "",
                    "tags": f.tags or [],
                    "ocr_content": content,
                }
                meili_client.index("volume_files").add_documents(
                    [document], primary_key="id"
                )
                print(f"  ✓ Meilisearch 同步成功")
            except Exception as e:
                print(f"  ⚠ Meilisearch 同步失败: {e}")

            print()  # 空行分隔

        print("全部处理完成")

    finally:
        db.close()


if __name__ == "__main__":
    main()
