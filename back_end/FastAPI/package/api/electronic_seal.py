# api/electronic_seal.py
import json
import os
from typing import List, Optional
from urllib.parse import unquote

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..core.config import ELECTRONIC_SEAL_ROOT, SEAL_APPLICATION_ROOT
from ..crud import electronic_seal as seal_crud  # 使用别名导入所有CRUD函数
from ..database.database import get_db
from ..models.user import User
from ..schemas.electronic_seal import (
    ElectronicSealCreate, ElectronicSealOut, ElectronicSealUpdate,
    SealApplicationCreate, SealApplicationOut, SealApplicationSimpleOut,
    SealApplicationReview, SealLocationLog, PaginatedResponse,
)

# 引入获取当前用户的依赖
from .deps import get_current_active_user

router = APIRouter(
    prefix="/electronic_seal",
    tags=["电子用印"]
)


# =================================================================
#  权限检查辅助函数
# =================================================================
def check_admin_permission(user: User):
    """检查是否为管理员或Owner"""
    if not user.role or user.role not in ["admin", "owner"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限操作")


def check_seal_approval_permission(user: User):
    """
    检查用户是否有权审批印章申请
    """
    # 直接使用 current_user 判断，不再需要查数据库
    # 1. Owner 放行
    if user.role == 'owner':
        return True

    # 2. 检查 can_approve_seal 权限
    perms = user.permissions or {}
    if perms.get('can_approve_seal', False) is True:
        return True

    raise HTTPException(status_code=403, detail="您没有审批印章的权限")


# =================================================================
# 电子印章管理 (Admin)
# =================================================================
@router.post("/seals", response_model=ElectronicSealOut, status_code=status.HTTP_201_CREATED)
async def create_electronic_seal(
        name: str = Form(..., description="印章名称"),
        file: UploadFile = File(..., description="印章图片文件（支持png/jpg格式）"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """【管理员】创建电子印章（需上传印章图片）"""
    check_admin_permission(current_user)
    seal_in = ElectronicSealCreate(name=name)
    try:
        # 直接使用 current_user.id
        return await seal_crud.create_electronic_seal(db, seal_in, file, current_user.id)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/seals", response_model=List[ElectronicSealOut])
def list_electronic_seals(
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """获取电子印章列表（通用）"""
    return seal_crud.get_electronic_seals(db, skip=skip, limit=limit, is_active=is_active)


@router.get("/seals/{seal_id}", response_model=ElectronicSealOut)
def get_electronic_seal_detail(
        seal_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """获取单个电子印章详情"""
    seal = seal_crud.get_electronic_seal_by_id(db, seal_id)
    if not seal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"电子印章ID {seal_id} 不存在")
    return seal


@router.get("/seals/{seal_id}/image")
async def get_seal_image(
        seal_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """获取印章图片（用于前端可视化）"""
    seal = seal_crud.get_electronic_seal_by_id(db, seal_id)
    if not seal:
        raise HTTPException(status_code=404, detail="印章不存在")

    full_path = os.path.join(ELECTRONIC_SEAL_ROOT, seal.image_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="印章图片文件不存在")

    return FileResponse(
        full_path,
        # 强制添加 CORS 标头
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
        }
    )


@router.put("/seals/{seal_id}", response_model=ElectronicSealOut)
def update_electronic_seal_status(
        seal_id: int,
        seal_in: ElectronicSealUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)  # 替换了 role
):
    """【管理员】更新电子印章启用状态"""
    check_admin_permission(current_user)
    try:
        updated_seal = seal_crud.update_electronic_seal(db, seal_id, seal_in)
        if not updated_seal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"电子印章ID {seal_id} 不存在")
        return updated_seal
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/seals/{seal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_electronic_seal(
        seal_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)  # 替换了 role
):
    """【管理员】删除电子印章（同时删除关联文件）"""
    check_admin_permission(current_user)
    try:
        success = seal_crud.delete_electronic_seal(db, seal_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"电子印章ID {seal_id} 不存在")
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# =================================================================
# 用印申请 (User/Admin)
# =================================================================
@router.post("/applications", response_model=SealApplicationOut, status_code=status.HTTP_201_CREATED)
async def create_seal_application(
        background_tasks: BackgroundTasks,
        seal_id: int = Form(..., description="申请使用的印章ID"),
        apply_reason: Optional[str] = Form(None, description="用印原因"),
        file: UploadFile = File(..., description="待盖章文件（Word/PDF）"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)  # 替换了 applicant_id
):
    """【用户】创建用印申请，上传原始文件（Word 文档转为后台异步转换）"""
    application_in = SealApplicationCreate(seal_id=seal_id, apply_reason=apply_reason)
    try:
        application = await seal_crud.create_seal_application(db, application_in, file, current_user.id)

        # 如果是 Word 文档，触发后台异步转换
        if application.file_type in [
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]:
            background_tasks.add_task(seal_crud.convert_application_word_to_pdf, application.id)

        return application
    except (ValueError, RuntimeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/applications", response_model=PaginatedResponse[SealApplicationSimpleOut])
def list_seal_applications(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页数量"),
        applicant_id: Optional[int] = Query(None, description="按申请人筛选"),
        status: Optional[str] = None,
        search: Optional[str] = Query(None, description="搜索文件名或申请人"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """获取用印申请列表（分页+搜索），用户查自己的，管理员查所有"""
    if status:
        status = unquote(status)

    # 非管理员/审批人，强制只能查自己的
    if current_user.role not in ["admin", "owner"] and not (
            current_user.permissions and current_user.permissions.get('can_approve_seal')):
        applicant_id = current_user.id

    skip = (page - 1) * page_size
    items, total = seal_crud.get_seal_applications(
        db, skip=skip, limit=page_size, applicant_id=applicant_id, status=status, search=search
    )
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/applications/{application_id}", response_model=SealApplicationOut)
def get_seal_application_detail(
        application_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """获取单个用印申请详情"""
    application = seal_crud.get_seal_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"用印申请ID {application_id} 不存在")

    # 【安全加固】：检查是否有权查看
    if current_user.role not in ["admin", "owner"] and not (
            current_user.permissions and current_user.permissions.get('can_approve_seal')):
        if application.applicant_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看该申请")

    return application


@router.get("/applications/{application_id}/preview_pdf")
async def preview_application_pdf(
        application_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """【管理员/用户】预览用于盖章的PDF底图 (Word转换后的文件)"""
    application = seal_crud.get_seal_application_by_id(db, application_id)
    if not application or not application.preview_pdf_path:
        raise HTTPException(status_code=404, detail="文件不存在或未完成转换")

    # 安全检查 (越权访问拦截)
    if current_user.role not in ["admin", "owner"] and not (
            current_user.permissions and current_user.permissions.get('can_approve_seal')):
        if application.applicant_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权预览该文件")

    file_path = os.path.join(SEAL_APPLICATION_ROOT, application.preview_pdf_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="预览文件已丢失")

    return FileResponse(file_path, media_type="application/pdf")


@router.get("/applications/{application_id}/download_original")
async def download_original_file(
        application_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """【用户】下载用户上传的原始文件"""
    application = seal_crud.get_seal_application_by_id(db, application_id)
    if not application or not application.original_file_path:
        raise HTTPException(status_code=404, detail="原始文件不存在")

    # 安全检查
    if current_user.role not in ["admin", "owner"] and not (
            current_user.permissions and current_user.permissions.get('can_approve_seal')):
        if application.applicant_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权下载该文件")

    file_path = os.path.join(SEAL_APPLICATION_ROOT, application.original_file_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="原始文件已丢失")

    return FileResponse(file_path, filename=application.original_file_name, media_type=application.file_type)


@router.delete("/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_seal_application(
        application_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)  # 替换了 user_id 和 role
):
    """【用户/管理员】删除用印申请（同时删除所有关联文件）"""
    application = seal_crud.get_seal_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"用印申请ID {application_id} 不存在")

    # 检查是否是管理员或申请人本人
    if current_user.role not in ["admin", "owner"] and application.applicant_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限删除此申请")

    try:
        success = seal_crud.delete_seal_application(db, application_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除操作失败")
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# =================================================================
# 用印审核 (Admin)
# =================================================================
@router.put("/applications/{application_id}/review", response_model=SealApplicationOut)
def review_seal_application(
        application_id: int,
        review_in: SealApplicationReview,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)  # 替换了 reviewer_id 和 role
):
    """【管理员/审批人】审核用印申请（通过/拒绝）"""
    check_seal_approval_permission(current_user)
    try:
        # 直接传入 current_user.id
        reviewed = seal_crud.review_seal_application(
            db, application_id, review_in, current_user.id
        )
        if not reviewed:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"用印申请ID {application_id} 不存在")
        return reviewed
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/applications/{application_id}/confirm", response_model=SealApplicationOut)
async def confirm_stamping_and_log(
        application_id: int,
        stamped_file: UploadFile = File(..., description="盖章后的PDF文件"),
        log_data_json: str = Form(..., description="盖章位置日志 (JSON 字符串)"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)  # 替换了 reviewer_id 和 role
):
    """【管理员/审批人】确认盖章完成，保存最终文件并记录坐标"""
    check_seal_approval_permission(current_user)
    try:
        # 1. 解析 JSON 字符串为 Pydantic 模型列表
        log_list_data = json.loads(log_data_json)
        # 验证和转换数据
        log_data = [SealLocationLog(
            x=log['x'], y=log['y'],
            page_number=log['page_number'],
            width=log['width'], height=log['height']
        ) for log in log_list_data]

        # 直接传入 current_user.id
        return await seal_crud.confirm_stamping(db, application_id, stamped_file, log_data, current_user.id)

    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="盖章日志数据格式错误，应为 JSON 字符串")
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/applications/{application_id}/download_stamped")
async def download_sealed_file(
        application_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """下载盖章后的文件"""
    application = seal_crud.get_seal_application_by_id(db, application_id)
    if not application or not application.stamped_file_path:
        raise HTTPException(status_code=404, detail="盖章后的文件不存在")

    # 安全检查 (越权访问拦截)
    if current_user.role not in ["admin", "owner"] and not (
            current_user.permissions and current_user.permissions.get('can_approve_seal')):
        if application.applicant_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权下载该文件")

    file_path = os.path.join(SEAL_APPLICATION_ROOT, application.stamped_file_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="盖章文件已丢失")

    # 文件名使用 original_file_name 加上前缀
    # 移除原文件可能的后缀，确保下载为 .pdf
    filename_base = application.original_file_name
    for suffix in ['.docx', '.doc', '.pdf']:
        if filename_base.lower().endswith(suffix):
            filename_base = filename_base[:-len(suffix)]
            break

    filename = f"已盖章_{filename_base}.pdf"

    return FileResponse(
        file_path,
        filename=filename,
        media_type='application/pdf'
    )