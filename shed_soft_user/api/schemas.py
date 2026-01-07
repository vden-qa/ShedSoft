from pydantic import BaseModel


class SUserId(BaseModel):
    user_id: str


class AddRealm(BaseModel):
    realm_name: str


class AddUser(BaseModel):
    id: str
    email: str
    email_verified: bool
    name: str
    preferred_username: str
    given_name: str
    family_name: str
    realm_id: int


class AddNote(BaseModel):
    title: str
    content: str


class AddNoteWithUserId(AddNote, SUserId):
    pass


class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    user_id: str

    class Config:
        from_attributes = True
