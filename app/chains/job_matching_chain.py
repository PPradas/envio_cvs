import os
from typing import List

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


class JobMatch(BaseModel):
    score: int = Field(description="Match percentage from 0 to 100")
    matching_skills: List[str] = Field(description="Technical skills from the CV that match job requirements")
    missing_skills: List[str] = Field(description="Required skills not found in the CV")
    explanation: str = Field(description="One sentence explaining the score")


def create_job_matching_chain():
    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        temperature=0,
        timeout=60,
    ).with_structured_output(JobMatch)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            (
                "You are a job matching expert. "
                "Score how well a candidate's profile fits a job offer on a scale of 0–100. "
                "Criteria: technical skills overlap (50 %), experience level and role fit (30 %), "
                "seniority match (20 %). Be objective and concise."
            ),
        ),
        (
            "human",
            (
                "CANDIDATE PROFILE\n"
                "Current title: {current_title}\n"
                "Years in current role: {years_in_current_role}\n"
                "Technical skills: {technical_skills}\n"
                "Recent experience: {recent_experience}\n\n"
                "JOB OFFER\n"
                "Title: {job_title}\n"
                "Company: {company}\n"
                "Required skills: {required_skills}\n"
                "Experience required: {experience_min}–{experience_max} years\n"
                "Description: {description}"
            ),
        ),
    ])

    return (prompt | llm).with_retry(stop_after_attempt=3)
