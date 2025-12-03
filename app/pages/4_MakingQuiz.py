import React, { useState } from "react";
import OpenAI from "openai";
import { useProject } from "../ProjectContext";

export default function QuizPage() {
  const { projectData, updateProjectData } = useProject();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(projectData.quiz || "");

  const generateQuiz = async () => {
    if (!projectData.apiKey) {
      setError("❗ OpenAI API Key가 없습니다. 1페이지에서 입력하세요.");
      return;
    }

    if (!projectData.content) {
      setError("❗ 업로드한 자료가 없습니다.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const openai = new OpenAI({ apiKey: projectData.apiKey });

      const prompt = `
다음 학습 자료를 기반으로 중요한 내용을 평가하는 연습문제를 만들어줘.

[자료 내용]
${projectData.content}

요구사항:
- 총 5문제
- 객관식 3문제 + 서술형 2문제
- 객관식은 보기 4개 포함
- 정답을 문제 아래에 "정답:" 형식으로 명시
- JSON 형태로 반환:
{
  "questions": [
    {
      "type": "multiple-choice" | "short-answer",
      "question": "",
      "choices": [],    // 객관식이면 포함, 서술형은 빈 배열
      "answer": ""
    }
  ]
}
`;

      const completion = await openai.responses.create({
        model: "gpt-4.1",
        input: prompt,
      });

      const responseText = completion.output_text;

      setResult(responseText);

      // Context에 저장 → 메모하는 기능
      updateProjectData({ quiz: responseText });
    } catch (err) {
      console.error(err);
      setError("❗ 연습문제 생성 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "24px" }}>
      <h2>연습 문제 생성</h2>

      <button onClick={generateQuiz} disabled={loading}>
        {loading ? "생성 중..." : "연습문제 생성하기"}
      </button>

      {error && <p style={{ color: "red" }}>{error}</p>}

      {result && (
        <div style={{ marginTop: "20px", whiteSpace: "pre-wrap" }}>
          <h3>생성된 연습문제</h3>
          <pre>{result}</pre>
        </div>
      )}
    </div>
  );
}
