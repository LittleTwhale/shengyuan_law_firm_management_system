#!/usr/bin/env python
"""
迁移脚本：将云服务器本地文件批量迁移至腾讯云 COS

用法（在云服务器上执行）:
    # 先配置好 .env 中的 COS 密钥
    cd /path/to/back_end/FastAPI
    fastapivenv/bin/python scripts/migrate_to_cos.py

可选参数:
    --dry-run      仅预览将要迁移的文件，不实际上传
    --root /data   云服务器上的数据根目录（默认从 config.py 读取）
"""

import os
import sys
import argparse
from pathlib import Path

# 确保能找到项目包（脚本位于 FastAPI/scripts/ 下，上两级即 FastAPI/）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ============================================================
# ============================================================
# COS 对象键模块前缀映射（与各 API 上传路径保持一致）
# ============================================================
COS_PREFIX_MAP = {
    "CASE_ATTACHMENT_ROOT":    "attachments",
    "DOCUMENT_TEMPLATE_ROOT":  "templates",
    "ELECTRONIC_SEAL_ROOT":    "seals",
    "SEAL_APPLICATION_ROOT":   "seal_applications",
    "ELECTRONIC_VOLUME_ROOT":  "electronic_volumes",
    "PDF_VOLUME_ROOT":         "pdf_volumes",
    "PARTY_FILE_ROOT":         "party_attachments",
}

# 迁移映射表：每一条目定义 表名 → 字段映射
# ============================================================
MIGRATION_MAP = [
    # (模型类, 根目录常量名, [(源字段, 目标cos_key字段), ...])
]

# 延迟导入，等解析完参数后再加载
def load_root_map():
    """读取模块级路径常量（config.py 中的 _ROOT 变量）"""
    import package.core.config as cfg
    return {
        "CASE_ATTACHMENT_ROOT":    cfg.CASE_ATTACHMENT_ROOT,
        "DOCUMENT_TEMPLATE_ROOT":  cfg.DOCUMENT_TEMPLATE_ROOT,
        "ELECTRONIC_SEAL_ROOT":    cfg.ELECTRONIC_SEAL_ROOT,
        "SEAL_APPLICATION_ROOT":   cfg.SEAL_APPLICATION_ROOT,
        "ELECTRONIC_VOLUME_ROOT":  cfg.ELECTRONIC_VOLUME_ROOT,
        "PDF_VOLUME_ROOT":         cfg.PDF_VOLUME_ROOT,
        "PARTY_FILE_ROOT":         cfg.PARTY_FILE_ROOT,
    }


def init_cos_client():
    """初始化 COS 客户端"""
    from package.core.config import settings
    from qcloud_cos import CosConfig, CosS3Client

    config = CosConfig(
        Region=settings.COS_REGION,
        SecretId=settings.COS_SECRET_ID,
        SecretKey=settings.COS_SECRET_KEY,
    )
    return CosS3Client(config)


def upload_file(client, local_path: str, cos_key: str) -> bool:
    """
    上传单个文件到 COS。
    如果文件不存在则跳过（可能已被清理或迁移过）。
    """
    if not os.path.exists(local_path):
        print(f"  ⚠ 文件不存在，跳过: {local_path}")
        return False

    from package.core.config import settings
    try:
        client.upload_file(
            Bucket=settings.COS_BUCKET,
            Key=cos_key,
            LocalFilePath=local_path,
        )
        return True
    except Exception as e:
        print(f"  ✗ 上传失败 [{cos_key}]: {e}")
        return False


def migrate_table(client, db_session, model, root_dir: str, field_pairs, cos_prefix: str, dry_run: bool):
    """
    迁移一张表。
    field_pairs: [(file_path_field, cos_key_field), ...]
    cos_prefix: COS 对象键模块前缀（如 attachments、templates）
    """
    from package.core.config import settings

    table_name = model.__tablename__

    # 过滤出模型中实际存在的字段对（部分表可能尚未添加 cos_key）
    valid_pairs = []
    for src, dst in field_pairs:
        if hasattr(model, src) and hasattr(model, dst):
            valid_pairs.append((src, dst))
        else:
            print(f"  ⚠ 字段不存在，跳过: {table_name}.{dst}")

    if not valid_pairs:
        print(f"  无需迁移（无匹配字段）")
        return 0, 0, 0

    records = db_session.query(model).all()
    total = len(records)
    done = 0
    skipped = 0
    failed = 0

    for record in records:
        for src_field, dst_field in valid_pairs:
            file_path = getattr(record, src_field, None)
            cos_key = getattr(record, dst_field, None)

            if not file_path:
                continue  # 路径为空，跳过
            if cos_key:
                skipped += 1
                continue  # 已迁移过

            local_path = os.path.join(root_dir, file_path)
            # 标准化 COS 对象键：模块前缀 + 正斜杠路径
            normalized_key = f"{cos_prefix}/{file_path.replace('\\', '/')}"

            if dry_run:
                print(f"  [模拟] {table_name}.{dst_field}")
                print(f"         源: {local_path}")
                print(f"         目标: cos://{settings.COS_BUCKET}/{normalized_key}")
                done += 1
                continue

            # 上传
            ok = upload_file(client, local_path, normalized_key)
            if not ok:
                failed += 1
                continue

            # 更新数据库 cos_key
            setattr(record, dst_field, normalized_key)
            db_session.add(record)
            done += 1

            # 每 20 条批量提交一次
            if done % 20 == 0:
                db_session.commit()
                print(f"  ... 已提交 {done}/{total}")

    # 最后提交一次
    if not dry_run and done > 0:
        db_session.commit()

    return done, skipped, failed


def main():
    parser = argparse.ArgumentParser(description="迁移本地文件至腾讯云 COS")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不实际执行上传")
    parser.add_argument("--root", type=str, default=None,
                        help="云服务器数据根目录（覆盖 config.py 中的路径）")
    args = parser.parse_args()

    # ---------- 加载环境和配置 ----------
    from dotenv import load_dotenv
    load_dotenv()

    root_map = load_root_map()
    from package.core.config import settings

    # 如果传了 --root，则替换所有根目录前缀
    if args.root:
        overlay_root = args.root.replace("\\", "/")
        for key in root_map:
            # 提取原有路径的尾部相对结构
            original = root_map[key]
            # 取最后两级目录（如 attachments / electronic_volumes）
            rel_suffix = "/".join(p for p in original.replace("\\", "/").split("/") if p and p not in ("D:", "d:", "E:", "e:"))
            root_map[key] = os.path.join(overlay_root, rel_suffix)

    print("=" * 60)
    print(f"存储模式: {settings.STORAGE_TYPE}")
    print(f"COS Bucket: {settings.COS_BUCKET}")
    print(f"COS Region: {settings.COS_REGION}")
    print(f"Dry-run: {args.dry_run}")
    if args.root:
        print(f"数据根目录覆盖: {args.root}")
    print("=" * 60)

    if settings.STORAGE_TYPE != "COS":
        print("\n⚠ 警告: STORAGE_TYPE 不是 COS，迁移后记得修改 .env！\n")

    # ---------- 初始化 COS 客户端 ----------
    client = init_cos_client()

    # ---------- 导入 ORM 模型 ----------
    from sqlalchemy.orm import Session
    from package.database.database import SessionLocal
    from package.models.case import Case
    from package.models.user import User
    from package.models.finance import CaseFinance
    from package.models.attachment import CaseAttachment
    from package.models.document import DocumentTemplate
    from package.models.electronic_seal import ElectronicSeal, SealApplication
    from package.models.electronic_volume_model import VolumeFile, CaseVolume

    db: Session = SessionLocal()

    # ---------- 定义所有要迁移的表 ----------
    tasks = [
        (CaseAttachment,   "CASE_ATTACHMENT_ROOT",    [("file_path", "cos_key")]),
        (DocumentTemplate, "DOCUMENT_TEMPLATE_ROOT",  [("file_path", "cos_key")]),
        (ElectronicSeal,   "ELECTRONIC_SEAL_ROOT",    [("image_path", "image_cos_key")]),
        (SealApplication,  "SEAL_APPLICATION_ROOT",   [
            ("original_file_path", "original_cos_key"),
            ("preview_pdf_path",   "preview_pdf_cos_key"),
            ("stamped_file_path",  "stamped_file_cos_key"),
        ]),
        (VolumeFile,       "ELECTRONIC_VOLUME_ROOT",  [("file_path", "cos_key")]),
        (CaseVolume,       "PDF_VOLUME_ROOT",         [("merged_file_path", "cos_key")]),
    ]

    # 尝试添加党建附件（表可能不存在）
    try:
        from package.models.party_building_model import PartyAttachment
        tasks.append((PartyAttachment, "PARTY_FILE_ROOT", [("file_path", "cos_key")]))
    except (ImportError, Exception):
        pass

    # ---------- 执行迁移 ----------
    grand_total = {"done": 0, "skipped": 0, "failed": 0}

    for model, root_key, field_pairs in tasks:
        root_dir = root_map[root_key]
        cos_prefix = COS_PREFIX_MAP.get(root_key, "")
        table_name = model.__tablename__
        print(f"\n{'=' * 50}")
        print(f"表: {table_name}")
        print(f"根目录: {root_dir}")
        print(f"COS 前缀: {cos_prefix}")
        print(f"{'=' * 50}")

        try:
            d, s, f = migrate_table(client, db, model, root_dir, field_pairs, cos_prefix, args.dry_run)
            grand_total["done"] += d
            grand_total["skipped"] += s
            grand_total["failed"] += f
            print(f"  → 完成: {d} 上传, {s} 跳过(已迁移), {f} 失败")
        except Exception as e:
            print(f"  ✗ 迁移 {table_name} 失败: {e}")
            import traceback
            traceback.print_exc()

    db.close()

    # ---------- 汇总 ----------
    print(f"\n{'=' * 60}")
    print(f"迁移汇总:")
    print(f"  新上传:   {grand_total['done']}")
    print(f"  已存在:   {grand_total['skipped']}")
    print(f"  失败:     {grand_total['failed']}")
    print(f"{'=' * 60}")

    if args.dry_run:
        print("\n提示: 移除 --dry-run 参数以实际执行迁移。")
    else:
        print("\n迁移完成！建议验证后删除本地旧文件以释放空间。")
        print("然后修改 .env 中 STORAGE_TYPE=COS 即可切换至云存储。")


if __name__ == "__main__":
    main()
