from typing import Optional

from sqlalchemy import func, join

from data import db_session
from data.recommendations import Recommendation
from data.status_recommendation import Status_recommendation
from model.recommendation import RecommendationModel, db_recommendation_to_model
from model.sent_recommendation import SentRecommendationModel
from model.status_recommendation import db_recommendation_status_to_model, RecommendationStatusModel

REC_STATUS_INIT, REC_STATUS_DONE, REC_STATUS_SKIP = '0', '1', '2'


class CyberAdventService:

    # Количество рекомендаций в адвенте
    async def get_recommendation_count(self) -> int:
        db_sess = db_session.create_session()
        recommendations_count = db_sess.query(Recommendation).count()
        db_sess.close()
        return recommendations_count


    # Получить описание рекомендации по ID
    async def get_recommendation_info_by_id(self, rec_id: int) -> Optional[RecommendationModel]:
        db_sess = db_session.create_session()
        db_rec = db_sess.query(Recommendation).filter(Recommendation.id == rec_id).first()
        db_sess.close()
        if db_rec:
            return db_recommendation_to_model(db_rec)
        return None


    # Количество отправленных рекомендаций пользователю
    async def sent_recommendation_count(self, user_id: int) -> int:
        db_sess = db_session.create_session()
        sent_recommendations_count = (db_sess.query(Status_recommendation)
                                      .filter(Status_recommendation.user_id == user_id)
                                      .count()
                                      )
        db_sess.close()
        return sent_recommendations_count


    # Все ли рекомендации отправлены пользователю
    async def is_all_recommendation_sent(self, user_id: int) -> bool:
        # Определяем количество рекомендаций, которые в принципе нужно было отправить
        recommendations_count = await self.get_recommendation_count()
        sent_recommendations_count = await self.sent_recommendation_count(user_id)
        return sent_recommendations_count >= recommendations_count


    # Выполнил ли пользователь адвент
    async def is_advent_completed(self, user_id: int) -> bool:
        # Определяем количество рекомендаций, которые в принципе нужно было отправить
        recommendations_count = await self.get_recommendation_count()

        db_sess = db_session.create_session()
        completed_recommendations_count = (db_sess.query(Status_recommendation)
                                           .filter(Status_recommendation.user_id == user_id,
                                                   Status_recommendation.rec_status == REC_STATUS_DONE)
                                           .count()
                                           )
        db_sess.close()
        return completed_recommendations_count >= recommendations_count


    # Получить статус отправленной ранее рекомендации пользователю по ID
    async def find_status_rec_by_id(self, user_id: int, rec_id: int) -> Optional[RecommendationStatusModel]:
        db_sess = db_session.create_session()
        # Находим рекомендацию в базе, которую нужно отложить
        db_rec = (db_sess.query(Status_recommendation).
               filter(Status_recommendation.user_id == user_id, Status_recommendation.rec_id == rec_id).
               first())
        db_sess.close()
        if db_rec:
            return db_recommendation_status_to_model(db_rec)
        return None


    # Отметить рекомендацию как выполненную
    async def done_rec(self, user_id: int, rec_id: int):
        db_sess = db_session.create_session()
        rec = (db_sess.query(Status_recommendation).
               filter(Status_recommendation.user_id == user_id, Status_recommendation.rec_id == rec_id).
               first())
        db_sess.close()

        if rec is None:
            return
        elif rec.rec_status == REC_STATUS_DONE:
            return

        rec.rec_status = REC_STATUS_DONE

        db_sess = db_session.create_session()
        db_sess.add(rec)
        db_sess.commit()
        db_sess.close()


    # Пометить рекомендацию как пропущенную
    async def skip_rec(self, user_id: int, rec_id: int):
        db_sess = db_session.create_session()
        # Находим рекомендацию в базе, которую нужно отложить
        rec = (db_sess.query(Status_recommendation).
               filter(Status_recommendation.user_id == user_id, Status_recommendation.rec_id == rec_id).
               first())
        db_sess.close()

        if rec is None:
            return
        elif rec.rec_status != REC_STATUS_INIT:
            return

        # Откладываем рекомендацию, меняя статус и затираем идентификатор сообщения (т.к. оно было удалено)
        rec.rec_status = REC_STATUS_SKIP
        rec.message_id = ""

        db_sess = db_session.create_session()
        db_sess.add(rec)
        db_sess.commit()
        db_sess.close()


    # Получить все ранее отправленные рекомендации этому пользователю
    async def get_sended_recommendations(self, user_id: int) -> list[RecommendationStatusModel]:
        db_sess = db_session.create_session()
        sent_recommendations = (db_sess.query(Status_recommendation)
                                .filter(Status_recommendation.user_id == user_id)
                                .order_by(Status_recommendation.rec_id).all()
                                )
        result = list()
        for rec in sent_recommendations:
            result.append(db_recommendation_status_to_model(rec))
        db_sess.close()
        return result


    # Получить определенное количество последних отправленных рекомендаций
    async def get_last_sended_recommendations(self, user_id: int, count: int) -> list[RecommendationStatusModel]:
        db_sess = db_session.create_session()
        sent_recommendations =  (db_sess.query(Status_recommendation)
                    .filter(Status_recommendation.user_id == user_id)
                    .order_by(Status_recommendation.rec_id.desc())
                    .limit(count)
                    .all())
        result = list()
        for rec in sent_recommendations:
            result.append(db_recommendation_status_to_model(rec))
        db_sess.close()
        return result


    # Получить страницу с отправленными рекомендациями
    async def get_recommendation_page(self, user_id: int, page_num: int, page_size: int) -> list[SentRecommendationModel]:
        db_sess = db_session.create_session()

        # Получаем пять последних отправленных рекомендаций пользователю
        j = join(Status_recommendation, Recommendation, Status_recommendation.rec_id == Recommendation.id)
        sent_recommendations = (db_sess.query(Status_recommendation.rec_id,
                                              Status_recommendation.rec_status,
                                              Recommendation.recommendation)
                                .select_from(j)
                                .filter(Status_recommendation.user_id == user_id)
                                .order_by(Status_recommendation.rec_id.desc())
                                .offset(page_num * page_size)
                                .limit(page_size)
                                .all())
        result = list()
        for idx, rec in enumerate(sent_recommendations):
            rec_id, rec_status, rec_name = rec[0], rec[1], rec[2]
            result.append(SentRecommendationModel(rec_id, rec_status, rec_name))
        db_sess.close()
        return result


    # Получить все ранее отправленные рекомендации, которые были пропущены
    async def get_skipped_recommendations(self, user_id: int) -> list[RecommendationStatusModel]:
        db_sess = db_session.create_session()
        skipped_recommendations = db_sess.query(Status_recommendation).filter(
            Status_recommendation.user_id == user_id, Status_recommendation.rec_status == REC_STATUS_SKIP).all()
        result = list()
        for rec in skipped_recommendations:
            result.append(db_recommendation_status_to_model(rec))
        db_sess.close()
        return result


    # Получить список идентификаторов пользователей, которым были отправлены еще не все рекомендации
    async def get_active_users_ids(self) -> list[int]:
        # Определяем количество рекомендаций, которые в принципе нужно было отправить
        recommendations_count = await self.get_recommendation_count()

        db_sess = db_session.create_session()
        user_ids = (db_sess.query(Status_recommendation.user_id).
                      group_by(Status_recommendation.user_id).
                      having(func.max(Status_recommendation.rec_id) < recommendations_count).
                      all())

        result = list()
        for row in user_ids:
            result.append(row[0])
        db_sess.close()
        return result


    # Добавить рекомендацию
    async def add_recommendation(self, rec: RecommendationStatusModel) -> RecommendationStatusModel:
        stat_rec = Status_recommendation()
        stat_rec.chat_id = rec.telegram_id
        stat_rec.user_id = rec.user_id
        stat_rec.send_time = rec.send_time
        stat_rec.message_id = rec.telegram_message_id
        stat_rec.rec_id = rec.rec_id
        stat_rec.rec_status = rec.rec_status

        db_sess = db_session.create_session()
        db_sess.add(stat_rec)
        db_sess.commit()
        db_sess.close()

        return rec


    # Получение всех существующих рекомендаций
    def get_all_recommendations(self) -> list[RecommendationModel]:
        db_sess = db_session.create_session()
        db_recs = db_sess.query(Recommendation).all()
        db_sess.close()
        all_recs = []
        for rec in db_recs:
            all_recs.append(db_recommendation_to_model(rec))
        return all_recs


    # Проинициализировать список рекомендаций для адвента
    def init_recommendations(self):
        db_sess = db_session.create_session()
        rec_count = db_sess.query(Recommendation).count()
        if rec_count > 0:
            return

        db_sess.add(Recommendation(recommendation='Установите обновление ПО на своём устройстве'))
        db_sess.add(Recommendation(recommendation='Обновите пароли от аккаунтов социальных сетей'))
        db_sess.add(Recommendation(recommendation='Отключите автоматическое подключение к Bluetooth и Wi-Fi'))
        db_sess.add(Recommendation(recommendation='Зашифруйте свои персональные данные'))
        db_sess.add(Recommendation(recommendation='Подключите двухфакторную аутентификацию для своих аккаунтов'))
        db_sess.add(Recommendation(recommendation='Проверьте наличие несанкционированных приложений на своём устройств'))
        db_sess.add(Recommendation(recommendation='Сделайте резервное копирование чатов в любом мессенджере'))
        db_sess.add(Recommendation(recommendation='Ограничьте разрешения любого приложения на устройстве'))
        db_sess.add(Recommendation(recommendation='Поставьте надёжный пароль на телефон'))
        db_sess.add(Recommendation(recommendation='Включите дистанционнное удаление данных с телефона'))
        db_sess.add(Recommendation(recommendation='Установите антивирусное ПО на всех своих устройствах'))
        db_sess.add(Recommendation(recommendation='Проверьте любую компанию на наличие сертификата кибезопасности'))
        db_sess.add(Recommendation(recommendation='Ограничьте доступ к вашим страницам в социальных сетях'))
        db_sess.add(Recommendation(recommendation='Установите вход по отпечатку пальца для ваших устройств'))
        db_sess.add(Recommendation(recommendation='Зарегистрируйтесь на сайте, прочитав политику конфиденциальности'))
        db_sess.add(Recommendation(recommendation='Обновите антивирусное ПО на вашем устройстве'))
        db_sess.add(Recommendation(recommendation='Сделайте резервное копирование данных вашего устройства'))
        db_sess.add(Recommendation(recommendation='"Почистите" список друзей в любой социальной сети'))
        db_sess.add(Recommendation(recommendation='Смените пароль вашей электронной почты'))
        db_sess.add(Recommendation(recommendation='"Почистите" электронный ящик от ненужных или подозрительных писем'))
        db_sess.add(Recommendation(recommendation='Выйдите с аккаунта в социальной сети со всех устройств, кроме своего'))
        db_sess.add(Recommendation(
            recommendation='Заблокируйте подозрительные аккауты, которые оставили заявку в друзья, в любом мессенджере или социальной сети'))
        db_sess.add(
            Recommendation(recommendation='Очистите чаты мессенджера от ненужной информации или просто удалите чат'))
        db_sess.add(Recommendation(
            recommendation='Обновите приложение мессенджера (если имеется), так как оно может содержать улучшение в области безопасности'))
        db_sess.add(Recommendation(recommendation='Проверьте вкладку "Спам" вашего электронного ящика'))
        db_sess.add(Recommendation(recommendation='Проведите разбор файлов вашего электронного диска и удалите ненужное'))
        db_sess.add(Recommendation(recommendation='Отключите геолокацию на вашем устройстве'))
        db_sess.add(Recommendation(recommendation='Удалите неиспользуемые аккаунты'))
        db_sess.add(
            Recommendation(recommendation='Удалите подозрительные или неиспользуемые приложения на вашем устройстве'))
        db_sess.add(Recommendation(recommendation='Заблокируте подозрительные чаты, предлагающие работу и т.д.'))
        db_sess.commit()
        db_sess.close()
