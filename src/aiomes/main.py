import aiohttp
from datetime import date, datetime as dt
from async_class import AsyncClass
from typing import List, Dict
from .utils import *
from .output_types import *
from .errors import *


class Client(AsyncClass):
    """
    Основной класс для работы с библиотекой

    """

    async def __ainit__(self, token):
        """
        :param token: Токен учащегося для работы со всеми методами, получаемый через user_auth

        """
        self.token = token

        user_profile = await self.make_request("family/web/v1/profile")
        user_profile = user_profile["children"][0]

        self.user_id = user_profile['id']
        self.person_id = user_profile['contingent_guid']
        self.first_name = user_profile['first_name']
        self.middle_name = user_profile.get('middle_name')
        self.last_name = user_profile['last_name']
        self.birth_date = user_profile['birth_date']
        self.class_level = user_profile['class_level_id']
        self.class_name = user_profile['class_name']
        self.class_unit = user_profile['class_unit_id']
        self.snils = user_profile.get('snils')
        self.phone = user_profile.get('phone')
        self.school_id = user_profile["school"]["id"]
        self.contract_id = user_profile["contract_id"]
        self.parents = [f"{parent.get('first_name')} {parent.get('last_name')}"
                        for parent in user_profile.get('representatives', [{}])]

    async def make_request(self, method, **query_options):
        """
        Метод для совершения необходимого запроса с соответвующими параметрами.

        — Заголовки для запросов —
        Обязательные:
        - auth-token — токен авторизации пользователя, получаемый после входа в систему
        - x-mes-subsystem — принимает familyweb, либо familymp (мобильные устройства)
        - x-mes-role — данная библиотека поддерживает только student
        Необязательные:
        - origin (также refer)
        - User-Agent

        :param method: нужный API-endpoint
        :return: JSON

        """

        headers = {
            "auth-token": self.token,
            "x-mes-subsystem": "familyweb",
            "x-mes-role": "student",
            "origin": "https://dnevnik.mos.ru/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            result = await session.get("https://school.mos.ru/api/" + method, params=query_options)

            if result.status != 200:
                raise RequestError(result.status)
            return await result.json()

    async def get_schedule(self, request_date=date.today()) -> List[ScheduleType]:
        """
        Получение расписания за дату
        :param request_date: Необходимая дата. По умолчанию - сегодня

        """
        schedule = []
        raw_schedule = await self.make_request("family/web/v1/schedule",
                                               student_id=self.user_id, date=str(request_date))

        for activity in raw_schedule['activities']:
            lesson = activity.get('lesson', {})
            if lesson.get('lesson_education_type') == 'OO' or "Разговоры" in lesson.get("subject_name", ""):
                schedule.append(
                    ScheduleType(
                        name=lesson['subject_name'],
                        room_number=activity['room_number'],
                        marks=None if not lesson['marks'] else await parse_marks_from_lesson(lesson['marks']),
                        start_time=activity['begin_time'],
                        end_time=activity['end_time'],
                        is_replaced=lesson['replaced']
                    )
                )

        return schedule if schedule else None

    async def get_schedule_short(self, dates: list) -> Dict[str, List[ShortScheduleType]]:
        """
        Получение краткого расписания, без оценок, кабинетов и замен
        :param dates: Необходимые даты (в массиве)

        """
        short_schedule = {}
        raw_ss = await self.make_request("family/web/v1/schedule/short",
                                         student_id=self.user_id, dates=','.join(map(str, dates)))

        for day in raw_ss['payload']:
            short_schedule[day['date']] = [
                ShortScheduleType(
                    name=s_lesson["subject_name"] if s_lesson["subject_name"] else s_lesson["group_name"],
                    start_time=s_lesson["begin_time"],
                    end_time=s_lesson["end_time"]
                )
                for s_lesson in day['lessons'] if s_lesson['lesson_education_type'] == 'OO' or
                'Разговоры' in s_lesson["group_name"]
            ]

        return short_schedule

    async def get_periods_schedule(self) -> List[PeriodsScheduleType]:
        """
        Получение расписания учебных периодов и каникул

        """
        period_schedule = []
        raw_periods = await self.make_request("ej/core/family/v1/periods_schedules",
                                              academic_year_id=self.class_level, student_id=self.user_id)
        if not raw_periods:
            return

        for period in raw_periods[0]["periods"]:
            period_schedule.append(
                PeriodsScheduleType(
                    name=period["name"],
                    starts=period.get("begin_date"),
                    ends=period.get("end_date")
                )
            )

        return period_schedule

    async def get_homeworks(self, from_date=date.today(), to_date=date.today()) -> List[HouseworkType]:
        """
        Получение домашнего задания за радиус дат
        :param from_date: Необходимая дата начала. По умолчанию - сегодня
        :param to_date: Необходимая дата окончания. По умолчанию - сегодня

        """
        homeworks = []
        raw_homeworks = await self.make_request(f"family/web/v1/homeworks?from={str(from_date)}",
                                                to=str(to_date), student_id=self.user_id)
        if not raw_homeworks["payload"]:
            return

        for homework in raw_homeworks["payload"]:
            material = homework.get('additional_materials', [{}])
            homeworks.append(
                HouseworkType(
                    subject_name=homework['subject_name'],
                    hw_date=dt.strptime(homework['date'], '%Y-%m-%d'),
                    description=homework["description"],
                    attached_files=[item['link'] for shit in material
                                    if shit['type'] == 'attachments' for item in shit['items']],
                    attached_tests=[item['urls'][0]['url'] for shit in material
                                    if shit['type'] == 'test_spec_binding' for item in shit['items']]
                )
            )

        return homeworks

    async def get_marks(self, from_date=date.today(), to_date=date.today()) -> List[BaseMarkType]:
        """
        Получение оценок за радиус дат
        :param from_date: Необходимая дата начала. По умолчанию - сегодня
        :param to_date: Необходимая дата окончания. По умолчанию - сегодня

        """
        marks = []
        raw_mark = await self.make_request(f"family/web/v1/marks?from={str(from_date)}",
                                           to=str(to_date), student_id=self.user_id)
        if not raw_mark["payload"]:
            return

        for mark in raw_mark["payload"]:
            marks.append(
                BaseMarkType(
                    subject_name=mark["subject_name"],
                    mark_date=dt.strptime(mark["date"], "%Y-%m-%d"),
                    value=mark["value"],
                    weight=mark["weight"],
                    reason=mark.get("control_form_name")
                )
            )

        return marks

    async def get_period_marks(self, year_id, period_id=0) -> List[TrimesterMarksType]:
        """
        Получение оценок за оценочный период
        :param year_id: Необходимый класс учащегося
        :param period_id: Необходимый период. По умолчанию - 1-й

        """

        period_marks = []
        raw_period_marks = await self.make_request("ej/report/family/v1/progress/json",
                                                   academic_year_id=year_id, student_profile_id=self.user_id)

        try:
            for subject in raw_period_marks:
                if subject["periods"]:
                    period = subject["periods"][period_id]
                    period_marks.append(
                        TrimesterMarksType(
                            subject_name=subject["subject_name"],
                            marks=[
                                mark["values"][0]["original"] + MARK_WEIGHTS_SYMBOLS[mark["weight"]]
                                for mark in period["marks"]
                            ],
                            average_mark=period["avg_five"],
                            final_mark=period.get("final_mark")

                        )
                    )
        except (ValueError, IndexError):
            return

        return period_marks

    async def get_past_final_marks(self, class_number: int) -> List[PrevYearMarksType]:
        """
        Получение итоговых оценок за прошлые года
        :param class_number: номер класса от 1 до 11 включительно. обязательный параметр

        """
        assert 1 <= class_number <= 11, "Номер класса - число от 1 до 11 включительно."

        prev_year_marks = []
        raw_prev_year = await self.make_request("ej/core/family/v1/final_marks_prev_year",
                                                academic_year_id=str(class_number), is_year_mark="true",
                                                student_profile_id=self.user_id)
        if not raw_prev_year:
            return

        for value in raw_prev_year:
            prev_year_marks.append(
                PrevYearMarksType(
                    subject_name=value["subject_name"],
                    final_mark=value.get("value"),
                )
            )

        return prev_year_marks

    async def get_school_info(self) -> SchoolInfoType:
        """
        Получение информации о школе

        """
        school_info = await self.make_request("family/web/v1/school_info",
                                              class_unit_id=self.class_unit, school_id=self.school_id)
        if not school_info:
            return

        return SchoolInfoType(
            name=school_info["name"],
            principal=school_info["principal"],
            address=school_info["address"]["address"],
            site=school_info.get("site"),
            email=school_info["email"],
            branches=len(school_info["branches"])
        )

    async def get_menu(self, request_date=date.today()) -> List[ComplexMealType]:
        """
        Получение меню блюд школьной столовой на весь [указанный] день
        :param request_date: Необходимая дата. По умолчанию - сегодня

        """
        menu = []
        raw_menu = await self.make_request("family/web/v1/menu",
                                           date=str(request_date), contract_id=self.contract_id)
        if not raw_menu['menu']:
            return

        for item in raw_menu['menu']:

            meals = [MealType(
                    name=meal['name'],
                    ingredients=meal['ingredients'],
                    calories=meal['nutrition']['calories'])
                for meal in item['meals']]

            menu.append(
                ComplexMealType(
                    title=item['title'],
                    price=item['summary'] / 100,
                    composition=meals
                )
            )

        return menu

    async def get_menu_buffet(self, request_date=date.today()) -> List[BuffetMenuType]:
        """
        Получение меню школьного буфета (не столовой)
        :param request_date: Необходимая дата. По умолчанию - сегодня

        """
        buffet_menu = []
        raw_menu = await self.make_request("family/web/v1/menu/buffet",
                                           date=str(request_date), contract_id=self.contract_id)
        if not raw_menu['menu']:
            return

        for item in raw_menu['menu'][0]['items']:
            buffet_menu.append(
                BuffetMenuType(
                    name=item['name'],
                    full_name=item['full_name'],
                    is_available=bool(item['available_now']),
                    price=item['price'] / 100
                )
            )

        return buffet_menu

    async def get_visits(self, from_date, to_date=date.today()) -> VisitType:
        """
        Получение посещаемости занятий
        :param to_date: Необходимая дата. По умолчанию - сегодня
        :param from_date: Необходимая дата. По умолчанию - сегодня

        """
        visits = []
        raw_visits = await self.make_request(f"family/web/v1/visits?from={str(from_date)}",
                                             to=str(to_date), contract_id=self.contract_id)
        if not raw_visits["payload"]:
            return

        for visit in raw_visits["payload"]:
            visit_data = visit["visits"][0]
            visits.append(
                VisitType(
                    visit_date=visit["date"],
                    in_time=visit_data["in"],
                    out_time=visit_data["out"],
                    duration=visit_data["duration"]
                )
            )

        return visits

    async def get_notifications(self) -> List[NotificationType]:
        """
        Получение уведомлений аккаунта

        """
        notifications = []
        raw_notifications = await self.make_request("family/web/v1/notifications/search",
                                                    student_id=self.user_id)

        for notification in raw_notifications:
            notifications.append(
                NotificationType(
                    event_date=dt.strptime(notification['datetime'], '%Y-%m-%d %H:%M:%S.%f'),
                    event_name=notification['event_type'],
                    subject_name=notification['subject_name'],
                    hw_description=notification.get('new_hw_description'),
                    mark_value=notification.get('new_mark_value'),
                    mark_weight=notification.get('new_mark_weight')
                )
            )

        return notifications

    async def get_class_rank(self, date_from=date.today(), date_to=date.today()) -> List[RankingType]:
        """
        Получение рейтинга ученика в его классе за радиус дат.
        :param: date_from: с даты...
        :param: date_to: ...по дату

        """
        ranking = []
        raw_ranking = await self.make_request("ej/rating/v1/rank/rankShort", personId=self.person_id,
                                              beginDate=str(date_from), endDate=str(date_to))

        for day in raw_ranking:
            ranking.append(
                RankingType(
                    rank_date=day["date"],
                    place=day["rankPlace"]
                )
            )

        return ranking

    async def get_docs(self) -> List[DocumentType]:
        """
        Позволяет получить документы пользователя

        """
        docs = []
        raw_docs = await self.make_request("family/web/v1/person-details",
                                           contingent_guid=self.person_id, profile_id=self.user_id)
        if not raw_docs["documents"]:
            return

        for doc in raw_docs["documents"]:
            docs.append(
                DocumentType(
                    type_id=doc["document_type_id"],
                    series=doc.get("series"),
                    number=doc.get("number"),
                    issuer=doc["issuer"],
                    issue_date=doc["issue_date"]
                )
            )

        return docs

    async def get_subjects(self) -> List:
        """
        Получение списка учебных предметов (всех)

        """
        raw_subjects = await self.make_request("family/web/v1/subjects/list",
                                               student_id=self.user_id)

        return [
            subject.get("subject_name") for subject in raw_subjects["payload"]
        ]
