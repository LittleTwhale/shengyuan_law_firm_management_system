from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
import os
import mimetypes

router = APIRouter(
    prefix="/template",
    tags=["template"]
)

# 模板文件目录
TEMPLATE_DIR = os.path.join("FastAPI", "static", "template")

@router.get("/download")
async def download_template(filename: str = Query(..., description="要下载的文件名")):
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
