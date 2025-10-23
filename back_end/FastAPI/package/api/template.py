from fastapi import APIRouter, HTTPException, Query, Depends, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import mimetypes

from ..core.config import DOCUMENT_TEMPLATE_ROOT
from ..crud.document import create_template, get_template_by_id, delete_template, get_templates
from ..database.database import get_db
from ..schemas.document import TemplateCreate, TemplateOut

router = APIRouter(
    prefix="/template",
    tags=["template"]
)

# 模板文件目录
TEMPLATE_DIR = os.path.join("FastAPI", "static", "template")

@router.get("/download")
async def download_template(filename: str = Query(..., description="要下载的文件名")):
    """
    通用模板下载接口
    """
    file_path = os.path.join(TEMPLATE_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"文件 {filename} 不存在")

    # 自动识别 MIME 类型
    mime_type, _ = mimetypes.guess_type(file_path)
    mime_type = mime_type or "application/octet-stream"

    # 使用 FileResponse 返回文件流
    return FileResponse(
        file_path,
        filename=filename,
        media_type=mime_type
    )

# 新增：文书模板上传接口
@router.post("/document", response_model=TemplateOut, status_code=status.HTTP_201_CREATED)
async def upload_document_template(
    uploaded_by: int,
    name: str = Query(..., description="模板名称（含扩展名）"),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传文书模板（保存到 根目录/当前年份/文件名）"""
    template_in = TemplateCreate(
        name=name,
        description=description,
        uploaded_by=uploaded_by
    )

    try:
        db_template = await create_template(
            db=db,
            template_in=template_in,
            file=file
        )
        # 检查是否为Word文件，若是则触发PDF转换
        if db_template.file_type in [
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]:
            # 构建Word文件的完整路径
            full_path = os.path.join(DOCUMENT_TEMPLATE_ROOT, str(db_template.file_path))

            # 异步执行转换（不阻塞当前请求）
            import threading
            from ..crud.document import convert_word_to_pdf
            threading.Thread(
                target=convert_word_to_pdf,
                args=(full_path,),
                daemon=True  # 随主线程退出而终止
            ).start()

        return db_template
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# 新增：获取文书模板列表
@router.get("/document", response_model=List[TemplateOut])
def list_document_templates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取所有文书模板列表（支持分页）"""
    return get_templates(db, skip=skip, limit=limit)


# 新增：获取单个文书模板详情
@router.get("/document/{template_id}", response_model=TemplateOut)
def get_document_template(template_id: int, db: Session = Depends(get_db)):
    """根据ID获取文书模板详情"""
    template = get_template_by_id(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模板ID {template_id} 不存在"
        )
    return template


# 新增：删除文书模板
@router.delete("/document/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_document_template(template_id: int, db: Session = Depends(get_db)):
    """删除文书模板（同时删除文件和数据库记录）"""
    try:
        success = delete_template(db, template_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"模板ID {template_id} 不存在"
            )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# 新增：下载文书模板
@router.get("/document/{template_id}/download")
def download_document_template(template_id: int, db: Session = Depends(get_db)):
    """下载指定ID的文书模板文件"""
    template = get_template_by_id(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模板ID {template_id} 不存在"
        )

    full_path = os.path.join(DOCUMENT_TEMPLATE_ROOT, template.file_path)
    if not os.path.exists(full_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板文件已丢失"
        )

    return FileResponse(
        path=full_path,
        filename=template.name,
        media_type=template.file_type or "application/octet-stream"
    )


# 新增：预览文书模板
@router.get("/document/{template_id}/preview")
def preview_document_template(template_id: int, db: Session = Depends(get_db)):
    """预览文书模板（支持图片、PDF和Word转换）"""
    template = get_template_by_id(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模板ID {template_id} 不存在"
        )

    full_path = os.path.join(DOCUMENT_TEMPLATE_ROOT, template.file_path)
    if not os.path.exists(full_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板文件已丢失"
        )

    # 支持直接预览的类型
    supported_types = {
        "image/jpeg", "image/png", "image/gif", "image/bmp", "image/webp",
        "application/pdf"
    }

    # Word文件处理（转换为PDF预览）
    if template.file_type in [
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]:
        from ..crud.document import convert_word_to_pdf
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

    if template.file_type not in supported_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"不支持预览该类型文件: {template.file_type}"
        )

    return FileResponse(
        path=full_path,
        media_type=template.file_type
    )