from .errors import *
from async_class import AsyncClass

AUTH_URL = ('https://login.mos.ru/sps/login/methods/password?bo=%2Fsps%2Foauth%2Fae%3Fresponse_type%3Dcode%26access_'
            'type%3Doffline%26client_id%3Ddnevnik.mos.ru%26scope%3Dopenid%2Bprofile%2Bbirthday%2Bcontacts%2Bsnils%2B'
            'blitz_user_rights%2Bblitz_change_password%26redirect_uri%3Dhttps%253A%252F%252Fschool.mos.ru%252Fv3%252'
            'Fauth%252Fsudir%252Fcallback%26state%3D')

SUCCESS_URL = 'https://school.mos.ru/auth/callback'

AUTH_STATES = {SUCCESS_URL: 'SUCCESS',
               'https://login.mos.ru/scon/flow': 'INCORRECT_CREDS',
               'https://login.mos.ru/sps/login/assets/javascripts/sMethods.js': '2FA_NEEDED'}

FA_STATES = {SUCCESS_URL: 'SUCCESS',
             'https://login.mos.ru/sps/login/assets/stylesheets/askToTrust.min.css': 'TRUST',
             'https://login.mos.ru/sps/login/assets/javascripts/vrfCode.js': 'FAILED_CODE'}


class AUTH(AsyncClass):
    async def __ainit__(self, ap):
        self.browser = await ap.firefox.launch()
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    async def obtain_token(self, login, password):
        """
        Основной метод получения токена
        :param login: Логин от mos.ru
        :param password: Пароль от mos.ru
        :return: str
        """
        await self.page.goto(AUTH_URL)
        await self.page.fill('#login', login)
        await self.page.fill('#password', password)
        await self.page.click('#bind')

        answer = await self.page.wait_for_event("request", lambda req: req.url in AUTH_STATES)
        state = AUTH_STATES[answer.url]

        if state == 'SUCCESS':
            return await self._obtain_cookie()

        elif state == 'INCORRECT_CREDS':
            await self.browser.close()
            raise InvalidCredentialsError

        return state

    async def proceed_2fa(self, sms_code):
        """
        В случае, если нужна 2FA ауентификация
        :param sms_code: 2fa confirm code
        :return: str
        """
        await self.page.fill('#sms-code', sms_code)  # rr
        await self.page.click('#verifyBtn')

        answer = await self.page.wait_for_event("request", lambda req: req.url in FA_STATES)
        status = FA_STATES[answer.url]

        if status == 'FAILED_CODE':
            await self.browser.close()
            raise Invalid2FACode
        elif status == 'TRUST':
            await self.page.click("#disagree")
            await self.page.wait_for_event("request", lambda req: req.url == SUCCESS_URL)

        return await self._obtain_cookie()

    async def _obtain_cookie(self):
        """
        Получить желаемый токен
        :return: str
        """
        for cookie in await self.context.cookies():
            if cookie['name'] == 'aupd_token':
                await self.browser.close()
                return cookie['value']
        raise UnknownError
