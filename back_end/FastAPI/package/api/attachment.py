# api/attachment.py
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime


from ..database.database import get_db
from ..models.attachment import CaseAttachment
from .deps import get_current_active_user
from ..models.user import User
from ..schemas.attachment import AttachmentCreate, AttachmentOut
from ..crud.attachment import create_attachment, get_attachments_by_case_id, delete_attachment_by_id
from ..crud.case import get_case_by_id  # 用于验证案件存在性

import os
import uuid
import shutil
from ..core.config import CASE_ATTACHMENT_ROOT, settings
from ..utils.storage_manager import get_upload_credential, get_file_preview_url, get_file_download_url, cleanup_local_file
from ..crud.attachment import convert_word_to_pdf

router = APIRouter(
    prefix="/attachments",
    tags=["attachment"]
)


def _attachment_word_convert_and_cleanup(save_path: str, cos_key: str):
    """
    后台任务：Word→PDF 转换 → 上传 PDF 到 COS 预览缓存 → 清理本地文件及空文件夹
    """
    try:
        pdf_path = convert_word_to_pdf(save_path)
        if pdf_path and settings.STORAGE_TYPE == "COS":
            from ..utils.storage_manager import _get_cos_client
            stem, _ = os.path.splitext(cos_key)
            pdf_cos_key = f"preview_cache/{stem}.pdf"
            _get_cos_client().upload_file(
                Bucket=settings.COS_BUCKET,
                Key=pdf_cos_key,
                LocalFilePath=pdf_path,
            )
        # 清理本地 Word 和临时 PDF
        if os.path.exists(save_path):
            cleanup_local_file(save_path, CASE_ATTACHMENT_ROOT)
        if pdf_path and os.path.exists(pdf_path):
            cleanup_local_file(pdf_path, CASE_ATTACHMENT_ROOT)
    except Exception as e:
        print(f"[AttachmentWordConvert] 处理失败: {e}")


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_attachment(
        case_id: int = Form(..., description="关联的案件ID"),
        file: Optional[UploadFile] = File(None, description="上传文件（LOCAL 模式必填）"),
        background_tasks: BackgroundTasks = BackgroundTasks(),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    上传案件附件
    - COS 模式 + Word 文件：本地保存 → 上传 COS → 后台转 PDF 预览 → 清理本地
    - COS 模式 + 非 Word 文件：返回 STS 临时凭证供前端直传 COS
    - LOCAL 模式：接收二进制文件流，保存到本地磁盘
    """
    # 验证案件存在性
    if not get_case_by_id(db, case_id):
        raise HTTPException(status_code=404, detail=f"案件ID {case_id} 不存在")

    if not file:
        raise HTTPException(400, "需要上传文件")

    file_name = file.filename or "unknown"

    if settings.STORAGE_TYPE == "COS":
        # 判断是否为 Word 文件（需要本地 LibreOffice 转换 PDF）
        is_word = file.content_type in [
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ] or file_name.lower().endswith(('.doc', '.docx'))

        now = datetime.now()
        path_prefix = f"attachments/{now.year}/{now.month:02d}/case{case_id}"

        if is_word:
            # === Word 文件：本地保存 → 上传 COS → 后台转换 PDF → 清理 ===
            unique_name = f"{uuid.uuid4().hex}{os.path.splitext(file_name)[1]}"
            relative_path = os.path.join("attachments", str(now.year), f"{now.month:02d}", f"case{case_id}", unique_name)
            save_path = os.path.join(CASE_ATTACHMENT_ROOT, relative_path)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            file_size = os.path.getsize(save_path)
            cos_key = relative_path.replace("\\", "/")

            # 上传原始文件到 COS
            from ..utils.storage_manager import _get_cos_client
            _get_cos_client().upload_file(
                Bucket=settings.COS_BUCKET,
                Key=cos_key,
                LocalFilePath=save_path,
            )

            # 创建数据库记录
            db_attachment = CaseAttachment(
                case_id=case_id,
                file_name=file_name,
                file_path=relative_path,
                cos_key=cos_key,
                file_size=file_size,
                file_type=file.content_type,
                uploaded_by=current_user.id,
            )
            db.add(db_attachment)
            db.commit()
            db.refresh(db_attachment)

            # 后台转换 PDF → 上传 COS 预览缓存 → 清理本地
            background_tasks.add_task(
                _attachment_word_convert_and_cleanup,
                save_path=save_path,
                cos_key=cos_key,
            )

            return db_attachment

        else:
            # === 非 Word 文件：STS 前端直传 COS ===
            cred = get_upload_credential(file_name, path_prefix)
            db_attachment = CaseAttachment(
                case_id=case_id,
                file_name=file_name,
                file_path=cred["key"],
                cos_key=cred["key"],
                file_size=0,
                file_type=file.content_type,
                uploaded_by=current_user.id,
            )
            db.add(db_attachment)
            db.commit()
            db.refresh(db_attachment)

            return {
                "type": "COS",
                "credentials": cred["credentials"],
                "bucket": cred["bucket"],
                "region": cred["region"],
                "key": cred["key"],
                "attachment_id": db_attachment.attachment_id,
                "file_name": file_name,
            }

    # === LOCAL 模式：接收二进制文件，写入本地磁盘 ===
    attachment_in = AttachmentCreate(
        case_id=case_id,
        uploaded_by=current_user.id
    )

    try:
        db_attachment = await create_attachment(
            db=db,
            attachment_in=attachment_in,
            file=file
        )

        # Word 文件后台生成 PDF 预览
        if db_attachment.file_type in [
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]:
            full_path = os.path.join(CASE_ATTACHMENT_ROOT, str(db_attachment.file_path))
            background_tasks.add_task(convert_word_to_pdf, full_path)

        return db_attachment

    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/case/{case_id}", response_model=List[AttachmentOut])
def get_case_attachments(
        case_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """根据案件ID查询所有附件"""
    # 验证案件存在性
    if not get_case_by_id(db, case_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"案件ID {case_id} 不存在"
        )

    return get_attachments_by_case_id(db, case_id)


@router.patch("/{attachment_id}/size")
def update_attachment_size(
    attachment_id: int,
    file_size: int = Query(..., description="文件大小（字节）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """STS 上传完成后回写文件大小"""
    attachment = db.query(CaseAttachment).filter(CaseAttachment.attachment_id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    attachment.file_size = file_size
    db.commit()
    return {"ok": True}


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
        attachment_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
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
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """下载附件文件（LOCAL 返回 FileResponse，COS 重定向到预签名 URL）"""

    attachment = db.query(CaseAttachment).filter(
        CaseAttachment.attachment_id == attachment_id
    ).first()

    if not attachment:
        raise HTTPException(status_code=404, detail=f"附件ID {attachment_id} 不存在")

    result = get_file_download_url(attachment, root_dir=CASE_ATTACHMENT_ROOT)
    if result["type"] == "ERROR":
        raise HTTPException(status_code=404, detail=result["message"])
    elif result["type"] == "COS":
        return RedirectResponse(url=result["url"])

    # LOCAL
    return FileResponse(
        path=result["file_path"],
        filename=str(attachment.file_name),
        media_type=attachment.file_type or "application/octet-stream"
    )

@router.get("/{attachment_id}/preview")
def preview_attachment(
        attachment_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    预览附件（图片/PDF/Word 自动转 PDF）
    - LOCAL：通过 storage_manager 获取路径并返回 FileResponse
    - COS：  通过 storage_manager 获取签名 URL 并 302 重定向
    """
    attachment = db.query(CaseAttachment).filter(
        CaseAttachment.attachment_id == attachment_id
    ).first()

    if not attachment:
        raise HTTPException(status_code=404, detail=f"附件ID {attachment_id} 不存在")

    # 使用 storage_manager 处理本地/COS 逻辑
    result = get_file_preview_url(attachment, root_dir=CASE_ATTACHMENT_ROOT)
    if result["type"] == "ERROR":
        raise HTTPException(status_code=404, detail=result["message"])
    elif result["type"] == "COS":
        return RedirectResponse(url=result["url"])

    # LOCAL 模式：返回文件流
    file_path = result["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="附件文件已丢失")

    # Word 转换后为 PDF 或 原文件
    is_word = attachment.file_type in [
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    if is_word:
        # storage_manager 已处理 PDF 转换，直接返回
        return FileResponse(path=file_path, media_type="application/pdf")

    # 非 Word 文件：验证是否为可预览类型
    supported_types = {
        "image/jpeg", "image/png", "image/gif", "image/bmp", "image/webp",
        "application/pdf"
    }
    if attachment.file_type not in supported_types:
        raise HTTPException(
            status_code=415,
            detail=f"不支持预览该类型文件: {attachment.file_type}"
        )

    return FileResponse(path=file_path, media_type=str(attachment.file_type))