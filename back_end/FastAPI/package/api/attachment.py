# api/attachment.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from ..database.database import get_db
from ..models.attachment import CaseAttachment
from ..schemas.attachment import AttachmentCreate, AttachmentOut
from ..crud.attachment import create_attachment, get_attachments_by_case_id, delete_attachment_by_id, \
    convert_word_to_pdf
from ..crud.case import get_case_by_id  # 用于验证案件存在性

from fastapi.responses import FileResponse
import os
from ..core.config import CASE_ATTACHMENT_ROOT

router = APIRouter(
    prefix="/attachments",
    tags=["attachment"]
)


@router.post("/", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
        case_id: int,
        uploaded_by: int,
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    """
    上传案件附件
    - 验证案件存在性
    - 接收文件并保存到服务器
    - 创建附件数据库记录
    - 对Word文件自动预生成PDF
    """
    # 验证案件存在性
    if not get_case_by_id(db, case_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"案件ID {case_id} 不存在"
        )

    # 构建附件创建参数
    attachment_in = AttachmentCreate(
        case_id=case_id,
        uploaded_by=uploaded_by
    )

    try:
        # 保存附件并获取数据库记录
        db_attachment = await create_attachment(
            db=db,
            attachment_in=attachment_in,
            file=file
        )

        # 检查是否为Word文件，若是则触发PDF转换
        if db_attachment.file_type in [
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]:
            # 构建Word文件的完整路径
            full_path = os.path.join(CASE_ATTACHMENT_ROOT, str(db_attachment.file_path))

            # 异步执行转换（不阻塞当前请求）
            import threading
            threading.Thread(
                target=convert_word_to_pdf,
                args=(full_path,),
                daemon=True  # 随主线程退出而终止
            ).start()

        return db_attachment

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/case/{case_id}", response_model=List[AttachmentOut])
def get_case_attachments(
        case_id: int,
        db: Session = Depends(get_db)
):
    """根据案件ID查询所有附件"""
    # 验证案件存在性
    if not get_case_by_id(db, case_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"案件ID {case_id} 不存在"
        )

    return get_attachments_by_case_id(db, case_id)


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
        attachment_id: int,
        db: Session = Depends(get_db)
):
    """删除附件（同时删除文件和数据库记录）"""
    try:
        success = delete_attachment_by_id(db, attachment_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"附件ID {attachment_id} 不存在"
            )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{attachment_id}/download")
def download_attachment(
        attachment_id: int,
        db: Session = Depends(get_db)
):
    """下载附件文件"""

    # 查询附件信息
    attachment = db.query(CaseAttachment).filter(
        CaseAttachment.attachment_id == attachment_id
    ).first()

    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"附件ID {attachment_id} 不存在"
        )

    # 构建完整文件路径
    full_path = os.path.join(CASE_ATTACHMENT_ROOT, str(attachment.file_path))
    if not os.path.exists(full_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="附件文件已丢失"
        )

    # 返回文件下载响应
    return FileResponse(
        path=full_path,
        filename=str(attachment.file_name),
        media_type=attachment.file_type or "application/octet-stream"
    )

@router.get("/{attachment_id}/preview")
def preview_attachment(
        attachment_id: int,
        db: Session = Depends(get_db)
):
    """
    预览图片或PDF附件
    - 直接返回文件内容，支持浏览器原生预览
    - 仅支持图片和PDF格式
    """
    from fastapi.responses import FileResponse

    # 查询附件信息
    attachment = db.query(CaseAttachment).filter(
        CaseAttachment.attachment_id == attachment_id
    ).first()

    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"附件ID {attachment_id} 不存在"
        )

    # 构建完整文件路径
    full_path = os.path.join(CASE_ATTACHMENT_ROOT, str(attachment.file_path))
    if not os.path.exists(full_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="附件文件已丢失"
        )

    # 验证文件类型是否支持预览
    supported_types = {
        # 图片类型
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/bmp",
        "image/webp",
        # PDF类型
        "application/pdf"
    }

    # Word文档处理：优先使用上传时预生成的PDF
    if attachment.file_type in [
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]:
        # 直接计算预生成的PDF路径（无需调用转换函数即可检查）
        name, _ = os.path.splitext(full_path)
        pdf_path = f"{name}.pdf"

        # 检查PDF是否存在且未过期（PDF修改时间晚于原文件）
        if os.path.exists(pdf_path):
            word_mtime = os.path.getmtime(full_path)
            pdf_mtime = os.path.getmtime(pdf_path)
            if pdf_mtime >= word_mtime:
                # 预生成的PDF有效，直接返回
                return FileResponse(
                    path=pdf_path,
                    media_type="application/pdf"
                )

        # 若PDF不存在或过期，再触发转换（兼容未预生成或文件更新的情况）
        pdf_path = convert_word_to_pdf(full_path)
        if pdf_path:
            return FileResponse(
                path=pdf_path,
                media_type="application/pdf"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Word文档转换预览格式失败，请下载查看"
            )

    if attachment.file_type not in supported_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"不支持预览该类型文件: {attachment.file_type}\n支持的类型: 图片(JPG/PNG等)和PDF"
        )

    # 返回文件用于预览（不指定filename，让浏览器直接显示而非下载）
    return FileResponse(
        path=full_path,
        media_type=str(attachment.file_type),
        # 不设置filename参数，浏览器会尝试直接显示文件
    )