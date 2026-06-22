"""
存储抽象层 — 统一管理文件上传凭证和预览 URL 生成
支持 LOCAL（本地文件系统）和 COS（腾讯云对象存储）两种模式

使用方式:
    from ..utils.storage_manager import get_upload_credential, get_file_preview_url

    # 获取上传凭证
    cred = get_upload_credential("报告.docx", "case_42/vol_1")

    # 获取预览 URL
    result = get_file_preview_url(file_record, root_dir=CASE_ATTACHMENT_ROOT)
    if result["type"] == "LOCAL":
        return FileResponse(path=result["file_path"], media_type="application/pdf")
    elif result["type"] == "COS":
        return RedirectResponse(url=result["url"])
"""

import os
import subprocess
import tempfile
import shutil
from typing import Any, Dict, Optional

from ..core.config import settings

# ============================================================
# LibreOffice 可执行文件路径
# ============================================================
LIBREOFFICE_PATH = r"C:\Program Files\LibreOffice\program\soffice.exe"

# ============================================================
# COS 客户端（单例懒加载）
# ============================================================
_cos_client: Any = None


def _get_cos_client():
    """获取 COS SDK 客户端（全局单例，首次调用时初始化）"""
    global _cos_client
    if _cos_client is not None:
        return _cos_client

    try:
        from qcloud_cos import CosConfig, CosS3Client
    except ImportError:
        raise ImportError(
            "缺少腾讯云 COS SDK，请执行: pip install cos-python-sdk-v5"
        )

    if not settings.COS_SECRET_ID or not settings.COS_SECRET_KEY:
        raise ValueError("COS_SECRET_ID 和 COS_SECRET_KEY 未配置")

    config = CosConfig(
        Region=settings.COS_REGION,
        SecretId=settings.COS_SECRET_ID,
        SecretKey=settings.COS_SECRET_KEY,
    )
    _cos_client = CosS3Client(config)
    return _cos_client


# ============================================================
# 内部工具：Word → PDF 转换（封装 LibreOffice 调用）
# ============================================================

def _convert_word_to_pdf(input_path: str) -> Optional[str]:
    """
    调用本地 LibreOffice 将 Word 文档转为 PDF
    Args:
        input_path: .doc / .docx 文件绝对路径
    Returns:
        转换后的 PDF 绝对路径，若无需转换或失败则返回 None
    """
    if not input_path.lower().endswith(('.doc', '.docx')):
        return None

    name, _ = os.path.splitext(input_path)
    output_path = f"{name}.pdf"

    # PDF 已存在且未过期 → 跳过转换
    if os.path.exists(output_path):
        if os.path.getmtime(output_path) >= os.path.getmtime(input_path):
            return output_path

    try:
        subprocess.run(
            [
                LIBREOFFICE_PATH,
                "--headless",
                "--convert-to", "pdf",
                "--outdir", os.path.dirname(input_path),
                input_path,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return output_path if os.path.exists(output_path) else None
    except Exception as e:
        print(f"[StorageManager] Word转PDF失败: {e}")
        return None


# ============================================================
# 公共函数 1：获取上传凭证
# ============================================================

def get_upload_credential(file_name: str, path_prefix: str) -> Dict[str, Any]:
    """
    获取文件上传凭证
    - LOCAL 模式：标记由后端直接接收上传
    - COS 模式：  调用 STS 生成前端直传的临时密钥

    Args:
        file_name:   文件名（含扩展名），如 "报告.docx"
        path_prefix: 存储路径前缀，如 "case_42/vol_1"
    Returns:
        LOCAL: {"type": "LOCAL"}
        COS:   {
                   "type": "COS",
                   "credentials": {"tmp_secret_id": ..., "tmp_secret_key": ..., "session_token": ...},
                   "bucket": "xxx",
                   "region": "ap-guangzhou",
                   "key": "case_42/vol_1/报告.docx",
                   "expired_time": 1760745600
               }
    """
    if settings.STORAGE_TYPE == "COS":
        try:
            from sts.sts import Sts
        except ImportError:
            raise ImportError(
                "缺少腾讯云 STS SDK，请执行: pip install qcloud-python-sts"
            )

        # 构造 COS 对象键（object key）
        cos_key = f"{path_prefix}/{file_name}" if path_prefix else file_name

        sts = Sts({
            "secret_id": settings.COS_SECRET_ID,
            "secret_key": settings.COS_SECRET_KEY,
            "duration_seconds": 1800,               # 临时密钥有效期 30 分钟
            "bucket": settings.COS_BUCKET,
            "region": settings.COS_REGION,
            "allow_prefix": path_prefix + "/*",     # 限定仅能上传到此前缀路径（需 * 通配符匹配子文件）
            "allow_actions": [
                "name/cos:PutObject",
                "name/cos:PostOb"
                "ject",
                "name/cos:InitiateMultipartUpload",
                "name/cos:ListParts",
                "name/cos:UploadPart",
                "name/cos:CompleteMultipartUpload",
            ],
        })

        response = sts.get_credential()
        creds = response.get("credentials", {})

        return {
            "type": "COS",
            "credentials": {
                "tmp_secret_id": creds.get("tmpSecretId"),
                "tmp_secret_key": creds.get("tmpSecretKey"),
                "session_token": creds.get("sessionToken"),
            },
            "bucket": settings.COS_BUCKET,
            "region": settings.COS_REGION,
            "key": cos_key,
            "expired_time": response.get("expiredTime"),
        }

    # LOCAL 模式：后端直接接收文件
    return {"type": "LOCAL"}


# ============================================================
# 公共函数 2：获取文件预览 URL
# ============================================================

def get_file_preview_url(
    file_record: Any,
    root_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    获取文件预览 URL

    处理流程：
    - 若是 Word 文档，优先尝试返回 PDF 版本（转换 + 缓存）
    - 图片 / PDF 等可直接预览的格式直接返回

    Args:
        file_record: 数据库 ORM 对象，需包含 file_path / file_name / file_type 等属性
                     若已存储 cos_key 则优先用作 COS 对象键
        root_dir:    本地存储根目录（LOCAL 模式需要，如 CASE_ATTACHMENT_ROOT）
    Returns:
        LOCAL: {"type": "LOCAL", "file_path": "D:/.../document.pdf"}
                  —— 调用方可用 FileResponse(path=...) 返回给前端
        COS:   {"type": "COS", "url": "https://...", "expires_in": 3600}
                  —— 调用方可直接 302 重定向或返回给前端
        ERROR: {"type": "ERROR", "message": "..."}
    """
    # ---- 提取文件基本信息 ----
    file_path: str = getattr(file_record, "file_path", "") or ""
    file_name: str = getattr(file_record, "file_name", "") or ""
    file_type: str = getattr(file_record, "file_type", "") or ""
    cos_key_fallback: str = getattr(file_record, "cos_key", "") or ""

    # STS 前端直传场景：file_path 可能为空，但 cos_key 有值
    if not file_path:
        if cos_key_fallback:
            file_path = cos_key_fallback  # 以 cos_key 作为有效路径
        else:
            return {"type": "ERROR", "message": "文件记录缺少 file_path 和 cos_key"}

    # ---- 判断是否为 Word 文档 ----
    is_word = (
        file_type
        in (
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        or file_name.lower().endswith((".doc", ".docx"))
    )

    if settings.STORAGE_TYPE == "COS":
        return _cos_preview(file_record, file_path, file_name, is_word)
    else:
        return _local_preview(root_dir, file_path, is_word)


def _local_preview(
    root_dir: Optional[str],
    file_path: str,
    is_word: bool,
) -> Dict[str, Any]:
    """LOCAL 模式预览：检查本地文件并返回文件路径"""
    if not root_dir:
        return {"type": "ERROR", "message": "LOCAL 模式需要提供 root_dir 参数"}

    full_path = os.path.join(root_dir, file_path)
    if not os.path.exists(full_path):
        return {"type": "ERROR", "message": f"文件不存在: {full_path}"}

    # Word 文档 → 尝试返回同目录下的 PDF 版本
    if is_word:
        pdf_path = _convert_word_to_pdf(full_path)
        if pdf_path:
            return {"type": "LOCAL", "file_path": pdf_path}
        # 转换失败，降级返回原文件
        return {"type": "LOCAL", "file_path": full_path}

    # 非 Word 文档（图片 / PDF 等），直接返回
    return {"type": "LOCAL", "file_path": full_path}


def _cos_preview(
    file_record: Any,
    file_path: str,
    file_name: str,
    is_word: bool,
) -> Dict[str, Any]:
    """COS 模式预览：返回临时签名的免密预览 URL"""
    client = _get_cos_client()

    # 优先使用 cos_key（数据库字段），否则回退到 file_path
    cos_key = getattr(file_record, "cos_key", None) or file_path

    # 确保有文件名（DocumentTemplate 等模型无 file_name 字段，需从 cos_key 提取）
    if not file_name:
        file_name = os.path.basename(cos_key) or "download"

    if not is_word:
        # 非 Word 文件：直接返回签名 URL
        url = client.get_presigned_url(
            Method="GET",
            Bucket=settings.COS_BUCKET,
            Key=cos_key,
            Expired=3600,  # 1 小时有效期
        )
        return {"type": "COS", "url": url, "expires_in": 3600}

    # ---- Word 文档：检查 / 生成 PDF 缓存 ----
    stem, _ = os.path.splitext(cos_key)
    pdf_cache_key = f"preview_cache/{stem}.pdf"

    # 检查 COS 上是否已有缓存 PDF
    try:
        client.head_object(Bucket=settings.COS_BUCKET, Key=pdf_cache_key)
        # 缓存命中
        url = client.get_presigned_url(
            Method="GET",
            Bucket=settings.COS_BUCKET,
            Key=pdf_cache_key,
            Expired=3600,
        )
        return {"type": "COS", "url": url, "expires_in": 3600}
    except Exception:
        pass  # 缓存不存在或访问异常，重新生成

    # 下载原文件 → 本地转换 → 上传 PDF 缓存
    tmp_dir = tempfile.mkdtemp(prefix="cos_preview_")
    try:
        # 下载原始 Word 文件
        tmp_input = os.path.join(tmp_dir, file_name)
        client.download_file(
            Bucket=settings.COS_BUCKET,
            Key=cos_key,
            DestFilePath=tmp_input,
        )

        # 本地转换为 PDF
        tmp_pdf = _convert_word_to_pdf(tmp_input)
        if not tmp_pdf:
            # 转换失败，降级返回原文件签名 URL
            url = client.get_presigned_url(
                Method="GET",
                Bucket=settings.COS_BUCKET,
                Key=cos_key,
                Expired=3600,
            )
            return {"type": "COS", "url": url, "expires_in": 3600}

        # 上传 PDF 到 COS 缓存路径
        client.upload_file(
            Bucket=settings.COS_BUCKET,
            Key=pdf_cache_key,
            LocalFilePath=tmp_pdf,
        )

        # 返回缓存 PDF 的签名 URL
        url = client.get_presigned_url(
            Method="GET",
            Bucket=settings.COS_BUCKET,
            Key=pdf_cache_key,
            Expired=3600,
        )
        return {"type": "COS", "url": url, "expires_in": 3600}

    except Exception as e:
        return {"type": "ERROR", "message": f"COS 预览处理失败: {e}"}

    finally:
        # 清理服务器本地临时文件
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ============================================================
# 公共函数 3：获取文件下载链接（原文件，不做格式转换）
# ============================================================

def get_file_download_url(
    file_record: Any,
    root_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    获取原始文件的下载链接（不转换格式，直接返回原文件）
    Args:
        file_record: 数据库 ORM 对象
        root_dir:    本地存储根目录
    Returns:
        LOCAL: {"type": "LOCAL", "file_path": "..."}
        COS:   {"type": "COS", "url": "...", "expires_in": 3600}
        ERROR: {"type": "ERROR", "message": "..."}
    """
    file_path: str = getattr(file_record, "file_path", "") or ""
    if not file_path and not getattr(file_record, "cos_key", None):
        return {"type": "ERROR", "message": "文件记录缺少 file_path 和 cos_key"}

    if settings.STORAGE_TYPE == "COS":
        cos_key = getattr(file_record, "cos_key", None) or file_path
        client = _get_cos_client()
        try:
            url = client.get_presigned_url(
                Method="GET",
                Bucket=settings.COS_BUCKET,
                Key=cos_key,
                Expired=3600,
            )
            return {"type": "COS", "url": url, "expires_in": 3600}
        except Exception as e:
            return {"type": "ERROR", "message": f"COS 签名失败: {e}"}

    # LOCAL 模式
    if not root_dir:
        return {"type": "ERROR", "message": "LOCAL 模式需要提供 root_dir"}
    full_path = os.path.join(root_dir, file_path) if root_dir else file_path
    if not os.path.exists(full_path):
        return {"type": "ERROR", "message": f"文件不存在: {full_path}"}
    return {"type": "LOCAL", "file_path": full_path}


# ============================================================
# 公共函数 4：本地文件清理（级联删除空文件夹）
# ============================================================

def cleanup_local_file(file_path: str, root_dir: str):
    """
    删除本地文件，并级联向上删除空文件夹直到 root_dir
    - 文件不存在时静默跳过
    - 非空目录保留，不会误删
    """
    # 1. 删除文件本体
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            print(f"[StorageManager] 文件删除失败: {file_path}, {e}")

    # 2. 级联向上删除空文件夹
    current = os.path.dirname(file_path)
    root_dir = os.path.abspath(root_dir)
    while current and os.path.abspath(current).startswith(root_dir) and current != root_dir:
        try:
            if os.path.isdir(current) and not os.listdir(current):
                os.rmdir(current)
                current = os.path.dirname(current)
            else:
                break  # 非空则停止向上
        except OSError:
            break
