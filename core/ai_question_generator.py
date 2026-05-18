"""
AI-Powered Question Generator
Uses Google Gemini API (free tier - 1500 requests/day).
Endpoint: generativelanguage.googleapis.com
"""
import json
import re
import requests
from typing import List, Dict, Optional
from django.conf import settings


class APINotConfiguredError(Exception):
    """Raised when HUGGINGFACE_API_TOKEN is not set."""
    pass


class APIGenerationError(Exception):
    """Raised when the API call fails or returns unusable output."""
    pass


class AIQuestionGenerator:
    """Generates quiz questions via the Google Gemini API."""

    def __init__(self):
        self.token = getattr(settings, 'HUGGINGFACE_API_TOKEN', '').strip()

    def _call_hf(self, prompt: str, max_tokens: int = 2000) -> Optional[str]:
        """Call Llama via Hugging Face Inference API."""
        try:
            response = requests.post(
                "https://router.huggingface.co/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "meta-llama/Llama-3.1-8B-Instruct",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.3,
                    "stream": False,
                },
                timeout=60,
            )
        except requests.RequestException as exc:
            raise APIGenerationError(f"Network error contacting Hugging Face: {exc}") from exc

        if response.status_code == 401:
            raise APIGenerationError("Invalid Hugging Face token. Check your HUGGINGFACE_API_TOKEN in .env.")
        if response.status_code == 429:
            raise APIGenerationError("Hugging Face rate limit reached. Wait a moment and try again.")
        if response.status_code != 200:
            raise APIGenerationError(f"Hugging Face returned HTTP {response.status_code}: {response.text[:300]}")

        try:
            return response.json()["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError) as exc:
            raise APIGenerationError(f"Unexpected response structure: {response.text[:300]}") from exc

    def generate_questions(
        self,
        text: str,
        num_questions: int = 5,
        question_types: Optional[List[str]] = None,
    ) -> List[Dict]:
        if not self.token:
            raise APINotConfiguredError(
                "GEMINI_API_KEY is not set. "
                "Add HUGGINGFACE_API_TOKEN to your .env file and restart the server."
            )

        if question_types is None:
            question_types = ['MCQ']

        truncated = text[:4000] if len(text) > 4000 else text

        type_instructions = {
            'MCQ':   'multiple choice questions, each with exactly 4 options',
            'TF':    'true/false questions',
            'SHORT': 'short answer questions (no options needed)',
        }
        types_desc = ' and '.join(
            type_instructions[t] for t in question_types if t in type_instructions
        )

        prompt = f"""You are an expert university quiz generator. Read the study material below and generate exactly {num_questions} {types_desc}.

Rules:
- Base every question strictly on the study material — do not invent facts
- Return ONLY a valid JSON array, no markdown, no explanation, nothing else
- Each object must have these exact keys:
  "question": the question text
  "type": "MCQ", "TF", or "SHORT"
  "options": list of strings — 4 options for MCQ, ["True","False"] for TF, [] for SHORT
  "correct_answer": exact correct answer string matching one of the options for MCQ/TF
  "explanation": one sentence from the material justifying the answer

STUDY MATERIAL:
{truncated}

Output only the JSON array starting with [ and ending with ]."""

        raw = self._call_hf(prompt, max_tokens=2000)
        questions_data = self._extract_json(raw)

        if not questions_data:
            raise APIGenerationError(
                f"Could not parse questions from model response. Raw: {raw[:300]}"
            )

        return self._normalise(questions_data, num_questions)

    def _extract_json(self, raw: str) -> Optional[List[Dict]]:
        cleaned = re.sub(r'^```(?:json)?\s*', '', raw.strip())
        cleaned = re.sub(r'\s*```$', '', cleaned).strip()
        try:
            data = json.loads(cleaned)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass
        match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                if isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                pass
        return None

    def _normalise(self, raw: List[Dict], limit: int) -> List[Dict]:
        result = []
        for i, item in enumerate(raw[:limit]):
            question_text = (item.get('question') or item.get('question_text', '')).strip()
            if not question_text:
                continue
            q_type = (item.get('type') or item.get('question_type', 'MCQ')).upper()
            if q_type not in ('MCQ', 'TF', 'SHORT'):
                q_type = 'MCQ'
            options = item.get('options', [])
            if isinstance(options, str):
                try:
                    options = json.loads(options)
                except json.JSONDecodeError:
                    options = []
            if q_type == 'TF':
                options = ['True', 'False']
            correct_answer = str(item.get('correct_answer', '')).strip()
            explanation = str(item.get('explanation', '')).strip()
            result.append({
                'question_text':  question_text,
                'question_type':  q_type,
                'options':        json.dumps(options),
                'correct_answer': correct_answer,
                'explanation':    explanation,
                'order':          i + 1,
            })
        return result


def generate_ai_questions(
    text: str,
    num_questions: int = 5,
    question_types: Optional[List[str]] = None,
) -> List[Dict]:
    """
    Generate quiz questions via Google Gemini API (free tier).
    Raises APINotConfiguredError or APIGenerationError on failure.
    """
    generator = AIQuestionGenerator()
    return generator.generate_questions(text, num_questions, question_types)
