from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

app = FastAPI()

# CORS 허용 (React와 연결)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 입력 데이터 모델
class QuizRequest(BaseModel):
    apiKey: str
    content: str

# 연습문제 생성 API
@app.post("/generate-quiz")
async def generate_quiz(payload: QuizRequest):
    client = OpenAI(api_key=payload.apiKey)

    prompt = f"""
다음 학습 자료를 기반으로 중요한 내용을 평가하는 연습문제를 만들어줘.

[자료 내용]
{payload.content}

요구사항:
- 총 5문제
- 객관식 3문제 + 서술형 2문제
- 객관식은 보기 4개 포함
- 정답을 문제 아래에 "정답:" 형식으로 명시
- 반드시 JSON 형태로 반환:

{{
  "questions": [
    {{
      "type": "multiple-choice" | "short-answer",
      "question": "",
      "choices": [],
      "answer": ""
    }}
  ]
}}
"""

    response = client.responses.create(
        model="gpt-4.1",
        input=prompt
    )

    # 최종 텍스트(Raw JSON)
    text_output = response.output_text

    return {
        "quiz": text_output
    }

