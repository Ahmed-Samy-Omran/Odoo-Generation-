import os
import shutil
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.models.schemas import GeneratorPayload
from app.generators.OdooModuleGenerator import OdooModuleGenerator
from app.services.zip_handler import ZipHandler
from app.services.ai_service import AIService

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


@app.get("/")
def read_root():
    return {"message": "Welcome to Odoo AI Module Generator API. Use /docs for documentation."}


@app.post("/generate-module/")
async def generate_module(payload: GeneratorPayload):
    """
    يستقبل تكوين الموديولات كـ JSON، يقوم بتوليد الملفات، ثم يرجع ملف ZIP يحتوي عليها جميعًا.
    """
    try:
        payload_data = payload.model_dump()
        modules = payload_data.get("modules", [])
        if not modules:
            raise HTTPException(status_code=400, detail="No modules specified in configuration")

        generator = OdooModuleGenerator(templates_dir=TEMPLATES_DIR)
        module_paths = []
        
        for config_data in modules:
            module_path = generator.generate_module(config_data, output_dir=OUTPUT_DIR)
            module_paths.append(module_path)

        zip_name = f"{modules[0].get('module_name', 'custom_module')}_batch.zip" if len(modules) > 1 else f"{modules[0].get('module_name', 'custom_module')}.zip"
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

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-requirements/")
async def analyze_requirements_and_generate(user_prompt: UserPrompt):
    """
    يستقبل وصفًا نصيًا للموديول، يستخدم AI لتحليله، ثم يولد ملف ZIP للموديول.
    """
    try:
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
        zip_name = f"{modules[0].get('module_name', 'custom_module')}_batch.zip" if len(modules) > 1 else f"{modules[0].get('module_name', 'custom_module')}.zip"
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

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"An error occurred during AI analysis or module generation: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)