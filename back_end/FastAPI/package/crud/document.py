# crud/document.py
import os
import subprocess
from datetime import datetime
from typing import List, Optional, cast
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import UploadFile

from ..models.document import DocumentTemplate
from ..schemas.document import TemplateCreate
from ..core.config import DOCUMENT_TEMPLATE_ROOT


def _generate_file_path() -> str:
    """生成模板存储路径（根目录/当前年份）"""
    year = datetime.now().strftime("%Y")
    relative_path = os.path.join(year)  # 结构：年/
    return relative_path


async def save_template_file(
        file: UploadFile,
) -> str:
    """保存模板文件到服务器并返回相对路径"""
    relative_dir = _generate_file_path()
    full_dir = os.path.join(DOCUMENT_TEMPLATE_ROOT, relative_dir)
    os.makedirs(full_dir, exist_ok=True)

    original_filename = file.filename
    full_file_path = os.path.join(full_dir, original_filename)

    # 处理文件名重复
    if os.path.exists(full_file_path):
        name, ext = os.path.splitext(original_filename)
        counter = 1
        while os.path.exists(os.path.join(full_dir, f"{name}({counter}){ext}")):
            counter += 1
        full_file_path = os.path.join(full_dir, f"{name}({counter}){ext}")

    try:
        # 分块写入文件
        with open(full_file_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)  # 1MB chunks
                if not chunk:
                    break
                f.write(chunk)
    except Exception as e:
        raise IOError(f"文件保存失败: {e}")

    # 返回相对路径（相对于根目录）
    return os.path.relpath(full_file_path, DOCUMENT_TEMPLATE_ROOT)


async def create_template(
        db: Session,
        template_in: TemplateCreate,
        file: UploadFile,
        file_type: Optional[str] = None,
):
    """创建模板记录（文件保存 + 数据库插入）"""
    try:
        # 保存文件
        file_path = await save_template_file(
            file=file
        )

        # 计算文件大小（字节）
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        # 转换为KB（与数据库定义一致）
        file_size_kb = file_size // 1024

        # 创建数据库记录
        db_template = DocumentTemplate(
            name=template_in.name,
            file_path=file_path,
            file_type=file_type or file.content_type,
            file_size=file_size_kb,
            description=template_in.description,
            uploaded_by=template_in.uploaded_by
        )
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        return db_template

    except (IOError, ValueError) as e:
        db.rollback()
        raise RuntimeError(f"文件处理异常: {e}")

    except SQLAlchemyError as e:
        db.rollback()
        # 回滚已保存的文件
        if 'file_path' in locals() and file_path:
            full_file_path = os.path.join(DOCUMENT_TEMPLATE_ROOT, file_path)
            if os.path.exists(full_file_path):
                os.remove(full_file_path)
        raise RuntimeError(f"数据库操作失败: {e}")

    finally:
        await file.close()


def get_templates(
        db: Session,
        skip: int = 0,
        limit: int = 100
) -> List[DocumentTemplate]:
    """获取模板列表（支持分页）"""
    return cast(
        List[DocumentTemplate],
        db.query(DocumentTemplate)
        .order_by(DocumentTemplate.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_template_by_id(
        db: Session,
        template_id: int
) -> Optional[DocumentTemplate]:
    """根据ID获取模板"""
    return db.query(DocumentTemplate).filter(
        DocumentTemplate.id == template_id
    ).first()


def delete_template(
        db: Session,
        template_id: int
) -> bool:
    """删除模板（文件 + 数据库记录）"""
    template = get_template_by_id(db, template_id)
    if not template:
        return False

    full_path = os.path.join(DOCUMENT_TEMPLATE_ROOT, template.file_path)
    try:
        # 删除文件
        if os.path.exists(full_path):
            os.remove(full_path)

            # 检查并删除转换的PDF（如果有）
            if full_path.lower().endswith(('.doc', '.docx')):
                pdf_path = os.path.splitext(full_path)[0] + '.pdf'
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)

        # 尝试删除空目录（年份目录）
        dir_path = os.path.dirname(full_path)
        if os.path.isdir(dir_path) and not os.listdir(dir_path):
            os.rmdir(dir_path)

        # 删除数据库记录
        db.delete(template)
        db.commit()
        return True

    except Exception as e:
        db.rollback()
        raise RuntimeError(f"删除模板失败: {e}")


def convert_word_to_pdf(input_path: str) -> Optional[str]:
    """Word转PDF（复用附件模块的转换逻辑）"""
    if not input_path.lower().endswith(('.doc', '.docx')):
        return None

    output_path = os.path.splitext(input_path)[0] + '.pdf'

    # 检查PDF是否已存在且有效
    if os.path.exists(output_path):
        if os.path.getmtime(output_path) >= os.path.getmtime(input_path):
            return output_path

    # 执行转换（注意：libreoffice路径需根据实际环境调整）
    try:
        subprocess.run(
            [
                r"C:\Program Files\LibreOffice\program\soffice.exe",  # Windows路径
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