# crud/seal_application.py
import os
from datetime import datetime
from typing import List, Optional, cast

from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from .document import convert_word_to_pdf
from .electronic_seal import get_electronic_seal_by_id
from ..core.config import SEAL_APPLICATION_ROOT, ELECTRONIC_SEAL_ROOT
from ..models.electronic_seal import SealApplication, SealPosition
from ..schemas.electronic_seal import SealApplicationCreate, SealApplicationReview, SealPositionBase


def _generate_application_path() -> str:
    """生成用印申请文件存储路径（根目录/年份/月份）"""
    year = datetime.now().strftime("%Y")
    month = datetime.now().strftime("%m")
    return os.path.join(year, month)


async def save_application_file(file: UploadFile) -> str:
    """
    保存用印申请文件并返回相对路径
    """
    relative_dir = _generate_application_path()
    full_dir = os.path.join(SEAL_APPLICATION_ROOT, relative_dir)
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

    # 保存文件
    try:
        with open(full_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)  # 1MB块
                if not chunk:
                    break
                f.write(chunk)
    except Exception as e:
        raise IOError(f"文件保存失败: {str(e)}")

    # 返回相对于根目录的路径
    return os.path.relpath(full_path, SEAL_APPLICATION_ROOT)


async def create_seal_application(
        db: Session,
        application_in: SealApplicationCreate,
        file: UploadFile,
        applicant_id: int
) -> SealApplication:
    """创建用印申请"""
    # 验证印章是否存在且启用
    seal = get_electronic_seal_by_id(db, application_in.seal_id)
    if not seal:
        raise ValueError(f"电子印章ID {application_in.seal_id} 不存在")
    if not seal.is_active:
        raise ValueError("该印章已被禁用")

    try:
        # 保存文件
        file_path = await save_application_file(file)

        # 计算文件大小
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)
        file_size_kb = file_size // 1024

        # 创建数据库记录
        db_application = SealApplication(
            applicant_id=applicant_id,
            file_name=application_in.file_name,
            file_path=file_path,
            file_type=file.content_type or "application/octet-stream",
            file_size=file_size_kb,
            seal_id=application_in.seal_id,
            application_reason=application_in.application_reason,
            status="待审核"
        )
        db.add(db_application)
        db.commit()
        db.refresh(db_application)
        return db_application

    except (IOError, ValueError) as e:
        db.rollback()
        raise RuntimeError(f"文件处理失败: {str(e)}")
    except SQLAlchemyError as e:
        db.rollback()
        # 回滚已保存的文件
        if 'file_path' in locals():
            full_path = os.path.join(SEAL_APPLICATION_ROOT, file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
        raise RuntimeError(f"数据库操作失败: {str(e)}")
    finally:
        await file.close()


def get_seal_applications(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        applicant_id: Optional[int] = None,
        status: Optional[str] = None
) -> List[SealApplication]:
    """查询用印申请列表"""
    query = db.query(SealApplication).options(
        joinedload(SealApplication.applicant),
        joinedload(SealApplication.seal),
        joinedload(SealApplication.seal_positions)
    )

    if applicant_id:
        query = query.filter(SealApplication.applicant_id == applicant_id)
    if status:
        query = query.filter(SealApplication.status == status)

    return cast(list[SealApplication],query.order_by(SealApplication.created_at.desc()) \
        .offset(skip) \
        .limit(limit) \
        .all())


def get_seal_application_by_id(
        db: Session,
        application_id: int
) -> Optional[SealApplication]:
    """通过ID查询用印申请详情"""
    return db.query(SealApplication) \
        .options(
        joinedload(SealApplication.applicant),
        joinedload(SealApplication.reviewer),
        joinedload(SealApplication.seal),
        joinedload(SealApplication.seal_positions)
    ) \
        .filter(SealApplication.id == application_id) \
        .first()


def review_seal_application(
        db: Session,
        application_id: int,
        review_in: SealApplicationReview,
        reviewer_id: int
) -> Optional[SealApplication]:
    """审核用印申请"""
    db_application = get_seal_application_by_id(db, application_id)
    if not db_application:
        return None

    # 验证状态（只能审核待审核的申请）
    if db_application.status != "待审核":
        raise RuntimeError(f"当前申请状态为 {db_application.status}，无法审核")

    try:
        # 更新审核信息
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


def create_seal_positions(
        db: Session,
        application_id: int,
        positions: List[SealPositionBase]
) -> List[SealPosition]:
    """创建印章位置配置"""
    try:
        db_positions = []
        for position in positions:
            db_position = SealPosition(
                application_id=application_id,
                page_num=position.page_num,
                x=position.x,
                y=position.y,
                width=position.width,
                height=position.height
            )
            db.add(db_position)
            db_positions.append(db_position)

        db.commit()
        for position in db_positions:
            db.refresh(position)
        return db_positions
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"创建印章位置失败: {str(e)}")


def get_seal_positions_by_application(
        db: Session,
        application_id: int
) -> List[SealPosition]:
    """获取申请的印章位置配置"""
    return cast(list[SealPosition],db.query(SealPosition) \
        .filter(SealPosition.application_id == application_id) \
        .all())


async def apply_seal_to_pdf(
        db: Session,
        application_id: int,
        positions: List[SealPositionBase]
) -> str:
    """
    对审核通过的申请执行盖章操作
    返回盖章后文件的相对路径
    """
    from PyPDF2 import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    import io

    db_application = get_seal_application_by_id(db, application_id)
    if not db_application:
        raise ValueError(f"用印申请ID {application_id} 不存在")

    # 验证状态
    if db_application.status != "已通过":
        raise RuntimeError(f"只有审核通过的申请才能盖章（当前状态：{db_application.status}）")

    # 获取PDF文件和印章路径
    original_file_path = os.path.join(SEAL_APPLICATION_ROOT, db_application.file_path)

    # 如果是Word文件，先转换为PDF
    if db_application.file_path.lower().endswith(('.doc', '.docx')):
        pdf_path = convert_word_to_pdf(original_file_path)
        if not pdf_path:
            raise RuntimeError("Word文件转换为PDF失败")
        pdf_full_path = pdf_path
    else:
        pdf_full_path = original_file_path

    if not os.path.exists(pdf_full_path):
        raise FileNotFoundError("待盖章的PDF文件不存在")

    seal = get_electronic_seal_by_id(db, db_application.seal_id)
    if not seal:
        raise ValueError(f"电子印章已被删除（ID: {db_application.seal_id}）")

    seal_full_path = os.path.join(ELECTRONIC_SEAL_ROOT, seal.image_path)
    if not os.path.exists(seal_full_path):
        raise FileNotFoundError(f"印章图片文件不存在（{seal_full_path}）")

    try:
        # 读取原始PDF
        reader = PdfReader(pdf_full_path)
        writer = PdfWriter()

        # 处理每个页面
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]

            # 查找当前页的印章位置
            page_positions = [p for p in positions if p.page_num == page_num + 1]
            if not page_positions:
                writer.add_page(page)
                continue

            # 创建临时PDF用于绘制印章
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)

            for pos in page_positions:
                # 绘制印章
                can.drawImage(
                    seal_full_path,
                    pos.x,
                    pos.y,
                    width=pos.width,
                    height=pos.height,
                    mask='auto'  # 支持透明度
                )

            can.save()
            packet.seek(0)

            # 合并印章到原页面
            stamp_reader = PdfReader(packet)
            stamp_page = stamp_reader.pages[0]
            page.merge_page(stamp_page)
            writer.add_page(page)

        # 保存盖章后的文件
        sealed_filename = f"sealed_{db_application.file_name}.pdf"
        sealed_relative_dir = _generate_application_path()
        sealed_full_dir = os.path.join(SEAL_APPLICATION_ROOT, sealed_relative_dir)
        os.makedirs(sealed_full_dir, exist_ok=True)

        sealed_full_path = os.path.join(sealed_full_dir, sealed_filename)
        with open(sealed_full_path, "wb") as f:
            writer.write(f)

        # 保存印章位置到数据库
        create_seal_positions(db, application_id, positions)

        # 更新数据库记录
        sealed_relative_path = os.path.relpath(sealed_full_path, SEAL_APPLICATION_ROOT)
        db_application.sealed_file_path = sealed_relative_path
        db.commit()

        return sealed_relative_path

    except Exception as e:
        db.rollback()
        raise RuntimeError(f"盖章操作失败: {str(e)}")


def delete_seal_application(
        db: Session,
        application_id: int
) -> bool:
    """删除用印申请"""
    db_application = get_seal_application_by_id(db, application_id)
    if not db_application:
        return False

    try:
        # 删除关联文件
        file_paths = [
            db_application.file_path,
            db_application.sealed_file_path
        ]

        for path in file_paths:
            if path:
                full_path = os.path.join(SEAL_APPLICATION_ROOT, path)
                if os.path.exists(full_path):
                    os.remove(full_path)

        # 删除数据库记录（关联的seal_positions会自动删除，因为有cascade）
        db.delete(db_application)
        db.commit()
        return True

    except Exception as e:
        db.rollback()
        raise RuntimeError(f"删除申请失败: {str(e)}")