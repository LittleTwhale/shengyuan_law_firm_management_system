# api/electronic_seal.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database.database import get_db
from ..schemas.electronic_seal import (
    ElectronicSealCreate, ElectronicSealOut, ElectronicSealUpdate,
    SealApplicationCreate, SealApplicationOut, SealApplicationSimpleOut,
    SealApplicationReview, SealPositionBase
)
from ..crud import electronic_seal as seal_crud
from ..crud import seal_application as application_crud

router = APIRouter(
    prefix="/electronic_seal",
    tags=["电子用印"]
)


# ------------------------------
# 电子印章管理接口
# ------------------------------
@router.post("/", response_model=ElectronicSealOut, status_code=status.HTTP_201_CREATED)
async def create_electronic_seal(
        name: str = Form(..., description="印章名称"),
        file: UploadFile = File(..., description="印章图片文件（支持png/jpg格式）"),
        db: Session = Depends(get_db)
):
    """创建电子印章（需上传印章图片）"""
    try:
        seal_in = ElectronicSealCreate(name=name)
        return await seal_crud.create_electronic_seal(db, seal_in, file)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/", response_model=List[ElectronicSealOut])
def list_electronic_seals(
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        db: Session = Depends(get_db)
):
    """获取电子印章列表（支持分页和状态筛选）"""
    return seal_crud.get_electronic_seals(db, skip=skip, limit=limit, is_active=is_active)


@router.get("/{seal_id}", response_model=ElectronicSealOut)
def get_electronic_seal(seal_id: int, db: Session = Depends(get_db)):
    """获取单个电子印章详情"""
    seal = seal_crud.get_electronic_seal_by_id(db, seal_id)
    if not seal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"电子印章ID {seal_id} 不存在"
        )
    return seal


@router.put("/{seal_id}", response_model=ElectronicSealOut)
def update_electronic_seal(
        seal_id: int,
        seal_in: ElectronicSealUpdate,
        db: Session = Depends(get_db)
):
    """更新电子印章信息（名称/启用状态）"""
    try:
        updated_seal = seal_crud.update_electronic_seal(db, seal_id, seal_in)
        if not updated_seal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"电子印章ID {seal_id} 不存在"
            )
        return updated_seal
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{seal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_electronic_seal(seal_id: int, db: Session = Depends(get_db)):
    """删除电子印章（同时删除关联文件）"""
    try:
        success = seal_crud.delete_electronic_seal(db, seal_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"电子印章ID {seal_id} 不存在"
            )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ------------------------------
# 用印申请接口
# ------------------------------
@router.post("/applications", response_model=SealApplicationOut, status_code=status.HTTP_201_CREATED)
async def create_seal_application(
        file_name: str = Form(..., description="申请盖章的文件名"),
        seal_id: int = Form(..., description="申请使用的印章ID"),
        application_reason: Optional[str] = Form(None, description="用印原因"),
        file: UploadFile = File(..., description="待盖章文件（支持pdf/doc/docx格式）"),
        applicant_id: int = Form(..., description="申请人ID"),
        db: Session = Depends(get_db)
):
    """创建用印申请（需上传待盖章文件）"""
    try:
        application_in = SealApplicationCreate(
            file_name=file_name,
            seal_id=seal_id,
            application_reason=application_reason
        )
        return await application_crud.create_seal_application(
            db, application_in, file, applicant_id
        )
    except (ValueError, RuntimeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if isinstance(e,
                                                                  ValueError) else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/applications", response_model=List[SealApplicationSimpleOut])
def list_seal_applications(
        skip: int = 0,
        limit: int = 100,
        applicant_id: Optional[int] = None,
        application_status: Optional[str] = None,
        db: Session = Depends(get_db)
):
    """获取用印申请列表（支持分页、申请人筛选和状态筛选）"""
    return application_crud.get_seal_applications(
        db, skip=skip, limit=limit, applicant_id=applicant_id, status=application_status
    )


@router.get("/applications/{application_id}", response_model=SealApplicationOut)
def get_seal_application(application_id: int, db: Session = Depends(get_db)):
    """获取单个用印申请详情"""
    application = application_crud.get_seal_application_by_id(db, application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用印申请ID {application_id} 不存在"
        )
    return application


@router.put("/applications/{application_id}/review", response_model=SealApplicationOut)
def review_seal_application(
        application_id: int,
        review_in: SealApplicationReview,
        db: Session = Depends(get_db)
):
    """审核用印申请（通过/拒绝）"""
    try:
        reviewed = application_crud.review_seal_application(
            db, application_id, review_in, review_in.reviewer_id
        )
        if not reviewed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"用印申请ID {application_id} 不存在"
            )
        return reviewed
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/applications/{application_id}/positions", response_model=List[SealPositionBase])
def set_seal_positions(
        application_id: int,
        positions: List[SealPositionBase],
        db: Session = Depends(get_db)
):
    """设置用印位置（仅审核通过的申请可设置）"""
    # 验证申请是否存在且已通过
    application = application_crud.get_seal_application_by_id(db, application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用印申请ID {application_id} 不存在"
        )
    if application.status != "已通过":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"只有审核通过的申请才能设置用印位置（当前状态：{application.status}）"
        )

    try:
        return application_crud.create_seal_positions(db, application_id, positions)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/applications/{application_id}/apply", response_model=SealApplicationOut)
async def apply_seal(
        application_id: int,
        db: Session = Depends(get_db)
):
    """执行盖章操作（需先设置用印位置）"""
    # 获取已设置的印章位置
    positions = application_crud.get_seal_positions_by_application(db, application_id)
    if not positions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先设置印章位置"
        )

    try:
        # 转换为Pydantic模型列表
        position_bases = [SealPositionBase(**pos.__dict__) for pos in positions]
        sealed_path = await application_crud.apply_seal_to_pdf(db, application_id, position_bases)

        # 更新申请记录中的盖章文件路径
        application = application_crud.get_seal_application_by_id(db, application_id)
        application.sealed_file_path = sealed_path
        db.commit()
        db.refresh(application)
        return application
    except (ValueError, RuntimeError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )