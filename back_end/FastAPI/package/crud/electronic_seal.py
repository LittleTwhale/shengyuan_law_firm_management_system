# back_end/FastAPI/package/crud/electronic_seal.py
import os
from datetime import datetime
from typing import List, Optional, Tuple, cast

from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from ..core.config import ELECTRONIC_SEAL_ROOT, SEAL_APPLICATION_ROOT
from ..crud.document import convert_word_to_pdf  # 假设已安装libreoffice并配置路径
from ..models.electronic_seal import ElectronicSeal, SealApplication, SealAuditLog
from ..schemas.electronic_seal import (
    ElectronicSealCreate, ElectronicSealUpdate,
    SealApplicationCreate, SealApplicationReview, SealLocationLog
)


# --- 文件路径生成和保存工具函数 ---

def _generate_seal_path() -> str:
    """生成印章存储路径（年/月）"""
    year = datetime.now().strftime("%Y")
    month = datetime.now().strftime("%m")
    return os.path.join(year, month)


def _generate_application_path() -> str:
    """生成用印申请文件存储路径（年/月）"""
    year = datetime.now().strftime("%Y")
    month = datetime.now().strftime("%m")
    return os.path.join(year, month)


async def save_file_to_disk(file: UploadFile, root_dir: str, sub_path: str) -> str:
    """通用文件保存函数，处理文件名重复并返回相对路径"""
    relative_dir = sub_path
    full_dir = os.path.join(root_dir, relative_dir)
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
        # 重置文件指针到开头，确保读取完整文件
        await file.seek(0)
        with open(full_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)  # 1MB 块
                if not chunk:
                    break
                f.write(chunk)
    except Exception as e:
        raise IOError(f"文件保存失败: {str(e)}")

    return os.path.relpath(full_path, root_dir)


# --- 电子印章 CRUD ---

async def create_electronic_seal(db: Session, seal_in: ElectronicSealCreate, file: UploadFile,
                                 uploaded_by: int) -> ElectronicSeal:
    """创建电子印章"""
    try:
        file_path = await save_file_to_disk(file, ELECTRONIC_SEAL_ROOT, _generate_seal_path())

        # 计算文件大小（KB）
        await file.seek(0)
        file_size = file.file.tell()
        file_size_kb = file_size // 1024
        await file.seek(0)

        db_seal = ElectronicSeal(
            name=seal_in.name,
            image_path=file_path,
            file_size=file_size_kb,
            uploaded_by=uploaded_by
        )
        db.add(db_seal)
        db.commit()
        db.refresh(db_seal)
        return db_seal
    except (IOError, ValueError, SQLAlchemyError) as e:
        db.rollback()
        raise RuntimeError(f"创建印章失败: {str(e)}")


def get_electronic_seals(db: Session, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None) -> List[
    ElectronicSeal]:
    """获取印章列表"""
    query = db.query(ElectronicSeal).options(joinedload(ElectronicSeal.uploader))
    if is_active is not None:
        query = query.filter(ElectronicSeal.is_active == is_active)
    return cast(List[ElectronicSeal], query.order_by(ElectronicSeal.created_at.desc()).offset(skip).limit(limit).all())


def get_electronic_seal_by_id(db: Session, seal_id: int) -> Optional[ElectronicSeal]:
    """通过ID获取印章详情"""
    return db.query(ElectronicSeal).options(joinedload(ElectronicSeal.uploader)).filter(
        ElectronicSeal.id == seal_id).first()


def update_electronic_seal(db: Session, seal_id: int, seal_in: ElectronicSealUpdate) -> Optional[ElectronicSeal]:
    """更新印章信息（启用状态）"""
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
    """删除印章（文件 + 数据库）"""
    db_seal = get_electronic_seal_by_id(db, seal_id)
    if not db_seal:
        return False

    try:
        full_path = os.path.join(ELECTRONIC_SEAL_ROOT, db_seal.image_path)
        if os.path.exists(full_path):
            os.remove(full_path)

        db.delete(db_seal)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"删除印章失败: {str(e)}")


# --- 用印申请 CRUD ---

async def create_seal_application(db: Session, application_in: SealApplicationCreate, file: UploadFile,
                                  applicant_id: int) -> SealApplication:
    """创建用印申请，并进行文件预处理（Word转PDF）"""
    seal = get_electronic_seal_by_id(db, application_in.seal_id)
    if not seal or not seal.is_active:
        raise ValueError("印章不存在或未启用")

    try:
        # 1. 保存原始文件
        original_file_path = await save_file_to_disk(
            file, SEAL_APPLICATION_ROOT, _generate_application_path()
        )

        # 记录原始文件信息
        original_file_name = file.filename
        file_type = file.content_type or "application/octet-stream"

        # 2. 预处理：判断文件类型，PDF 直接可用，Word 需后台转换
        full_original_path = os.path.join(SEAL_APPLICATION_ROOT, original_file_path)
        preview_pdf_path = None

        if file_type == "application/pdf":
            preview_pdf_path = original_file_path
        elif file_type in ["application/msword",
                           "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            # Word 文档转为异步后台处理，此处暂不设置 preview_pdf_path
            pass
        else:
            raise RuntimeError("不支持的文件类型，仅支持 PDF/Word 文档")

        # 3. 创建数据库记录
        db_application = SealApplication(
            applicant_id=applicant_id,
            seal_id=application_in.seal_id,
            original_file_name=original_file_name,
            original_file_path=original_file_path,
            file_type=file_type,
            preview_pdf_path=preview_pdf_path,
            apply_reason=application_in.apply_reason,
            status="待审核"
        )
        db.add(db_application)
        db.commit()
        db.refresh(db_application)
        return db_application

    except (IOError, ValueError, RuntimeError) as e:
        db.rollback()
        # 发生文件或转换错误时，尝试清理已保存的原始文件
        if 'original_file_path' in locals():
            full_path = os.path.join(SEAL_APPLICATION_ROOT, original_file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
        raise RuntimeError(f"申请创建失败: {str(e)}")
    except SQLAlchemyError as e:
        db.rollback()
        # 发生数据库错误时，尝试清理已保存的原始文件
        if 'original_file_path' in locals():
            full_path = os.path.join(SEAL_APPLICATION_ROOT, original_file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
        raise RuntimeError(f"申请创建数据库操作失败: {str(e)}")


def get_seal_applications(db: Session, skip: int = 0, limit: int = 10, applicant_id: Optional[int] = None,
                          status: Optional[str] = None,
                          search: Optional[str] = None) -> Tuple[List[SealApplication], int]:
    """获取用印申请列表（分页 + 搜索），返回 (items, total)"""
    from ..models.user import User

    query = db.query(SealApplication).options(
        joinedload(SealApplication.applicant),
        joinedload(SealApplication.reviewer),
        joinedload(SealApplication.seal)
    )

    if applicant_id:
        query = query.filter(SealApplication.applicant_id == applicant_id)
    if status:
        query = query.filter(SealApplication.status == status)

    # 搜索：匹配文件名或申请人姓名
    if search:
        query = query.join(SealApplication.applicant).filter(
            (SealApplication.original_file_name.ilike(f'%{search}%')) |
            (User.real_name.ilike(f'%{search}%'))
        )

    total = query.count()
    items = cast(List[SealApplication], query.order_by(SealApplication.created_at.desc()).offset(skip).limit(limit).all())
    return items, total


def get_seal_application_by_id(db: Session, application_id: int) -> Optional[SealApplication]:
    """获取单个用印申请详情，包含关联信息"""
    return db.query(SealApplication).options(
        joinedload(SealApplication.applicant),
        joinedload(SealApplication.reviewer),
        joinedload(SealApplication.seal),
        joinedload(SealApplication.audit_logs)
    ).filter(SealApplication.id == application_id).first()


def review_seal_application(db: Session, application_id: int, review_in: SealApplicationReview, reviewer_id: int) -> \
Optional[SealApplication]:
    """审核用印申请"""
    db_application = get_seal_application_by_id(db, application_id)
    if not db_application:
        return None
    if db_application.status != "待审核":
        raise ValueError(f"当前申请状态为 {db_application.status}，无法审核")

    try:
        db_application.status = review_in.status
        db_application.reviewer_id = reviewer_id
        db_application.review_time = datetime.now()
        db_application.review_remark = review_in.review_remark

        db.commit()
        db.refresh(db_application)
        return db_application
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"审核操作失败: {str(e)}")


async def confirm_stamping(db: Session, application_id: int, stamped_file: UploadFile, log_data: List[SealLocationLog],
                           reviewer_id: int) -> SealApplication:
    """
    确认盖章完成：保存盖章文件，更新申请状态和日志
    log_data 是前端传回的坐标列表
    """
    db_application = get_seal_application_by_id(db, application_id)
    if not db_application:
        raise ValueError(f"申请ID {application_id} 不存在")
    if db_application.status != "待审核":
        raise ValueError(f"当前申请状态为 '{db_application.status}'，无法执行盖章确认操作。")

    try:
        # 1. 保存已盖章的PDF文件
        stamped_file_path = await save_file_to_disk(
            stamped_file, SEAL_APPLICATION_ROOT, _generate_application_path()
        )

        # 2. 更新申请记录
        db_application.stamped_file_path = stamped_file_path
        db_application.status = "已通过"
        # 记录审核人/操作人
        db_application.reviewer_id = reviewer_id
        db_application.review_time = datetime.now()

        # 3. 保存盖章操作日志（先清理旧日志，再添加新日志）
        db.query(SealAuditLog).filter(SealAuditLog.application_id == application_id).delete()

        for log in log_data:
            db_log = SealAuditLog(
                application_id=application_id,
                page_number=log.page_number,
                x_coordinate=log.x,
                y_coordinate=log.y,
                seal_width=log.width,
                seal_height=log.height
            )
            db.add(db_log)

        db.commit()
        db.refresh(db_application)
        return db_application

    except (IOError, ValueError, SQLAlchemyError) as e:
        db.rollback()
        # 清理已保存的盖章文件（如果保存成功但后续步骤失败）
        if 'stamped_file_path' in locals():
            full_path = os.path.join(SEAL_APPLICATION_ROOT, stamped_file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
        raise RuntimeError(f"确认盖章操作失败: {str(e)}")


def convert_application_word_to_pdf(application_id: int) -> bool:
    """
    后台任务：对 Word 文档申请执行 Word → PDF 转换并更新记录。
    该函数自己管理数据库会话，适合作为 BackgroundTasks 的回调。
    返回 True 表示转换成功，False 表示失败。
    """
    from ..database.database import SessionLocal
    db = SessionLocal()
    try:
        application = db.query(SealApplication).filter(SealApplication.id == application_id).first()
        if not application:
            return False

        full_path = os.path.join(SEAL_APPLICATION_ROOT, application.original_file_path)
        if not os.path.exists(full_path):
            return False

        pdf_path = convert_word_to_pdf(full_path)
        if pdf_path:
            application.preview_pdf_path = os.path.relpath(pdf_path, SEAL_APPLICATION_ROOT)
            db.commit()
            return True
        return False
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()


def delete_seal_application(db: Session, application_id: int) -> bool:
    """删除用印申请 (包括所有关联文件)"""
    db_application = get_seal_application_by_id(db, application_id)
    if not db_application:
        return False

    try:
        # 收集所有需要删除的文件路径（相对路径）
        file_paths = [
            db_application.original_file_path,
            db_application.preview_pdf_path,
            db_application.stamped_file_path
        ]

        for rel_path in file_paths:
            if rel_path:
                full_path = os.path.join(SEAL_APPLICATION_ROOT, rel_path)
                if os.path.exists(full_path):
                    try:
                        os.remove(full_path)
                    except OSError as e:
                        # 单个文件删除失败不应阻塞数据库记录删除，记录警告后继续
                        import logging
                        logging.warning(f"删除文件失败: {full_path}, 错误: {e}")

        # 删除数据库记录 (日志会通过 cascade 自动删除)
        db.delete(db_application)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"删除申请失败: {str(e)}")