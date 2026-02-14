# package/api/party_building.py

import os
import shutil
import threading
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..core.config import PARTY_FILE_ROOT, PARTY_IMAGE_ROOT
from ..database.database import get_db
from ..models.user import User
from ..api.deps import get_current_user  # 获取当前登录用户的依赖
from ..schemas import party_building_schema as schemas
from ..crud import party_building_crud as crud
from ..crud.attachment import convert_word_to_pdf

# 确保目录存在
os.makedirs(PARTY_FILE_ROOT, exist_ok=True)
os.makedirs(PARTY_IMAGE_ROOT, exist_ok=True)

router = APIRouter(
    prefix="/party_building",
    tags=["Party Building (党建)"]
)


# ---------------- 权限依赖 ----------------

def require_party_admin(current_user: User = Depends(get_current_user)):
    """
    细粒度权限验证：检查用户是否有 'party_admin' 权限
    """
    # 1. Owner拥有最高权限
    if current_user.role in ['owner']:
        return current_user

    # 2. 检查自定义权限字段 (JSON)
    perms = current_user.permissions or {}
    if perms.get("party_admin") is True:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="您没有管理党建资料的权限"
    )


# ==========================================
# 1. 分类管理接口 (Category)
# ==========================================

@router.post("/categories", response_model=schemas.PartyCategoryOut)
def create_category(
        category_in: schemas.PartyCategoryCreate,
        db: Session = Depends(get_db),
        user: User = Depends(require_party_admin)  # 仅管理员可操作
):
    return crud.create_category(db, category_in)


@router.get("/categories", response_model=List[schemas.PartyCategoryOut])
def read_categories(
        active_only: bool = False,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user)  # 登录用户均可查看
):
    return crud.get_categories(db, only_active=active_only)


@router.put("/categories/{category_id}", response_model=schemas.PartyCategoryOut)
def update_category(
        category_id: int,
        category_in: schemas.PartyCategoryUpdate,
        db: Session = Depends(get_db),
        user: User = Depends(require_party_admin)
):
    category = crud.get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    return crud.update_category(db, category, category_in)


@router.delete("/categories/{category_id}")
def delete_category(
        category_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(require_party_admin)
):
    # 检查该分类下是否有文章
    materials = crud.get_materials(db, category_id=category_id, limit=1)
    if materials:
        raise HTTPException(status_code=400, detail="该分类下仍有资料，无法删除")

    success = crud.delete_category(db, category_id)
    if not success:
        raise HTTPException(status_code=404, detail="分类不存在")
    return {"detail": "删除成功"}


# ==========================================
# 2. 资料管理接口 (Material / Article)
# ==========================================

@router.post("/materials", response_model=schemas.PartyMaterialOut)
def create_material(
        material_in: schemas.PartyMaterialCreate,
        db: Session = Depends(get_db),
        user: User = Depends(require_party_admin)
):
    # 验证分类是否存在
    if not crud.get_category(db, material_in.category_id):
        raise HTTPException(status_code=404, detail="所选分类不存在")

    material = crud.create_material(db, material_in, publisher_id=user.id)
    return material


@router.get("/materials", response_model=schemas.PartyMaterialPage)  # <--- 修改返回类型
def read_materials(
        skip: int = 0,
        limit: int = 20,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user)
):
    total, materials = crud.get_materials(db, skip, limit, category_id, search)

    # 补充发布人姓名 (因为使用了 joinedload，这里可以简化)
    results = []
    for m in materials:
        # 即使使用了 joinedload，为了确保 Pydantic 能读到 publisher_name
        # 我们可以手动赋值，或者在 Schema 里配置 @validator
        if m.publisher:
            m.publisher_name = m.publisher.real_name
        results.append(m)

    return {"total": total, "items": results}


@router.get("/materials/{material_id}", response_model=schemas.PartyMaterialOut)
def read_material_detail(
        material_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user)
):
    material = crud.get_material(db, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="资料不存在")

    # 增加阅读量
    crud.increment_view_count(db, material_id)

    # 补充信息
    if material.publisher:
        material.publisher_name = material.publisher.real_name

    return material


@router.put("/materials/{material_id}", response_model=schemas.PartyMaterialOut)
def update_material(
        material_id: int,
        material_in: schemas.PartyMaterialUpdate,
        db: Session = Depends(get_db),
        user: User = Depends(require_party_admin)
):
    material = crud.get_material(db, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="资料不存在")
    return crud.update_material(db, material, material_in)


@router.delete("/materials/{material_id}")
def delete_material(
        material_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(require_party_admin)
):
    # 1. 先查询出资料信息（包含附件列表）
    material = crud.get_material(db, material_id)

    if not material:
        raise HTTPException(status_code=404, detail="资料不存在")

    # 2. 遍历并删除物理文件
    if material.attachments:
        for attachment in material.attachments:
            full_path = os.path.join(PARTY_FILE_ROOT, attachment.file_path)
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                    print(f"已物理删除文件: {full_path}")
                except Exception as e:
                    print(f"删除文件失败 {full_path}: {e}")

            pdf_path = os.path.splitext(full_path)[0] + ".pdf"
            if os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                    print(f"已物理删除pdf文件: {pdf_path}")
                except Exception as e:
                    print(f"删除pdf                                           文件失败 {pdf_path}: {e}")

    # 3. 删除数据库记录 (级联删除会自动清理 attachment 表的记录)
    success = crud.delete_material(db, material_id)
    if not success:
        raise HTTPException(status_code=404, detail="删除过程出错")

    return {"detail": "删除成功"}


# ==========================================
# 3. 附件管理接口 (Attachments)
# ==========================================

@router.post("/attachments", response_model=schemas.PartyAttachmentOut)
async def upload_attachment(
        material_id: int = Form(...),
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        user: User = Depends(require_party_admin)
):
    """上传红头文件/学习资料等附件"""
    # 1. 检查资料是否存在
    material = crud.get_material(db, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="关联的资料ID不存在")

    # 2. 生成安全的文件名
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(PARTY_FILE_ROOT, unique_filename)

    # 3. 保存文件
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail="文件保存失败")

    # === 如果是Word文档，异步生成PDF ===
    if file.content_type in [
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]:
        threading.Thread(
            target=convert_word_to_pdf,
            args=(file_path,),  # 传入绝对路径
            daemon=True
        ).start()

    # 4. 获取文件大小
    file_size = os.path.getsize(file_path)

    # 5. 写入数据库
    attachment = crud.create_party_attachment(
        db,
        material_id=material_id,
        uploaded_by=user.id,
        file_name=file.filename,
        file_path=unique_filename,  # 只存文件名，不存绝对路径
        file_size=file_size,
        file_type=file.content_type
    )

    # 补充上传人名字以便返回
    attachment.uploaded_by_name = user.real_name
    return attachment


@router.get("/attachments/{attachment_id}/download")
def download_attachment(
        attachment_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user)
):
    attachment = crud.get_attachment(db, attachment_id)

    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")

    full_path = os.path.join(PARTY_FILE_ROOT, attachment.file_path)

    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="文件在服务器上已丢失")

    # 加上 quote 处理中文文件名，防止下载时文件名乱码
    from urllib.parse import quote
    return FileResponse(
        path=full_path,
        filename=attachment.file_name,
        media_type='application/octet-stream',
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{quote(attachment.file_name)}"}
    )


@router.delete("/attachments/{attachment_id}")
def delete_attachment(
        attachment_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(require_party_admin)
):
    # 使用 CRUD
    attachment = crud.get_attachment(db, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")

    full_path = os.path.join(PARTY_FILE_ROOT, attachment.file_path)

    # 物理删除
    # 1. 删除原文件
    if os.path.exists(full_path):
        try:
            os.remove(full_path)
        except OSError:
            pass

    # 2. 删除可能存在的PDF副本 (针对Word)
    pdf_path = os.path.splitext(full_path)[0] + ".pdf"
    if os.path.exists(pdf_path):
        try:
            os.remove(pdf_path)
        except OSError:
            pass

    # 数据库删除
    crud.delete_party_attachment(db, attachment_id)
    return {"detail": "附件已删除"}


@router.get("/attachments/{attachment_id}/preview")
def preview_attachment(
        attachment_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user)  # 所有登录用户均可预览
):
    """
    预览党建附件 (支持图片、PDF、Word自动转PDF)
    """
    attachment = crud.get_attachment(db, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")

    full_path = os.path.join(PARTY_FILE_ROOT, attachment.file_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="文件在服务器上已丢失")

    # 1. 优先直接支持的类型 (图片, PDF)
    supported_types = {
        "image/jpeg", "image/png", "image/gif", "image/bmp", "image/webp",
        "application/pdf"
    }

    # 2. Word文档特殊处理
    if attachment.file_type in [
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]:
        # 预测PDF路径
        name, _ = os.path.splitext(full_path)
        pdf_path = f"{name}.pdf"

        # 检查PDF是否有效（存在且比原文件新）
        if os.path.exists(pdf_path):
            word_mtime = os.path.getmtime(full_path)
            pdf_mtime = os.path.getmtime(pdf_path)
            if pdf_mtime >= word_mtime:
                return FileResponse(path=pdf_path, media_type="application/pdf")

        # 若无效，尝试实时转换
        pdf_path = convert_word_to_pdf(full_path)
        if pdf_path:
            return FileResponse(path=pdf_path, media_type="application/pdf")
        else:
            raise HTTPException(status_code=500, detail="预览生成失败，请下载查看")

    # 3. 其他不支持预览的类型
    if attachment.file_type not in supported_types:
        raise HTTPException(
            status_code=415,
            detail=f"不支持在线预览此格式: {attachment.file_type}"
        )

    # 4. 返回原文件预览
    return FileResponse(
        path=full_path,
        media_type=str(attachment.file_type)
    )


# ==========================================
# 4. 富文本图片上传 (Rich Text Image)
# ==========================================

@router.post("/upload_image")
async def upload_rich_text_image(
        request: Request,
        file: UploadFile = File(...),
        user: User = Depends(require_party_admin)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="只能上传图片文件")

    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(PARTY_IMAGE_ROOT, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 【关键】这里返回的 URL 必须能被浏览器访问到
    # 假设你在 main.py 里把 PARTY_IMAGE_ROOT 挂载到了 /static/party_images
    # 那么 URL 应该是：

    # 方式 A: 相对路径 (如果前端和后端同域)
    # url = f"/static/party_images/{unique_filename}"

    # 方式 B: 包含域名的完整路径 (建议从配置读取 BASE_URL)
    url = f"http://127.0.0.1:8002/static_resources/party_images/{unique_filename}"

    return {
        "errno": 0,
        "data": {
            "url": url,
            "alt": file.filename,
            "href": ""
        }
    }
