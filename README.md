# aiomes
  
**AIOMES**  - ассинхронная Python-библиотека, написанная на aiohttp и async_playwright, с легким доступом к сервису [МЭШ](https://school.mos.ru)

## Примечание:    
> Библиотека может работать только с профилем ученика.   


## Установка:
```
pip install aiomes
```
```
playwright install
```


## Авторизация по логину и паролю
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
## Авторизация по токену
```python
import asyncio
import aiomes

TOKEN = ...

async def main():
  user = await aiomes.Client(token)

asyncio.run(main())
```
### Получение расписания
```python
schedule = await user.get_schedule()

for subject in schedule:
    print(f"{subject.name}, {subject.start_time} - {subject.end_time}, к. {subject.room_number}; {subject.marks}")
```
### Получение короткого расписания
```python
short_schedule = await user.get_schedule_short()
    
for subject in short_schedule:
    print(f"{subject.name}, {subject.start_time} - {subject.end_time}")
```
### Получение расписания каникул
```python
periods_schedule = await user.get_periods_schedule()

for subject in periods_schedule:
    print(f"{period.name}: {period.starts} — {period.ends}")
```
 [ *Asyncronous Input Output Moscow Electronic School* ]
