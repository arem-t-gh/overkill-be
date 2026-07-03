from user.models import UserRead


class UserReadWithAccessToken(UserRead):
    access_token: str
