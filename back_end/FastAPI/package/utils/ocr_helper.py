# utils/ocr_helper.py
import logging
import os
import cv2
import numpy as np

# ============================================================
# 【第一道防线】环境变量配置
# 必须在 import paddle 之前设置
# ============================================================

# 1. 禁用 PIR (新版执行器) - 解决 Windows 崩溃的核心
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_enable_pir_in_executor"] = "0"

# 2. 禁用 MKLDNN (加速库) - 解决识别结果为空/兼容性问题
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_mkldnn"] = "0"
os.environ["DN_ENABLE_ONEDNN"] = "0"

# PDF与Word处理
import pdfplumber
from docx import Document
# OCR处理
from paddleocr import PaddleOCR

logger = logging.getLogger(__name__)

# ============================================================
# 初始化 PaddleOCR
# ============================================================
ocr_engine = None

print("--- 正在初始化 PaddleOCR (Minimal Mode) ---")
try:
    # 【修复 1】: 去掉所有报错的参数 (use_gpu, show_log, enable_mkldnn)
    # 既然环境变量已经禁用了 mkldnn，这里不需要再传参数
    # 既然 use_gpu 报错，说明它内部可能自动管理或参数名变了，直接去掉
    ocr_engine = PaddleOCR(
        use_angle_cls=True,  # 开启方向检测
        lang="ch",  # 中文
        ocr_version="PP-OCRv4"  # 尝试强制指定 v4 (更稳定)
    )
    print("--- PaddleOCR 初始化成功 (v4) ---")
    logger.info("PaddleOCR initialized successfully.")

except Exception as e:
    print(f"!!! PaddleOCR v4 初始化出错: {e}")

    try:
        print("--- 尝试最简参数兜底初始化 ---")
        # 如果 v4 指定失败，完全交给默认值
        ocr_engine = PaddleOCR(use_angle_cls=True, lang="ch")
        print("--- PaddleOCR 初始化成功 (Default) ---")
    except Exception as e2:
        print(f"!!! PaddleOCR 彻底失败: {e2}")
        ocr_engine = None


def extract_text_from_docx(file_path: str) -> str:
    """提取 Word (.docx) 文本"""
    try:
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        logger.error(f"Docx error: {e}")
        return ""


def _read_image_robust(file_path: str):
    """
    读取图片：解决 Windows 中文路径问题
    """
    try:
        if not os.path.exists(file_path):
            return None
        return cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    except Exception as e:
        logger.error(f"Image read error: {e}")
        return None


def _ocr_image_data(image_data) -> str:
    """
    辅助函数：对图片数据进行 PaddleOCR 识别
    """
    if ocr_engine is None:
        return "错误：OCR模型未成功启动"

    try:
        # 【修复 2】: 移除 cls=True 参数
        # 错误日志明确指出 "unexpected keyword argument 'cls'"
        # 新版 API 中，只要初始化时设置了 use_angle_cls=True，
        # 这里直接传 image_data 即可。
        result = ocr_engine.ocr(image_data)

        page_text = []
        if result is None:
            return ""

        # 结果解析兼容
        # PaddleOCR 返回结构通常是列表的列表
        ocr_res = result[0] if result else None

        if isinstance(ocr_res, list):
            for line in ocr_res:
                # line 结构预期: [[box], ['text', score]]
                if isinstance(line, list) and len(line) >= 2 and line[1]:
                    text_content = line[1][0]
                    page_text.append(text_content)

        return "\n".join(page_text)

    except Exception as e:
        error_msg = f"[OCR运行时错误: {str(e)}]"
        logger.error(error_msg)
        print(f"!!! {error_msg}")
        return error_msg


def extract_pdf_hybrid(file_path: str, min_text_len: int = 50) -> str:
    """
    PDF 混合提取策略
    """
    full_content = []

    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                # 1. 尝试直接提取文本
                text = page.extract_text() or ""
                clean_text = text.replace(" ", "").replace("\n", "")

                if len(clean_text) > min_text_len:
                    full_content.append(f"--- 第 {i + 1} 页 (电子提取) ---\n{text}")
                else:
                    # Case B: 扫描件 -> 图片 -> OCR
                    # 200dpi 够用且快
                    pil_image = page.to_image(resolution=200).original

                    img_array = np.array(pil_image)
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

                    ocr_text = _ocr_image_data(img_array)
                    full_content.append(f"--- 第 {i + 1} 页 (OCR识别) ---\n{ocr_text}")

    except Exception as e:
        logger.error(f"PDF Hybrid Extract Error: {e}")
        return f"PDF处理错误: {str(e)}"

    return "\n\n".join(full_content)


def perform_smart_extraction(file_path: str, file_type: str) -> str:
    """
    统一入口：智能识别文件内容
    """
    if not os.path.exists(file_path):
        return "文件路径不存在"

    file_ext = os.path.splitext(file_path)[1].lower()

    try:
        # 1. Word (.docx)
        if file_ext == '.docx':
            return extract_text_from_docx(file_path)

        # 2. Word (.doc)
        if file_ext == '.doc':
            pdf_path = os.path.splitext(file_path)[0] + ".pdf"
            if os.path.exists(pdf_path):
                return extract_pdf_hybrid(pdf_path)
            else:
                return "待转换PDF文件未找到"

        # 3. PDF
        if file_ext == '.pdf' or file_type == 'application/pdf':
            return extract_pdf_hybrid(file_path)

        # 4. 图片
        if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.webp']:
            img_array = _read_image_robust(file_path)
            if img_array is not None:
                return _ocr_image_data(img_array)
            else:
                return "图片读取失败"
    except Exception as e:
        logger.error(f"Extraction execution failed: {e}")
        return ""

    return ""