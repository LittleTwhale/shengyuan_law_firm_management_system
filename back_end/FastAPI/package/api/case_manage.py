# api/case_manage.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal

from ..database.database import get_db
from ..models.case import Case
from ..schemas.user import UserOut
from ..schemas.case import CaseOut, CasePageOut, CaseSimpleOut, CaseCreate, CaseUpdate

from ..crud.user import get_all_lawyers, get_user_id_by_name
from ..crud.case import list_cases_by_user_role, get_case_by_id, count_cases_by_user_role, create_case, update_case, \
    delete_case, export_cases_by_user_role, list_bank_cases_by_user_role, count_bank_cases_by_user_role, \
    export_bank_cases_by_user_role, split_with_separators

from io import BytesIO
from urllib.parse import quote
from openpyxl import Workbook, load_workbook
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
    main_lawyer_id: Optional[int] = None,  # 新增主办律师参数
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
        category=category,  # 传递给CRUD函数
        main_lawyer_id=main_lawyer_id,
    )
    total = count_cases_by_user_role(
        db=db,
        user_id=user_id,
        role=role,
        keyword=keyword,  # 传递给统计函数
        category=category,  # 传递给统计函数
        main_lawyer_id=main_lawyer_id,
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
        main_lawyer_id: Optional[int] = None,
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
        main_lawyer_id=main_lawyer_id,
    )
    total = count_bank_cases_by_user_role(
        db=db,
        user_id=user_id,
        role=role,
        keyword=keyword,  # 传递给统计函数
        main_lawyer_id=main_lawyer_id,
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
        "付款到期日", "案由", "介入阶段", "原告/申请人/侦察机关/检察院", "上诉人或第三人",
        "被上诉人", "被告(人)", "代理权限", "审理法院", "开庭时间", "立案日",
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
        "付款到期日", "案由", "介入阶段", "原告/申请人/侦察机关/检察院", "上诉人或第三人",
        "被上诉人", "被告(人)", "代理权限", "审理法院", "开庭时间", "立案日",
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


# 利益冲突检测
@router.post("/check_conflict", status_code=status.HTTP_200_OK)
def check_interest_conflict(
        case_data: CaseCreate,
        db: Session = Depends(get_db)
):
    """检测新增案件的利益冲突"""
    # 获取当前委托人
    client_name = case_data.client_name
    if not client_name:
        raise HTTPException(status_code=400, detail="委托人姓名不能为空")

    # 获取所有顾问单位（法律顾问业务的委托人）
    consultant_units = db.query(Case.client_name).filter(
        Case.case_category == "法律顾问业务",
        Case.is_deleted == False
    ).distinct().all()
    consultant_units = [unit[0] for unit in consultant_units]  # 提取委托人名称列表

    # 定义分隔符
    separators = ["、", ",", "，", " ", "；", ";"]

    # 拆分当前案件的被告
    current_defendants = [d.strip() for d in split_with_separators(case_data.defendant or "", separators) if d.strip()]

    precise_conflicts = []

    # 检测1：常规利益冲突 - 当前委托人在其他案件中作为原告/被告
    conflict_cases = db.query(Case).filter(
        or_(
            Case.plaintiff.like(f"%{client_name}%"),
            Case.defendant.like(f"%{client_name}%")
        ),
        Case.is_deleted == False
    ).all()

    for case in conflict_cases:
        # 拆分原告字段为主体列表
        plaintiffs = [p.strip() for p in split_with_separators(str(case.plaintiff), separators) if p.strip()]
        # 拆分被告字段为主体列表
        defendants = [d.strip() for d in split_with_separators(case.defendant or "", separators) if d.strip()]

        # 常规冲突：当前委托人在对方案件中作为原/被告
        normal_conflict = client_name in plaintiffs or client_name in defendants

        if normal_conflict:
            conflict_info = {
                "case": case,
                "conflict_type": "常规利益冲突",
                "role": "原告" if client_name in plaintiffs else "被告",
                "conflict_reason": f"当前委托人在案件 {case.case_number} 中作为{('原告' if client_name in plaintiffs else '被告')}"
            }
            precise_conflicts.append(conflict_info)

    # 检测2：顾问单位冲突 - 当前案件的被告包含顾问单位
    # 这部分独立于上面的检测，即使conflict_cases为空也会执行
    consultant_conflict_units = []
    for unit in consultant_units:
        if unit in current_defendants:
            consultant_conflict_units.append(unit)

    if consultant_conflict_units:
        # 为每个冲突的顾问单位创建一个冲突记录
        for unit in consultant_conflict_units:
            # 查找该顾问单位对应的法律顾问业务案件
            consultant_case = db.query(Case).filter(
                Case.client_name == unit,
                Case.case_category == "法律顾问业务",
                Case.is_deleted == False
            ).first()

            if consultant_case:
                conflict_info = {
                    "case": consultant_case,  # 使用法律顾问业务案件信息
                    "conflict_type": "顾问单位作为被告",
                    "role": "被告（顾问单位）",
                    "conflict_reason": f"当前案件的被告 '{unit}' 是本所法律顾问单位",
                    "consultant_unit": unit
                }
                precise_conflicts.append(conflict_info)

    if precise_conflicts:
        # 提取冲突详情
        conflict_details = []
        for item in precise_conflicts:
            detail = {
                "case_number": item["case"].case_number,
                "other_lawyer_id": item["case"].main_lawyer_id,
                "other_lawyer_name": item["case"].main_lawyer.real_name if item["case"].main_lawyer else "未知",
                "role": item["role"],
                "conflict_type": item["conflict_type"],
                "message": item["conflict_reason"]
            }
            if "consultant_unit" in item:
                detail["consultant_unit"] = item["consultant_unit"]

            conflict_details.append(detail)

        return {"has_conflict": True, "details": conflict_details}

    return {"has_conflict": False}

@router.post("/import", status_code=200)
def import_cases_from_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    📦 批量导入案件接口
    Import multiple cases from uploaded Excel file.
    """
    # ---------------- 1️⃣ 读取Excel文件 ----------------
    try:
        # 验证文件格式
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="仅支持.xlsx和.xls格式的Excel文件")

        wb = load_workbook(filename=BytesIO(file.file.read()), data_only=True)  # data_only确保读取单元格值而非公式
        ws = wb.active
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"无法读取Excel文件：{str(e)}")
    finally:
        file.file.close()  # 确保文件流关闭

    headers = [str(cell.value).strip() if cell.value else "" for cell in ws[1]]  # 获取表头并标准化
    # 校验表头（与导出字段严格匹配）
    required_cols = ["案件号", "委托日期", "委托人", "案件类别", "主办律师"]
    for col in required_cols:
        if col not in headers:
            raise HTTPException(status_code=400, detail=f"Excel表头缺少必要字段：{col}")

    total_rows = 0
    success_rows = 0
    failed_cases = []  # 存储失败详情（案件号+原因）

    # ---------------- 2️⃣ 遍历Excel数据行 ----------------
    for row in ws.iter_rows(min_row=2, values_only=True):
        total_rows += 1
        row_data = dict(zip(headers, row))
        case_number = row_data.get("案件号") or f"第{total_rows}行"

        try:
            # ⚙️ 律师信息转换（姓名转ID）
            main_lawyer_id = get_user_id_by_name(db, row_data.get("主办律师"))
            assistant_lawyer_id = get_user_id_by_name(db, row_data.get("助理律师"))
            execution_lawyer_id = get_user_id_by_name(db, row_data.get("执行主办律师"))
            execution_assistant_id = get_user_id_by_name(db, row_data.get("执行助理律师"))

            # 验证主办律师必须存在
            if not main_lawyer_id:
                failed_cases.append({
                    "case_number": case_number,
                    "reason": f"主办律师不存在：{row_data.get('主办律师')}"
                })
                continue

            # 验证案件号唯一性
            existing_case = db.query(Case).filter(
                Case.case_number == str(row_data.get("案件号")).strip(),
                Case.is_deleted == False
            ).first()
            if existing_case:
                failed_cases.append({
                    "case_number": case_number,
                    "reason": "案件号已存在"
                })
                continue

            # 📅 日期字段处理（兼容Excel日期格式和字符串）
            def parse_date(date_value):
                if not date_value:
                    return None
                if isinstance(date_value, str):
                    try:
                        from datetime import datetime
                        return datetime.strptime(date_value, "%Y-%m-%d").date()
                    except ValueError:
                        return None
                return date_value  # 已为date类型

            # 💰 数字字段处理
            def parse_decimal(value):
                if not value:
                    return 0
                try:
                    return Decimal(str(value).replace(",", ""))  # 处理千分位符号
                except:
                    return 0

            # 🧱 构造完整CaseCreate数据模型（补全所有字段）
            new_case = CaseCreate(
                # 基本信息
                commission_date=parse_date(row_data.get("委托日期")),
                client_name=str(row_data.get("委托人")).strip() if row_data.get("委托人") else None,
                client_id_number=str(row_data.get("委托人身份证号/单位税号")).strip() if row_data.get(
                    "委托人身份证号/单位税号") else None,
                client_phone=str(row_data.get("委托人电话")).strip() if row_data.get("委托人电话") else None,
                case_category=str(row_data.get("案件类别")).strip() if row_data.get("案件类别") else None,
                case_source=str(row_data.get("案件来源")).strip() if row_data.get("案件来源") else None,
                fee_method=str(row_data.get("收费方式")).strip() if row_data.get("收费方式") else None,
                risk_ratio=str(row_data.get("风险比例")).strip() if row_data.get("风险比例") else None,
                case_income=parse_decimal(row_data.get("案件收入")),

                # 诉讼相关
                payment_due_date=parse_date(row_data.get("付款到期日")),
                cause=str(row_data.get("案由")).strip() if row_data.get("案由") else None,
                stage=str(row_data.get("介入阶段")).strip() if row_data.get("介入阶段") else None,
                plaintiff=str(row_data.get("原告/申请人/侦察机关/检察院")).strip() if row_data.get("原告/申请人") else None,
                appellant_info=str(row_data.get("上诉人或第三人")).strip() if row_data.get(
                    "上诉人或第三人") else None,
                extra_appellant_info=str(row_data.get("被上诉人")).strip() if row_data.get(
                    "被上诉人") else None,
                defendant=str(row_data.get("被告(人)")).strip() if row_data.get("被告(人)") else None,
                agency_power=str(row_data.get("代理权限")).strip() if row_data.get("代理权限") else None,
                court=str(row_data.get("审理法院")).strip() if row_data.get("审理法院") else None,
                hearing_date=parse_date(row_data.get("开庭时间")),
                filing_date=parse_date(row_data.get("立案日")),
                closing_date=parse_date(row_data.get("结案时间")),
                location=str(row_data.get("案件地点")).strip() if row_data.get("案件地点") else None,
                details=str(row_data.get("案件详情")).strip() if row_data.get("案件详情") else None,

                # 律师信息
                main_lawyer_id=main_lawyer_id,
                assistant_lawyer_id=assistant_lawyer_id,
                execution_lawyer_id=execution_lawyer_id,
                execution_assistant_id=execution_assistant_id,

                # 状态与标记
                is_major=(str(row_data.get("是否重大")).strip() == "是"),
                has_paper_file=(str(row_data.get("是否纸质卷宗")).strip() == "是"),
                is_dismissed=(str(row_data.get("是否解除")).strip() == "是"),
                has_record=(str(row_data.get("是否笔录")).strip() == "是"),
                has_preservation=(str(row_data.get("是否保全")).strip() == "是"),
                preservation_start=parse_date(row_data.get("保全开始日")),
                preservation_end=parse_date(row_data.get("保全终止日")),

                # 结案与执行
                case_code=str(row_data.get("案号")).strip() if row_data.get("案号") else None,
                closing_status=str(row_data.get("结案状态")).strip() if row_data.get("结案状态") else None,
                closing_method=str(row_data.get("结案方式")).strip() if row_data.get("结案方式") else None,

                # 诉讼费
                litigation_fee_payment_date=parse_date(row_data.get("诉讼费缴费时间")),
                litigation_fee_payment_amount=parse_decimal(row_data.get("诉讼费缴费金额")),
                litigation_fee_refund_date=parse_date(row_data.get("诉讼费退费时间")),
                litigation_fee_refund_amount=parse_decimal(row_data.get("诉讼费退费金额")),

                # 执行相关
                execution_application_date=parse_date(row_data.get("申请执行日")),
                mediation_due_date=parse_date(row_data.get("调解到期日")),
                execution_due_date=parse_date(row_data.get("执行到期日"))
            )

            # ---------------- 3️⃣ 保存到数据库 ----------------
            # 注意：create_case函数已处理案件号生成，无需手动设置case_number
            db_case = create_case(db=db, case_in=new_case)
            db.commit()
            success_rows += 1

        except SQLAlchemyError as e:
            db.rollback()
            failed_cases.append({
                "case_number": case_number,
                "reason": f"数据库错误：{str(e)}"
            })
        except Exception as e:
            failed_cases.append({
                "case_number": case_number,
                "reason": f"数据处理错误：{str(e)}"
            })

    # ---------------- 4️⃣ 返回导入结果 ----------------
    return {
        "total_cases": total_rows,
        "imported_cases": success_rows,
        "failed_cases": failed_cases
    }