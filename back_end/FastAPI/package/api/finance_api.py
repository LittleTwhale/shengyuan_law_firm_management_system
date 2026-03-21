# api/finance_api.py
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..models.finance_model import CaseFinance
from ..models.user import User
from ..models.case import Case
from ..schemas.finance_schema import (
    FinanceStatsQuery,
    FinanceStatsResponse,
    CaseFinanceResponse,
    CaseFinanceUpdate,
    FinancialRecordCreate,
    FinancialRecordResponse,
    InvoiceRecordCreate,
    InvoiceRecordResponse, CaseFinancePagination, LawyerWithdrawalResponse, LawyerWithdrawalCreate
)
from ..crud.finance_crud import finance as crud_finance
# 依赖
from .deps import get_current_active_user

router = APIRouter(prefix="/finance", tags=["finance"])


# =================================================================
#  权限校验辅助函数 (内部使用)
# =================================================================

def check_finance_manage_permission(user: User):
    """
    检查用户是否有【财务管理】权限
    判定逻辑：Role 为 owner 或 permissions JSON 中包含 finance_manage=True
    """
    is_owner = user.role == 'owner'
    # 注意：Permissions 字段可能是 None，需要做安全访问
    has_perm = user.permissions and user.permissions.get("finance_manage") is True

    if not (is_owner or has_perm):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足：您没有财务管理权限"
        )


def check_case_view_permission(db: Session, case_id: int, user: User):
    """
    检查用户是否有查看【特定案件】财务的权限
    判定逻辑：
    1. 管理员/财务/Owner -> 直接通过
    2. 普通用户 -> 必须是该案件的主办/助理/执行/执行助理
    """
    # 1. 超级权限检查
    if user.role in ['admin', 'owner']:
        return
    if user.permissions and user.permissions.get("finance_manage"):
        return

    # 2. 案件关系检查
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    is_related = (
            case.main_lawyer_id == user.id or
            case.assistant_lawyer_id == user.id or
            case.assistant_lawyer_2_id == user.id or
            case.execution_lawyer_id == user.id or
            case.execution_assistant_id == user.id
    )

    if not is_related:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足：您无权查看该案件的财务信息"
        )


# =================================================================
#  读取接口 (列表、统计、详情)
# =================================================================

@router.post("/list", response_model=CaseFinancePagination)
def get_finance_list(
        query: FinanceStatsQuery,
        skip: int = Query(0, ge=0),
        limit: int = Query(20, ge=1),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    获取财务列表 (带分页信息)
    """
    items, total = crud_finance.get_multi(
        db=db,
        current_user=current_user,
        query_params=query,
        skip=skip,
        limit=limit
    )

    # 返回符合 CaseFinancePagination 结构的数据
    return {"items": items, "total": total}


@router.post("/stats", response_model=FinanceStatsResponse)
def get_finance_stats(
        query: FinanceStatsQuery,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    获取顶部的统计汇总数据 (总收入、总开票等)
    - 统计范围会自动遵循权限规则
    """
    return crud_finance.get_statistics(db, current_user, query)


@router.get("/case/{case_id}", response_model=CaseFinanceResponse)
def get_case_finance_detail(
        case_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    获取单个案件的财务详情
    - 如果该案件尚无财务记录，CRUD 会自动初始化一条空记录
    """
    # 先检查是否有权查看该案件
    check_case_view_permission(db, case_id, current_user)

    finance = crud_finance.get_by_case_id(db, case_id)
    return finance


# =================================================================
#  写入接口 (需财务权限)
# =================================================================

@router.put("/{finance_id}", response_model=CaseFinanceResponse)
def update_finance_summary(
        finance_id: int,
        finance_in: CaseFinanceUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    修改财务总表信息 (合同额、备注等)
    """
    check_finance_manage_permission(current_user)

    finance = crud_finance.update_summary(db, finance_id, finance_in)
    if not finance:
        raise HTTPException(status_code=404, detail="财务记录不存在")
    return finance


@router.post("/record", response_model=FinancialRecordResponse)
def create_financial_record(
        record_in: FinancialRecordCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    登记一笔新的【收支流水】(收款/退款)
    - 系统会自动重算总表的实收/未付金额
    """
    check_finance_manage_permission(current_user)

    # 额外检查关联的 finance_id 是否存在
    finance = db.query(CaseFinance).filter(CaseFinance.id == record_in.finance_id).first()
    if not finance:
        raise HTTPException(status_code=404, detail="关联的财务总表记录不存在")
    # --- 修复代码结束 ---

    return crud_finance.create_record(db, record_in, current_user.id)


@router.delete("/record/{record_id}")
def delete_financial_record(
        record_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    删除某条流水 (仅用于录入错误时的纠正)
    """
    check_finance_manage_permission(current_user)

    success = crud_finance.delete_record(db, record_id)
    if not success:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"message": "删除成功"}


@router.post("/invoice", response_model=InvoiceRecordResponse)
def create_invoice_record(
        invoice_in: InvoiceRecordCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    登记一笔新的【发票记录】
    """
    check_finance_manage_permission(current_user)
    return crud_finance.create_invoice(db, invoice_in, current_user.id)

@router.delete("/invoice/{invoice_id}")
def delete_invoice_record(
        invoice_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    删除发票记录
    """
    # 鉴权
    check_finance_manage_permission(current_user)

    success = crud_finance.delete_invoice(db, invoice_id)
    if not success:
        raise HTTPException(status_code=404, detail="发票记录不存在")
    return {"message": "删除成功"}


# =================================================================
#   律师领款管理接口
# =================================================================

@router.post("/withdrawal", response_model=LawyerWithdrawalResponse)
def create_lawyer_withdrawal(
        withdrawal_in: LawyerWithdrawalCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    登记一笔新的【律师领款】记录
    - 系统会自动重算总表的累计领款金额
    - 必须有财务管理权限
    """
    check_finance_manage_permission(current_user)

    # 1. 检查关联的财务总表是否存在
    finance = db.query(CaseFinance).filter(CaseFinance.id == withdrawal_in.finance_id).first()
    if not finance:
        raise HTTPException(status_code=404, detail="关联的财务总表记录不存在")

    # 2. 检查领款律师是否存在 (可选，数据库外键也会拦截，但这里报错更友好)
    lawyer = db.query(User).filter(User.id == withdrawal_in.lawyer_id).first()
    if not lawyer:
        raise HTTPException(status_code=404, detail="指定的律师不存在")

    # 3. 执行创建
    return crud_finance.create_withdrawal(db, withdrawal_in, current_user.id)


@router.delete("/withdrawal/{withdrawal_id}")
def delete_lawyer_withdrawal(
        withdrawal_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    删除某条领款记录 (仅用于录入错误时的纠正)
    - 删除后会自动扣减总领款金额
    """
    check_finance_manage_permission(current_user)

    success = crud_finance.delete_withdrawal(db, withdrawal_id)
    if not success:
        raise HTTPException(status_code=404, detail="领款记录不存在")

    return {"message": "删除成功"}

# =================================================================
#  导出接口
# =================================================================

@router.post("/export", response_class=StreamingResponse)
def export_finance_excel(
        query: FinanceStatsQuery,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    导出筛选后的财务 Excel 表
    """
    # 1. 调用 CRUD 生成 Excel 文件的内存流
    excel_io = crud_finance.export_excel(db, current_user, query)

    # 2. URL 编码文件名，防止中文乱码
    filename = quote("财务统计报表.xlsx")

    # 3. 返回流式响应
    return StreamingResponse(
        excel_io,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=utf-8''{filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )