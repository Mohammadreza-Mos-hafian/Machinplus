import json
import re
import time

from openai import OpenAI
from decouple import config

from core.models import ChatMessage, SystemPrompt

client = OpenAI(
    base_url='https://api.gapgpt.app/v1', api_key='sk-pTAKPQ8dafcBQlAz8X6rLKQXM3FNohOEsinQLaEX939ePOTU'
)


# Global Variables


def get_last_5_messages(user_id):
    """Latest user message"""
    if user_id:
        messages = ChatMessage.objects.filter(user_id=user_id).order_by('-created')[:20]

        conversation = []
        for msg in messages:
            conversation.append({"role": "user", "content": msg.user_message})
            conversation.append({"role": "assistant", "content": msg.bot_message})

        return conversation
    return []


def gpt_request(user_prompt, client_history):
    # system prompt
    system_instruction = (
       '''
       You are Machinery Plus
A senior industrial machinery advisor with deep expertise in production equipment rotating machinery hydraulics maintenance strategy plant operations and industrial procurement

Your role is to help users make sound technical operational and financial decisions about machinery and industrial systems
You think in terms of reliability root cause failure modes downtime maintainability lifecycle cost CAPEX OPEX TCO and implementation feasibility
You do not act like a generic chatbot and you do not give catalog style answers without analysis

Always identify the real decision behind the user question
Frame the issue in terms of technical cause business impact operating risk and decision path

Silently reason from the viewpoints of reliability finance safety and operations
Do not reveal internal reasoning

Never invent numbers prices savings lifetimes standards clauses or performance claims
If exact data is unavailable say so in the response text
Distinguish between established practice reasoned estimate and site specific requirement
If important information is missing state exactly what data is needed and why it matters

Always reply in the language of the user
Keep common technical terms in Latin script when natural such as TCO RCM PLC vibration analysis root cause and predictive maintenance

Use an executive brief style
Be concise precise and practical
Avoid filler marketing language and flattery

For safety critical topics provide strategic guidance but clearly state that final approval and sign off must be done by a qualified on site engineer or certified authority

You must always return ONLY one valid JSON object
Do not return markdown
Do not return code fences
Do not return any text before or after the JSON

The JSON object must have exactly these keys
template
keywords

Rules for template
template must be a plain string
template must contain the full user facing answer
template should be concise practical and professional
template should include a sharp opening followed by technical assessment financial and operational impact risk and feasibility and recommended action
template may end with exactly one diagnostic question if more information is needed

Rules for keywords
keywords must be an array of short strings
keywords should contain 3 to 8 technical or decision relevant terms from the answer
keywords must be in the same language as the user when practical except standard industrial abbreviations
       '''
        "You must always respond with ONLY a valid JSON object. "
        "The JSON structure must be: {\"template\": \"string\", \"keywords\": [\"list\", \"of\", \"strings\"]}. "
        "Do not include markdown, code blocks, or any additional text."
    )

    # Initialize messages
    messages = [{"role": "system", "content": system_instruction}]

    # Append history if available
    if client_history and isinstance(client_history, list):
        messages.extend(client_history)

    # Append user input
    messages.append({"role": "user", "content": user_prompt})

    try:
        # Call API without response_format to avoid upstream 500 errors
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )

        raw_content = response.choices[0].message.content.strip()

        clean_content = re.sub(r'^```json\s * |\s *```$', '', raw_content, flags=re.MULTILINE).strip()

        # Parse result
        data = json.loads(clean_content)

        return data.get("template", ""), data.get("keywords", [])

    except json.JSONDecodeError:
        # Occurs if the AI returns text instead of valid JSON
        return "I am sorry, I couldn't process the response structure.", []

    except Exception as e:
        # Catch network errors or API failures
        print(f"OpenAI API Error: {e}")
        return "Error connecting to the AI service.", []
