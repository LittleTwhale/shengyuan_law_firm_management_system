# api/case_manage.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from collections import defaultdict
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal

from ..database.database import get_db
from ..models.case import Case, CaseParty
from ..schemas.user import UserOut
from ..schemas.case import CaseOut, CasePageOut, CaseSimpleOut, CaseCreate, CaseUpdate, CaseExportQuery

from ..crud.user import get_all_lawyers, get_user_id_by_name
from ..crud.case import list_cases_by_user_role, get_case_by_id, count_cases_by_user_role, create_case, update_case, \
    delete_case, export_cases_by_user_role, list_bank_cases_by_user_role, count_bank_cases_by_user_role, \
    export_bank_cases_by_user_role, split_with_separators, export_cases_to_excel

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
    year: Optional[str] = None,
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
        year=year,
        sort_field=sort_field,
        sort_dir=sort_dir,
    )
    total = count_bank_cases_by_user_role(
        db=db,
        user_id=user_id,
        role=role,
        keyword=keyword,  # 传递给统计函数
        main_lawyer_id=main_lawyer_id,
        year=year,
    )
    cases_simple = [CaseSimpleOut.model_validate(c) for c in cases]
    return {"items": cases_simple, "total": total}


# 5️⃣ 导出案件表格
@router.post("/export", response_class=StreamingResponse)
def export_cases(
        user_id: int,
        role: str,
        query: CaseExportQuery,
        db: Session = Depends(get_db)
):
    """
    根据筛选条件导出案件明细 (支持分Sheet导出普通案件和银行案件)
    """
    excel_io = export_cases_to_excel(db, user_id, role, query)

    filename = f"业务数据明细_{datetime.now().strftime('%Y%m%d%H%M')}.xlsx"
    encoded_filename = quote(filename)

    return StreamingResponse(
        excel_io,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
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
    side_a = {'原告', '申请人', '上诉人'}
    side_b = {'被告', '被告人', '被申请人', '被上诉人'}

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
            if p.party_type in side_b:
                found_side = "B"
                break
            elif p.party_type in side_a:
                found_side = "A"
                # 不 break，继续找看是否有更明确的 B 角色（极少见）

    if found_side:
        client_side = found_side
    else:
        # 2.2 如果委托人没挂诉讼头衔，通过“其他人是谁”来反推
        # 如果列表里有被告，那委托人大概率是原告
        has_side_b = any(p.party_type in side_b for p in input_parties)
        if has_side_b:
            client_side = "A"
        else:
            # 如果列表里只有原告，且委托人名字不在其中，那委托人可能是被告（较少见，通常是被告委托）
            has_side_a = any(p.party_type in side_a for p in input_parties)
            if has_side_a:
                client_side = "B"

    # 2.3 提取对手名字
    target_opponent_types = side_a if client_side == "B" else side_b
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
            p.name in host_client_names and p.party_type in side_b
            for p in all_case_parties
        )
        if has_host_as_defendant:
            host_side = "B"

        # 3.2 确定新委托人(在历史案件中)的阵营
        target_role_side = "Unknown"
        if party_record.party_type in side_a:
            target_role_side = "A"
        elif party_record.party_type in side_b:
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
    📦 批量导入案件接口 (V3: 双Sheet关联模式，完美适配 CaseParty 结构)
    """
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="仅支持.xlsx和.xls格式的Excel文件")

        wb = load_workbook(filename=BytesIO(file.file.read()), data_only=True)

        # 校验两个必须的 Sheet
        if "案件列表" not in wb.sheetnames or "当事人列表" not in wb.sheetnames:
            raise HTTPException(status_code=400, detail="Excel模板错误：必须包含'案件列表'和'当事人列表'两个工作表")

        ws_cases = wb["案件列表"]
        ws_parties = wb["当事人列表"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"无法读取Excel文件：{str(e)}")
    finally:
        file.file.close()

    # ---------------- 1. 解析【当事人列表】 ----------------
    parties_headers = [str(cell.value).strip() if cell.value else "" for cell in ws_parties[1]]
    parties_dict = defaultdict(list)  # 格式: { "案件号": [party1, party2, ...] }

    for row in ws_parties.iter_rows(min_row=2, values_only=True):
        p_row = dict(zip(parties_headers, row))
        link_case_no = str(p_row.get("关联案件号", "")).strip()
        p_type = str(p_row.get("当事人类型", "")).strip()
        p_name = str(p_row.get("姓名/名称", "")).strip()

        # 如果缺少关联号、类型或姓名，则跳过该当事人
        if not link_case_no or not p_type or not p_name:
            continue

        parties_dict[link_case_no].append({
            "party_type": p_type,
            "name": p_name,
            "phone": str(p_row.get("联系电话", "")).strip() or None,
            "id_number": str(p_row.get("身份证号/统一社会信用代码", "")).strip() or None,
            "address": str(p_row.get("联系地址", "")).strip() or None,
            "legal_representative": str(p_row.get("法定代表人", "")).strip() or None,
        })

    # ---------------- 2. 解析【案件列表】 ----------------
    cases_headers = [str(cell.value).strip() if cell.value else "" for cell in ws_cases[1]]

    required_cols = ["案件号", "委托日期", "案件类别", "主办律师"]
    for col in required_cols:
        if col not in cases_headers:
            raise HTTPException(status_code=400, detail=f"'案件列表'工作表缺少必要字段：{col}")

    total_rows = 0
    success_rows = 0
    failed_cases = []

    def parse_date(date_value):
        if not date_value: return None
        if isinstance(date_value, str):
            try:
                return datetime.strptime(date_value, "%Y-%m-%d").date()
            except ValueError:
                return None
        return date_value

    def parse_decimal(value):
        if not value: return 0
        try:
            return Decimal(str(value).replace(",", ""))
        except:
            return 0

    for row in ws_cases.iter_rows(min_row=2, values_only=True):
        # 检查是否为空行（依据案件号判断）
        if not row[0]:
            continue

        total_rows += 1
        row_data = dict(zip(cases_headers, row))

        case_number = str(row_data.get("案件号", "")).strip()

        try:
            # 获取律师ID
            main_lawyer_id = get_user_id_by_name(db, row_data.get("主办律师"))
            if not main_lawyer_id:
                failed_cases.append(
                    {"case_number": case_number, "reason": f"主办律师不存在：{row_data.get('主办律师')}"})
                continue

            # ---------------- 3. 解析银行案件专属字段 ----------------
            case_category = str(row_data.get("案件类别", "")).strip()
            bank_details = None

            if case_category == "银行案件":
                bank_details = {
                    "branch_name": str(row_data.get("支行名称", "")).strip() or None,
                    "collateral_info": str(row_data.get("抵/质押物信息", "")).strip() or None,
                    "collateral_location": str(row_data.get("抵押物位置", "")).strip() or None,
                    "account_manager": str(row_data.get("客户经理", "")).strip() or None,
                    "loan_type": str(row_data.get("贷款类型", "")).strip() or None,
                    "loan_account": str(row_data.get("贷款账号", "")).strip() or None,
                    "loan_principal": parse_decimal(row_data.get("贷款本金")),
                    "litigation_target_amount": parse_decimal(row_data.get("诉讼标的金额(含利息)")),
                    "credit_card_penalty": parse_decimal(row_data.get("信用卡违约金")),
                    "loan_date": parse_date(row_data.get("借款日")),
                    "loan_due_date": parse_date(row_data.get("到期日")),
                    "statute_of_limitations": parse_date(row_data.get("诉讼时效")),
                    "case_acceptance_date": parse_date(row_data.get("收案日期")),
                    "material_fetcher": str(row_data.get("取材料人", "")).strip() or None,
                    "pre_litigation_collection": str(row_data.get("诉前催收情况", "")).strip() or None,
                    "seal_date": parse_date(row_data.get("盖章日")),
                    "material_submission_date": parse_date(row_data.get("材料提交法院日")),
                    "handling_judge": str(row_data.get("承办法官", "")).strip() or None,
                    "judgment_date": parse_date(row_data.get("裁判时间")),
                    "judgment_method": str(row_data.get("裁判方式", "")).strip() or None,
                    "judgment_summary": str(row_data.get("裁判摘要", "")).strip() or None,
                    "lawyer_fee_supported": parse_decimal(row_data.get("支持律师费金额")),
                    "defendant_paid_lawyer_fee": parse_decimal(row_data.get("被告支付律师费金额")),
                    "is_settled": (str(row_data.get("是否还清", "")).strip() == "是"),
                    "has_second_instance_or_retrial": (str(row_data.get("是否有二审/再审", "")).strip() == "是"),
                    "execution_case_number": str(row_data.get("执行案号", "")).strip() or None,
                    "execution_filing_date": parse_date(row_data.get("执行立案时间")),
                    "execution_judge": str(row_data.get("执行法官", "")).strip() or None,
                    "borrower_work_unit": str(row_data.get("借款人工作单位", "")).strip() or None,
                    "is_execution_recovery": (str(row_data.get("是否为恢复执行", "")).strip() == "是"),
                    "execution_material_receipt_date": parse_date(row_data.get("收取执行材料时间")),
                    "execution_material_submission_date": parse_date(row_data.get("执行材料提交法院时间")),
                    "execution_principal": parse_decimal(row_data.get("执行本金金额")),
                    "execution_lawyer_fee": parse_decimal(row_data.get("执行律师费金额")),
                    "property_investigation": str(row_data.get("财产调查情况", "")).strip() or None,
                    "network_control_status": str(row_data.get("网络查控财产情况", "")).strip() or None,
                    "execution_plan": str(row_data.get("承办人执行方案", "")).strip() or None,
                    "court_execution_measures": str(row_data.get("法院执行措施", "")).strip() or None,
                    "seizure_freeze_date": parse_date(row_data.get("查封冻结时间")),
                    "auction_status": str(row_data.get("拍卖程序", "")).strip() or None,
                    "auction_deal_price": parse_decimal(row_data.get("拍卖变卖成交价")),
                    "execution_settlement_content": str(row_data.get("执行和解内容", "")).strip() or None,
                    "procedure_termination_date": parse_date(row_data.get("终本时间")),
                    "termination_reason": str(row_data.get("终本原因", "")).strip() or None,
                    "execution_conclusion_date": parse_date(row_data.get("终结执行时间")),
                    "execution_recovery_date": parse_date(row_data.get("恢复执行时间")),
                    "payoff_date": parse_date(row_data.get("还清时间")),
                    "execution_collection_amount": parse_decimal(row_data.get("执行回款总金额")),
                    "collection_source": str(row_data.get("执行回款来源", "")).strip() or None,
                    "mediation_tracking": str(row_data.get("调解案件履行跟踪情况", "")).strip() or None,
                }

            # ---------------- 4. 组装 CaseCreate ----------------
            # 💡 核心：通过 case_number 从字典中提取对应的当事人列表
            matched_parties = parties_dict.get(case_number, [])

            new_case = CaseCreate(
                case_number=case_number,  # 必须传入以保持关联
                commission_date=parse_date(row_data.get("委托日期")),
                case_category=case_category,
                parties=matched_parties,  # 将关联的当事人列表直接塞入
                bank_case_details=bank_details,

                case_source=str(row_data.get("案件来源", "")).strip() or None,
                fee_method=str(row_data.get("收费方式", "")).strip() or None,
                risk_ratio=str(row_data.get("风险比例", "")).strip() or None,
                case_income=parse_decimal(row_data.get("案件收入")),
                payment_due_date=parse_date(row_data.get("付款到期日")),
                cause=str(row_data.get("案由", "")).strip() or None,
                stage=str(row_data.get("介入阶段", "")).strip() or None,
                agency_power=str(row_data.get("代理权限", "")).strip() or None,
                court=str(row_data.get("审理法院", "")).strip() or None,
                hearing_date=parse_date(row_data.get("开庭时间")),
                filing_date=parse_date(row_data.get("立案日")),
                closing_date=parse_date(row_data.get("结案时间")),
                location=str(row_data.get("案件地点", "")).strip() or None,
                details=str(row_data.get("案件详情", "")).strip() or None,

                main_lawyer_id=main_lawyer_id,
                assistant_lawyer_id=get_user_id_by_name(db, row_data.get("助理律师")),
                execution_lawyer_id=get_user_id_by_name(db, row_data.get("执行主办律师")),
                execution_assistant_id=get_user_id_by_name(db, row_data.get("执行助理律师")),

                is_major=(str(row_data.get("是否重大", "")).strip() == "是"),
                has_paper_file=(str(row_data.get("是否纸质卷宗", "")).strip() == "是"),
                is_dismissed=(str(row_data.get("是否解除", "")).strip() == "是"),
                has_record=(str(row_data.get("是否笔录", "")).strip() == "是"),
                has_preservation=(str(row_data.get("是否保全", "")).strip() == "是"),
                preservation_start=parse_date(row_data.get("保全开始日")),
                preservation_end=parse_date(row_data.get("保全终止日")),

                closing_status=str(row_data.get("结案状态", "")).strip() or None,
                closing_method=str(row_data.get("结案方式", "")).strip() or None,

                litigation_fee_payment_date=parse_date(row_data.get("诉讼费缴费时间")),
                litigation_fee_payment_amount=parse_decimal(row_data.get("诉讼费缴费金额")),
                litigation_fee_refund_date=parse_date(row_data.get("诉讼费退费时间")),
                litigation_fee_refund_amount=parse_decimal(row_data.get("诉讼费退费金额")),

                execution_application_date=parse_date(row_data.get("申请执行日")),
                mediation_due_date=parse_date(row_data.get("调解到期日")),
                execution_due_date=parse_date(row_data.get("执行到期日"))
            )

            # ---------------- 5. 写入数据库 ----------------
            create_case(db=db, case_in=new_case)
            db.commit()
            success_rows += 1

        except SQLAlchemyError as e:
            db.rollback()
            failed_cases.append({"case_number": case_number, "reason": f"数据库错误：{str(e)}"})
        except Exception as e:
            failed_cases.append({"case_number": case_number, "reason": f"数据处理错误：{str(e)}"})

    return {
        "total_cases": total_rows,
        "imported_cases": success_rows,
        "failed_cases": failed_cases
    }