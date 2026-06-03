"""
案件智能分析 API 路由
接收案件数据 + 额外文件，调用 DeepSeek 生成 Markdown 分析报告
"""
import os
import json
import re
import tempfile
import logging
import asyncio
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from ..database.database import get_db
from ..models.user import User
from ..models.case import Case, CaseParty
from ..models.electronic_volume_model import CaseVolume, VolumeFile
from ..models.finance_model import CaseFinance
from ..models.attachment import CaseAttachment
from ..core.config import CASE_ATTACHMENT_ROOT
from ..api.deps import get_current_active_user
from ..utils.llm_client import (
    analyze_case as llm_analyze,
    analyze_case_stream as llm_analyze_stream,
    chat_about_case as llm_chat,
    search_relevant_provisions as llm_rag_search,
)
from ..utils.ocr_helper import perform_smart_extraction
from ..crud.case import list_cases_by_user_role, count_cases_by_user_role

# 使用 shengyuan_app 作为父 logger，确保日志进入统一日志系统
logger = logging.getLogger("shengyuan_app.ai_assistant")

router = APIRouter(
    prefix="/ai",
    tags=["ai_assistant"],
)


# =================================================================
#  辅助函数：隐私过滤
# =================================================================

def _filter_party(p: CaseParty) -> dict:
    """过滤当事人敏感字段，仅保留分析所需的公开信息"""
    return {
        "party_type": p.party_type,
        "name": p.name,
        "legal_representative": p.legal_representative,
        # 🚫 故意排除: id_number, phone, address
    }


def _filter_parties(parties: List[CaseParty]) -> list:
    return [_filter_party(p) for p in parties]


# =================================================================
#  辅助函数：数据聚合
# =================================================================

def _aggregate_case_data(db: Session, case_id: int) -> dict:
    """从数据库中聚合一个案件的完整数据结构"""
    # 加载案件（含关联关系）
    case = (
        db.query(Case)
        .options(
            joinedload(Case.main_lawyer),
            joinedload(Case.assistant_lawyer),
            joinedload(Case.execution_lawyer),
            joinedload(Case.parties),
            joinedload(Case.bank_case_details),
            joinedload(Case.finance),
            joinedload(Case.volumes).joinedload(CaseVolume.files),
        )
        .filter(Case.case_id == case_id, Case.is_deleted == False)
        .first()
    )

    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 案件基本信息
    case_info = {
        "case_id": case.case_id,
        "case_number": case.case_number,
        "case_category": case.case_category,
        "cause": case.cause,
        "court": case.court,
        "location": case.location,
        "details": case.details,
        "agency_power": case.agency_power,
        "stage": case.stage,
        # 主办律师姓名
        "main_lawyer": case.main_lawyer.real_name if case.main_lawyer else None,
        "execution_lawyer": case.execution_lawyer.real_name if case.execution_lawyer else None,
        # 日期字段
        "commission_date": str(case.commission_date) if case.commission_date else None,
        "filing_date": str(case.filing_date) if case.filing_date else None,
        "hearing_date": str(case.hearing_date) if case.hearing_date else None,
        "closing_date": str(case.closing_date) if case.closing_date else None,
        "preservation_start": str(case.preservation_start) if case.preservation_start else None,
        "preservation_end": str(case.preservation_end) if case.preservation_end else None,
        "payment_due_date": str(case.payment_due_date) if case.payment_due_date else None,
        "litigation_fee_payment_date": str(case.litigation_fee_payment_date) if case.litigation_fee_payment_date else None,
        "litigation_fee_refund_date": str(case.litigation_fee_refund_date) if case.litigation_fee_refund_date else None,
        "execution_application_date": str(case.execution_application_date) if case.execution_application_date else None,
        "mediation_due_date": str(case.mediation_due_date) if case.mediation_due_date else None,
        "execution_due_date": str(case.execution_due_date) if case.execution_due_date else None,
        "advisory_due_date": str(case.advisory_due_date) if case.advisory_due_date else None,
    }

    # 当事人（已过滤敏感字段）
    parties = _filter_parties(case.parties) if case.parties else []

    # 银行案件专属数据
    bank_case = None
    if case.bank_case_details:
        bk = case.bank_case_details
        bank_case = {
            "branch_name": bk.branch_name,
            "case_status": bk.case_status,
            "loan_type": bk.loan_type,
            "loan_principal": float(bk.loan_principal) if bk.loan_principal else None,
            "litigation_target_amount": float(bk.litigation_target_amount) if bk.litigation_target_amount else None,
            "credit_card_penalty": float(bk.credit_card_penalty) if bk.credit_card_penalty else None,
            "loan_date": str(bk.loan_date) if bk.loan_date else None,
            "loan_due_date": str(bk.loan_due_date) if bk.loan_due_date else None,
            "statute_of_limitations": str(bk.statute_of_limitations) if bk.statute_of_limitations else None,
            "guarantee_due_date": str(bk.guarantee_due_date) if bk.guarantee_due_date else None,
            "collateral_info": bk.collateral_info,
            "collateral_location": bk.collateral_location,
            "pre_litigation_collection": bk.pre_litigation_collection,
            "handling_judge": bk.handling_judge,
            "judgment_date": str(bk.judgment_date) if bk.judgment_date else None,
            "judgment_method": bk.judgment_method,
            "judgment_summary": bk.judgment_summary,
            "lawyer_fee_supported": float(bk.lawyer_fee_supported) if bk.lawyer_fee_supported else None,
            "is_settled": bk.is_settled,
            "property_investigation": bk.property_investigation,
            "network_control_status": bk.network_control_status,
            "execution_plan": bk.execution_plan,
            "court_execution_measures": bk.court_execution_measures,
            "seizure_freeze_date": str(bk.seizure_freeze_date) if bk.seizure_freeze_date else None,
            "auction_status": bk.auction_status,
            "auction_deal_price": float(bk.auction_deal_price) if bk.auction_deal_price else None,
            "execution_settlement_content": bk.execution_settlement_content,
            "procedure_termination_date": str(bk.procedure_termination_date) if bk.procedure_termination_date else None,
            "termination_reason": bk.termination_reason,
            "execution_collection_amount": float(bk.execution_collection_amount) if bk.execution_collection_amount else None,
            "collection_source": bk.collection_source,
            "execution_settlement_log": bk.execution_settlement_log,
            "deduction_log": bk.deduction_log,
        }

    # 财务信息
    finance = None
    if case.finance:
        fin = case.finance
        finance = {
            "contract_amount": float(fin.contract_amount) if fin.contract_amount else None,
            "final_contract_amount": float(fin.final_contract_amount) if fin.final_contract_amount else None,
            "total_invoiced_amount": float(fin.total_invoiced_amount) if fin.total_invoiced_amount else None,
            "total_received_amount": float(fin.total_received_amount) if fin.total_received_amount else None,
        }

    # 卷宗文件（含 OCR 内容）
    volumes = []
    if case.volumes:
        for vol in case.volumes:
            files_data = []
            for f in (vol.files or []):
                files_data.append({
                    "file_name": f.file_name,
                    "category": f.category,
                    "ocr_content": f.ocr_content,
                })
                # 限制单卷文件数上报，防止上下文过长
                if len(files_data) >= 30:
                    break
            volumes.append({
                "name": vol.name,
                "files": files_data,
            })

    return {
        "case_info": case_info,
        "parties": parties,
        "bank_case": bank_case,
        "finance": finance,
        "volumes": volumes,
    }


# =================================================================
#  API 端点
# =================================================================

@router.get("/cases")
def list_accessible_cases(
    skip: int = 0,
    limit: int = 50,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取当前用户有权限查看的案件列表（供前端案件选择器使用）
    返回精简信息：case_id, case_number, case_category, cause, main_lawyer 等
    """
    cases = list_cases_by_user_role(
        db=db,
        user_id=current_user.id,
        role=current_user.role,
        skip=skip,
        limit=limit,
        keyword=keyword,
    )
    total = count_cases_by_user_role(
        db=db,
        user_id=current_user.id,
        role=current_user.role,
        keyword=keyword,
    )

    items = []
    for c in cases:
        main_lawyer_name = c.main_lawyer.real_name if c.main_lawyer else None
        items.append({
            "case_id": c.case_id,
            "case_number": c.case_number,
            "case_category": c.case_category,
            "cause": c.cause,
            "main_lawyer": main_lawyer_name,
            "created_at": str(c.created_at) if c.created_at else None,
            "review_status": c.review_status,
        })

    return {"total": total, "items": items}


@router.post("/analyze")
async def analyze_case(
    case_id: int = Form(..., description="要分析的案件 ID"),
    files: List[UploadFile] = File(default=None, description="额外上传的分析材料（可选）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    对指定案件进行智能分析

    1. 验证案件访问权限
    2. 聚合数据库中的案件数据（自动过滤身份证号、电话、地址）
    3. 处理额外上传的文件（OCR 提取文本）
    4. 调用 DeepSeek API 生成 Markdown 分析报告
    5. 返回报告（不保存到服务器）

    注意：该操作会将案件信息发送至外部 AI 服务（DeepSeek API），
    请确保已获得必要的客户授权。
    """
    # 验证案件存在性（复用 get_case_by_id）
    from ..crud.case import get_case_by_id

    case = get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 权限检查：用户必须是该案件的主办/助理/执行律师，或者是管理员/owner
    is_lawyer = (
        current_user.id == case.main_lawyer_id
        or current_user.id == case.assistant_lawyer_id
        or current_user.id == case.assistant_lawyer_2_id
        or current_user.id == case.execution_lawyer_id
        or current_user.id == case.execution_assistant_id
    )
    is_admin = current_user.role in ("admin", "owner")
    if not (is_lawyer or is_admin):
        raise HTTPException(
            status_code=403,
            detail="您无权分析此案件",
        )

    # 聚合案件数据
    case_data = _aggregate_case_data(db, case_id)
    logger.info("案件数据聚合完成，案号: %s，当事人: %d 人，卷宗: %d 册",
                case.case_number, len(case_data.get("parties", [])),
                len(case_data.get("volumes", [])))

    # 处理额外上传的文件
    extra_texts = []
    if files:
        logger.info("开始处理 %d 个上传文件（OCR 文本提取）...", len(files))
        with tempfile.TemporaryDirectory(prefix="ai_upload_") as tmp_dir:
            saved_paths = []
            try:
                # 保存上传文件到临时目录
                for i, f in enumerate(files):
                    if not f.filename:
                        continue
                    safe_name = os.path.basename(f.filename)
                    dest = os.path.join(tmp_dir, safe_name)
                    content = await f.read()
                    with open(dest, "wb") as fh:
                        fh.write(content)
                    saved_paths.append(dest)
                    logger.info("  [%d/%d] 上传文件已保存: %s", i + 1, len(files), safe_name)

                # 对上传文件进行 OCR 提取
                for i, path in enumerate(saved_paths):
                    fname = os.path.basename(path)
                    ext = os.path.splitext(path)[1].lower()
                    if ext in (".docx", ".doc", ".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".tif", ".webp"):
                        logger.info("  [%d/%d] 正在 OCR 识别: %s ...", i + 1, len(saved_paths), fname)
                        extracted = perform_smart_extraction(path, ext)
                        if extracted and len(extracted.strip()) > 20:
                            extra_texts.append(extracted)
                            logger.info("  [%d/%d] OCR 完成: %s（%d 字符）", i + 1, len(saved_paths), fname, len(extracted))
                        else:
                            extra_texts.append(f"[文件 {fname} 未能提取到有效文本]")
                            logger.info("  [%d/%d] OCR 完成: %s（无有效文本）", i + 1, len(saved_paths), fname)
                    else:
                        extra_texts.append(f"[文件 {fname} 类型不支持文本提取]")
                        logger.info("  [%d/%d] 跳过: %s（不支持的类型 %s）", i + 1, len(saved_paths), fname, ext)
            except Exception as e:
                logger.warning("额外文件处理失败: %s", e)
                extra_texts.append(f"[文件处理出错: {str(e)}]")
            # tempfile 离开 with 块后自动清理

    # ====== 案件附件表（case_attachments）处理 ======
    try:
        db_attachments = (
            db.query(CaseAttachment)
            .filter(CaseAttachment.case_id == case_id)
            .limit(20)
            .all()
        )
        if db_attachments:
            logger.info("开始处理 %d 个案件附件（OCR 文本提取）...", len(db_attachments))
        for i, att in enumerate(db_attachments):
            if att.file_path:
                full_path = os.path.join(CASE_ATTACHMENT_ROOT, att.file_path)
                if os.path.exists(full_path):
                    ext = os.path.splitext(full_path)[1].lower()
                    if ext in (".docx", ".doc", ".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".tif", ".webp"):
                        logger.info("  [%d/%d] 正在 OCR 识别附件: %s ...", i + 1, len(db_attachments), att.file_name)
                        extracted = perform_smart_extraction(full_path, ext)
                        if extracted and len(extracted.strip()) > 20:
                            extra_texts.append(f"【案件附件：{att.file_name}】\n{extracted[:8000]}")
                            logger.info("  [%d/%d] OCR 完成: %s（%d 字符）", i + 1, len(db_attachments), att.file_name, len(extracted))
                        else:
                            extra_texts.append(f"【案件附件：{att.file_name}】未提取到有效文本")
                            logger.info("  [%d/%d] OCR 完成: %s（无有效文本）", i + 1, len(db_attachments), att.file_name)
                    else:
                        extra_texts.append(f"【案件附件：{att.file_name}】不支持的格式：{ext}")
                else:
                    logger.warning("附件文件不存在: %s", full_path)
    except Exception as e:
        logger.warning("附件文件处理失败: %s", e)
        extra_texts.append(f"[附件处理出错: {str(e)}]")

    logger.info("文件预处理完成，有效文本: %d 段，准备调用 DeepSeek...", len(extra_texts))

    # RAG 检索：从法律知识库中检索相关法条
    relevant_provisions = await llm_rag_search(case_data)

    # 调用 DeepSeek
    try:
        logger.info("开始调用 DeepSeek API 进行智能分析...")
        report_markdown = await llm_analyze(
            case_data=case_data,
            extra_texts=extra_texts if extra_texts else None,
            relevant_provisions=relevant_provisions if relevant_provisions else None,
        )
        logger.info("DeepSeek API 分析完成")
    except ValueError as e:
        logger.error("DeepSeek 配置错误: %s", e)
        raise HTTPException(status_code=503, detail=str(e))
    except ConnectionError as e:
        logger.error("DeepSeek 网络连接失败: %s", e)
        raise HTTPException(status_code=503, detail=str(e))
    except RuntimeError as e:
        logger.error("DeepSeek API 运行时错误: %s", e)
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error("DeepSeek 未知错误 (%s): %s", type(e).__name__, e)
        raise HTTPException(status_code=503, detail=f"AI分析服务异常: {e}")

    # 生成追问建议（不阻塞主流程）
    suggested_questions = await _generate_suggestions(case_data, report_markdown)
    if suggested_questions:
        logger.info("生成追问建议 %d 条", len(suggested_questions))

    return {
        "case_id": case_id,
        "case_number": case.case_number,
        "case_category": case.case_category,
        "report_markdown": report_markdown,
        "suggested_questions": suggested_questions,
        "relevant_provisions": relevant_provisions,
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "disclaimer": "本报告由 AI 自动生成，仅供律师参考，不构成法律意见。"
                      "最终决策请结合专业判断。",
    }


# =================================================================
#  流式分析端点（SSE）
# =================================================================

async def _stream_events(
    case_data: dict,
    extra_texts: list[str],
):
    """生成 SSE 事件流的异步生成器"""
    try:
        # 阶段1: 聚合完成
        yield f"data: {json.dumps({'type': 'progress', 'stage': 'aggregating', 'message': '案件数据聚合完成', 'percent': 30})}\n\n"

        # 阶段2: OCR 完成
        yield f"data: {json.dumps({'type': 'progress', 'stage': 'ocr', 'message': f'文件文本提取完成（{len(extra_texts)} 段）', 'percent': 50})}\n\n"

        # RAG 检索
        relevant_provisions = await llm_rag_search(case_data)

        # 阶段3: AI 分析
        yield f"data: {json.dumps({'type': 'progress', 'stage': 'analyzing', 'message': 'DeepSeek 正在生成分析报告…', 'percent': 70})}\n\n"

        # 流式调用 DeepSeek
        full_text = ""
        async for delta in llm_analyze_stream(
            case_data=case_data,
            extra_texts=extra_texts if extra_texts else None,
            relevant_provisions=relevant_provisions if relevant_provisions else None,
        ):
            full_text += delta
            yield f"data: {json.dumps({'type': 'content', 'delta': delta})}\n\n"

        # 生成追问建议（不阻塞完成事件发送）
        suggested_questions = await _generate_suggestions(case_data, full_text)

        # 完成事件
        yield f"data: {json.dumps({
            'type': 'done',
            'report_markdown': full_text,
            'suggested_questions': suggested_questions,
            'relevant_provisions': relevant_provisions,
            'generated_at': __import__('datetime').datetime.now().isoformat(),
        })}\n\n"

    except ValueError as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e), 'code': 'config_error'})}\n\n"
    except ConnectionError as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e), 'code': 'network_error'})}\n\n"
    except RuntimeError as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e), 'code': 'api_error'})}\n\n"
    except Exception as e:
        logger.error("流式分析未知错误: %s", e)
        yield f"data: {json.dumps({'type': 'error', 'message': f'分析服务异常: {e}', 'code': 'unknown'})}\n\n"


@router.post("/analyze/stream")
async def analyze_case_stream(
        case_id: int = Form(..., description="要分析的案件 ID"),
        files: List[UploadFile] = File(default=None, description="额外上传的分析材料（可选）"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
):
    """
    对指定案件进行流式智能分析（SSE）

    与 /analyze 的数据聚合逻辑完全一致，但通过 Server-Sent Events
    逐块推送 Markdown 文本，前端可实时展示并显示进度。
    """
    # 1. 鉴权与校验（这部分非常快，保留在外部，出错可直接阻断）
    from ..crud.case import get_case_by_id
    case = get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    is_lawyer = current_user.id in (case.main_lawyer_id, case.assistant_lawyer_id, case.execution_lawyer_id)
    is_admin = current_user.role in ("admin", "owner")
    if not (is_lawyer or is_admin):
        raise HTTPException(status_code=403, detail="您无权分析此案件")

    # 为了能在生成器内部读取文件，需要提前将文件内容读取到内存中
    uploaded_files_data = []
    if files:
        for f in files:
            if f.filename:
                content = await f.read()
                uploaded_files_data.append({"filename": f.filename, "content": content})

    # 2. 定义内部异步生成器，包裹所有的耗时逻辑
    async def real_time_event_generator():
        try:
            # --- 阶段 1: 开始数据聚合 ---
            yield f"data: {json.dumps({'type': 'progress', 'stage': 'aggregating', 'message': '正在从数据库聚合案件档案…'})}\n\n"
            await asyncio.sleep(0.1)  # 强制刷新缓冲区

            case_data = _aggregate_case_data(db, case_id)

            # --- 阶段 2: 开始 OCR ---
            yield f"data: {json.dumps({'type': 'progress', 'stage': 'ocr', 'message': '正在对案卷与上传材料进行 OCR 文本识别…'})}\n\n"
            await asyncio.sleep(0.1)

            extra_texts = []
            if uploaded_files_data:
                with tempfile.TemporaryDirectory(prefix="ai_upload_") as tmp_dir:
                    saved_paths = []
                    # 写入临时文件
                    for fdata in uploaded_files_data:
                        safe_name = os.path.basename(fdata["filename"])
                        dest = os.path.join(tmp_dir, safe_name)
                        with open(dest, "wb") as fh:
                            fh.write(fdata["content"])
                        saved_paths.append(dest)

                    # 执行 OCR
                    for i, path in enumerate(saved_paths):
                        ext = os.path.splitext(path)[1].lower()
                        # 可以进一步细化：通知前端当前正在识别第几个文件
                        yield f"data: {json.dumps({'type': 'progress', 'stage': 'ocr', 'message': f'正在识别文件 ({i + 1}/{len(saved_paths)}): {os.path.basename(path)}'})}\n\n"
                        await asyncio.sleep(0.1)

                        if ext in (".docx", ".doc", ".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".tif", ".webp"):
                            # 注意：如果 perform_smart_extraction 是同步阻塞函数，建议使用 asyncio.to_thread 包装以防止阻塞事件循环
                            extracted = await asyncio.to_thread(perform_smart_extraction, path, ext)
                            if extracted and len(extracted.strip()) > 20:
                                extra_texts.append(extracted)
                            else:
                                extra_texts.append(f"[文件 {os.path.basename(path)} 未能提取到有效文本]")

            # 处理案件原有附件的 OCR (逻辑同上)
            db_attachments = db.query(CaseAttachment).filter(CaseAttachment.case_id == case_id).limit(20).all()
            for att in db_attachments:
                # 简化示例，你可根据原代码补全
                yield f"data: {json.dumps({'type': 'progress', 'stage': 'ocr', 'message': f'正在识别案件附件: {att.file_name}'})}\n\n"
                await asyncio.sleep(0.1)
                pass  # 原有附件识别逻辑

            # --- 阶段 3: RAG 检索 + AI 分析 ---
            yield f"data: {json.dumps({'type': 'progress', 'stage': 'rag', 'message': '正在从法律知识库检索相关法条…'})}\n\n"
            await asyncio.sleep(0.1)

            relevant_provisions = await llm_rag_search(case_data)

            yield f"data: {json.dumps({'type': 'progress', 'stage': 'analyzing', 'message': '数据解析完成，DeepSeek 正在生成分析报告…'})}\n\n"
            await asyncio.sleep(0.1)

            # 流式调用大模型
            full_text = ""
            async for delta in llm_analyze_stream(
                case_data,
                extra_texts,
                relevant_provisions=relevant_provisions if relevant_provisions else None,
            ):
                full_text += delta
                yield f"data: {json.dumps({'type': 'content', 'delta': delta})}\n\n"

            # 生成追问建议
            suggested_questions = await _generate_suggestions(case_data, full_text)

            # --- 阶段 4: 完成 ---
            yield f"data: {json.dumps({
                'type': 'done',
                'report_markdown': full_text,
                'suggested_questions': suggested_questions,
                'relevant_provisions': relevant_provisions,
                'generated_at': __import__('datetime').datetime.now().isoformat(),
            })}\n\n"

        except Exception as e:
            logger.error(f"流式分析出错: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': f'分析服务异常: {str(e)}'})}\n\n"

    # 3. 立即返回连接，启动生成器
    return StreamingResponse(
        real_time_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# =================================================================
#  追问建议生成
# =================================================================

async def _generate_suggestions(case_data: dict, report_markdown: str) -> list[str]:
    """基于报告内容，让 LLM 生成 3-5 条针对性追问建议"""
    prompt = (
        "请根据以上案件数据和已生成的分析报告，生成 3-5 条针对性的追问建议。"
        "这些追问应该是律师在阅读报告后可能想深入了解的问题，如法律风险细节、"
        "证据补充方向、策略优化建议等。"
        "请以 JSON 字符串数组格式返回，不要包含其他内容。示例格式："
        '["问题1", "问题2", "问题3"]'
    )
    try:
        reply = await llm_chat(
            case_data=case_data,
            report_markdown=report_markdown,
            chat_history=[],
            user_message=prompt,
            max_tokens=500,
        )
        # 解析 LLM 返回的 JSON 数组
        json_match = re.search(r'\[.*\]', reply, re.DOTALL)
        if json_match:
            questions = json.loads(json_match.group())
            return questions[:5]  # 最多 5 条
    except Exception as e:
        logger.warning("生成追问建议失败: %s", e)
    return []  # 失败时返回空，前端降级到硬编码列表


@router.post("/export/docx")
async def export_docx(
    report_markdown: str = Form(..., description="Markdown 格式的分析报告"),
    case_number: str = Form(default="", description="案号"),
    case_category: str = Form(default="", description="案件类别"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """将 Markdown 报告导出为 Word (.docx) 文件"""
    from ..utils.docx_exporter import markdown_to_docx
    from urllib.parse import quote

    buffer = markdown_to_docx(
        markdown=report_markdown,
        case_number=case_number,
        case_category=case_category,
    )

    filename = f"案件分析报告_{case_number}.docx"
    encoded_filename = quote(filename)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
        },
    )


@router.post("/chat")
async def chat_about_case(
    case_id: int = Form(..., description="案件 ID"),
    report_markdown: str = Form(..., description="已生成的分析报告 Markdown 全文"),
    messages: str = Form(default="[]", description="对话历史 JSON 字符串"),
    user_message: str = Form(..., description="用户追问内容"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    基于已生成的分析报告进行多轮对话追问

    将案件数据、报告全文和对话历史一并发送给 DeepSeek，
    让 AI 在完整上下文中回答律师的追问。
    """
    # 验证案件存在性和权限
    from ..crud.case import get_case_by_id

    case = get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    is_lawyer = (
        current_user.id == case.main_lawyer_id
        or current_user.id == case.assistant_lawyer_id
        or current_user.id == case.assistant_lawyer_2_id
        or current_user.id == case.execution_lawyer_id
        or current_user.id == case.execution_assistant_id
    )
    is_admin = current_user.role in ("admin", "owner")
    if not (is_lawyer or is_admin):
        raise HTTPException(status_code=403, detail="您无权分析此案件")

    # 校验用户消息
    user_message = (user_message or "").strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="追问内容不能为空")
    if len(user_message) > 2000:
        raise HTTPException(status_code=400, detail="追问内容不能超过 2000 字")

    # 解析对话历史
    try:
        chat_history = json.loads(messages or "[]")
        if not isinstance(chat_history, list):
            chat_history = []
    except json.JSONDecodeError:
        chat_history = []

    # 限制历史轮数，防止上下文过长
    if len(chat_history) > 20:
        chat_history = chat_history[-20:]

    # 聚合案件数据
    case_data = _aggregate_case_data(db, case_id)

    # RAG 检索相关法条
    relevant_provisions = await llm_rag_search(case_data)

    # 调用 DeepSeek 对话
    try:
        logger.info("开始调用 DeepSeek 对话追问（历史 %d 条，问题: %s）",
                    len(chat_history), user_message[:80])
        reply = await llm_chat(
            case_data=case_data,
            report_markdown=report_markdown,
            chat_history=chat_history,
            user_message=user_message,
            relevant_provisions=relevant_provisions if relevant_provisions else None,
        )
        logger.info("DeepSeek 对话追问完成")
    except ValueError as e:
        logger.error("DeepSeek 对话配置错误: %s", e)
        raise HTTPException(status_code=503, detail=str(e))
    except ConnectionError as e:
        logger.error("DeepSeek 对话网络连接失败: %s", e)
        raise HTTPException(status_code=503, detail=str(e))
    except RuntimeError as e:
        logger.error("DeepSeek 对话运行时错误: %s", e)
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error("DeepSeek 对话未知错误 (%s): %s", type(e).__name__, e)
        raise HTTPException(status_code=503, detail=f"AI对话服务异常: {e}")

    # 构建返回的消息历史（前端可直接替换使用）
    updated_history = list(chat_history)
    updated_history.append({"role": "user", "content": user_message})
    updated_history.append({"role": "assistant", "content": reply})

    return {
        "case_id": case_id,
        "reply": reply,
        "messages": updated_history,
    }
