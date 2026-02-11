# api/case_review.py
import os
import tempfile
from typing import Optional

from docxtpl import DocxTemplate
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi import BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from ..core.config import TEMPLATE_DIR
from ..crud.case_review import list_pending_cases, count_pending_cases, update_review_status, \
    check_interest_conflict_for_case, get_case_approval_context
from ..database.database import get_db
from ..models.case import Case
from ..models.user import User
from ..schemas.case import CasePageOut, CaseSimpleOut, CaseOut

router = APIRouter(
    prefix="/case_review",
    tags=["case_review"]
)


# --- 辅助函数：权限检查 ---
def check_review_permission(db: Session, user_id: int):
    """
    检查用户是否有权审核案件
    逻辑：Role为Owner，或者 permissions['can_review_case'] 为 True
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=403, detail="用户不存在")

    # 1. Owner 拥有最高权限
    if user.role == 'owner':
        return True

    # 2. 检查细粒度权限
    # user.permissions 可能为 None (旧数据) 或 字典
    perms = user.permissions or {}
    if perms.get('can_review_case', False) is True:
        return True

    raise HTTPException(status_code=403, detail="您没有审核案件的权限")

@router.get("/pending", response_model=CasePageOut)
def get_pending_cases(
        user_id: int = Query(..., description="当前操作的用户ID"),
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
        review_status: str,
        role: Optional[str] = None,
        force: bool = Query(False, description="是否强制通过（忽略利益冲突）"),  # 新增参数
        db: Session = Depends(get_db)
):
    """
    审核案件（通过/拒绝，仅管理员可操作）
    """
    check_review_permission(db, reviewer_id)

    # 1. 审核通过逻辑
    if review_status == "已审核":
        # 如果不是强制通过，则进行冲突检测
        if not force:
            conflict_result = check_interest_conflict_for_case(db, case_id)
            if conflict_result["has_conflict"]:
                # 409 Conflict: 返回详细信息给前端展示
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "INTEREST_CONFLICT",
                        "message": "检测到潜在利益冲突，是否强制通过？",
                        "conflicts": conflict_result["details"]
                    }
                )

    # 2. 执行更新
    try:
        updated_case = update_review_status(
            db=db,
            case_id=case_id,
            review_status=review_status,
            reviewer_id=reviewer_id
        )
        if not updated_case:
            raise HTTPException(status_code=404, detail="案件不存在")

        return updated_case

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{case_id}/approval_form", response_class=FileResponse)
def generate_approval_form(
        case_id: int,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
):
    """
    生成并下载案件审批表 (Word格式)
    """
    # 1. 查询案件信息 (关键修改：使用 options(joinedload(...)) 预加载 parties)
    # 如果不预加载，在 crud 函数中遍历 case.parties 时会触发 N+1 查询或报错
    case = db.query(Case).options(
        joinedload(Case.parties),
        joinedload(Case.main_lawyer),
        joinedload(Case.assistant_lawyer),
        joinedload(Case.reviewer)
    ).filter(Case.case_id == case_id).first()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="案件不存在"
        )

    # 2. 校验状态
    if case.review_status != "已审核":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"当前案件状态为'{case.review_status}'，仅'已审核'案件可生成审批表"
        )

    # 3. 准备模板路径
    template_path = os.path.join(TEMPLATE_DIR, "case_approval_template.docx")
    if not os.path.exists(template_path):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器缺少审批表模板文件"
        )

    try:
        # 4. 获取填充数据 (调用 CRUD 中的新函数)
        # 这个函数已经处理了 CaseParty 的分类聚合逻辑
        context = get_case_approval_context(case)

        # 5. 渲染模板 (使用 docxtpl)
        # docxtpl 会自动匹配 Word 中的 {{client_name}} 和 context 字典中的 key
        tpl = DocxTemplate(template_path)
        tpl.render(context)

        # 6. 保存到临时文件
        # 使用 tempfile 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tpl.save(tmp.name)
            tmp_path = tmp.name

        # 7. 设置下载文件名
        filename = f"案件审批表_{case.case_number}.docx"

        # 解决中文文件名在不同浏览器乱码的兼容性处理（可选，FastAPI通常处理得很好）
        from urllib.parse import quote
        encoded_filename = quote(filename)

        # 添加后台任务：响应发送后删除临时文件
        background_tasks.add_task(os.remove, tmp_path)

        return FileResponse(
            path=tmp_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )

    except Exception as e:
        print(f"Generate document error: {e}")
        # 如果临时文件已创建但在报错前未删除，尝试清理
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成审批表失败: {str(e)}"
        )