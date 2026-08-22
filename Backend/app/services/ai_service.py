import re
import json
import httpx
from typing import Dict, Any
from app.core.config import settings
from app.schemas.request import RequirementParseResult


class AIService:
    @staticmethod
    async def parse_requirement(raw_description: str) -> RequirementParseResult:
        """
        Parses a natural-language service requirement into structured JSON.
        Uses AI API if AI_API_KEY is available; otherwise uses deterministic fallback parser.
        """
        if settings.AI_API_KEY and settings.AI_API_KEY.strip():
            try:
                result = await AIService._parse_with_ai(raw_description)
                if result:
                    return result
            except Exception as e:
                # Fallback on AI error
                pass

        return AIService._parse_with_fallback(raw_description)

    @staticmethod
    async def _parse_with_ai(raw_description: str) -> RequirementParseResult:
        """Call AI provider API with structured output prompt."""
        system_prompt = (
            "You are an expert requirement parser for LocalConnect, a hyperlocal service platform in India.\n"
            "Convert the user's natural language input (English or Hinglish) into a JSON object matching this schema:\n"
            "{\n"
            '  "category": string or null,\n'
            '  "service": string or null,\n'
            '  "skills": list of strings,\n'
            '  "budget_min": number or null,\n'
            '  "budget_max": number or null,\n'
            '  "radius_km": number or null (default 5.0),\n'
            '  "availability": list of day strings (e.g. ["Saturday", "Sunday"]),\n'
            '  "level": string or null (e.g. "Class 10"),\n'
            '  "preferences": object,\n'
            '  "confidence": number between 0.0 and 1.0\n'
            "}\n"
            "Do NOT invent missing information. Only extract what is clearly stated or directly implied."
        )

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.AI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": raw_description},
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1,
                },
            )
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                parsed_json = json.loads(content)
                return RequirementParseResult(**parsed_json)
        return None

    @staticmethod
    def _parse_with_fallback(raw_description: str) -> RequirementParseResult:
        """
        Deterministic keyword & regex fallback parser for English and Hinglish requirements.
        Extracts budget, availability, categories, services, and skills.
        """
        text = raw_description.lower()

        # Category & Service Detection
        category = None
        service = None
        skills = []

        if any(w in text for w in ["math", "maths", "tutor", "tuition", "teacher", "class 10", "12th"]):
            category = "Education"
            service = "Math Tutor"
            skills.append("Mathematics")
            if "class 10" in text or "10th" in text:
                skills.append("Class 10 Mathematics")
            if "class 12" in text or "12th" in text:
                skills.append("Class 12 Mathematics")

        elif any(w in text for w in ["plumber", "pipe", "leak", "tap"]):
            category = "Home Maintenance"
            service = "Plumbing"
            skills.append("Plumbing Repairs")

        elif any(w in text for w in ["electrician", "wiring", "light", "switch", "power"]):
            category = "Home Maintenance"
            service = "Electrical Service"
            skills.append("Electrical Repairs")

        elif any(w in text for w in ["clean", "cleaning", "maid", "housekeeping"]):
            category = "Home Maintenance"
            service = "Home Cleaning"
            skills.append("Deep Cleaning")

        elif any(w in text for w in ["photo", "photographer", "video", "wedding"]):
            category = "Creative & Tech"
            service = "Photography"
            skills.append("Event Photography")

        elif any(w in text for w in ["ui", "ux", "design", "designer", "website", "developer"]):
            category = "Creative & Tech"
            service = "UI/UX Design"
            skills.append("UI Design")

        # Budget extraction (INR / Rs / ₹ / "under 500" / "under ₹500" / "500 ke andar")
        budget_max = None
        budget_min = None
        budget_match = re.search(r"(?:under|below|max|within|₹|rs\.?|inr)?\s*(\d{3,5})\s*(?:rs|inr|₹|ke andar)?", text)
        if budget_match:
            try:
                val = float(budget_match.group(1))
                if val >= 100:  # reasonable minimum budget threshold
                    budget_max = val
            except ValueError:
                pass

        # Availability extraction
        availability = []
        if "weekend" in text or "saturday" in text or "sunday" in text:
            availability.extend(["Saturday", "Sunday"])
        if "weekday" in text or "monday" in text:
            availability.extend(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])

        # Radius extraction
        radius_km = 5.0
        radius_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:km|kilometer|kilometers)", text)
        if radius_match:
            try:
                radius_km = float(radius_match.group(1))
            except ValueError:
                pass

        return RequirementParseResult(
            category=category,
            service=service,
            skills=skills,
            budget_min=budget_min,
            budget_max=budget_max,
            radius_km=radius_km,
            availability=availability,
            confidence=0.85 if (category and service) else 0.60,
        )
