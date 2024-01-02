# aiomes
  
**AIOMES**  - ассинхронная Python-библиотека, написанная на aiohttp и async_playwright, с легким доступом к сервису [МЭШ](https://school.mos.ru)

## Примечание:
> Библиотека может работать только с профилем ученика.   


## Установка:
```bash
pip install aiomes
```
```bash
playwright install
```

## Оглавление методов библиотеки:
- **[Вход по логину / паролю](#авторизация-по-логину-и-паролю)**
- **[Вход по токену](#авторизация-по-токену)**
- [Получение расписания](#получение-расписания)
- [Получение короткого расписания](#получение-короткого-расписания)
- [Получение каникулярного расписания](#получение-расписания-каникул)
- [Получение Д/З](#получение-домашнего-задания)
- [Получение оценок](#получение-оценок-за-дату)
- [Получение итоговых оценок](#получение-оценок-за-период)
- [Получение прошлогодних итоговых оценок](#получение-итог-оценок-за-прошлые-года)
- [Получение инфо о школе](#получение-информации-о-школе)
- [Получению меню школьной столовой](#получение-меню-школьной-столовой)
- [Получение меню школьного буфета](#получение-меню-школьного-буфета)
- [Получение посещаемости](#получение-посещаемости)
- [Получение уведомлений](#получение-всех-уведомлений)
- [Получение рейтинга в классе](#получение-рейтинга-в-классе)
- [Получение документов](#получение-документов-ученика)
- [Получение списка предметов](#получение-списка-предметов)

## Методы:
### Авторизация по логину и паролю
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
### Авторизация по токену
```python
import asyncio
import aiomes

TOKEN = ...

async def main():
  user = await aiomes.Client(TOKEN)

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
short_schedule = await user.get_schedule_short([today, today+timedelta(1), ...])
    
for subject in short_schedule:
    print(f"{subject.name}, {subject.start_time} - {subject.end_time}")
```
### Получение расписания каникул
```python
periods_schedule = await user.get_periods_schedule()

for subject in periods_schedule:
    print(f"{period.name}: {period.starts} — {period.ends}")
```
### Получение домашнего задания
```python
homework = await user.get_homeworks()

for hw in homework:
    print(f"{hw.subject_name}: {hw.description}; {hw.attached_files}, {hw.attached_tests}")
```
### Получение оценок за дату
```python
marks = await user.get_marks()

for mark in marks:
    print(f"{mark.subject_name}: {mark. value} [{mark.weight}] - {mark.reason}")
```
### Получение оценок за период
```python
period_marks = await user.get_period_marks(period_id=0)  # [Первый период]

for per_mark in period_marks:
    print(f"{per_mark.subject_name} - {per_mark.average_mark}; {per_mark.marks}")
```
### Получение итог. оценок за прошлые года
```python
past_marks = await user.get_past_final_marks(class_number=9)  # [Номер класса]

for past_mark in past_marks:
    print(f"{past_mark.subject_name} - {past_mark.final_mark}")
```
### Получение информации о школе
```python
school = await user.get_school_info()

print(school.name, school.address)
print(school.site, school.email)
print(school.principal)
```

### Получение меню школьной столовой
```python
today = date.today()
menu = await user.get_menu(today)

for item in menu:
    print(f'{item.title} — {item.price}:')
    for meal in item.composition:
        print(f'- {meal.name}, {meal.ingredients}, {meal.calories}')
    print('-'*35)
```
### Получение меню школьного буфета
```python
today = date.today()
buffet_menu = await user.get_menu_buffet(today)

for item in buffet_menu:
    print(item.name, item.full_name, item.price, item.is_available)
```

### Получение посещаемости
```python
today = date.today()
attendance = await user.get_visits(from_date=today - timedelta(7), to_date=today)

for day in attendance:
    print(f"{day.visit_date}: {day.in_time}-{day.out_time}, {day.duration}")
```
### Получение всех уведомлений
```python
notifications = await user.get_notifications()

for n in notifications:
    n_date = datetime.strftime(n.event_date, '%d/%m')
    print(f'{n_date}, {n.event_name} [{n.mark_value}], [{n.hw_description}]')
```
### Получение рейтинга в классе
```python
today = date.today()
ranking = await user.get_class_rank(date_from=today - timedelta(7), date_to=today)

for day in ranking:
    print(f"{day.rank_date}, {day.place}")
```
### Получение документов ученика
```python
docs = await user.get_docs()

for doc in docs:
    print(f"{doc.type_id} / {doc.series}, {doc.number} / {doc.issuer}, {doc.issue_date}")
```
### Получение списка предметов
```python
subjects = await user.get_subjects()

print(", ".join(subjects))
```

[ *Asyncronous Input Output Moscow Electronic School* ]