from typing import Optional, List
from dataclasses import dataclass

@dataclass(frozen=True)
class ArticleModel:
    company_name: str
    company_details: str
    address: str
    detail_page_url: str
    source_url: str
    category: str
    company_website: str
    company_email: Optional[str]
    facebook: Optional[str]
    twitter: Optional[str]
    region: List[str]
    consultant_name: str
    consultant_email: str
    linkedin: str = ''
    instagram: str = ''
    performance_score: str = ''
    seo_score: str = ''
    status: str = ''
    updated_number: str = ''
    updated_email: str = ''
    pitch: str = ''
    assigned_email: str = ''
    agent_email: str = ''