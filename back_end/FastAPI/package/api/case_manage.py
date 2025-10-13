# api/case_manage.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database.database import get_db
from ..schemas.user import UserOut
from ..schemas.case import CaseOut, CasePageOut, CaseSimpleOut, CaseCreate, CaseUpdate

from ..crud.user import get_all_lawyers
from ..crud.case import list_cases_by_user_role, get_case_by_id, count_cases_by_user_role, create_case, update_case, \
    delete_case, export_cases_by_user_role, list_bank_cases_by_user_role, count_bank_cases_by_user_role, \
    export_bank_cases_by_user_role

from io import BytesIO
from urllib.parse import quote
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from datetime import datetime

router = APIRouter(
    prefix="/cases",
    tags=["case_manage"]
)


# 1️⃣ 获取正式生效案件列表（分页可选）
@router.get("/", response_model=CasePageOut)
def get_cases(
    user_id: int,
    role: str,
    skip: int = 0,
    limit: int = 100,
    keyword: Optional[str] = None,  # 新增搜索关键词参数
    category: Optional[str] = None,  # 新增案件类别参数
    db: Session = Depends(get_db)
):
    """
    获取案件列表
    """
    cases = list_cases_by_user_role(
        db=db,
        user_id=user_id,
        role=role,
        skip=skip,
        limit=limit,
        keyword=keyword,  # 传递给CRUD函数
        category=category  # 传递给CRUD函数
    )
    total = count_cases_by_user_role(
        db=db,
        user_id=user_id,
        role=role,
        keyword=keyword,  # 传递给统计函数
        category=category  # 传递给统计函数
    )
    cases_simple = [CaseSimpleOut.model_validate(c) for c in cases]
    return {"items": cases_simple, "total": total}

# 2️⃣ 获取银行案件列表
@router.get("/bank_cases", response_model=CasePageOut)
def get_bank_cases(
        user_id: int,
        role: str,
        skip: int = 0,
        limit: int = 100,
        keyword: Optional[str] = None,  # 新增搜索关键词参数
        db: Session = Depends(get_db)
):
    """
    获取银行案件列表
    """
    cases = list_bank_cases_by_user_role(
        db=db,
        user_id=user_id,
        role=role,
        skip=skip,
        limit=limit,
        keyword=keyword,
    )
    total = count_bank_cases_by_user_role(
        db=db,
        user_id=user_id,
        role=role,
        keyword=keyword,  # 传递给统计函数
    )
    cases_simple = [CaseSimpleOut.model_validate(c) for c in cases]
    return {"items": cases_simple, "total": total}


# 5️⃣ 导出案件表格
@router.get("/export/all", response_class=StreamingResponse)
def export_cases(
        user_id: int,
        role: str,
        db: Session = Depends(get_db)
):
    """导出案件数据为Excel"""
    # 1. 获取数据
    cases = export_cases_by_user_role(db, user_id, role)
    if not cases:
        raise HTTPException(status_code=404, detail="无符合条件的案件数据")

    # 2. 创建Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "案件列表"

    # 3. 设置表头
    headers = [
        "案件ID", "案件号", "委托日期", "委托人", "委托人身份证号/单位税号", "委托人电话",
        "案件类别", "案件来源", "收费方式", "风险比例", "案件收入",
        "付款到期日", "案由", "介入阶段", "原告/申请人", "上诉人或第三人信息补充",
        "补上诉人或补告信息补充", "被告", "代理权限", "审理法院", "开庭时间", "立案日",
        "结案时间", "案件地点", "案件详情",
        "主办律师", "助理律师", "执行主办律师", "执行助理律师",
        "案件审核状态", "是否重大", "是否纸质卷宗", "是否解除", "是否笔录", "是否保全",
        "是否删除", "保全开始日", "保全终止日",
        "案号", "结案状态", "结案方式",
        "诉讼费缴费时间", "诉讼费缴费金额", "诉讼费退费时间", "诉讼费退费金额",
        "申请执行日", "调解到期日", "执行到期日",
        "创建时间", "更新时间"
    ]
    ws.append(headers)

    # 4. 设置表头样式
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    # 5. 填充数据
    for case in cases:
        ws.append([
            case.case_id,
            case.case_number,
            case.commission_date.strftime("%Y-%m-%d") if case.commission_date else "",
            case.client_name,
            case.client_id_number or "",
            case.client_phone or "",
            case.case_category,
            case.case_source or "",
            case.fee_method or "",
            case.risk_ratio or "",
            str(case.case_income or 0),
            case.payment_due_date.strftime("%Y-%m-%d") if case.payment_due_date else "",
            case.cause or "",
            case.stage or "",
            case.plaintiff or "",
            case.appellant_info or "",
            case.extra_appellant_info or "",
            case.defendant or "",
            case.agency_power or "",
            case.court or "",
            case.hearing_date.strftime("%Y-%m-%d") if case.hearing_date else "",
            case.filing_date.strftime("%Y-%m-%d") if case.filing_date else "",
            case.closing_date.strftime("%Y-%m-%d") if case.closing_date else "",
            case.location or "",
            case.details or "",
            case.main_lawyer.real_name if case.main_lawyer else "",
            case.assistant_lawyer.real_name if case.assistant_lawyer else "",
            case.execution_lawyer.real_name if case.execution_lawyer else "",
            case.execution_assistant.real_name if case.execution_assistant else "",
            case.review_status,
            "是" if case.is_major else "否",
            "是" if case.has_paper_file else "否",
            "是" if case.is_dismissed else "否",
            "是" if case.has_record else "否",
            "是" if case.has_preservation else "否",
            "是" if case.is_deleted else "否",
            case.preservation_start.strftime("%Y-%m-%d") if case.preservation_start else "",
            case.preservation_end.strftime("%Y-%m-%d") if case.preservation_end else "",
            case.case_code or "",
            case.closing_status or "",
            case.closing_method or "",
            case.litigation_fee_payment_date.strftime("%Y-%m-%d") if case.litigation_fee_payment_date else "",
            str(case.litigation_fee_payment_amount or 0),
            case.litigation_fee_refund_date.strftime("%Y-%m-%d") if case.litigation_fee_refund_date else "",
            str(case.litigation_fee_refund_amount or 0),
            case.execution_application_date.strftime("%Y-%m-%d") if case.execution_application_date else "",
            case.mediation_due_date.strftime("%Y-%m-%d") if case.mediation_due_date else "",
            case.execution_due_date.strftime("%Y-%m-%d") if case.execution_due_date else "",
            case.created_at.strftime("%Y-%m-%d %H:%M") if case.created_at else "",
            case.updated_at.strftime("%Y-%m-%d %H:%M") if case.updated_at else ""
        ])

    # 6. 调整列宽
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter  # 获取列字母
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2) * 1.2
        ws.column_dimensions[column].width = adjusted_width

    # 7. 保存到内存
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    # 8. 返回文件流
    filename = f"案件数据_{datetime.now().strftime('%Y%m%d%H%M')}.xlsx"
    encoded_filename = quote(filename)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )

@router.get("/export/bank_cases", response_class=StreamingResponse)
def export_cases(
        user_id: int,
        role: str,
        db: Session = Depends(get_db)
):
    """导出银行案件数据为Excel"""
    # 1. 获取数据
    cases = export_bank_cases_by_user_role(db, user_id, role)
    if not cases:
        raise HTTPException(status_code=404, detail="无符合条件的案件数据")

    # 2. 创建Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "案件列表"

    # 3. 设置表头
    headers = [
        "案件ID", "案件号", "委托日期", "委托人", "委托人身份证号/单位税号", "委托人电话",
        "案件类别", "案件来源", "收费方式", "风险比例", "案件收入",
        "付款到期日", "案由", "介入阶段", "原告/申请人", "上诉人或第三人信息补充",
        "补上诉人或补告信息补充", "被告", "代理权限", "审理法院", "开庭时间", "立案日",
        "结案时间", "案件地点", "案件详情",
        "主办律师", "助理律师", "执行主办律师", "执行助理律师",
        "案件审核状态", "是否重大", "是否纸质卷宗", "是否解除", "是否笔录", "是否保全",
        "是否删除", "保全开始日", "保全终止日",
        "案号", "结案状态", "结案方式",
        "诉讼费缴费时间", "诉讼费缴费金额", "诉讼费退费时间", "诉讼费退费金额",
        "申请执行日", "调解到期日", "执行到期日",
        "创建时间", "更新时间"
    ]
    ws.append(headers)

    # 4. 设置表头样式
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    # 5. 填充数据
    for case in cases:
        ws.append([
            case.case_id,
            case.case_number,
            case.commission_date.strftime("%Y-%m-%d") if case.commission_date else "",
            case.client_name,
            case.client_id_number or "",
            case.client_phone or "",
            case.case_category,
            case.case_source or "",
            case.fee_method or "",
            case.risk_ratio or "",
            str(case.case_income or 0),
            case.payment_due_date.strftime("%Y-%m-%d") if case.payment_due_date else "",
            case.cause or "",
            case.stage or "",
            case.plaintiff or "",
            case.appellant_info or "",
            case.extra_appellant_info or "",
            case.defendant or "",
            case.agency_power or "",
            case.court or "",
            case.hearing_date.strftime("%Y-%m-%d") if case.hearing_date else "",
            case.filing_date.strftime("%Y-%m-%d") if case.filing_date else "",
            case.closing_date.strftime("%Y-%m-%d") if case.closing_date else "",
            case.location or "",
            case.details or "",
            case.main_lawyer.real_name if case.main_lawyer else "",
            case.assistant_lawyer.real_name if case.assistant_lawyer else "",
            case.execution_lawyer.real_name if case.execution_lawyer else "",
            case.execution_assistant.real_name if case.execution_assistant else "",
            case.review_status,
            "是" if case.is_major else "否",
            "是" if case.has_paper_file else "否",
            "是" if case.is_dismissed else "否",
            "是" if case.has_record else "否",
            "是" if case.has_preservation else "否",
            "是" if case.is_deleted else "否",
            case.preservation_start.strftime("%Y-%m-%d") if case.preservation_start else "",
            case.preservation_end.strftime("%Y-%m-%d") if case.preservation_end else "",
            case.case_code or "",
            case.closing_status or "",
            case.closing_method or "",
            case.litigation_fee_payment_date.strftime("%Y-%m-%d") if case.litigation_fee_payment_date else "",
            str(case.litigation_fee_payment_amount or 0),
            case.litigation_fee_refund_date.strftime("%Y-%m-%d") if case.litigation_fee_refund_date else "",
            str(case.litigation_fee_refund_amount or 0),
            case.execution_application_date.strftime("%Y-%m-%d") if case.execution_application_date else "",
            case.mediation_due_date.strftime("%Y-%m-%d") if case.mediation_due_date else "",
            case.execution_due_date.strftime("%Y-%m-%d") if case.execution_due_date else "",
            case.created_at.strftime("%Y-%m-%d %H:%M") if case.created_at else "",
            case.updated_at.strftime("%Y-%m-%d %H:%M") if case.updated_at else ""
        ])

    # 6. 调整列宽
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter  # 获取列字母
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2) * 1.2
        ws.column_dimensions[column].width = adjusted_width

    # 7. 保存到内存
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    # 8. 返回文件流
    filename = f"案件数据_{datetime.now().strftime('%Y%m%d%H%M')}.xlsx"
    encoded_filename = quote(filename)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )

# 2️⃣ 获取单条案件详情
@router.get("/{case_id}", response_model=CaseOut)
def get_case(case_id: int, db: Session = Depends(get_db)):
    """
    获取案件详情
    """
    case = get_case_by_id(db=db, case_id=case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="案件不存在")
    return case


# 3️⃣ 普通用户提交案件操作申请（新增/修改/删除）
@router.post("/case_create", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
def create_new_case(case_in: CaseCreate, db: Session = Depends(get_db)):
    """
    创建新案件
    """
    try:
        new_case = create_case(db=db, case_in=case_in)
        return new_case
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/case_update/{case_id}", response_model=CaseOut)
def update_existing_case(case_id: int, case_in: CaseUpdate, db: Session = Depends(get_db)):
    """
    更新案件
    """
    updated_case = update_case(db=db, case_id=case_id, case_in=case_in)
    if not updated_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="案件不存在")
    return updated_case

@router.delete("/case_delete/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_case(case_id: int, db: Session = Depends(get_db)):
    """
    删除案件（逻辑删除）
    """
    success = delete_case(db=db, case_id=case_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="案件不存在")
    return


# 4️⃣ 获取所有律师列表
@router.get("/users/lawyers", response_model=List[UserOut])
def list_lawyers(db: Session = Depends(get_db)):
    return get_all_lawyers(db)

