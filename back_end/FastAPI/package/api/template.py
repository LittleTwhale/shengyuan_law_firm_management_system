from fastapi import APIRouter, HTTPException, Query, Depends, status, UploadFile, File, Form
from fastapi.responses import FileResponse,StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from docxtpl import DocxTemplate
from io import BytesIO
from urllib.parse import quote
import os
import mimetypes

from ..core.config import DOCUMENT_TEMPLATE_ROOT
from ..crud.case import get_case_by_id
from ..crud.document import create_template, get_template_by_id, delete_template, get_templates
from ..database.database import get_db
from ..schemas.document import TemplateCreate, TemplateOut

from .deps import get_current_active_user
from ..models.user import User

router = APIRouter(
    prefix="/template",
    tags=["template"]
)

# 模板文件目录
TEMPLATE_DIR = os.path.join("FastAPI", "static", "template")

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

@router.post("/document", response_model=TemplateOut, status_code=status.HTTP_201_CREATED)
async def upload_document_template(
    name: str = Query(..., description="模板名称"),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user) # 注入当前用户
):
    """上传文书模板（保存到 根目录/当前年份/文件名）"""
    template_in = TemplateCreate(
        name=name,
        description=description,
        uploaded_by=current_user.id
    )

    try:
        db_template = await create_template(
            db=db,
            template_in=template_in,
            file=file
        )
        # 检查是否为Word文件，若是则触发PDF转换
        if db_template.file_type in [
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]:
            # 构建Word文件的完整路径
            full_path = os.path.join(DOCUMENT_TEMPLATE_ROOT, str(db_template.file_path))

            # 异步执行转换（不阻塞当前请求）
            import threading
            from ..crud.document import convert_word_to_pdf
            threading.Thread(
                target=convert_word_to_pdf,
                args=(full_path,),
                daemon=True  # 随主线程退出而终止
            ).start()

        return db_template
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

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
    current_user: User = Depends(get_current_active_user) # 增加鉴权
):
    """下载指定ID的文书模板文件"""
    template = get_template_by_id(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模板ID {template_id} 不存在"
        )

    full_path = os.path.join(DOCUMENT_TEMPLATE_ROOT, template.file_path)
    if not os.path.exists(full_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板文件已丢失"
        )

    return FileResponse(
        path=full_path,
        filename=template.name,
        media_type=template.file_type or "application/octet-stream"
    )

@router.get("/document/{template_id}/preview")
def preview_document_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user) # 增加鉴权
):
    """预览文书模板（支持图片、PDF和Word转换）"""
    template = get_template_by_id(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模板ID {template_id} 不存在"
        )

    full_path = os.path.join(DOCUMENT_TEMPLATE_ROOT, template.file_path)
    if not os.path.exists(full_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板文件已丢失"
        )

    # 支持直接预览的类型
    supported_types = {
        "image/jpeg", "image/png", "image/gif", "image/bmp", "image/webp",
        "application/pdf"
    }

    # Word文件处理（转换为PDF预览）
    if template.file_type in [
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]:
        from ..crud.document import convert_word_to_pdf
        pdf_path = convert_word_to_pdf(full_path)
        if pdf_path:
            return FileResponse(
                path=pdf_path,
                media_type="application/pdf",
                headers={"Content-Disposition": "inline"}  # 设置为内联显示
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Word文档转换预览格式失败，请下载查看"
            )

    if template.file_type not in supported_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"不支持预览该类型文件: {template.file_type}"
        )

    return FileResponse(
        path=full_path,
        media_type=template.file_type,
        headers={"Content-Disposition": "inline"}  # 设置为内联显示
    )


@router.post("/document/{template_id}/generate/{case_id}", summary="根据模板和案件自动生成文书")
async def generate_document_from_template(
        template_id: int,
        case_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    根据选择的 Word 模板和案件 ID，自动填充数据并生成文书下载
    """
    # 1. 验证并获取模板
    template = get_template_by_id(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    if not template.file_type.startswith("application/vnd.openxmlformats") and "msword" not in template.file_type:
        raise HTTPException(status_code=400, detail="该模板不是 Word 文档，无法进行自动填充")

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
        "业务收入":case.case_income or "0.00",
        "法院案号": case.case_code or "",  # 法院案号

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