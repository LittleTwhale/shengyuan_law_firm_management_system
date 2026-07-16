"""
起诉状要素提取 API 路由
接收用户上传的民事起诉状文件（PDF/Word/图片），通过 OCR + DeepSeek v4-pro
提取关键字段，返回结构化 JSON 供前端填充到要素式模板中。
"""
import asyncio
import logging
import os
import tempfile
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..models.user import User
from ..api.deps import get_current_active_user
from ..utils.ocr_helper import perform_smart_extraction
from ..utils.complaint_extractor import extract_complaint_fields

logger = logging.getLogger("shengyuan_app.complaint_form_api")

router = APIRouter(
    prefix="/complaint-form",
    tags=["complaint_form"],
)

# 支持的文件扩展名
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".jpg", ".jpeg", ".png", ".bmp", ".tif", ".webp"}

# 单文件最大大小（30MB）
MAX_FILE_SIZE = 30 * 1024 * 1024

# 合并后的 OCR 文本最大长度（避免 prompt 过长，deepseek 上下文足够大但也要控制成本）
MAX_OCR_TEXT_LENGTH = 30000


@router.post("/extract")
async def extract_complaint_form_fields(
    files: List[UploadFile] = File(..., description="民事起诉状文件（PDF/Word/图片）"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    上传民事起诉状文件，通过 OCR + DeepSeek 提取要素字段

    流程：
    1. 接收并校验上传文件
    2. 保存到临时目录
    3. 对每个文件执行 OCR 文本提取
    4. 合并所有 OCR 文本
    5. 调用 DeepSeek 提取结构化字段
    6. 返回 JSON 字段数据

    Returns:
        {
            "success": true,
            "fields": { ... JSON 字段数据 ... },
            "ocr_length": 12345,
            "file_count": 2,
            "disclaimer": "本结果由 AI 自动生成，请仔细核对后使用"
        }
    """
    # ── 1. 基础校验 ──
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请至少上传一个文件",
        )

    # ── 2. 文件类型和大小校验 ──
    for f in files:
        if not f.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件名不能为空",
            )

        ext = os.path.splitext(f.filename)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件格式: {ext}，支持的格式: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
            )

        # 读取文件内容以检查大小（不阻塞地读入内存）
        content = await f.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件 {f.filename} 超过最大限制 30MB",
            )
        # 重置文件指针，后续保存时还需要读取
        await f.seek(0)

    logger.info(
        "用户 %s 上传 %d 个文件进行起诉状提取",
        current_user.real_name or current_user.accounts,
        len(files),
    )

    # ── 3. 保存文件到临时目录并执行 OCR ──
    ocr_texts: List[str] = []

    try:
        with tempfile.TemporaryDirectory(prefix="complaint_form_") as tmp_dir:
            for f in files:
                ext = os.path.splitext(f.filename)[1].lower()
                # 构建临时文件路径
                safe_name = f.filename.replace("/", "_").replace("\\", "_")
                tmp_path = os.path.join(tmp_dir, safe_name)

                # 写入临时文件
                content = await f.read()
                with open(tmp_path, "wb") as tmp_file:
                    tmp_file.write(content)

                logger.info("文件已保存: %s (%d 字节)", safe_name, len(content))

                # 执行 OCR 提取（使用 asyncio.to_thread 避免阻塞事件循环）
                try:
                    extracted = await asyncio.to_thread(
                        perform_smart_extraction, tmp_path, ext
                    )
                except Exception as ocr_err:
                    logger.error("OCR 提取失败（文件: %s）: %s", safe_name, ocr_err)
                    extracted = f"[OCR 提取失败: {str(ocr_err)}]"

                if extracted and len(extracted.strip()) > 10:
                    ocr_texts.append(
                        f"=== 文件: {f.filename} ===\n{extracted.strip()}"
                    )
                else:
                    logger.warning("文件 %s OCR 结果为空或过短", safe_name)
                    ocr_texts.append(
                        f"=== 文件: {f.filename} ===\n[未识别到有效文本内容]"
                    )

        # tempfile 离开 with 块后自动清理
    except HTTPException:
        raise
    except Exception as e:
        logger.error("文件处理异常: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件处理失败: {str(e)}",
        )

    # ── 4. 合并 OCR 文本 ──
    combined_text = "\n\n".join(ocr_texts)

    if len(combined_text) < 20:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="未能从上传的文件中提取到足够文本内容，请检查文件是否为扫描件或图片格式",
        )

    # 截断过长的文本（控制 token 消耗）
    if len(combined_text) > MAX_OCR_TEXT_LENGTH:
        logger.info(
            "OCR 文本过长（%d 字符），截断至 %d 字符",
            len(combined_text),
            MAX_OCR_TEXT_LENGTH,
        )
        combined_text = combined_text[:MAX_OCR_TEXT_LENGTH]

    logger.info(
        "OCR 提取完成，共 %d 个文件，合并文本 %d 字符",
        len(files),
        len(combined_text),
    )

    # ── 5. 调用 DeepSeek v4-pro 提取字段 ──
    try:
        fields = await extract_complaint_fields(combined_text)
    except ValueError as e:
        # API Key 未配置等配置错误
        logger.error("提取器配置错误: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 提取服务配置错误: {str(e)}",
        )
    except ConnectionError as e:
        # 网络连接错误
        logger.error("DeepSeek API 连接失败: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"无法连接到 AI 服务，请检查网络后重试",
        )
    except RuntimeError as e:
        # API 调用或 JSON 解析失败
        logger.error("DeepSeek API 调用失败: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI 服务调用失败: {str(e)}",
        )
    except Exception as e:
        logger.error("起诉状提取未知错误: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"起诉状提取失败，请稍后重试",
        )

    # ── 6. 返回结果 ──
    return {
        "success": True,
        "fields": fields,
        "ocr_length": len(combined_text),
        "file_count": len(files),
        "disclaimer": "本结果由 AI 自动生成，请仔细核对所有字段后再导出 PDF。未识别字段已留空。",
    }
