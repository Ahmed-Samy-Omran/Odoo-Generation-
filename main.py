import os
import shutil
import httpx
import json
import logging
import traceback
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.models.schemas import GeneratorPayload
from app.generators.OdooModuleGenerator import OdooModuleGenerator
from app.services.zip_handler import ZipHandler
from app.services.ai_service import AIService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Odoo AI Module Generator",
    description="API to generate Odoo modules from JSON configuration",
    version="1.0.0"
)

# الحصول على المسارات الأساسية
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
OUTPUT_DIR = os.path.join(BASE_DIR, "generated_modules")

# التأكد من وجود مجلد المخرجات
os.makedirs(OUTPUT_DIR, exist_ok=True)

ai_service = AIService()


class UserPrompt(BaseModel):
    prompt: str


# Global Exception Handlers
@app.exception_handler(httpx.ConnectError)
async def http_connect_error_handler(request: Request, exc: httpx.ConnectError):
    logger.error(f"HTTP Connect Error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "success": False,
            "error_type": "NETWORK_ERROR",
            "message": "Could not connect to an external service. Please check network connectivity.",
            "debug_details": str(exc)
        },
    )


@app.exception_handler(json.JSONDecodeError)
async def json_decode_error_handler(request: Request, exc: json.JSONDecodeError):
    logger.error(f"JSON Decode Error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error_type": "INVALID_JSON",
            "message": "The request body contains invalid JSON data.",
            "debug_details": str(exc)
        },
    )


@app.exception_handler(OSError)
async def os_error_handler(request: Request, exc: OSError):
    logger.error(f"OS Error (File System): {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_type": "STORAGE_ERROR",
            "message": "A file system error occurred. Please try again or contact support.",
            "debug_details": str(exc)
        },
    )


@app.exception_handler(Exception)
async def catch_all_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_type": "UNKNOWN_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
            "debug_details": traceback.format_exc()
        },
    )


@app.get("/")
def read_root():
    return {"message": "Welcome to Odoo AI Module Generator API. Use /docs for documentation."}


@app.post("/generate-module/")
async def generate_module(payload: GeneratorPayload):
    """
    يستقبل تكوين الموديولات كـ JSON، يقوم بتوليد الملفات، ثم يرجع ملف ZIP يحتوي عليها جميعًا.
    """
    payload_data = payload.model_dump()
    modules = payload_data.get("modules", [])
    if not modules:
        raise HTTPException(status_code=400, detail="No modules specified in configuration")

    generator = OdooModuleGenerator(templates_dir=TEMPLATES_DIR)
    module_paths = []

    for config_data in modules:
        module_path = generator.generate_module(config_data, output_dir=OUTPUT_DIR)
        module_paths.append(module_path)

    zip_name = f"{modules[0].get('module_name', 'custom_module')}_batch.zip" if len(
        modules) > 1 else f"{modules[0].get('module_name', 'custom_module')}.zip"
    zip_path = os.path.join(OUTPUT_DIR, zip_name)

    ZipHandler.create_batch_zip(module_paths, zip_path)

    if os.path.exists(zip_path):
        return FileResponse(
            path=zip_path,
            filename=zip_name,
            media_type="application/x-zip-compressed"
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to create ZIP file")


@app.post("/analyze-requirements/")
async def analyze_requirements_and_generate(user_prompt: UserPrompt):
    """
    يستقبل وصفًا نصيًا للموديول، يستخدم AI لتحليله، ثم يولد ملف ZIP للموديول.
    """
    # 1. تحليل متطلبات المستخدم باستخدام AI
    payload = ai_service.analyze_requirements(user_prompt.prompt)

    # 2. تحويل Pydantic model إلى dictionary
    payload_data = payload.model_dump()
    modules = payload_data.get("modules", [])
    if not modules:
        raise HTTPException(status_code=400, detail="No modules analyzed from the prompt")

    generator = OdooModuleGenerator(templates_dir=TEMPLATES_DIR)
    module_paths = []

    for config_data in modules:
        module_path = generator.generate_module(config_data, output_dir=OUTPUT_DIR)
        module_paths.append(module_path)

    # 3. ضغط الموديولات في ملف ZIP
    zip_name = f"{modules[0].get('module_name', 'custom_module')}_batch.zip" if len(
        modules) > 1 else f"{modules[0].get('module_name', 'custom_module')}.zip"
    zip_path = os.path.join(OUTPUT_DIR, zip_name)

    ZipHandler.create_batch_zip(module_paths, zip_path)

    # 4. إرجاع ملف الـ ZIP للمستخدم
    if os.path.exists(zip_path):
        return FileResponse(
            path=zip_path,
            filename=zip_name,
            media_type="application/x-zip-compressed"
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to create ZIP file")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
