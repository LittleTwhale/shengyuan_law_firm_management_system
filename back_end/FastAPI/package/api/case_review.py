# api/case_review.py
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from ..database.database import get_db
from ..schemas.case import CasePageOut, CaseSimpleOut, CaseOut
from ..crud.case_review import list_pending_cases, count_pending_cases, update_review_status

router = APIRouter(
    prefix="/case_review",
    tags=["case_review"]
)


@router.get("/pending", response_model=CasePageOut)
def get_pending_cases(
        role: Optional[str] = None,
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        db: Session = Depends(get_db)
):
    """
    获取待审核案件列表（仅管理员可访问）
    """
    # 验证管理员权限
    if not role or role not in ["admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无审核案件权限"
        )

    cases = list_pending_cases(db, skip=skip, limit=limit)
    total = count_pending_cases(db)
    cases_simple = [CaseSimpleOut.model_validate(case) for case in cases]
    return {"items": cases_simple, "total": total}


@router.put("/{case_id}/review", response_model=CaseOut)
def review_case(
        case_id: int,
        reviewer_id: int,
        review_status: str,  # 接收"已审核"或"已拒绝"
        role: Optional[str] = None,
        db: Session = Depends(get_db)
):
    """
    审核案件（通过/拒绝，仅管理员可操作）
    """
    # 验证管理员权限
    if not role or role not in ["admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无审核案件权限"
        )

    try:
        updated_case = update_review_status(
            db=db,
            case_id=case_id,
            review_status=review_status,
            reviewer_id=reviewer_id
        )
        if not updated_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="案件不存在或已被删除"
            )
        return updated_case
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
