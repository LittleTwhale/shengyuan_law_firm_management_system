# crud/electronic_volume_crud.py
import os
from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from ..core.config import PDF_VOLUME_ROOT
from ..models.case import Case
from ..models.electronic_volume_model import CaseVolume, VolumeFile
from ..models.user import User
from ..schemas.electronic_volume_schema import (
    CaseVolumeCreate,
    CaseVolumeUpdate,
    VolumeFileCreate,
    VolumeFileUpdate,
    VolumeFilterQuery
)


# =========================================================
# 内部工具函数：筛选与权限逻辑复用
# =========================================================

def _apply_volume_filters(query, db: Session, current_user: User, params: Optional[VolumeFilterQuery] = None):
    """
    通用筛选器：同时应用于“卷宗列表查询”和“全局文件搜索”
    1. 处理权限 (User vs Admin/Permission)
    2. 处理筛选 (关键词、日期、律师、案由)
    """

    # ---------------- 1. 权限控制 (Row-Level Security) ----------------
    # 逻辑：
    # -  Owner: 查看所有
    # - 有 "volume_manage" 权限: 查看所有
    # - 普通用户: 只能查看自己是 主办/助理/执行/执行助理 的案件卷宗

    can_view_all = False
    if current_user.role in ['owner']:
        can_view_all = True
    elif current_user.permissions and current_user.permissions.get("volume_manage"):
        can_view_all = True

    if not can_view_all:
        # 关联 Case 表进行权限过滤 (如果 Query 还没 join Case，需要调用方保证已 join 或在此处处理)
        # 注意：这里假设调用方已经 join(Case) 或 query 是基于 Case 相关模型的
        # 为保险起见，这里显式添加 filter 条件，SQLAlchemy 会自动处理 join 如果已经 join 过

        query = query.filter(
            or_(
                Case.main_lawyer_id == current_user.id,
                Case.assistant_lawyer_id == current_user.id,
                Case.execution_lawyer_id == current_user.id,
                Case.execution_assistant_id == current_user.id,
            )
        )

    # ---------------- 2. 业务筛选条件 ----------------
    if params:
        # 关键词搜索 (同时匹配 卷宗名称 OR 案件号 OR 委托人)
        if params.keyword:
            search = f"%{params.keyword}%"
            # 注意：CaseVolume.name 是卷宗名，Case.case_number 是案号
            query = query.filter(
                or_(
                    CaseVolume.name.ilike(search),
                    Case.case_number.ilike(search),
                    Case.client_name.ilike(search)
                )
            )

        # 按案件类别
        if params.case_category:
            query = query.filter(Case.case_category == params.case_category)

        # 按主办律师
        if params.lawyer_id:
            query = query.filter(Case.main_lawyer_id == params.lawyer_id)

        # 按日期范围 (基于案件委托日期)
        if params.start_date:
            query = query.filter(Case.commission_date >= params.start_date)
        if params.end_date:
            query = query.filter(Case.commission_date <= params.end_date)

    return query


# =========================================================
# 卷宗 (CaseVolume) 操作
# =========================================================

def create_volume(db: Session, volume_in: CaseVolumeCreate) -> CaseVolume:
    """创建新的电子卷宗"""
    db_volume = CaseVolume(
        case_id=volume_in.case_id,
        name=volume_in.name,
        sort_order=volume_in.sort_order,
        physical_location=volume_in.physical_location
    )
    db.add(db_volume)
    db.commit()
    db.refresh(db_volume)
    return db_volume


def get_volume_by_id(db: Session, volume_id: int) -> Optional[CaseVolume]:
    """根据ID获取卷宗详情（包含文件列表）"""
    return db.query(CaseVolume) \
        .options(
        joinedload(CaseVolume.files).joinedload(VolumeFile.uploader)
    ) \
        .filter(CaseVolume.id == volume_id) \
        .first()


def invalidate_volume_merge_status(db: Session, volume_id: int):
    """
    使卷宗的合并状态失效：
    1. 物理删除已生成的 PDF 文件
    2. 将数据库 merged_file_path 置为 None
    """
    volume = db.query(CaseVolume).filter(CaseVolume.id == volume_id).first()
    if not volume:
        return

    if volume.merged_file_path:
        # 1. 物理删除
        full_path = os.path.join(PDF_VOLUME_ROOT, volume.merged_file_path)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
                print(f"Deleted old merged file: {full_path}")
            except Exception as e:
                print(f"Error deleting merged file: {e}")

        # 2. 数据库重置
        volume.merged_file_path = None
        db.commit()
        db.refresh(volume)

def get_multi_volumes(
        db: Session,
        current_user: User,
        query_params: VolumeFilterQuery,
        skip: int = 0,
        limit: int = 20
) -> Tuple[List[CaseVolume], int, int]:
    """
    获取卷宗列表 (支持分页、筛选、权限控制)
    仿照 Finance 的 get_multi 逻辑
    """
    # 1. 构建基础查询，Join Case 表以便获取案件信息
    query = db.query(CaseVolume).join(Case, CaseVolume.case_id == Case.case_id)

    # 预加载案件信息和主办律师信息，防止 N+1
    query = query.options(
        joinedload(CaseVolume.case).joinedload(Case.main_lawyer)
    )

    # 2. 应用通用筛选器 (权限 + 搜索)
    query = _apply_volume_filters(query, db, current_user, query_params)

    # 3. 获取总数
    total = query.count()

    # 4. 获取已归档(已合并)的数量 - 基于当前筛选条件
    merged_count = query.filter(CaseVolume.merged_file_path.isnot(None)).count()

    # 5. 排序与分页 (默认按案件创建时间倒序，同一案件内按卷宗排序)
    query = query.order_by(Case.created_at.desc(), CaseVolume.sort_order.asc())
    items = query.offset(skip).limit(limit).all()

    return items, total, merged_count


def get_volumes_by_case(
        db: Session,
        case_id: int,
        current_user: User,
) -> List[CaseVolume]:
    """
    获取指定案件下的所有卷宗列表
    包含权限校验：普通用户只能查看自己相关的案件卷宗
    """
    query = db.query(CaseVolume).join(Case, CaseVolume.case_id == Case.case_id)
    query = query.filter(CaseVolume.case_id == case_id)

    # 复用通用权限逻辑 (传入空的 query_params 即可，仅做权限校验)
    query = _apply_volume_filters(query, db, current_user, params=None)

    # 按 sort_order 升序排列
    return query.order_by(CaseVolume.sort_order.asc(), CaseVolume.id.asc()).all()


def update_volume(
        db: Session,
        volume_id: int,
        volume_in: CaseVolumeUpdate
) -> Optional[CaseVolume]:
    """更新卷宗信息"""
    volume = db.query(CaseVolume).filter(CaseVolume.id == volume_id).first()
    if not volume:
        return None

    update_data = volume_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(volume, field, value)

    db.commit()
    db.refresh(volume)
    return volume


def update_merged_file_path(db: Session, volume_id: int, file_path: str) -> bool:
    """更新卷宗的合并PDF路径"""
    volume = db.query(CaseVolume).filter(CaseVolume.id == volume_id).first()
    if volume:
        volume.merged_file_path = file_path
        db.commit()
        return True
    return False


def delete_volume(db: Session, volume_id: int) -> bool:
    """删除卷宗 (级联删除卷内文件在 Model 中已配置 cascade)"""
    volume = db.query(CaseVolume).filter(CaseVolume.id == volume_id).first()
    if not volume:
        return False

    db.delete(volume)
    db.commit()
    return True


# =========================================================
# 卷内文件 (VolumeFile) 操作
# =========================================================

def create_volume_file(
        db: Session,
        file_in: VolumeFileCreate,
        uploader_id: int
) -> VolumeFile:
    """创建卷内文件记录"""
    db_file = VolumeFile(
        **file_in.model_dump(),
        uploaded_by=uploader_id
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


def get_file_by_id(db: Session, file_id: int) -> Optional[VolumeFile]:
    return db.query(VolumeFile).filter(VolumeFile.id == file_id).first()


def update_volume_file(
        db: Session,
        file_id: int,
        file_in: VolumeFileUpdate
) -> Optional[VolumeFile]:
    """更新文件信息（重命名、移动分类、更新OCR等）"""
    file_obj = db.query(VolumeFile).filter(VolumeFile.id == file_id).first()
    if not file_obj:
        return None

    update_data = file_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(file_obj, field, value)

    db.commit()
    db.refresh(file_obj)
    return file_obj


def delete_volume_file(db: Session, file_id: int) -> bool:
    """删除文件记录"""
    file_obj = db.query(VolumeFile).filter(VolumeFile.id == file_id).first()
    if not file_obj:
        return False

    db.delete(file_obj)
    db.commit()
    return True


def get_files_in_volume(
        db: Session,
        volume_id: int,
        category: Optional[str] = None,
        keyword: Optional[str] = None
) -> List[VolumeFile]:
    """
    查询某卷宗下的文件列表
    注：这里一般不需要太复杂的权限判断，因为既然能获取到 Volume 详情，就能获取文件
    """
    query = db.query(VolumeFile) \
        .options(joinedload(VolumeFile.uploader)) \
        .filter(VolumeFile.volume_id == volume_id)

    if category:
        query = query.filter(VolumeFile.category == category)

    if keyword:
        search_term = f"%{keyword}%"
        query = query.filter(
            or_(
                VolumeFile.file_name.like(search_term),
                VolumeFile.summary.like(search_term),
                VolumeFile.ocr_content.like(search_term),
                # 简单处理 JSON 字段的字符串搜索
                VolumeFile.tags.cast(str).like(search_term)
            )
        )

    # 默认按 sort_order 排序，其次按 ID
    return query.order_by(VolumeFile.sort_order.asc(), VolumeFile.id.asc()).all()


def search_all_files(
        db: Session,
        current_user: User,
        keyword: str,
        skip: int = 0,
        limit: int = 20
) -> List[VolumeFile]:
    """
    全局文件搜索 (在所有我有权限的案件卷宗中搜索文件)
    """
    # 1. 基础查询
    query = db.query(VolumeFile).join(CaseVolume).join(Case)
    query = query.options(joinedload(VolumeFile.uploader))

    # 2. 权限过滤 (复用逻辑)
    # 构造一个临时的 params 对象或手动传参，这里为了复用 _apply_volume_filters
    # 我们只利用它的权限部分，搜索部分因为是针对 File 字段，需要单独写
    query = _apply_volume_filters(query, db, current_user, params=None)

    # 3. 关键词过滤 (针对 File 字段)
    search_term = f"%{keyword}%"
    query = query.filter(
        or_(
            VolumeFile.file_name.like(search_term),
            VolumeFile.summary.like(search_term),
            VolumeFile.ocr_content.like(search_term)
        )
    )

    return query.offset(skip).limit(limit).all()


def search_files_with_count(
        db: Session,
        current_user: User,
        keyword: str,
        skip: int = 0,
        limit: int = 20
) -> Tuple[List[VolumeFile], int]:
    """
    带总数统计的全局文件搜索，用于分页
    """
    # 1. 构建基础查询
    query = db.query(VolumeFile).join(CaseVolume).join(Case)
    query = query.options(joinedload(VolumeFile.uploader))

    # 2. 权限过滤
    query = _apply_volume_filters(query, db, current_user, params=None)

    # 3. 关键词过滤
    if keyword:
        search_term = f"%{keyword}%"
        query = query.filter(
            or_(
                VolumeFile.file_name.like(search_term),
                VolumeFile.summary.like(search_term),
                VolumeFile.ocr_content.like(search_term)
            )
        )

    # 4. 获取总数
    total = query.count()

    # 5. 获取分页数据
    items = query.order_by(Case.created_at.desc(), VolumeFile.id.desc()) \
        .offset(skip).limit(limit).all()

    return items, total


def batch_update_sort_order(db: Session, sort_data: List[dict]):
    """
    批量更新排序
    sort_data 示例: [{"id": 1, "sort_order": 1}, {"id": 2, "sort_order": 2}]
    """
    for item in sort_data:
        db.query(VolumeFile).filter(VolumeFile.id == item['id']).update(
            {"sort_order": item['sort_order']}
        )
    db.commit()