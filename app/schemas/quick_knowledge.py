from typing import Optional

from pydantic import BaseModel


class UserInfo(BaseModel):

    name: Optional[str] = None

    location: Optional[str] = None

    district: Optional[str] = None
    
    state: Optional[str] = None

class QuickKnowledgeRequest(BaseModel):

    userinfo: Optional[UserInfo] = None

    knowledge: str