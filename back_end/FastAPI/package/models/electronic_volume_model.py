# models/electronic_volume_model.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, func, JSON
from sqlalchemy.orm import relationship
from ..database.database import Base


class CaseVolume(Base):
    """
    案件电子卷宗-卷册表
    对应表: case_volumes
    """
    __tablename__ = "case_volumes"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    case_id = Column(Integer, ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=True, index=True,
                     comment="关联案件ID（独立卷宗时为空）")

    # 核心显示字段
    name = Column(String(100), nullable=False, comment="案卷名称")

    # 缓存优化字段
    merged_file_path = Column(String(512), nullable=True, comment="合并后的PDF文件路径 (缓存)")

    # 排序与位置
    sort_order = Column(Integer, default=0, comment="显示排序")
    physical_location = Column(String(255), nullable=True, comment="纸质原件存放位置")

    # 独立卷宗扩展字段
    is_standalone = Column(Integer, default=0, comment="是否独立卷宗（不绑定系统案件）")
    client_name = Column(String(100), nullable=True, comment="委托人姓名")
    client_phone = Column(String(20), nullable=True, comment="委托人电话")
    main_lawyer_name = Column(String(50), nullable=True, comment="主办律师")
    case_description = Column(String(500), nullable=True, comment="案件简要描述")
    category = Column(String(50), nullable=True, comment="案件类别")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="创建人ID")

    # 基础元数据
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.now(), server_onupdate=func.now(), nullable=False,
                        comment="更新时间")

    # ---------------- ORM 关系 ----------------

    # 1. 关联到 Case 表 (多对一)
    # back_populates 指向 Case 模型中的 volumes 属性
    case = relationship("Case", back_populates="volumes")

    # 2. 关联到卷内文件 (一对多)
    # cascade="all, delete-orphan" 表示删除卷册时，自动删除下面的所有文件记录
    files = relationship("VolumeFile", back_populates="volume", cascade="all, delete-orphan",
                         order_by="VolumeFile.sort_order")

    # 3. 关联到创建人
    creator = relationship("User", back_populates="created_standalone_volumes")


class VolumeFile(Base):
    """
    案件电子卷宗-卷内文件详情表
    对应表: volume_files
    """
    __tablename__ = "volume_files"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    volume_id = Column(Integer, ForeignKey("case_volumes.id", ondelete="CASCADE"), nullable=False, index=True,
                       comment="所属案卷ID")

    # 文件基础信息
    file_name = Column(String(255), nullable=False, index=True, comment="文件显示名称")
    file_path = Column(String(512), nullable=False, comment="文件存储路径")
    file_size = Column(Integer, default=0, comment="文件大小(字节)")
    file_type = Column(String(255), nullable=True, comment="文件类型")

    # 核心分类与排序
    category = Column(String(50), default='其他材料', nullable=False, index=True, comment="文件目录分类")
    sort_order = Column(Integer, default=0, comment="卷内排序")

    # 页码管理
    page_start = Column(Integer, nullable=True, comment="起始页码")
    page_end = Column(Integer, nullable=True, comment="结束页码")

    # 检索增强字段
    tags = Column(JSON, nullable=True, comment="标签数组")
    summary = Column(Text, nullable=True, comment="人工填写的摘要/备注")
    # 注意: MySQL中是longtext, SQLAlchemy中Text即可自动处理大文本
    ocr_content = Column(Text, nullable=True, comment="系统识别的全文文本")

    # 操作记录
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="上传人ID")
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False, comment="上传时间")

    # ---------------- ORM 关系 ----------------

    # 1. 关联到卷册 (多对一)
    volume = relationship("CaseVolume", back_populates="files")

    # 2. 关联到上传用户 (多对一)
    uploader = relationship("User", back_populates="uploaded_volume_files")

    @property
    def uploader_name(self):
        return self.uploader.real_name if self.uploader else None