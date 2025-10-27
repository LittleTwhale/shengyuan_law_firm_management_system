# crud/electronic_seal.py
import os
from datetime import datetime
from typing import List, Optional, cast
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import UploadFile

from ..models.electronic_seal import ElectronicSeal  # 需先定义印章模型
from ..schemas.electronic_seal import ElectronicSealCreate, ElectronicSealUpdate
from ..core.config import ELECTRONIC_SEAL_ROOT  # 印章存储根目录


def _generate_seal_path() -> str:
    """生成印章存储路径（根目录/年份/月份）"""
    year = datetime.now().strftime("%Y")
    month = datetime.now().strftime("%m")
    return os.path.join(year, month)  # 结构：年/月/


async def save_seal_file(file: UploadFile) -> str:
    """保存印章图片文件到服务器，返回相对路径"""
    relative_dir = _generate_seal_path()
    full_dir = os.path.join(ELECTRONIC_SEAL_ROOT, relative_dir)
    os.makedirs(full_dir, exist_ok=True)

    original_filename = file.filename
    if not original_filename:
        raise ValueError("文件名称不能为空")

    # 处理文件名重复
    full_path = os.path.join(full_dir, original_filename)
    if os.path.exists(full_path):
        name, ext = os.path.splitext(original_filename)
        counter = 1
        while os.path.exists(os.path.join(full_dir, f"{name}_{counter}{ext}")):
            counter += 1
        full_path = os.path.join(full_dir, f"{name}_{counter}{ext}")

    # 分块写入文件
    try:
        with open(full_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)  # 1MB 块
                if not chunk:
                    break
                f.write(chunk)
    except Exception as e:
        raise IOError(f"印章文件保存失败: {str(e)}")

    # 返回相对于根目录的路径
    return os.path.relpath(full_path, ELECTRONIC_SEAL_ROOT)


async def create_electronic_seal(
    db: Session,
    seal_in: ElectronicSealCreate,
    file: UploadFile,
) -> ElectronicSeal:
    """创建电子印章（文件保存 + 数据库记录）"""
    try:
        # 保存印章图片
        file_path = await save_seal_file(file)

        # 计算文件大小（KB）
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)
        file_size_kb = file_size // 1024

        # 创建数据库记录
        db_seal = ElectronicSeal(
            name=seal_in.name,
            image_path=file_path,
            image_type=file.content_type or "image/unknown",
            image_size=file_size_kb,
            is_active=True,  # 默认为启用状态
        )
        db.add(db_seal)
        db.commit()
        db.refresh(db_seal)
        return db_seal

    except (IOError, ValueError) as e:
        db.rollback()
        raise RuntimeError(f"文件处理失败: {str(e)}")

    except SQLAlchemyError as e:
        db.rollback()
        # 回滚已保存的文件
        if 'file_path' in locals():
            full_path = os.path.join(ELECTRONIC_SEAL_ROOT, file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
        raise RuntimeError(f"数据库操作失败: {str(e)}")

    finally:
        await file.close()


def get_electronic_seals(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None
) -> List[ElectronicSeal]:
    """获取印章列表（支持分页和状态筛选）"""
    query = db.query(ElectronicSeal)
    if is_active is not None:
        query = query.filter(ElectronicSeal.is_active == is_active)
    return cast(
        List[ElectronicSeal],
        query.order_by(ElectronicSeal.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_electronic_seal_by_id(db: Session, seal_id: int) -> Optional[ElectronicSeal]:
    """通过ID获取印章详情"""
    return db.query(ElectronicSeal).filter(ElectronicSeal.id == seal_id).first()


def update_electronic_seal(
    db: Session,
    seal_id: int,
    seal_in: ElectronicSealUpdate
) -> Optional[ElectronicSeal]:
    """更新印章信息（名称/启用状态）"""
    db_seal = get_electronic_seal_by_id(db, seal_id)
    if not db_seal:
        return None

    try:
        # 批量更新字段
        update_data = seal_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_seal, key, value)
        db.commit()
        db.refresh(db_seal)
        return db_seal
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"更新印章失败: {str(e)}")


def delete_electronic_seal(db: Session, seal_id: int) -> bool:
    """删除印章（文件 + 数据库记录）"""
    db_seal = get_electronic_seal_by_id(db, seal_id)
    if not db_seal:
        return False

    try:
        # 删除文件
        full_path = os.path.join(ELECTRONIC_SEAL_ROOT, db_seal.image_path)
        if os.path.exists(full_path):
            os.remove(full_path)

        # 清理空目录
        dir_path = os.path.dirname(full_path)
        if os.path.isdir(dir_path) and not os.listdir(dir_path):
            os.rmdir(dir_path)
        # 递归清理上级空目录（年份目录）
        year_dir = os.path.dirname(dir_path)
        if os.path.isdir(year_dir) and not os.listdir(year_dir):
            os.rmdir(year_dir)

        # 删除数据库记录
        db.delete(db_seal)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"删除印章失败: {str(e)}")