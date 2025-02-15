from pdf2image import convert_from_bytes
import os
import tempfile
from PIL import Image
from django.core.files.base import ContentFile

# ✅ Poppler 경로 (Mac Homebrew 환경)
POPPLER_PATH = "/opt/homebrew/bin"


def convert_to_fax_tiff(files):
    images = []
    for file in files:
        try:
            if file.name.lower().endswith(".pdf"):
                print(f"📜 PDF 변환 시작: {file.name}")  # ✅ 디버깅 로그
                pdf_images = convert_from_bytes(file.read(), dpi=300, poppler_path=POPPLER_PATH)

                # ✅ PDF 이미지를 1-bit (TIFF G4 지원 가능)로 변환
                pdf_images = [img.convert("1") for img in pdf_images]
                images.extend(pdf_images)
                print(f"✅ PDF 변환 완료, 페이지 수: {len(pdf_images)}")
            else:
                print(f"🖼 이미지 변환 시작: {file.name}")
                img = Image.open(file).convert("1")  # ✅ 1-bit 변환
                images.append(img)
                print(f"✅ 이미지 변환 완료")
        except Exception as e:
            print(f"❌ 변환 실패: {str(e)}")
            raise ValueError(f"파일 변환 실패: {str(e)}")

    if not images:
        raise ValueError("변환할 이미지가 없습니다.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".tiff") as temp_file:
        temp_filename = temp_file.name
        images[0].save(temp_filename, format="TIFF", compression="group4", save_all=True, append_images=images[1:])
        print(f"📂 TIFF 파일 저장 완료: {temp_filename}")

    with open(temp_filename, "rb") as converted_file:
        content = ContentFile(converted_file.read(), name="merged_fax.tiff")

    os.remove(temp_filename)  # ✅ 임시 파일 삭제
    return content
