import base64
import os
from typing import List

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field


class WorkExperience(BaseModel):
    company: str = Field(description="Company name")
    title: str = Field(description="Job title held at this company")
    start_date: str = Field(description="Start date (e.g. 'Jan 2020' or '2020')")
    end_date: str = Field(description="End date or 'Present' if current")
    description: str = Field(description="Brief description of responsibilities and achievements")


class EducationEntry(BaseModel):
    institution: str = Field(description="Name of the educational institution")
    degree: str = Field(description="Degree, certification or course name")
    start_date: str = Field(description="Start date or year")
    end_date: str = Field(description="End date or year")
    description: str = Field(default="", description="Additional details or achievements")


class CVProfile(BaseModel):
    name: str = Field(description="Full name of the candidate")
    email: str = Field(default="", description="Email address if found")
    current_title: str = Field(description="Current or most recent job title")
    years_in_current_role: int = Field(description="Years of experience in the current or most recent role")
    summary: str = Field(description="2–3 sentence professional summary")
    work_experience: List[WorkExperience] = Field(description="Work history, most recent first")
    education: List[EducationEntry] = Field(description="Educational background, most recent first")
    technical_skills: List[str] = Field(description="All technical skills, tools and frameworks mentioned")
    languages: List[str] = Field(description="Human languages spoken with level if available")


_SYSTEM = (
    "You are an expert CV/resume parser. "
    "Extract ALL structured information from the CV provided. "
    "For work_experience and education include every entry you find. "
    "Be exhaustive with technical_skills. "
    "Infer years_in_current_role from the dates of the most recent job."
)


def create_cv_extraction_chain():
    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        temperature=0,
        timeout=60,
    ).with_structured_output(CVProfile)

    def _invoke(input_dict: dict) -> CVProfile:
        pdf_bytes: bytes = input_dict["pdf_bytes"]
        b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")
        messages = [
            SystemMessage(content=_SYSTEM),
            HumanMessage(content=[
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": b64,
                    },
                },
                {"type": "text", "text": "Parse this CV and extract all information."},
            ]),
        ]
        return llm.invoke(messages)

    return _invoke
