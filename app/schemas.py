from pydantic import BaseModel, Field

class WeekendCreate(BaseModel):
    saturday: str  # YYYY-MM-DD
    on_duty_team: str  # 'A' | 'B'

class SundayAssignmentsIn(BaseModel):
    morning: list[str] = Field(default_factory=list)
    afternoon: list[str] = Field(default_factory=list)
