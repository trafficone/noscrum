"""
User backend handler for Noscrum
"""
import time
import logging
import bcrypt
from flask_login import UserMixin

# imports for JWT + FastAPI
import jwt

# from fastapi import Depends
# from fastapi.security import OAuth2PasswordBearer
# from typing import Optional, Dict
from noscrum.noscrum_api.config import (
    SECRET,
    JWT_ALGORITHM,
    JWT_AUDIENCE,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login/token")
from noscrum.noscrum_backend.db import User, UserPreference, get_db

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


class UserClass(UserMixin):
    """
    UserManager class for Noscrum
    handles all login/authentication actions
    """

    def __init__(self, user_id: str):
        super().__init__()
        self._is_authenticated = super().is_authenticated
        self.user = _get_user(user_id)
        if self.user is None:
            self._is_authenticated = False
            self.id = None
        else:
            self.id = int(self.user.id)

    @property
    def is_active(self) -> bool:
        """
        is_active property, which is from database is_active && is_authenticated
        is used to determine spaces where blocked users may not go
        """
        is_auth = self.is_authenticated
        return is_auth and self.user.active

    @property
    def is_authenticated(self) -> bool:
        """
        property used to determine if a user is currently
        authenticated or not. Defaults to False, is set to True by logging in
        """
        return self._is_authenticated

    @property
    def username(self) -> str:
        """
        username property to simplify accessing user object username
        """
        return self.user.username

    def get_id(self) -> int:
        """
        Returns User ID value, used in current_user.id
        """
        return self.id

    def authenticate(self, password: str) -> bool:
        """
        Authenticate a user given a certain password.
        uses bcrypt.checkpw to securely(ish) check password
        against database
        """
        password = bytes(password, "utf-8")
        user_password = self.user.password
        if not isinstance(user_password, bytes):
            user_password = bytes(user_password, "utf-8")
        self._is_authenticated = bcrypt.checkpw(password, user_password)
        return self.is_authenticated

    def set_password(self, password: str) -> None:
        """
        Set (or reset) password for a user
        Creates new salted password hash using bcrypt
        incorporates new salt as well.
        """
        if not self.is_authenticated:
            return
        self.user.password = bcrypt.hashpw(password, bcrypt.gensalt())

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
        if not isinstance(insecure_password, bytes):
            insecure_password = bytes(insecure_password, "utf-8")
        user_values["password"] = bcrypt.hashpw(insecure_password, bcrypt.gensalt())
        app_db = get_db()
        new_user = User(**user_values)
        try:
            app_db.session.add(new_user)  # pylint: disable=no-member
        except Exception as database_error:
            logger.error(database_error)
            raise ValueError("Could Not Create User with the parameters given")
        app_db.session.commit()  # pylint: disable=no-member
        return UserClass(new_user.id)

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
        token = jwt.encode(payload, SECRET, algorithm=JWT_ALGORITHM)

        return {"access_token": token}
