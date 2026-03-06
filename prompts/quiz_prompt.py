# quiz_prompt.py

QUIZ_PROMPTS = {
    "math":  """
Use this summary to generate multiple-choice questions covering all key points.
Avoid repeated questions. Make questions clear and concise, generate 5 quiz questions.

Return the result ONLY in valid JSON format.

Format:

[
  {{
    "question": "question text",
    "options": [
      "A. option",
      "B. option",
      "C. option",
      "D. option"
    ],
    "answer": "B",
    "explanation": "short explanation"
  }}
]

Material:
{material}
"""
,
    "history":  """
Use this summary to generate multiple-choice questions covering all key points.
Avoid repeated questions. Make questions clear and concise. generate 5 quiz questions.

Return the result ONLY in valid JSON format.

Format:

[
  {{
    "question": "question text",
    "options": [
      "A. option",
      "B. option",
      "C. option",
      "D. option"
    ],
    "answer": "B",
    "explanation": "short explanation"
   }}
]

Material:
{material}
""",
    "finance": """
Use this summary to generate multiple-choice questions covering all key points.
Avoid repeated questions. Make questions clear and concise, generate 5 quiz questions.

Return the result ONLY in valid JSON format.

Format:

[
  {{
    "question": "question text",
    "options": [
      "A. option",
      "B. option",
      "C. option",
      "D. option"
    ],
    "answer": "B",
    "explanation": "short explanation"
   }}
]

Material:
{material}
""",
    "art": """
Use this summary to generate multiple-choice questions covering all key points.
Avoid repeated questions. Make questions clear and concise, generate 5 quiz questions.

Return the result ONLY in valid JSON format.

Format:

[
  {{
    "question": "question text",
    "options": [
      "A. option",
      "B. option",
      "C. option",
      "D. option"
    ],
    "answer": "B",
    "explanation": "short explanation"
  }}
]

Material:
{material}
""",
   "medical": """
Use this summary to generate multiple-choice questions covering all key points.
Avoid repeated questions. Make questions clear and concise, generate 5 quiz questions.

Return the result ONLY in valid JSON format.

Format:

[
  {{
    "question": "question text",
    "options": [
      "A. option",
      "B. option",
      "C. option",
      "D. option"
    ],
    "answer": "B",
    "explanation": "short explanation"
  }}
]

Material:
{material}
"""

}