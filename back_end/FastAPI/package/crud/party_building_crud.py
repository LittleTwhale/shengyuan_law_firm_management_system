# crud/party_building_crud.py
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from ..models.party_building_model import PartyMaterial, PartyCategory, PartyAttachment
from ..schemas.party_building_schema import PartyCategoryCreate, PartyCategoryUpdate, PartyMaterialCreate, \
    PartyMaterialUpdate


# ==========================================
# 分类管理 (Category)
# ==========================================

def get_category(db: Session, category_id: int):
    return db.query(PartyCategory).filter(PartyCategory.id == category_id).first()


def get_categories(db: Session, only_active: bool = False):
    query = db.query(PartyCategory)
    if only_active:
        query = query.filter(PartyCategory.is_active == True)
    # 按权重排序（大的在前），其次按ID
    return query.order_by(desc(PartyCategory.sort_order), PartyCategory.id).all()


def create_category(db: Session, category_in: PartyCategoryCreate):
    db_obj = PartyCategory(
        name=category_in.name,
        sort_order=category_in.sort_order,
        is_active=category_in.is_active
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_category(db: Session, db_obj: PartyCategory, category_in: PartyCategoryUpdate):
    update_data = category_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_category(db: Session, category_id: int) -> bool:
    db_obj = get_category(db, category_id)
    if not db_obj:
        return False
    # 注意：如果该分类下有文章，因为外键是 RESTRICT，数据库会报错，需要在API层捕获
    db.delete(db_obj)
    db.commit()
    return True


# ==========================================
# 资料管理 (Material)
# ==========================================

def get_material(db: Session, material_id: int):
    # 使用 joinedload 预加载关联数据，避免 N+1 问题
    return db.query(PartyMaterial) \
        .options(joinedload(PartyMaterial.publisher), joinedload(PartyMaterial.category),
                 joinedload(PartyMaterial.attachments)) \
        .filter(PartyMaterial.id == material_id) \
        .first()


def get_materials(
        db: Session,
        skip: int = 0,
        limit: int = 10,
        category_id: int = None,
        search: str = None
):
    query = db.query(PartyMaterial)

    if category_id:
        query = query.filter(PartyMaterial.category_id == category_id)

    if search:
        query = query.filter(
            (PartyMaterial.title.ilike(f"%{search}%")) |
            (PartyMaterial.document_number.ilike(f"%{search}%"))
        )

    # 1. 获取总数
    total = query.count()

    # 2. 获取分页数据 (预加载 publisher 和 category)
    items = query.options(
        joinedload(PartyMaterial.publisher),
        joinedload(PartyMaterial.category)
    ).order_by(desc(PartyMaterial.created_at)).offset(skip).limit(limit).all()

    return total, items  # 返回元组


def create_material(db: Session, material_in: PartyMaterialCreate, publisher_id: int):
    db_obj = PartyMaterial(
        title=material_in.title,
        issuing_authority=material_in.issuing_authority,
        document_number=material_in.document_number,
        content=material_in.content,
        category_id=material_in.category_id,
        publisher_id=publisher_id
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_material(db: Session, db_obj: PartyMaterial, material_in: PartyMaterialUpdate):
    update_data = material_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_material(db: Session, material_id: int) -> bool:
    db_obj = get_material(db, material_id)
    if not db_obj:
        return False
    # 这里的级联删除已经在 Model 中配置（cascade="all, delete-orphan"），
    # 所以删除 Material 会自动删除关联的 Attachments
    db.delete(db_obj)
    db.commit()
    return True


def increment_view_count(db: Session, material_id: int):
    """增加阅读量"""
    db_obj = get_material(db, material_id)
    if db_obj:
        db_obj.view_count += 1
        db.commit()


# ==========================================
# 附件管理 (Attachment)
# ==========================================

def create_party_attachment(
        db: Session,
        material_id: int,
        uploaded_by: int,
        file_name: str,
        file_path: str,
        file_size: int,
        file_type: str
):
    db_obj = PartyAttachment(
        material_id=material_id,
        uploaded_by=uploaded_by,
        file_name=file_name,
        file_path=file_path,
        file_size=file_size,
        file_type=file_type
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_party_attachment(db: Session, attachment_id: int) -> bool:
    # 物理文件删除需要在 API 层结合 os.remove 进行，这里只删库
    attachment = db.query(PartyAttachment).filter(PartyAttachment.id == attachment_id).first()
    if not attachment:
        return False
    db.delete(attachment)
    db.commit()
    return True

def get_attachment(db: Session, attachment_id: int):
    return db.query(PartyAttachment).filter(PartyAttachment.id == attachment_id).first()