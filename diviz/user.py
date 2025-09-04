from pydantic import BaseModel

class User(BaseModel):
    username: str | None = None
    email: str
    name: str | None = None
    groups: list[str] | None = None
    id: str | None = None # User ID
    ext_id: str | None = None # External ID from IDP provider
    ext_type: str | None = None # External ID type

    def mailto(self):
        return f"mailto:{self.username} <{self.email}>"
