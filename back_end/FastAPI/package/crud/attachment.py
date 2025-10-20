# crud/attachment.py
import os
import subprocess
from datetime import datetime
from typing import List, Optional, cast

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from fastapi import UploadFile
from ..models.attachment import CaseAttachment
from ..models.case import Case
from ..schemas.attachment import AttachmentCreate
from ..core.config import CASE_ATTACHMENT_ROOT


def _generate_file_path(case_id: int, db: Session) -> str:
    """
    生成附件存储路径（年/月/案件号）
    Generate the folder path for attachments (year/month/case_id)
    """
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")

    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise ValueError(f"案件ID {case_id} 不存在 (Case ID {case_id} not found)")

    case_number_dir = f"case{case.case_id}"
    relative_path = os.path.join(year, month, case_number_dir)
    return relative_path


async def save_attachment_file(
    db: Session,
    case_id: int,
    file: UploadFile,
) -> str:
    """
    保存文件到服务器并返回相对路径
    Save uploaded file to the server and return relative path.
    """
    relative_dir = _generate_file_path(case_id, db)
    full_dir = os.path.join(CASE_ATTACHMENT_ROOT, relative_dir)
    os.makedirs(full_dir, exist_ok=True)

    original_filename = file.filename
    full_file_path = os.path.join(full_dir, original_filename)

    # 处理文件名重复（Handle filename conflict）
    if os.path.exists(full_file_path):
        name, ext = os.path.splitext(original_filename)
        counter = 1
        while os.path.exists(os.path.join(full_dir, f"{name}({counter}){ext}")):
            counter += 1
        full_file_path = os.path.join(full_dir, f"{name}({counter}){ext}")

    try:
        # 手动分块写入，类型系统友好 & 支持大文件
        # Write in chunks to avoid type issues and memory pressure
        with open(full_file_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)  # 每次读取 1MB
                if not chunk:
                    break
                f.write(chunk)
    except Exception as e:
        raise IOError(f"文件保存失败: {e} (Failed to save file: {e})")
    # 返回相对路径
    return os.path.relpath(full_file_path, CASE_ATTACHMENT_ROOT)


async def create_attachment(
    db: Session,
    attachment_in: AttachmentCreate,
    file: UploadFile,
    file_type: Optional[str] = None,
) :
    """
    创建附件记录（文件保存 + 数据库插入，含事务控制）
    Create attachment (file saving + DB insert) with transaction safety.
    """
    try:
        # 1️⃣ 保存文件
        file_path = await save_attachment_file(
            db=db,
            case_id=attachment_in.case_id,
            file=file
        )

        # 2️⃣ 计算文件大小（从 file.file 句柄读取）
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        # 3️⃣ 创建数据库记录
        db_attachment = CaseAttachment(
            case_id=attachment_in.case_id,
            file_name=file.filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type or file.content_type,
            uploaded_by=attachment_in.uploaded_by,
        )
        db.add(db_attachment)

        # 4️⃣ 提交事务
        db.commit()
        db.refresh(db_attachment)
        return db_attachment

    except (IOError, ValueError) as e:
        db.rollback()
        raise RuntimeError(f"文件或案件处理异常: {e}")

    except SQLAlchemyError as e:
        db.rollback()
        # 如果数据库失败，则删除已保存的文件，防止孤立文件
        # 只有在 file_path 已赋值的情况下才尝试删除文件
        if 'file_path' in locals() and file_path:
            full_file_path = os.path.join(CASE_ATTACHMENT_ROOT, file_path)
            if os.path.exists(full_file_path):
                os.remove(full_file_path)
        raise RuntimeError(f"数据库操作失败: {e}")

    finally:
        await file.close()


def get_attachments_by_case_id(db: Session, case_id: int) -> List[CaseAttachment]:
    """
    根据案件ID查询所有附件
    Get all attachments by case ID.
    """
    attachments = db.query(CaseAttachment).filter(CaseAttachment.case_id == case_id).all()
    return cast(List[CaseAttachment], attachments)


def delete_attachment_by_id(db: Session, attachment_id: int) -> bool:
    """
    删除附件（文件 + 数据库记录），含异常捕获
    Delete attachment (file + DB record) safely.
    """
    attachment: Optional[CaseAttachment] = (
        db.query(CaseAttachment).filter(CaseAttachment.attachment_id == attachment_id).first()
    )
    if not attachment:
        return False

    full_path = os.path.join(CASE_ATTACHMENT_ROOT, attachment.file_path)
    try:
        if os.path.exists(full_path):
            os.remove(full_path)
        # 删除文件后检查并删除空目录
        dir_path = os.path.dirname(full_path)
        if os.path.isdir(dir_path) and not os.listdir(dir_path):
            os.rmdir(dir_path)
        db.delete(attachment)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"删除附件失败: {e}")


def convert_word_to_pdf(input_path: str) -> Optional[str]:
    """
    使用libreoffice将Word文档转换为PDF
    需要先安装libreoffice: sudo apt-get install libreoffice (Linux)
    """
    if not input_path.lower().endswith(('.doc', '.docx')):
        return None

    # 输出PDF路径（与原文件同目录）
    name, _ = os.path.splitext(input_path)
    output_path = f"{name}.pdf"

    if os.path.exists(output_path):
        # 检查PDF生成时间是否晚于原文件（避免原文件更新后未重新转换）
        word_mtime = os.path.getmtime(input_path)  # Word文件最后修改时间
        pdf_mtime = os.path.getmtime(output_path)  # PDF文件最后修改时间
        if pdf_mtime >= word_mtime:
            return output_path  # PDF存在且未过期，直接返回

    # 执行转换命令
    try:
        subprocess.run(
            [
                r"D:\Down\LibreOffice\program\soffice.exe",
                "--headless",
                "--convert-to", "pdf",
                "--outdir", os.path.dirname(input_path),
                input_path
            ],
            check=True,
            capture_output=True,
            text=True
        )
        return output_path if os.path.exists(output_path) else None
    except Exception as e:
        print(f"Word转PDF失败: {e}")
        return None
