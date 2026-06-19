# api/electronic_seal.py
import json
import os
import uuid
import shutil
from datetime import datetime
from typing import List, Optional
from urllib.parse import unquote

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..core.config import ELECTRONIC_SEAL_ROOT, SEAL_APPLICATION_ROOT, settings
from ..crud import electronic_seal as seal_crud
from ..database.database import get_db
from ..models.user import User
from ..models.electronic_seal import ElectronicSeal, SealApplication
from ..schemas.electronic_seal import (
    ElectronicSealCreate, ElectronicSealOut, ElectronicSealUpdate,
    SealApplicationCreate, SealApplicationOut, SealApplicationSimpleOut,
    SealApplicationReview, SealLocationLog, PaginatedResponse,
)
from ..utils.storage_manager import get_upload_credential, get_file_preview_url, get_file_download_url, cleanup_local_file

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
@router.post("/seals", status_code=status.HTTP_201_CREATED)
async def create_electronic_seal(
        name: str = Form(..., description="印章名称"),
        file: Optional[UploadFile] = File(None, description="印章图片（LOCAL 模式必填）"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """【管理员】创建电子印章（COS 模式返回 STS 凭证，LOCAL 模式接收文件）"""
    check_admin_permission(current_user)

    if settings.STORAGE_TYPE == "COS":
        if not file:
            raise HTTPException(400, "COS 模式需要获取文件名")
        now = datetime.now()
        path_prefix = f"seals/{now.year}/{now.month:02d}"
        cred = get_upload_credential(file.filename or "seal.png", path_prefix)
        db_seal = ElectronicSeal(
            name=name,
            image_path=cred["key"],
            image_cos_key=cred["key"],
            file_size=0,
            is_active=True,
            uploaded_by=current_user.id,
        )
        db.add(db_seal)
        db.commit()
        db.refresh(db_seal)
        return {
            "type": "COS",
            "credentials": cred["credentials"],
            "bucket": cred["bucket"],
            "region": cred["region"],
            "key": cred["key"],
            "seal_id": db_seal.id,
        }

    # LOCAL 模式
    if not file:
        raise HTTPException(400, "LOCAL 模式需要上传文件")
    seal_in = ElectronicSealCreate(name=name)
    try:
        return await seal_crud.create_electronic_seal(db, seal_in, file, current_user.id)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


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
    """获取印章图片（LOCAL 返回文件流，COS 重定向到签名 URL）"""
    from types import SimpleNamespace

    seal = seal_crud.get_electronic_seal_by_id(db, seal_id)
    if not seal:
        raise HTTPException(status_code=404, detail="印章不存在")

    # ElectronicSeal 使用 image_path 而非 file_path
    record = SimpleNamespace(
        file_path=seal.image_path,
        file_name=seal.name,
        file_type="image/png",
        cos_key=getattr(seal, 'image_cos_key', None),
    )
    result = get_file_preview_url(record, root_dir=ELECTRONIC_SEAL_ROOT)
    if result["type"] == "ERROR":
        raise HTTPException(status_code=404, detail=result["message"])
    elif result["type"] == "COS":
        return RedirectResponse(url=result["url"])

    return FileResponse(
        result["file_path"],
        headers={"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET"}
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


@router.patch("/seals/{seal_id}/size")
def update_seal_size(
    seal_id: int,
    file_size: int = Query(..., description="文件大小（KB）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """STS 上传完成后回写印章文件大小（KB）"""
    seal = seal_crud.get_electronic_seal_by_id(db, seal_id)
    if not seal:
        raise HTTPException(status_code=404, detail="印章不存在")
    seal.file_size = file_size
    db.commit()
    return {"ok": True}


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
def _seal_app_word_convert_and_cleanup(save_path: str, cos_key: str, application_id: int):
    """
    后台任务：Word→PDF 转换 → 上传 PDF 到 COS 预览缓存 → 更新 DB → 清理本地文件
    """
    from ..crud.attachment import convert_word_to_pdf
    from ..database.database import SessionLocal
    try:
        pdf_path = convert_word_to_pdf(save_path)
        if not pdf_path:
            print(f"[SealAppConvert] Word 转 PDF 失败: {save_path}")
            return

        if settings.STORAGE_TYPE == "COS":
            from ..utils.storage_manager import _get_cos_client
            stem, _ = os.path.splitext(cos_key)
            pdf_cos_key = f"preview_cache/{stem}.pdf"
            _get_cos_client().upload_file(
                Bucket=settings.COS_BUCKET,
                Key=pdf_cos_key,
                LocalFilePath=pdf_path,
            )
            # 更新 DB 中的预览 PDF key
            db = SessionLocal()
            try:
                app = db.query(SealApplication).filter(SealApplication.id == application_id).first()
                if app:
                    app.preview_pdf_cos_key = pdf_cos_key
                    db.commit()
            except Exception as e:
                db.rollback()
                print(f"[SealAppConvert] DB 更新失败: {e}")
            finally:
                db.close()

        # 清理本地文件及空文件夹
        if os.path.exists(save_path):
            cleanup_local_file(save_path, SEAL_APPLICATION_ROOT)
        if os.path.exists(pdf_path):
            cleanup_local_file(pdf_path, SEAL_APPLICATION_ROOT)
    except Exception as e:
        print(f"[SealAppConvert] 处理失败: {e}")


@router.post("/applications", status_code=status.HTTP_201_CREATED)
async def create_seal_application(
        background_tasks: BackgroundTasks,
        seal_id: int = Form(..., description="申请使用的印章ID"),
        apply_reason: Optional[str] = Form(None, description="用印原因"),
        file: Optional[UploadFile] = File(None, description="待盖章文件（LOCAL 模式必填）"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    【用户】创建用印申请
    - COS 模式 + Word 文件：本地保存 → 上传 COS → 后台转 PDF 底图 → 清理
    - COS 模式 + 非 Word 文件：STS 前端直传 COS
    - LOCAL 模式：接收文件并后台转 PDF
    """
    application_in = SealApplicationCreate(seal_id=seal_id, apply_reason=apply_reason)

    if not file:
        raise HTTPException(400, "需要上传文件")

    file_name = file.filename or "document.pdf"

    if settings.STORAGE_TYPE == "COS":
        now = datetime.now()
        path_prefix = f"seal_applications/{now.year}/{now.month:02d}"

        # 判断是否为 Word 文件（需要转 PDF 底图）
        is_word = file.content_type in [
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ] or file_name.lower().endswith(('.doc', '.docx'))

        if is_word:
            # === Word 文件：本地保存 → 上传 COS → 后台转换 PDF → 清理 ===
            unique_name = f"{uuid.uuid4().hex}{os.path.splitext(file_name)[1]}"
            relative_path = os.path.join("seal_applications", str(now.year), f"{now.month:02d}", unique_name)
            save_path = os.path.join(SEAL_APPLICATION_ROOT, relative_path)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            cos_key = relative_path.replace("\\", "/")

            # 上传原始文件到 COS
            from ..utils.storage_manager import _get_cos_client
            _get_cos_client().upload_file(
                Bucket=settings.COS_BUCKET,
                Key=cos_key,
                LocalFilePath=save_path,
            )

            # 创建数据库记录
            db_app = SealApplication(
                applicant_id=current_user.id,
                seal_id=seal_id,
                original_file_name=file_name,
                original_file_path=relative_path,
                original_cos_key=cos_key,
                file_type=file.content_type or "application/octet-stream",
                apply_reason=apply_reason,
                status="待审核",
            )
            db.add(db_app)
            db.commit()
            db.refresh(db_app)

            # 后台转换 PDF 底图 → 上传 COS → 更新 DB → 清理
            background_tasks.add_task(
                _seal_app_word_convert_and_cleanup,
                save_path=save_path,
                cos_key=cos_key,
                application_id=db_app.id,
            )

            return db_app

        else:
            # === 非 Word 文件：STS 前端直传 COS ===
            cred = get_upload_credential(file_name, path_prefix)
            db_app = SealApplication(
                applicant_id=current_user.id,
                seal_id=seal_id,
                original_file_name=file_name,
                original_file_path=cred["key"],
                original_cos_key=cred["key"],
                file_type=file.content_type or "application/octet-stream",
                apply_reason=apply_reason,
                status="待审核",
            )
            db.add(db_app)
            db.commit()
            db.refresh(db_app)

            return {
                "type": "COS",
                "credentials": cred["credentials"],
                "bucket": cred["bucket"],
                "region": cred["region"],
                "key": cred["key"],
                "application_id": db_app.id,
            }

    # LOCAL 模式
    try:
        application = await seal_crud.create_seal_application(db, application_in, file, current_user.id)

        if application.file_type in [
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]:
            background_tasks.add_task(seal_crud.convert_application_word_to_pdf, application.id)

        return application
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=400, detail=str(e))


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
    """【管理员/用户】预览用于盖章的PDF底图 (支持LOCAL和COS)"""
    from types import SimpleNamespace

    application = seal_crud.get_seal_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="用印申请不存在")
    if not application.preview_pdf_path and not getattr(application, 'preview_pdf_cos_key', None):
        raise HTTPException(status_code=404, detail="文件不存在或未完成转换")

    # 安全检查
    if current_user.role not in ["admin", "owner"] and not (
            current_user.permissions and current_user.permissions.get('can_approve_seal')):
        if application.applicant_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权预览该文件")

    # SealApplication 使用 preview_pdf_path 而非 file_path，映射为统一命名
    record = SimpleNamespace(
        file_path=application.preview_pdf_path,
        file_name=application.original_file_name,
        file_type="application/pdf",
        cos_key=getattr(application, 'preview_pdf_cos_key', None),
    )
    result = get_file_preview_url(record, root_dir=SEAL_APPLICATION_ROOT)
    if result["type"] == "ERROR":
        raise HTTPException(status_code=404, detail=result["message"])
    elif result["type"] == "COS":
        return RedirectResponse(url=result["url"])

    return FileResponse(result["file_path"], media_type="application/pdf")


@router.get("/applications/{application_id}/download_original")
async def download_original_file(
        application_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """【用户】下载原始文件（LOCAL/COS 双模式）"""
    from types import SimpleNamespace

    application = seal_crud.get_seal_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="用印申请不存在")

    # 安全检查
    if current_user.role not in ["admin", "owner"] and not (
            current_user.permissions and current_user.permissions.get('can_approve_seal')):
        if application.applicant_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权下载该文件")

    record = SimpleNamespace(
        file_path=application.original_file_path,
        file_name=application.original_file_name,
        file_type=application.file_type,
        cos_key=getattr(application, 'original_cos_key', None),
    )
    result = get_file_download_url(record, root_dir=SEAL_APPLICATION_ROOT)
    if result["type"] == "ERROR":
        raise HTTPException(status_code=404, detail=result["message"])
    elif result["type"] == "COS":
        return RedirectResponse(url=result["url"])

    return FileResponse(
        result["file_path"],
        filename=application.original_file_name,
        media_type=application.file_type
    )


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

    # 禁止申请人删除已通过的记录（管理员/owner 不受此限制）
    if current_user.role not in ["admin", "owner"] and application.status == "已通过":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="已盖章的申请记录不能被申请人删除")

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


@router.post("/applications/{application_id}/confirm")
async def confirm_stamping_and_log(
        application_id: int,
        stamped_file: Optional[UploadFile] = File(None, description="盖章后的PDF文件"),
        log_data_json: str = Form(..., description="盖章位置日志 (JSON 字符串)"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """【管理员/审批人】确认盖章完成（LOCAL 接收文件，COS 记录 cos_key）"""
    check_seal_approval_permission(current_user)
    try:
        log_list_data = json.loads(log_data_json)
        log_data = [SealLocationLog(
            x=log['x'], y=log['y'],
            page_number=log['page_number'],
            width=log['width'], height=log['height']
        ) for log in log_list_data]

        # COS 模式
        if settings.STORAGE_TYPE == "COS":
            if not stamped_file:
                raise HTTPException(400, "COS 模式需要获取文件名")
            now = datetime.now()
            path_prefix = f"seal_applications/{now.year}/{now.month:02d}"
            cred = get_upload_credential(stamped_file.filename or "stamped.pdf", path_prefix)
            application = seal_crud.get_seal_application_by_id(db, application_id)
            if not application:
                raise HTTPException(404, "申请不存在")
            if application.status != "待审核":
                raise HTTPException(400, f"当前状态 '{application.status}' 无法盖章确认")

            application.stamped_file_cos_key = cred["key"]
            application.status = "已通过"
            application.reviewer_id = current_user.id
            application.review_time = datetime.now()
            # 记录审计日志
            from ..models.electronic_seal import SealAuditLog
            db.query(SealAuditLog).filter(SealAuditLog.application_id == application_id).delete()
            for log in log_data:
                db.add(SealAuditLog(
                    application_id=application_id,
                    page_number=log.page_number, x_coordinate=log.x, y_coordinate=log.y,
                    seal_width=log.width, seal_height=log.height
                ))
            db.commit()
            db.refresh(application)

            return {
                "type": "COS",
                "credentials": cred["credentials"],
                "bucket": cred["bucket"],
                "region": cred["region"],
                "key": cred["key"],
                "application_id": application_id,
            }

        # LOCAL 模式
        if not stamped_file:
            raise HTTPException(400, "LOCAL 模式需要上传盖章文件")
        return await seal_crud.confirm_stamping(db, application_id, stamped_file, log_data, current_user.id)

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="盖章日志数据格式错误")
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/applications/{application_id}/download_stamped")
async def download_sealed_file(
        application_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """下载盖章后的文件（LOCAL/COS 双模式）"""
    from types import SimpleNamespace

    application = seal_crud.get_seal_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="用印申请不存在")

    if not application.stamped_file_path and not getattr(application, 'stamped_file_cos_key', None):
        raise HTTPException(status_code=404, detail="盖章后的文件不存在")

    # 安全检查
    if current_user.role not in ["admin", "owner"] and not (
            current_user.permissions and current_user.permissions.get('can_approve_seal')):
        if application.applicant_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权下载该文件")

    record = SimpleNamespace(
        file_path=application.stamped_file_path,
        file_name=application.original_file_name,
        file_type="application/pdf",
        cos_key=getattr(application, 'stamped_file_cos_key', None),
    )
    result = get_file_download_url(record, root_dir=SEAL_APPLICATION_ROOT)
    if result["type"] == "ERROR":
        raise HTTPException(status_code=404, detail=result["message"])
    elif result["type"] == "COS":
        return RedirectResponse(url=result["url"])

    filename_base = application.original_file_name
    for suffix in ['.docx', '.doc', '.pdf']:
        if filename_base.lower().endswith(suffix):
            filename_base = filename_base[:-len(suffix)]
            break
    filename = f"已盖章_{filename_base}.pdf"

    return FileResponse(result["file_path"], filename=filename, media_type='application/pdf')