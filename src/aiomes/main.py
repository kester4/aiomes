import aiohttp
from datetime import date
from async_class import AsyncClass
from typing import List
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
        Позволяет совершить необходимый запрос
        :param method: адрес запроса
        :return: JSON
        """
        headers = {
            "auth-token": self.token,
            "authorization": f"Bearer {self.token}",
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
            if lesson.get('lesson_education_type') != 'OO' and "Разговоры" not in lesson.get("subject_name", ""):
                continue
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

    async def get_schedule_short(self, request_date=date.today()):
        """
        Позволяет получить краткое расписание, без оценок, кабинетов и замен
        :param request_date: Необходимая дата. По умолчанию - сегодня
        """
        short_schedule = []
        raw_ss = await self.make_request("family/web/v1/schedule/short",
                                         student_id=self.user_id, dates=str(request_date))

        for s_lesson in raw_ss["payload"][0]["lessons"]:
            if s_lesson['lesson_education_type'] != 'OO' and "Разговоры" not in s_lesson["group_name"]:
                continue
            short_schedule.append(
                ShortScheduleType(
                    name=s_lesson["subject_name"] if s_lesson["subject_name"] else s_lesson["group_name"],
                    start_time=s_lesson["begin_time"],
                    end_time=s_lesson["end_time"]
                )
            )

        return short_schedule if short_schedule else None

    async def get_periods_schedule(self) -> List[PeriodsScheduleType]:
        """
        Позволяет получить расписание каникул и учебных периодов
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

    async def get_homeworks(self, request_date=date.today()) -> List[HouseworkType]:
        """
        Позволяет получить Д/З за дату
        :param request_date: Необходимая дата. По умолчанию - сегодня
        """
        homeworks = []
        raw_homeworks = await self.make_request(f"family/web/v1/homeworks?from={str(request_date)}",
                                                to=str(request_date), student_id=self.user_id)
        if not raw_homeworks["payload"]:
            return

        for homework in raw_homeworks["payload"]:
            material = homework.get('additional_materials', [{}])
            homeworks.append(
                HouseworkType(
                    subject_name=homework['subject_name'],
                    description=homework["description"],
                    attached_files=[item['link'] for shit in material
                                    if shit['type'] == 'attachments' for item in shit['items']],
                    attached_tests=[item['urls'][0]['url'] for shit in material
                                    if shit['type'] == 'test_spec_binding' for item in shit['items']]
                )
            )

        return homeworks

    async def get_marks(self, request_date=date.today()) -> List[BaseMarkType]:
        """
        Позволяет получить оценки за дату
        :param request_date: Необходимая дата. По умолчанию - сегодня
        """
        marks = []
        raw_mark = await self.make_request(f"family/web/v1/marks?from={str(request_date)}",
                                           to=str(request_date), student_id=self.user_id)
        if not raw_mark["payload"]:
            return

        for mark in raw_mark["payload"]:
            marks.append(
                BaseMarkType(
                    subject_name=mark["subject_name"],
                    value=mark["value"],
                    weight=mark["weight"],
                    reason=mark.get("control_form_name")
                )
            )

        return marks

    async def get_period_marks(self, period_id=0) -> List[TrimesterMarksType]:
        """
        Повзоляет получить оценки за оценочный период
        :param period_id: Необходимый период. По умолчанию - 1-й
        :return:
        """
        period_marks = []
        raw_period_marks = await self.make_request("ej/report/family/v1/progress/json",
                                                   academic_year_id=self.class_level, student_profile_id=self.user_id)

        for subject in raw_period_marks:
            if subject["periods"]:
                period_marks.append(
                    TrimesterMarksType(
                        subject_name=subject["subject_name"],
                        marks=[
                            mark["values"][0]["original"] + MARK_WEIGHTS_SYMBOLS[mark["weight"]]
                            for mark in subject["periods"][0]["marks"]
                        ],
                        average_mark=subject["periods"][period_id]["avg_five"]
                    )
                )
        # except (ValueError, IndexError):
        #     return 1

        return period_marks

    async def get_past_final_marks(self, class_number: int) -> List[PrevYearMarksType]:
        """
        Позволяет получить итоговые оценки за прошлые года
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
        Позволяет получить информацию о школе
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
        Позволяет получить список учебных предметов
        """
        raw_subjects = await self.make_request("family/web/v1/subjects/list",
                                               student_id=self.user_id)

        return [
            subject.get("subject_name") for subject in raw_subjects["payload"]
        ]
