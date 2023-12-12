# aiomes
  
**AIOMES**  - ассинхронная Python-библиотека, написанная на aiohttp и async_playwright, с легким доступом к сервису МЭШ.

### Примечание:    
&nbsp;&nbsp;&nbsp;&nbsp;Библиотека может работать только с профилем ученика.   


### Установка
```
pip install aiomes
```
```
playwright install
```

### Использование
```python
from playwright.async_api import async_playwright
import asyncio
import aiomes

LOGIN = ...
PASSWORD = ...

async def main():
    async with async_playwright() as p:
        auth = await aiomes.AUTH(p)
        token = await auth.obtain_token(LOGIN, PASSWORD)

        if token == '2FA_NEEDED':
            sms_code = str(input())  # Реализация вашей логики получения 2FA-кода
            token = await auth.proceed_2fa(sms_code)

    user = await aiomes.Client(token)

asyncio.run(main())
```  
 [ *Asyncronous Input Output Moscow Electronic School* ]
