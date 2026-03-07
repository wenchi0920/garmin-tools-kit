import garth
from garth.exc import GarthException
from loguru import logger

class Client(object):
    def __init__(self, email, password, session_dir='.garth') -> None:
        self._email = email
        self._password = password
        self._session_dir = session_dir

        if not self.login():
            logger.error(f"登入失敗: {email}")
            raise Exception("Login failed")

    def login(self) -> bool:
        try:
            logger.debug(f"嘗試從目錄恢復會話: {self._session_dir}")
            garth.resume(self._session_dir)
            logger.info(f"成功恢復會話: {garth.client.username}")
        except (FileNotFoundError, GarthException):
            logger.info(f"會話不存在或已過期，正在嘗試登入: {self._email}")
            garth.login(self._email, self._password)
            garth.save(self._session_dir)
            logger.info(f"登入成功並儲存會話至: {self._session_dir}")
        return True
