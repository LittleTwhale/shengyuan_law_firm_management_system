# api/electronic_volume.py

import json
import os
import shutil
import threading
import time
import uuid
from datetime import datetime, date
from typing import List, Optional

# 引入 PDF 处理库
from PyPDF2 import PdfReader, PdfWriter, Transformation, PdfMerger
from PyPDF2.generic import RectangleObject, AnnotationBuilder
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from reportlab.lib import colors
# 引入 ReportLab 用于生成目录页
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader  # 引入图片读取工具
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from ..api.deps import get_current_user
from ..core.config import ELECTRONIC_VOLUME_ROOT, PDF_VOLUME_ROOT
# 引入本模块的 CRUD 和 Schema
from ..crud import electronic_volume_crud as crud
from ..crud.attachment import convert_word_to_pdf  # 复用现有的Word转PDF工具
# 引入项目依赖
from ..database.database import get_db, SessionLocal
from ..models.case import Case
from ..models.electronic_volume_model import VolumeFile
from ..models.user import User
from ..schemas import electronic_volume_schema as schemas
from ..schemas.electronic_volume_schema import SortItem
from ..utils.ocr_helper import perform_smart_extraction

# 确保存储目录存在
os.makedirs(ELECTRONIC_VOLUME_ROOT, exist_ok=True)
os.makedirs(PDF_VOLUME_ROOT, exist_ok=True)

# 获取当前文件所在目录的上级目录作为基准
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.join(BASE_DIR, "assets", "fonts", "SimHei.ttf") # 或者 NotoSans.ttf

# 全局注册一次字体
try:
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont('CustomChinese', FONT_PATH))
        HAS_CHINESE_FONT = True
    else:
        print(f"Warning: Font file not found at {FONT_PATH}")
        HAS_CHINESE_FONT = False
except Exception as e:
    print(f"Font register error: {e}")
    HAS_CHINESE_FONT = False

router = APIRouter(
    prefix="/electronic_volumes",
    tags=["Electronic Volume (电子卷宗)"]
)


# ==========================================
# 辅助函数：权限与业务逻辑检查
# ==========================================

def check_volume_write_permission(db: Session, user: User, case_id: int):
    """
    检查用户是否有权对指定案件的卷宗进行【写操作】（增删改）
    逻辑：
    1. 超级管理员/拥有 volume_manage 权限 -> 通过
    2. 案件的主办/助理/执行/执行助理 -> 通过
    3. 否则 -> 拒绝
    """
    # 1. 超级权限
    if user.role in ['owner']:
        return True
    if user.permissions and user.permissions.get("volume_manage"):
        return True

    # 2. 案件相关人校验
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="关联案件不存在")

    # 业务要求：只能对【已审核】的案件上传卷宗
    if case.review_status != "已审核":
        raise HTTPException(
            status_code=400,
            detail=f"案件状态为'{case.review_status}'，仅'已审核'案件可维护电子卷宗"
        )

    is_related = (
            case.main_lawyer_id == user.id or
            case.assistant_lawyer_id == user.id or
            case.assistant_lawyer_2_id == user.id or
            case.execution_lawyer_id == user.id or
            case.execution_assistant_id == user.id
    )

    if not is_related:
        raise HTTPException(status_code=403, detail="您无权操作此案件的卷宗")

    return True


# ==========================================
# 1. 卷宗 (CaseVolume) 接口
# ==========================================

@router.post("/", response_model=schemas.CaseVolumeOut)
def create_volume(
        volume_in: schemas.CaseVolumeCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """创建新的电子卷宗册"""
    # 权限校验
    check_volume_write_permission(db, current_user, volume_in.case_id)

    return crud.create_volume(db, volume_in)


@router.get("/", response_model=schemas.CaseVolumePageOut)
def list_volumes(
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        case_category: Optional[str] = None,
        lawyer_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    获取卷宗列表（支持分页、搜索、筛选）
    - 普通用户只能看到自己相关的案件卷宗
    - 管理员可查看全部
    """
    query_params = schemas.VolumeFilterQuery(
        keyword=keyword,
        case_category=case_category,
        lawyer_id=lawyer_id,
        start_date=start_date,
        end_date=end_date,
    )

    skip = (page - 1) * page_size
    items, total, merged_count = crud.get_multi_volumes(db, current_user, query_params, skip=skip, limit=page_size)

    return {"total": total, "merged_count": merged_count, "items": items}


@router.get("/case/{case_id}", response_model=List[schemas.CaseVolumeOut])
def list_volumes_by_case(
        case_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """获取指定案件下的所有卷宗"""
    return crud.get_volumes_by_case(db, case_id, current_user)


@router.get("/{volume_id}", response_model=schemas.CaseVolumeOut)
def get_volume_detail(
        volume_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """获取卷宗详情（包含卷内文件列表）"""
    volume = crud.get_volume_by_id(db, volume_id)
    if not volume:
        raise HTTPException(status_code=404, detail="卷宗不存在")

    # 这里也可以加一个 Read 权限校验，但 get_volumes_by_case 里的逻辑通常已经覆盖
    # 如果需要严格控制，可以复用 crud._apply_volume_filters 的逻辑进行二次检查

    return volume


@router.put("/{volume_id}", response_model=schemas.CaseVolumeOut)
def update_volume(
        volume_id: int,
        volume_in: schemas.CaseVolumeUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """更新卷宗信息（重命名、排序等）"""
    volume = crud.get_volume_by_id(db, volume_id)
    if not volume:
        raise HTTPException(status_code=404, detail="卷宗不存在")

    check_volume_write_permission(db, current_user, volume.case_id)

    return crud.update_volume(db, volume_id, volume_in)


@router.delete("/{volume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_volume(
        volume_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    删除卷宗（级联删除卷内文件）
    修改：同时删除磁盘上的物理文件夹
    """
    volume = crud.get_volume_by_id(db, volume_id)
    if not volume:
        raise HTTPException(status_code=404, detail="卷宗不存在")

    check_volume_write_permission(db, current_user, volume.case_id)

    # 1. 物理删除文件夹
    # 路径规则：ELECTRONIC_VOLUME_ROOT / case_{id} / vol_{id}
    volume_dir = os.path.join(ELECTRONIC_VOLUME_ROOT, f"case_{volume.case_id}", f"vol_{volume_id}")

    if os.path.exists(volume_dir):
        try:
            shutil.rmtree(volume_dir)
        except Exception as e:
            # 记录日志，但不阻断数据库删除
            print(f"Error deleting directory {volume_dir}: {e}")

    # 同时删除可能存在的已合并PDF (在 PDF_VOLUME_ROOT)
    merged_dir_pdf = os.path.join(PDF_VOLUME_ROOT, f"case_{volume.case_id}", f"vol_{volume_id}")
    if os.path.exists(merged_dir_pdf):
        try:
            shutil.rmtree(merged_dir_pdf)
        except Exception as e:
            print(f"Error deleting pdf directory {merged_dir_pdf}: {e}")

    # 2. 数据库删除（级联删除文件记录）
    crud.delete_volume(db, volume_id)
    return


# ==========================================
# 2. 卷内文件 (VolumeFile) 接口
# ==========================================

# ==========================================
# 后台任务函数
# ==========================================

def background_ocr_task(file_id: int, file_path: str, file_type: str):
    """
    后台 OCR 任务
    """
    print(f"[Task] 开始处理文件 ID: {file_id}")

    # =================  针对 .doc 的特殊等待逻辑 =================
    if file_path.endswith('.doc'):
        pdf_path = os.path.splitext(file_path)[0] + ".pdf"
        # 简单的轮询等待，最多等 20 秒
        max_retries = 10
        for i in range(max_retries):
            if os.path.exists(pdf_path):
                break
            print(f"[Task] 等待 .doc 转 PDF 完成... ({i + 1}/{max_retries})")
            time.sleep(2)  # 每次等2秒
    # ===================================================================

    # 执行智能提取 (耗时操作)
    try:
        content = perform_smart_extraction(file_path, file_type)
    except Exception as e:
        print(f"[Task] Extraction failed: {e}")
        return

    if not content:
        print(f"[Task] 未提取到内容 ID: {file_id}")
        return

    # 更新数据库
    db = SessionLocal()
    try:
        file_obj = db.query(VolumeFile).filter(VolumeFile.id == file_id).first()
        if file_obj:
            file_obj.ocr_content = content
            db.commit()
            print(f"[Task] 成功更新数据库 ID: {file_id}, 字数: {len(content)}")
    except Exception as e:
        print(f"[Task] DB Error: {e}")
        db.rollback()
    finally:
        db.close()

@router.post("/files", response_model=schemas.VolumeFileOut)
async def upload_volume_file(
        volume_id: int = Form(..., description="所属卷宗ID"),
        category: str = Form("其他材料", description="文件分类"),
        sort_order: int = Form(0, description="排序"),
        summary: Optional[str] = Form(None, description="摘要备注"),
        tags: Optional[str] = Form(None, description="标签JSON字符串"),
        file: UploadFile = File(...),
        background_tasks: BackgroundTasks = BackgroundTasks(),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    上传文件到卷宗
    - 自动保存文件
    - 自动关联案件
    - 如果是Word文档，异步触发转PDF以供预览和后续合并
    """
    # 1. 验证卷宗
    volume = crud.get_volume_by_id(db, volume_id)
    if not volume:
        raise HTTPException(status_code=404, detail="卷宗不存在")

    check_volume_write_permission(db, current_user, volume.case_id)

    # 2. 保存文件到磁盘
    # 目录结构: ELECTRONIC_VOLUME_ROOT / case_{id} / volume_{id} / file
    save_dir = os.path.join(ELECTRONIC_VOLUME_ROOT, f"case_{volume.case_id}", f"vol_{volume_id}")
    os.makedirs(save_dir, exist_ok=True)

    file_ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4().hex}{file_ext}"
    save_path = os.path.join(save_dir, unique_name)

    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {e}")

    # ===  如果是Word文档，异步生成PDF ===
    # 这样在预览和合并时可以直接使用
    if file.content_type in [
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ] or file.filename.lower().endswith(('.doc', '.docx')):
        threading.Thread(
            target=convert_word_to_pdf,
            args=(save_path,),  # 传入绝对路径，生成的pdf会在同目录
            daemon=True
        ).start()

    # 3. 构造 Create Schema
    # 存储的路径是相对路径，方便迁移
    relative_path = os.path.join(f"case_{volume.case_id}", f"vol_{volume_id}", unique_name)
    file_size = os.path.getsize(save_path)

    # 解析 tags
    tag_list = []
    if tags:
        try:
            tag_list = json.loads(tags)
        except:
            pass

    file_in = schemas.VolumeFileCreate(
        volume_id=volume_id,
        file_name=file.filename,
        file_path=relative_path,
        file_size=file_size,
        file_type=file.content_type,
        category=category,
        sort_order=sort_order,
        summary=summary,
        tags=tag_list
    )

    # 4. 写入数据库
    new_file = crud.create_volume_file(db, file_in, current_user.id)
    # 内容变更，旧的合并文件失效
    crud.invalidate_volume_merge_status(db, volume_id)

    # ================= 触发 OCR 任务 =================
    # 获取文件的绝对路径用于 OCR 读取
    full_disk_path = os.path.join(ELECTRONIC_VOLUME_ROOT, relative_path)

    # 添加到后台队列，不阻塞当前 Return
    background_tasks.add_task(
        background_ocr_task,
        file_id=new_file.id,
        file_path=full_disk_path,
        file_type=file.content_type
    )
    # =======================================================

    return new_file

@router.put("/files/{file_id}", response_model=schemas.VolumeFileOut)
def update_volume_file(
        file_id: int,
        file_in: schemas.VolumeFileUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    更新卷内文件信息（重命名、修改排序、标签、摘要、移动分类）
    """
    # 1. 查文件
    file_obj = crud.get_file_by_id(db, file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 2. 查权限 (通过 Volume -> Case)
    volume = crud.get_volume_by_id(db, file_obj.volume_id)
    check_volume_write_permission(db, current_user, volume.case_id)

    # 3. 执行更新
    updated_file = crud.update_volume_file(db, file_id, file_in)
    # 内容变更，旧的合并文件失效
    if updated_file:
        crud.invalidate_volume_merge_status(db, updated_file.volume_id)
    return updated_file

@router.post("/files/batch_sort", status_code=200)
def batch_update_sort(
    sort_data: List[SortItem],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量更新文件排序"""
    if not sort_data:
        return {"msg": "ok"}

    # 1. 取出第一个文件的 ID
    first_file_id = sort_data[0].id

    # 2. 查询文件对象以获取 volume_id
    file_obj = crud.get_file_by_id(db, first_file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 3. 通过文件的 volume_id 获取卷宗并校验权限
    volume = crud.get_volume_by_id(db, file_obj.volume_id)
    if not volume:
        raise HTTPException(status_code=404, detail="关联卷宗不存在")

    check_volume_write_permission(db, current_user, volume.case_id)

    # 4. 执行批量更新
    #    确保传入的是字典列表
    crud.batch_update_sort_order(db, [item.model_dump() for item in sort_data])

    # 排序变更，旧的合并文件失效
    crud.invalidate_volume_merge_status(db, volume.id)
    return {"msg": "ok"}

@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_volume_file(
        file_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """删除卷内文件"""
    file_obj = crud.get_file_by_id(db, file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 查 Volume 进而查 Case 进而查权限
    volume = crud.get_volume_by_id(db, file_obj.volume_id)
    check_volume_write_permission(db, current_user, volume.case_id)

    # 物理删除文件
    full_path = os.path.join(ELECTRONIC_VOLUME_ROOT, file_obj.file_path)
    if os.path.exists(full_path):
        try:
            os.remove(full_path)
        except:
            pass

    # 同时尝试删除可能存在的预览PDF副本
    pdf_path_temp = os.path.splitext(full_path)[0] + ".pdf"
    if os.path.exists(pdf_path_temp):
        try:
            os.remove(pdf_path_temp)
        except:
            pass

    # 获取 volume_id (在删除 DB 记录前)
    vol_id = file_obj.volume_id
    # 内容变更，旧的合并文件失效
    crud.invalidate_volume_merge_status(db, vol_id)

    crud.delete_volume_file(db, file_id)
    return


@router.get("/files/{file_id}/download")
def download_volume_file(
        file_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """下载单个文件"""
    file_obj = crud.get_file_by_id(db, file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="文件不存在")

    full_path = os.path.join(ELECTRONIC_VOLUME_ROOT, file_obj.file_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="文件实体已丢失")

    # 简单的文件名编码处理
    from urllib.parse import quote
    encoded_name = quote(file_obj.file_name)

    return FileResponse(
        full_path,
        filename=file_obj.file_name,
        media_type=file_obj.file_type or "application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_name}"}
    )


@router.get("/files/{file_id}/preview")
def preview_volume_file(
        file_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    预览卷内文件 (支持图片、PDF、Word自动转PDF)
    """
    file_obj = crud.get_file_by_id(db, file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="文件不存在")

    full_path = os.path.join(ELECTRONIC_VOLUME_ROOT, file_obj.file_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="文件在服务器上已丢失")

    # 1. 优先直接支持的类型 (图片, PDF)
    supported_types = {
        "image/jpeg", "image/png", "image/gif", "image/bmp", "image/webp",
        "application/pdf"
    }

    # 2. Word文档特殊处理
    if file_obj.file_type in [
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ] or full_path.lower().endswith(('.doc', '.docx')):
        # 预测PDF路径 (同目录下同名的pdf)
        name, _ = os.path.splitext(full_path)
        pdf_path = f"{name}.pdf"

        # 检查PDF是否存在
        if os.path.exists(pdf_path):
            return FileResponse(path=pdf_path, media_type="application/pdf")

        # 若无效（上传时转换失败或尚未完成），尝试实时转换
        # 注意：这里调用会阻塞请求，如果是大文件可能会稍慢
        converted_pdf = convert_word_to_pdf(full_path)
        if converted_pdf:
            return FileResponse(path=converted_pdf, media_type="application/pdf")
        else:
            raise HTTPException(status_code=500, detail="预览生成失败，请下载查看")

    # 3. 其他不支持预览的类型
    if file_obj.file_type not in supported_types and not full_path.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=415,
            detail=f"不支持在线预览此格式: {file_obj.file_type}"
        )

    # 4. 返回原文件预览
    return FileResponse(
        path=full_path,
        media_type=str(file_obj.file_type)
    )


# ==========================================
# 3. 核心功能：卷宗合并导出 (含目录生成)
# ==========================================
def _create_decoration_pdf(
        output_path: str,
        page_num: int,
        total_pages: int,
        volume_name: str,
        logo_path: str = None
):
    """
    生成单页装饰：
    1. 装饰线边距 15mm (留出顶部 15mm 空间给 Logo)
    2. Logo 位于顶部空白区，紧贴页面顶部边缘
    3. 卷宗名和页码位置微调
    """
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4  # A4 宽 x 高

    # === 1. 定义布局参数 ===
    # 装饰线框的边距：15mm
    border_margin = 15 * mm

    # 绘制外围装饰边框 (矩形)
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    # 边框顶部 y = height - 15mm
    c.rect(border_margin, border_margin, width - 2 * border_margin, height - 2 * border_margin)

    # === 2. 绘制 Logo (位于顶部空隙，紧贴顶边) ===
    if logo_path and os.path.exists(logo_path):
        try:
            img = ImageReader(logo_path)
            img_w, img_h = img.getSize()
            aspect = img_h / float(img_w)

            # --- 尺寸限制 ---
            # 顶部空间只有 15mm (border_margin)
            # 为了美观，留 1mm 间隙不压装饰线，最大高度设为 14mm
            max_logo_height = 14 * mm
            max_logo_width = 60 * mm  # 宽度不过分长即可

            # 计算显示尺寸
            display_h = max_logo_height
            display_w = display_h / aspect

            if display_w > max_logo_width:
                display_w = max_logo_width
                display_h = display_w * aspect

            # --- 坐标定位  ---
            # x:  留1mm
            logo_x = 1 * mm

            # y: 紧贴页面顶部
            # 页面顶端是 height。图片绘制点是左下角。
            # 所以 y = 页面高度 - 图片高度 - 顶部微小留白(例如1mm，防止被打印机裁切)
            logo_y = height - display_h - 1 * mm

            c.drawImage(logo_path, logo_x, logo_y, width=display_w, height=display_h,
                        preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Logo draw error: {e}")

    # === 3. 绘制顶部卷宗名称 (居中，位于顶部空隙) ===
    # 字体设置
    font_name = "CustomChinese"  # 假设已注册
    c.setFont(font_name, 12)

    # 文字垂直位置：
    # Logo 在左边，标题在中间。
    # 让标题的基线位于顶部空白区域的中间偏下，或者与 Logo 视觉中心对齐。
    # 顶部区域高度 15mm，中心约在 height - 7.5mm
    c.drawCentredString(width / 2, height - 10 * mm, f"{volume_name}")

    # === 4. 绘制页码 (底部居中，位于底部空隙) ===
    page_info = f"- {page_num} / {total_pages} -"
    c.setFont("Helvetica", 10)
    # 底部边距也是 15mm，文字放在距底 6mm 处
    c.drawCentredString(width / 2, 6 * mm, page_info)

    c.save()


def _create_toc_pdf(toc_entries: List[dict], output_path: str, volume_name: str) -> dict:
    """
    生成目录页。
    :param toc_entries: list of dict {'name': str, 'page_display': int, 'target_index': int}
    :return: dict { page_index_of_toc: [ {rect: list, target_index: int}, ... ] }
    """
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    font_name = "CustomChinese" if 'CustomChinese' in pdfmetrics.getRegisteredFontNames() else "Helvetica"

    # 标题
    c.setFont(font_name, 18)
    c.drawCentredString(width / 2, height - 30 * mm, f"{volume_name} - 卷宗目录")

    # 表头
    c.setFont(font_name, 10)
    y_header = height - 45 * mm
    c.drawString(20 * mm, y_header, "文件名称")
    c.drawRightString(width - 20 * mm, y_header, "页码")
    c.line(20 * mm, y_header - 2 * mm, width - 20 * mm, y_header - 2 * mm)

    c.setFont(font_name, 12)
    y = height - 60 * mm
    line_height = 10 * mm

    link_map = {}  # { toc_page_idx: [ {rect:..., target_index:...} ] }
    current_toc_page_idx = 0

    for idx, entry in enumerate(toc_entries, 1):
        if y < 20 * mm:
            c.showPage()
            current_toc_page_idx += 1
            c.setFont(font_name, 12)
            y = height - 30 * mm

        name = entry['name']
        page_display = entry['page_display']  # 显示的页码
        target_index = entry['target_index']  # 实际跳转的 PDF 页索引（从0开始）

        # 文字绘制
        display_name = f"{idx}. {name}"
        if len(display_name) > 45:
            display_name = display_name[:42] + "..."

        # ================== 视觉优化：超链接样式 ==================
        # 1. 设置文字为超链接蓝色
        c.setFillColor(colors.blue)
        c.drawString(20 * mm, y, display_name)
        c.drawRightString(width - 20 * mm, y, str(page_display))

        # 2. 绘制下划线
        text_width = c.stringWidth(display_name, font_name, 12)
        c.setStrokeColor(colors.blue)
        c.setLineWidth(0.5)
        # 在文字下方 2pt 处画下划线
        c.line(20 * mm, y - 2, 20 * mm + text_width, y - 2)

        # 3. 恢复黑色画笔，用于绘制后续的虚线填充
        c.setFillColor(colors.black)
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        # ==========================================================

        # 虚线
        c.setDash(1, 3)
        c.line(20 * mm + text_width + 5, y + 1, width - 25 * mm, y + 1)
        c.setDash([])

        # 记录链接区域 (稍微扩大点击区域的高度，覆盖下划线，提高点击手感)
        # [x1, y1, x2, y2]
        rect = [20 * mm, y - 4, width - 20 * mm, y + 10]

        if current_toc_page_idx not in link_map:
            link_map[current_toc_page_idx] = []

        link_map[current_toc_page_idx].append({
            "rect": rect,
            "target_index": target_index
        })

        y -= line_height

    c.save()
    return link_map


def _get_pdf_page_count(pdf_path: str) -> int:
    """获取PDF页数"""
    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except:
        return 0


def _process_merge(db, volume, files, output_path):
    """
    高级合并逻辑（使用 PdfMerger 合并正文，提高稳定性）
    """
    writer = PdfWriter()
    temp_files = []  # 待清理的临时文件列表

    # Logo 路径（请根据实际路径配置）
    logo_path = os.path.join("D:\\", "syls", "front_end", "sy_lawyers_office", "src", "assets", "img", "logo.png")

    # ---------------- 1. 准备文件列表 ----------------
    ready_files = []
    for f_obj in files:
        abs_path = os.path.join(ELECTRONIC_VOLUME_ROOT, f_obj.file_path)
        if not os.path.exists(abs_path):
            continue

        pdf_path = None
        # 判断类型并转换为 PDF（原有逻辑不变）
        if f_obj.file_type == 'application/pdf' or abs_path.lower().endswith('.pdf'):
            pdf_path = abs_path
        elif abs_path.lower().endswith(('.doc', '.docx')):
            try:
                converted = convert_word_to_pdf(abs_path)
                if converted and os.path.exists(converted):
                    pdf_path = converted
            except Exception as e:
                print(f"Word convert error: {e}")
        elif abs_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            try:
                from PIL import Image
                img = Image.open(abs_path)
                img = img.convert('RGB')
                temp_pdf = abs_path + ".temp.pdf"
                img.save(temp_pdf)
                pdf_path = temp_pdf
                temp_files.append(temp_pdf)
            except Exception as e:
                print(f"Image convert error: {e}")

        if pdf_path:
            p_count = _get_pdf_page_count(pdf_path)
            if p_count > 0:
                ready_files.append({
                    "obj": f_obj,
                    "path": pdf_path,
                    "pages": p_count
                })

    # ---------------- 2. 规划页码 & 链接索引 (双段生成法解决目录多页问题) ----------------

    # 【第一步：预演生成，获取真实目录页数】
    dummy_toc_path = output_path + ".dummy_toc.pdf"
    # 假装生成一次，页码填0即可，主要为了看这些条目会撑出几页
    dummy_toc_data = [{"name": f["obj"].file_name, "page_display": 0, "target_index": 0} for f in ready_files]
    _create_toc_pdf(dummy_toc_data, dummy_toc_path, volume.name)

    # 获取真实的目录页数
    toc_page_count = _get_pdf_page_count(dummy_toc_path)

    # 获取完毕，清理临时文件
    if os.path.exists(dummy_toc_path):
        try:
            os.remove(dummy_toc_path)
        except:
            pass

    # 【第二步：根据真实目录页数，排布正文页码】
    current_writer_index = toc_page_count  # 正文在最终PDF的物理起始索引（接在目录后）
    toc_data = []
    total_pages_display = toc_page_count + sum(item['pages'] for item in ready_files)
    current_display_page = toc_page_count + 1  # 视觉显示的起始页码

    for item in ready_files:
        f_obj = item["obj"]
        start_page_index_in_pdf = current_writer_index
        f_obj.page_start = current_display_page
        f_obj.page_end = current_display_page + item['pages'] - 1
        toc_data.append({
            "name": f_obj.file_name,
            "page_display": current_display_page,
            "target_index": start_page_index_in_pdf
        })
        current_writer_index += item['pages']
        current_display_page += item['pages']
    db.commit()

    # ---------------- 3. 生成目录页 ----------------
    toc_pdf_path = output_path + ".toc.pdf"
    link_map = _create_toc_pdf(toc_data, toc_pdf_path, volume.name)
    temp_files.append(toc_pdf_path)

    # 将目录页加入最终 writer
    try:
        toc_reader = PdfReader(toc_pdf_path)
        for page in toc_reader.pages:
            writer.add_page(page)
    except Exception as e:
        print(f"ToC merge error: {e}")

    # ---------------- 4. 使用 PdfMerger 合并所有正文为一个临时 PDF ----------------
    body_merger = PdfMerger()
    for item in ready_files:
        body_merger.append(item["path"])
    temp_body_path = output_path + ".body.pdf"
    with open(temp_body_path, "wb") as f:
        body_merger.write(f)
    temp_files.append(temp_body_path)

    # ---------------- 5. 逐页叠加装饰（从临时正文 PDF 读取） ----------------
    a4_w, a4_h = A4
    content_margin = 16 * mm
    safe_w = a4_w - 2 * content_margin
    safe_h = a4_h - 2 * content_margin

    body_reader = PdfReader(temp_body_path)
    global_page_counter = toc_page_count + 1  # 当前页面在最终文档中的页码（从目录后开始）

    for src_page in body_reader.pages:
        # 5.1 生成装饰底图
        deco_pdf_path = f"{output_path}.temp_{global_page_counter}.pdf"
        _create_decoration_pdf(
            deco_pdf_path,
            global_page_counter,
            total_pages_display,
            volume.name,
            logo_path
        )
        temp_files.append(deco_pdf_path)  # 统一清理

        deco_reader = PdfReader(deco_pdf_path)
        deco_page = deco_reader.pages[0]

        # 5.2 缩放正文页，使其安全地放入 A4 内部
        mb = src_page.mediabox
        src_w = float(mb.width)
        src_h = float(mb.height)
        scale = min(safe_w / src_w, safe_h / src_h)
        tx = (a4_w - src_w * scale) / 2
        ty = (a4_h - src_h * scale) / 2
        op = Transformation().scale(scale).translate(tx, ty)
        src_page.add_transformation(op)

        # 5.3 合并装饰页和正文页
        deco_page.merge_page(src_page)

        # 5.4 添加到最终文档
        writer.add_page(deco_page)
        global_page_counter += 1

    # ---------------- 6. 统一添加目录链接 ----------------
    for toc_page_idx, links in link_map.items():
        for link in links:
            try:
                # 使用官方推荐的 AnnotationBuilder 创建链接注解
                annotation = AnnotationBuilder.link(
                    rect=link['rect'],  # 传入坐标数组 [x1, y1, x2, y2]
                    target_page_index=link['target_index']
                )
                # 将注解添加到对应的目录页
                writer.add_annotation(
                    page_number=toc_page_idx,
                    annotation=annotation
                )
            except Exception as e:
                print(f"链接添加失败: {e}")

    # ---------------- 7. 保存最终 PDF ----------------
    with open(output_path, "wb") as f_out:
        writer.write(f_out)

    # ---------------- 8. 清理所有临时文件 ----------------
    for p in temp_files:
        if os.path.exists(p):
            try:
                os.remove(p)
            except:
                pass


# 抽离出的后台执行PDF合并函数
def background_merge_task(volume_id: int):
    # 后台任务必须拥有独立的数据库会话
    db = SessionLocal()
    try:
        volume = crud.get_volume_by_id(db, volume_id)
        if not volume:
            return

        files = crud.get_files_in_volume(db, volume_id)
        if not files:
            return

        merged_dir = os.path.join(PDF_VOLUME_ROOT, f"case_{volume.case_id}", f"vol_{volume_id}")
        os.makedirs(merged_dir, exist_ok=True)
        merged_filename = f"{volume.name}_Merged_{datetime.now().strftime('%Y%m%d%H%M')}.pdf"
        merged_path = os.path.join(merged_dir, merged_filename)

        # 执行极度耗时的合并
        _process_merge(db, volume, files, merged_path)

        # 成功后更新数据库
        relative_path = os.path.join(f"case_{volume.case_id}", f"vol_{volume_id}", merged_filename)
        crud.update_merged_file_path(db, volume_id, relative_path)

    except Exception as e:
        print(f"[Merge Task] 合并失败: {e}")
        # 这里建议未来在数据库给卷宗加个 merge_status 字段，记录 "合并失败" 状态
    finally:
        db.close()

@router.post("/{volume_id}/merge", response_model=schemas.CaseVolumeOut)
def merge_volume_files(
        volume_id: int,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    触发卷宗合并
    1. 获取卷内所有文件（按 sort_order 排序）
    2. 转PDF + 统计页码 + 更新数据库 page_start/end
    3. 生成目录页 (TOC)
    4. 合并保存到 PDF_VOLUME_ROOT 目录
    """
    volume = crud.get_volume_by_id(db, volume_id)
    if not volume:
        raise HTTPException(status_code=404, detail="卷宗不存在")

    # 在开始新的合并前，强制清理旧的合并文件和记录
    # 这确保了如果合并过程中途失败，不会留下旧的 merged_file_path 指向
    crud.invalidate_volume_merge_status(db, volume_id)
    # 重新刷新 volume 对象以获取最新的状态 (merged_file_path 应为 None)
    db.refresh(volume)

    background_tasks.add_task(background_merge_task, volume_id)

    return volume


@router.get("/{volume_id}/download_merged")
def download_merged_volume(
        volume_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """下载已合并的 PDF 文件"""
    volume = crud.get_volume_by_id(db, volume_id)
    if not volume:
        raise HTTPException(status_code=404, detail="卷宗不存在")

    if not volume.merged_file_path:
        raise HTTPException(status_code=404, detail="该卷宗尚未执行合并操作，或合并文件不存在")

    # 路径拼接使用 PDF_VOLUME_ROOT
    full_path = os.path.join(PDF_VOLUME_ROOT, volume.merged_file_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="合并文件实体已丢失，请重新执行合并")

    filename = f"{volume.name}_全卷.pdf"
    from urllib.parse import quote
    encoded_name = quote(filename)

    return FileResponse(
        full_path,
        filename=filename,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_name}"}
    )


@router.get("/{volume_id}/preview_merged")
def preview_merged_volume(
        volume_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    预览已合并的 PDF 电子卷宗
    """
    volume = crud.get_volume_by_id(db, volume_id)
    if not volume:
        raise HTTPException(status_code=404, detail="卷宗不存在")

    if not volume.merged_file_path:
        raise HTTPException(status_code=404, detail="该卷宗尚未执行合并操作")

    # 路径拼接使用 PDF_VOLUME_ROOT
    full_path = os.path.join(PDF_VOLUME_ROOT, volume.merged_file_path)

    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="合并文件实体已丢失，请重新执行合并")

    # 直接返回文件，不带 attachment header，浏览器/前端可直接渲染
    return FileResponse(
        full_path,
        media_type="application/pdf"
    )