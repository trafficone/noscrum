from noscrum.noscrum_backend.db import User, UserPreference, get_db
from flask_login import UserMixin, AnonymousUserMixin
import logging
import bcrypt

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


def _get_preferences(user_id):
    """
    Get the preferences of the current user
    """
    return UserPreference.query.filter(UserPreference.user_id == user_id).all()


class UserClass(UserMixin):
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
        is_auth = self.is_authenticated
        return is_auth and self.user.active

    @property
    def is_authenticated(self) -> bool:
        return self._is_authenticated    
    
    @property 
    def username(self) -> str:
        return self.user.username

    def get_id(self) -> int:
        return self.id

    def authenticate(self,password: str) -> bool:
        password = bytes(password,'utf-8')
        self._is_authenticated = bcrypt.checkpw(password,bytes(self.user.password,'utf-8'))
        return self.is_authenticated

    def set_password(self,password: str) -> None:
        if not self.is_authenticated:
            return
        self.user.password = bcrypt.hashpw(password, bcrypt.gensalt())

    @staticmethod
    def create_user(**user_properties):
        user_specific_properties = ['username','email','first_name','last_name']
        #preference_properties = []
        user_values = {prop:user_properties.get(prop) for prop in user_specific_properties}
        user_values['password'] = bcrypt.hashpw(user_properties.get('insecure_password'),bcrypt.gensalt())
        app_db = get_db()
        new_user = User(**user_values)
        try:
            app_db.session.add(new_user)
        except Exception as e:
            logger.error(e)
            raise ValueError("Could Not Create User with the parameters given")
        app_db.session.commit()
        return UserClass(new_user.id)
