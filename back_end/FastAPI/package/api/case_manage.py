# api/case_manage.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal

from ..database.database import get_db
from ..models.case import Case, CaseParty
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
    year: Optional[str] = None,  # 新增年份参数
    sort_field: Optional[str] = "created_at",  # 排序参数
    sort_dir: Optional[str] = "desc",  # 排序方式
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
        year=year,
        sort_field=sort_field,
        sort_dir=sort_dir,
    )
    total = count_cases_by_user_role(
        db=db,
        user_id=user_id,
        role=role,
        keyword=keyword,  # 传递给统计函数
        category=category,  # 传递给统计函数
        main_lawyer_id=main_lawyer_id,
        year=year,
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
    sort_field: Optional[str] = "created_at",  # 排序参数
    sort_dir: Optional[str] = "desc",  # 排序方式
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
        sort_field=sort_field,
        sort_dir=sort_dir,
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
    """
    基于 CaseParty 表的全维度利益冲突检测 (重构版)
    完全弃用 Case.client_name 字段，仅依赖 party_type='委托人' 识别身份。

    逻辑流程：
    1. 从提交的 parties 中提取 '委托人' 名字列表。
    2. 确定委托人在本案中的诉讼阵营 (A:原告方 vs B:被告方)，从而锁定“对手名单”。
    3. 检测代理冲突：对手名单中的人，是否是我们历史案件的委托人？
    4. 检测自益冲突：当前委托人，是否在我们历史案件中处于对立面？
    """

    # 定义阵营集合
    SIDE_A = {'原告', '申请人', '上诉人'}
    SIDE_B = {'被告', '被申请人', '被上诉人'}

    input_parties = case_data.parties or []

    # ---------------------------------------------------------
    # 1. 提取当前案件的委托人 (New Clients)
    # ---------------------------------------------------------
    new_client_names = set()
    for p in input_parties:
        if p.party_type == '委托人' and p.name:
            new_client_names.add(p.name.strip())

    # 如果没填委托人（这在业务上不应该发生，但需防御），尝试用 Case.client_name 兜底或报错
    if not new_client_names and case_data.client_name:
        new_client_names.add(case_data.client_name.strip())

    if not new_client_names:
        # 如果还没找到，无法进行检测，直接返回（或根据业务需求报错）
        return {"has_conflict": False, "details": []}

    # ---------------------------------------------------------
    # 2. 确定委托人阵营 & 锁定对手 (New Opponents)
    # ---------------------------------------------------------
    client_side = "A"  # 默认为原告方

    # 2.1 尝试通过名字匹配，看委托人是否兼任了原告或被告
    found_side = None
    for p in input_parties:
        if p.name.strip() in new_client_names:
            if p.party_type in SIDE_B:
                found_side = "B"
                break
            elif p.party_type in SIDE_A:
                found_side = "A"
                # 不 break，继续找看是否有更明确的 B 角色（极少见）

    if found_side:
        client_side = found_side
    else:
        # 2.2 如果委托人没挂诉讼头衔，通过“其他人是谁”来反推
        # 如果列表里有被告，那委托人大概率是原告
        has_side_b = any(p.party_type in SIDE_B for p in input_parties)
        if has_side_b:
            client_side = "A"
        else:
            # 如果列表里只有原告，且委托人名字不在其中，那委托人可能是被告（较少见，通常是被告委托）
            has_side_a = any(p.party_type in SIDE_A for p in input_parties)
            if has_side_a:
                client_side = "B"

    # 2.3 提取对手名字
    target_opponent_types = SIDE_A if client_side == "B" else SIDE_B
    new_case_opponents = set()

    for p in input_parties:
        if p.party_type in target_opponent_types and p.name:
            new_case_opponents.add(p.name.strip())

    # 兼容旧字段 (如果前端还在用 defendant 字段)
    if not new_case_opponents and case_data.defendant and client_side == "A":
        separators = ["、", ",", "，", " ", "；", ";"]
        new_case_opponents = [d.strip() for d in split_with_separators(case_data.defendant, separators) if
                              d.strip()]

    precise_conflicts = []
    # 用于去重 (case_id, conflict_type)
    processed_conflicts = set()

    # =========================================================================
    # 检测 A: 代理冲突 (Representation Conflict)
    # 核心问题：新案件的对手，是我们正在服务的客户吗？
    # =========================================================================

    if new_case_opponents:
        # 查询数据库：CaseParty 中 type='委托人' 且 name 在对手名单中的记录
        # 且关联的 Case 未删除

        existing_client_conflicts = db.query(CaseParty).join(Case).filter(
            CaseParty.party_type == '委托人',
            CaseParty.name.in_(new_case_opponents),
            Case.is_deleted == False
        ).all()

        for record in existing_client_conflicts:
            case = record.case

            conflict_key = (case.case_id, "agency_conflict")
            if conflict_key in processed_conflicts: continue

            conflict_info = {
                "case_number": case.case_number,
                "other_lawyer_name": case.main_lawyer.real_name if case.main_lawyer else "未知",
                "conflict_type": "利益冲突（起诉现有客户）",
                "role": "委托人",  # 在历史案件中，他是委托人
                "message": f"新案件的对手方 '{record.name}' 是我所现有案件【{case.case_number}】的委托人。"
            }
            if case.case_category == "法律顾问业务":
                conflict_info["message"] = f"新案件的对手方 '{record.name}' 是我所法律顾问单位。"

            precise_conflicts.append(conflict_info)
            processed_conflicts.add(conflict_key)

    # =========================================================================
    # 检测 B: 自益冲突 (Self-Interest Conflict)
    # 核心问题：新案件的委托人，是我们正在起诉的人吗？
    # =========================================================================

    # 1. 找出新委托人参与过的所有未结案件 (作为任意角色)
    history_participations = db.query(CaseParty).join(Case).filter(
        CaseParty.name.in_(new_client_names),
        Case.is_deleted == False,
    ).all()

    for party_record in history_participations:
        case = party_record.case

        # 跳过新委托人就是该历史案件委托人的情况（这是回头客，不是冲突）
        # 这里需要查一下该 case 的委托人是谁

        # 2. 查询该历史案件的委托人 (Host Clients)
        host_clients = db.query(CaseParty).filter(
            CaseParty.case_id == case.case_id,
            CaseParty.party_type == '委托人'
        ).all()
        host_client_names = {hc.name for hc in host_clients}

        # 如果新委托人也是历史案件的委托人 -> 相同阵营，无冲突
        if party_record.name in host_client_names:
            continue

        # 3. 判断阵营对立
        # 历史案件的委托人阵营 (Host Client Side)
        # 我们需要知道历史案件的委托人是 原告(A) 还是 被告(B)
        # 既然数据都存 CaseParty，我们查一下历史案件里有没有同名的“原告”或“被告”记录

        # 查该案件所有当事人
        all_case_parties = case.parties  # 利用 relationship 加载

        host_side = "A"  # 默认历史客户是原告

        # 3.1 确定历史客户的阵营
        has_host_as_defendant = any(
            p.name in host_client_names and p.party_type in SIDE_B
            for p in all_case_parties
        )
        if has_host_as_defendant:
            host_side = "B"

        # 3.2 确定新委托人(在历史案件中)的阵营
        target_role_side = "Unknown"
        if party_record.party_type in SIDE_A:
            target_role_side = "A"
        elif party_record.party_type in SIDE_B:
            target_role_side = "B"

        # 3.3 比较：如果阵营不同，且都不是未知，则判定冲突
        if target_role_side != "Unknown" and host_side != target_role_side:

            conflict_key = (case.case_id, "self_conflict")
            if conflict_key in processed_conflicts: continue

            conflict_info = {
                "case_number": case.case_number,
                "other_lawyer_name": case.main_lawyer.real_name if case.main_lawyer else "未知",
                "conflict_type": "利益冲突（正在起诉该客户）",
                "role": party_record.party_type,
                "message": (
                    f"新委托人 '{party_record.name}' 在现有案件【{case.case_number}】中"
                    f"是【{party_record.party_type}】，"
                    f"处于我方委托人（{','.join(host_client_names)}）的对立面。"
                )
            }
            precise_conflicts.append(conflict_info)
            processed_conflicts.add(conflict_key)

    if precise_conflicts:
        return {"has_conflict": True, "details": precise_conflicts}

    return {"has_conflict": False, "details": []}

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