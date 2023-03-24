"""
User backend handler for Noscrum
"""
import time
import logging
from typing import Optional
import bcrypt
from flask_login import UserMixin

# imports for JWT + FastAPI
import jwt
from pydantic import BaseModel
from sqlalchemy import Column

# from fastapi import Depends
# from fastapi.security import OAuth2PasswordBearer
# from typing import Optional, Dict
from noscrum_backend.config import (
    SECRET,
    JWT_ALGORITHM,
    JWT_AUDIENCE,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login/token")
from noscrum_backend.db import User, UserPreference, get_db

logger = logging.getLogger()


def _get_user(user_id):
    """
    Return user record given an identity value
    @param user_id user's identification value
    """
    return User.query.filter(User.id == user_id).first()


def get_user_by_username(username):
    """
    Return user record given a username request
    """
    return User.query.filter(User.username == username).first()


def get_preferences(user_id):
    """
    Get the preferences of the current user
    """
    return UserPreference.query.filter(UserPreference.user_id == user_id).all()


class UserToken:
    def __init__(self, username: str, expires: int, **kwargs):
        if expires > time.time():
            raise Exception("Invalid Token: Expired")
        self.username = username


class UserClass(UserMixin, BaseModel):
    """
    UserManager class for Noscrum
    handles all login/authentication actions
    """

    id: Optional[int]
    user: Optional[User]

    def __init__(self, user_id: str):
        super().__init__()
        self.user = _get_user(user_id)
        self._is_authenticated = super().is_authenticated
        if self.user is None:
            self._is_authenticated = False
            self.id = None
        else:
            self.id = int(self.user.id)

    @property
    def is_active(self) -> bool:
        """
        is_active property, which is from database is_active
        is used to determine spaces where blocked users may not go
        """
        if not isinstance(self.user, User) or not isinstance(self.user.active, bool):
            return False
        return self.user.active

    @property
    def is_authenticated(self) -> bool:
        """
        property used to determine if a user is currently
        authenticated or not. Defaults to False, is set to True by logging in
        """
        # print(self)
        if not isinstance(self._is_authenticated, bool):
            return False
        return self._is_authenticated

    @property
    def username(self) -> str:
        """
        username property to simplify accessing user object username
        """
        if not isinstance(self.user, User) or not isinstance(self.user.username, str):
            raise Exception("Cannot get Username: User is None")
        return self.user.username

    def get_id(self) -> int:
        """
        Returns User ID value, used in current_user.id
        """
        if not isinstance(self.id, int):
            raise Exception("Cannot get ID: ID is NULL")
        return self.id

    def authenticate(self, input_pw: str) -> bool:
        """
        Authenticate a user given a certain password.
        uses bcrypt.checkpw to securely(ish) check password
        against database
        """
        password = bytes(input_pw, "utf-8")
        if not isinstance(self.user, User) or not isinstance(
            self.user.password, Column
        ):
            return False
        user_password = self.user.password  # type: ignore
        if not isinstance(user_password, bytes):
            user_password = bytes(user_password, "utf-8")  # type: ignore
        self._is_authenticated = bcrypt.checkpw(password, user_password)
        return self.is_authenticated

    def set_password(self, password: str) -> None:
        """
        Set (or reset) password for a user
        Creates new salted password hash using bcrypt
        incorporates new salt as well.
        """
        if not self.is_authenticated or not isinstance(password, str):
            return
        hashed_pw: bytes = bcrypt.hashpw(bytes(password, "utf-8"), bcrypt.gensalt())
        self.user.password = hashed_pw  # type: ignore (SQLAlchemy is doing stuff here)
        return

    @staticmethod
    def create_user(**user_properties):
        """
        Create a new user object given certain properties
        """
        # FIXME: This does not validate user until db request
        user_specific_properties = ["username", "email", "first_name", "last_name"]
        # preference_properties = []
        user_values = {
            prop: user_properties.get(prop) for prop in user_specific_properties
        }
        insecure_password = user_properties.get("insecure_password")
        if isinstance(insecure_password, str):
            insecure_password = bytes(insecure_password, "utf-8")
        elif not isinstance(insecure_password, bytes) or len(insecure_password) == 0:
            raise Exception("Cannot create user without password")
        user_values["password"] = bcrypt.hashpw(insecure_password, bcrypt.gensalt())
        app_db = get_db()
        if get_user_by_username(user_properties.get("username")) is not None:
            raise ValueError("Username already registered")
        if user_properties.get("email") == "":
            user_properties["email"] = None

        try:
            new_user = User(**user_values)
            app_db.session.add(new_user)  # pylint: disable=no-member
            app_db.session.commit()  # pylint: disable=no-member
        except Exception as database_error:
            logger.error(database_error)
            raise ValueError("Could not create user with the parameters given")
        return UserClass(new_user.id)  # type: ignore

    @staticmethod
    async def get_user_token(
        *, token: str
    ):  # = Depends(oauth2_scheme)) -> Optional[User]:
        """
        Get a UserToken object from a JWT token input
        """
        try:
            decoded_token = jwt.decode(
                token, str(SECRET), audience=JWT_AUDIENCE, algorithms=[JWT_ALGORITHM]
            )
            return UserToken(**decoded_token)
        except Exception as jwt_error:
            raise jwt_error

    @staticmethod
    async def signJWT(username: str):  # -> Dict[str, str]:
        """
        Sign a JWT token using instance's secret
        """
        payload = {
            "username": username,
            "iat": time.time(),
            "expires": time.time() + ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
        token = jwt.encode(payload, str(SECRET), algorithm=JWT_ALGORITHM)

        return {"access_token": token}
