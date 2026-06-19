from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Depends, status, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from docxtpl import DocxTemplate
from io import BytesIO
from urllib.parse import quote
import os
import uuid
import shutil
import mimetypes

from ..core.config import DOCUMENT_TEMPLATE_ROOT, settings
from ..crud.case import get_case_by_id
from ..crud.document import create_template, get_template_by_id, delete_template, get_templates, convert_word_to_pdf
from ..database.database import get_db
from ..models.document import DocumentTemplate
from ..schemas.document import TemplateCreate, TemplateOut
from ..utils.storage_manager import get_upload_credential, get_file_preview_url, get_file_download_url, cleanup_local_file

from .deps import get_current_active_user
from ..models.user import User

router = APIRouter(
    prefix="/template",
    tags=["template"]
)

# 模板文件目录
TEMPLATE_DIR = os.path.join("FastAPI", "static", "template")


def _template_word_convert_and_cleanup(save_path: str, cos_key: str):
    """
    后台任务：Word→PDF 转换 → 上传 PDF 到 COS 预览缓存 → 清理本地文件及空文件夹
    """
    try:
        pdf_path = convert_word_to_pdf(save_path)
        if pdf_path and settings.STORAGE_TYPE == "COS":
            from ..utils.storage_manager import _get_cos_client
            stem, _ = os.path.splitext(cos_key)
            pdf_cos_key = f"preview_cache/{stem}.pdf"
            _get_cos_client().upload_file(
                Bucket=settings.COS_BUCKET,
                Key=pdf_cos_key,
                LocalFilePath=pdf_path,
            )
        # 清理本地 Word 和临时 PDF
        if os.path.exists(save_path):
            cleanup_local_file(save_path, DOCUMENT_TEMPLATE_ROOT)
        if pdf_path and os.path.exists(pdf_path):
            cleanup_local_file(pdf_path, DOCUMENT_TEMPLATE_ROOT)
    except Exception as e:
        print(f"[TemplateWordConvert] 处理失败: {e}")


@router.get("/download")
async def download_template(
    filename: str = Query(..., description="要下载的文件名"),
    current_user: User = Depends(get_current_active_user)  # 增加鉴权，防止未登录用户下载
):
    """
    通用模板下载接口
    """
    file_path = os.path.join(TEMPLATE_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"文件 {filename} 不存在")

    # 自动识别 MIME 类型
    mime_type, _ = mimetypes.guess_type(file_path)
    mime_type = mime_type or "application/octet-stream"

    # 使用 FileResponse 返回文件流
    return FileResponse(
        file_path,
        filename=filename,
        media_type=mime_type
    )

@router.post("/document", status_code=status.HTTP_201_CREATED)
async def upload_document_template(
    name: str = Query(..., description="模板名称"),
    description: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None, description="模板文件（LOCAL 模式必填）"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    上传文书模板
    - COS 模式 + Word 文件：本地保存 → 上传 COS → 后台转 PDF 预览 → 清理本地
    - COS 模式 + 非 Word 文件：返回 STS 临时凭证供前端直传 COS
    - LOCAL 模式：接收二进制文件流，保存到本地磁盘
    """
    template_in = TemplateCreate(
        name=name,
        description=description,
        uploaded_by=current_user.id
    )

    if not file:
        raise HTTPException(400, "需要上传文件")

    file_name = file.filename or "unknown"

    if settings.STORAGE_TYPE == "COS":
        # 判断是否为 Word 文件（需要本地 LibreOffice 转换 PDF）
        is_word = file.content_type in [
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ] or file_name.lower().endswith(('.doc', '.docx'))

        now = datetime.now()
        path_prefix = f"templates/{now.year}/{now.month:02d}"

        if is_word:
            # === Word 文件：本地保存 → 上传 COS → 后台转换 PDF → 清理 ===
            unique_name = f"{uuid.uuid4().hex}{os.path.splitext(file_name)[1]}"
            relative_path = os.path.join("templates", str(now.year), f"{now.month:02d}", unique_name)
            save_path = os.path.join(DOCUMENT_TEMPLATE_ROOT, relative_path)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            file_size = os.path.getsize(save_path)
            cos_key = relative_path.replace("\\", "/")

            # 上传原始文件到 COS
            from ..utils.storage_manager import _get_cos_client
            _get_cos_client().upload_file(
                Bucket=settings.COS_BUCKET,
                Key=cos_key,
                LocalFilePath=save_path,
            )

            # 创建数据库记录
            db_template = DocumentTemplate(
                name=name,
                file_path=relative_path,
                cos_key=cos_key,
                file_type=file.content_type or "application/octet-stream",
                file_size=file_size,
                description=description,
                uploaded_by=current_user.id,
            )
            db.add(db_template)
            db.commit()
            db.refresh(db_template)

            # 后台转换 PDF → 上传 COS 预览缓存 → 清理本地
            background_tasks.add_task(
                _template_word_convert_and_cleanup,
                save_path=save_path,
                cos_key=cos_key,
            )

            return db_template

        else:
            # === 非 Word 文件：STS 前端直传 COS ===
            cred = get_upload_credential(file_name, path_prefix)
            db_template = DocumentTemplate(
                name=name,
                file_path=cred["key"],
                cos_key=cred["key"],
                file_type=file.content_type or "application/octet-stream",
                file_size=0,
                description=description,
                uploaded_by=current_user.id,
            )
            db.add(db_template)
            db.commit()
            db.refresh(db_template)

            return {
                "type": "COS",
                "credentials": cred["credentials"],
                "bucket": cred["bucket"],
                "region": cred["region"],
                "key": cred["key"],
                "template_id": db_template.id,
                "file_name": file_name,
            }

    # LOCAL 模式
    try:
        db_template = await create_template(
            db=db,
            template_in=template_in,
            file=file
        )

        # Word 文件后台生成 PDF
        if db_template.file_type in [
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]:
            full_path = os.path.join(DOCUMENT_TEMPLATE_ROOT, str(db_template.file_path))
            background_tasks.add_task(convert_word_to_pdf, full_path)

        return db_template
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/document", response_model=List[TemplateOut])
def list_document_templates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user) # 增加鉴权
):
    """获取所有文书模板列表（支持分页）"""
    return get_templates(db, skip=skip, limit=limit)

@router.get("/document/{template_id}", response_model=TemplateOut)
def get_document_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user) # 增加鉴权
):
    """根据ID获取文书模板详情"""
    template = get_template_by_id(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模板ID {template_id} 不存在"
        )
    return template

@router.patch("/document/{template_id}/size")
def update_template_size(
    template_id: int,
    file_size: int = Query(..., description="文件大小（KB）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """STS 上传完成后回写模板文件大小（KB）"""
    template = get_template_by_id(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    template.file_size = file_size
    db.commit()
    return {"ok": True}


@router.delete("/document/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_document_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除文书模板（同时删除文件和数据库记录）"""
    try:
        success = delete_template(db, template_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"模板ID {template_id} 不存在"
            )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/document/{template_id}/download")
def download_document_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """下载指定ID的文书模板文件"""
    template = get_template_by_id(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"模板ID {template_id} 不存在")

    result = get_file_download_url(template, root_dir=DOCUMENT_TEMPLATE_ROOT)
    if result["type"] == "ERROR":
        raise HTTPException(status_code=404, detail=result["message"])
    elif result["type"] == "COS":
        return RedirectResponse(url=result["url"])

    return FileResponse(
        path=result["file_path"],
        filename=template.name,
        media_type=template.file_type or "application/octet-stream"
    )

@router.get("/document/{template_id}/preview")
def preview_document_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """预览文书模板（图片/PDF/Word转PDF，支持LOCAL和COS双模式）"""
    template = get_template_by_id(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"模板ID {template_id} 不存在")

    result = get_file_preview_url(template, root_dir=DOCUMENT_TEMPLATE_ROOT)
    if result["type"] == "ERROR":
        raise HTTPException(status_code=404, detail=result["message"])
    elif result["type"] == "COS":
        return RedirectResponse(url=result["url"])

    # LOCAL 模式
    file_path = result["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="模板文件已丢失")

    is_word = template.file_type in [
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    if is_word:
        return FileResponse(path=file_path, media_type="application/pdf",
                            headers={"Content-Disposition": "inline"})

    supported_types = {
        "image/jpeg", "image/png", "image/gif", "image/bmp", "image/webp",
        "application/pdf"
    }
    if template.file_type not in supported_types:
        raise HTTPException(status_code=415, detail=f"不支持预览该类型文件: {template.file_type}")

    return FileResponse(path=file_path, media_type=template.file_type,
                        headers={"Content-Disposition": "inline"})


@router.post("/document/{template_id}/generate/{case_id}", summary="根据模板和案件自动生成文书")
async def generate_document_from_template(
        template_id: int,
        case_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    根据选择的 Word 模板和案件 ID，自动填充数据并生成文书下载
    - LOCAL 模式：直接读取本地模板文件
    - COS 模式：从 COS 下载模板到临时目录，处理完毕自动清理
    """
    import tempfile
    import shutil as shutil_mod

    # 1. 验证并获取模板
    template = get_template_by_id(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    if not template.file_type.startswith("application/vnd.openxmlformats") and "msword" not in template.file_type:
        raise HTTPException(status_code=400, detail="该模板不是 Word 文档，无法进行自动填充")

    # 获取模板文件（LOCAL 直接从磁盘，COS 下载到临时目录）
    _tmp_cleanup = None
    if settings.STORAGE_TYPE == "COS":
        from ..utils.storage_manager import _get_cos_client
        cos_client = _get_cos_client()
        cos_key = getattr(template, "cos_key", None) or template.file_path
        tmp_dir = tempfile.mkdtemp(prefix="template_gen_")
        _tmp_cleanup = tmp_dir
        full_template_path = os.path.join(tmp_dir, template.name or "template.docx")
        try:
            cos_client.download_file(
                Bucket=settings.COS_BUCKET, Key=cos_key, DestFilePath=full_template_path
            )
        except Exception as e:
            shutil_mod.rmtree(tmp_dir, ignore_errors=True)
            raise HTTPException(status_code=404, detail=f"模板文件下载失败: {e}")
    else:
        full_template_path = os.path.join(DOCUMENT_TEMPLATE_ROOT, template.file_path)
        if not os.path.exists(full_template_path):
            raise HTTPException(status_code=404, detail="模板实体文件丢失")

    # 2. 验证并获取案件数据
    case = get_case_by_id(db=db, case_id=case_id)
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 定义辅助函数：遍历 case.parties 列表，根据指定类型提取当事人名称，并用“、”拼接
    def get_party_names(party_type: str) -> str:
        if not case.parties:
            return ""
        # 过滤出符合类型的当事人名称列表
        names = [p.name for p in case.parties if p.party_type == party_type]
        # 使用顿号拼接多个当事人，如果列表为空则返回空字符串
        return "、".join(names)

    # 定义辅助函数：根据当事人类型，提取指定字段（如 phone, address）并用“、”拼接
    def get_party_attr(party_type: str, attr_name: str) -> str:
        if not case.parties:
            return ""
        # 过滤出符合类型的当事人，并提取指定的属性值（剔除空值或None）
        values = [
            getattr(p, attr_name) for p in case.parties
            if p.party_type == party_type and getattr(p, attr_name)
        ]
        return "、".join(values)

    # 日期处理逻辑
    now = datetime.now()  # 获取当前时间作为默认签订日期

    # 辅助函数：安全地将 Date 对象提取为年、月、日的字典
    def extract_date_parts(date_obj, prefix: str):
        if date_obj:
            return {
                f"{prefix}年": date_obj.year,
                f"{prefix}月": f"{date_obj.month:02d}",  # 格式化为两位数，例如 05
                f"{prefix}日": f"{date_obj.day:02d}"
            }
        else:
            # 如果数据库中没有填写该日期，则返回空格以便打印后手写
            return {
                f"{prefix}年": "    ",
                f"{prefix}月": "  ",
                f"{prefix}日": "  "
            }

    # 3. 组装占位符映射字典 (Context)
    # 这里的键对应 Word 里可用的 {{ 变量名 }}
    context = {
        # 基础案件信息
        "业务号": case.case_number or "",
        "法院": case.court or "",
        "案由": case.cause or "",
        "主办律师": case.main_lawyer.real_name if case.main_lawyer else "",
        "委托日期": case.commission_date.strftime("%Y年%m月%d日") if case.commission_date else "",
        "开庭时间": case.hearing_date.strftime("%Y年%m月%d日") if case.hearing_date else "",
        "结案时间": case.closing_date.strftime("%Y年%m月%d日") if case.closing_date else "",
        "业务收入":case.case_income or "0.00",
        "法院案号": case.case_code or "",
        "介入阶段": case.stage or "",
        "案件详情": case.details or "",

        # 动态提取当事人信息（完全依赖 CaseParty 表）
        "委托人": get_party_names("委托人"),
        "委托人电话":get_party_attr("委托人", "phone"),
        "委托人地址": get_party_attr("委托人", "address"),
        "原告": get_party_names("原告"),
        "被告": get_party_names("被告"),
        "被告人": get_party_names("被告人"),
        "第三人": get_party_names("第三人"),

        # --- 注入当前时间）---
        "导出日期年": now.year,
        "导出日期月": f"{now.month:02d}",
        "导出日期日": f"{now.day:02d}",
    }

    # --- 注入日期 ---
    context.update(extract_date_parts(case.commission_date, "委托日期"))
    context.update(extract_date_parts(case.advisory_due_date, "顾问到期"))

    # 如果是银行案件，追加银行专属字段
    if case.case_category == "银行案件" and case.bank_case_details:
        bank = case.bank_case_details
        context.update({
            "loan_principal": str(bank.loan_principal) if bank.loan_principal else "0", # 贷款本金
            "loan_account": bank.loan_account or "",                                    # 贷款账号
            "branch_name": bank.branch_name or "",                                      # 支行名称
            "handling_judge": bank.handling_judge or ""
        })

    # 4. 渲染 Word 文档
    try:
        doc = DocxTemplate(full_template_path)
        doc.render(context)

        # 将生成的 Word 保存在内存中（不落盘，直接传给前端）
        file_stream = BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)

        # 5. 构造安全的下载文件名
        safe_template_name = os.path.splitext(template.name)[0]
        # 如果没有提取到业务号，给一个默认前缀防止文件名出错
        prefix_name = context['业务号'] if context['业务号'] else "未命名案件"
        download_filename = f"{prefix_name}-{safe_template_name}.docx"
        encoded_filename = quote(download_filename)

        return StreamingResponse(
            file_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"文书生成失败: {str(e)}")
    finally:
        # COS 模式：清理临时下载的模板文件
        if _tmp_cleanup:
            shutil_mod.rmtree(_tmp_cleanup, ignore_errors=True)