from pydantic import BaseModel

class User(BaseModel):
    username: str | None = None
    email: str

    def mailto(self):
        return f"mailto:{self.username} <{self.email}>"
