import asyncio
from typing import Callable, Any, Awaitable, Dict

from aiogram import BaseMiddleware, F
from aiogram.types import Message, TelegramObject

from cachetools import TTLCache


class AlbumsMiddleware(BaseMiddleware):
    def __init__(self, wait_time_seconds: int):
        super().__init__()
        self.wait_time_seconds = wait_time_seconds
        self.albums_cache = TTLCache(
            ttl=float(wait_time_seconds) + 20.0,
            maxsize=1000
        )
        self.lock = asyncio.Lock()

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            print("%s used not for Message, but for %s", self.__class__.__name__, type(event))
            return await handler(event, data)

        event: Message

        # If there is no media_group
        # just pass update further
        if event.media_group_id is None:
            return await handler(event, data)

        album_id: str = event.media_group_id

        async with self.lock:
            self.albums_cache.setdefault(album_id, list())
            self.albums_cache[album_id].append(event)

        # Wait for some time until other updates are collected
        await asyncio.sleep(self.wait_time_seconds)

        # Find the smallest message_id in batch, this will be our only update
        # which will pass to handlers
        my_message_id = smallest_message_id = event.message_id

        item: Message
        for item in self.albums_cache[album_id]:
            smallest_message_id = min(smallest_message_id, item.message_id)

        # If current message_id in not the smallest, drop the update;
        # it's already saved in self.albums_cache
        if my_message_id != smallest_message_id:
            return

        # Если сотрудник прислал более одного фото, то скипаем апдейт
        if str(await data["state"].get_state()).split(":")[-1] == "employee_photo":
            await event.answer(text="Нужно прислать одно фото!")
            return

        context: F = data["state"]
        context.album = self.albums_cache[album_id]

        # обрабатывается ситуация, когда человек прислал несколько фотографий павильона
        if str(await data["state"].get_state()).split(":")[-1] == "working_place_photo":
            for info in context.album:
                if info.video:
                    await event.answer(text="Нужны только фото!")
                    return

            await data["state"].update_data(working_place_photo=[photo.photo[-1].file_id for photo in context.album])

        # обрабатывается ситуация, когда человек прислал несколько фотографий раздевалки
        if str(await data["state"].get_state()).split(":")[-1] == "cloakroom_photo":
            for info in context.album:
                if info.video:
                    await event.answer(text="Нужны только фото!")
                    return

            await data["state"].update_data(cloakroom_photo=[photo.photo[-1].file_id for photo in context.album])

        # обрабатывается ситуация, когда человек прислал несколько фотографий дефектов на коньках
        if str(await data["state"].get_state()).split(":")[-1] == "defects_photo":
            for info in context.album:
                if info.video:
                    await event.answer(text="Нужны только фото!")
                    return

            await data["state"].update_data(defects_photo=[photo.photo[-1].file_id for photo in context.album])

        # обрабатывается ситуация, когда человек прислал несколько фотографий дефектов у пингвинов
        if str(await data["state"].get_state()).split(":")[-1] == "penguins_defects_photo":
            for info in context.album:
                if info.video:
                    await event.answer(text="Нужны только фото!")
                    return

            await data["state"].update_data(penguins_defects_photo=[photo.photo[-1].file_id for photo in context.album])

        # обрабатывается ситуация, когда человек прислал несколько фотографий дефектов у ящиков хранения
        if str(await data["state"].get_state()).split(":")[-1] == "boxes_defects_photo":
            for info in context.album:
                if info.video:
                    await event.answer(text="Нужны только фото!")
                    return

            await data["state"].update_data(
                boxes_defects_photo=[photo.photo[-1].file_id for photo in context.album])

        # обрабатывается ситуация, когда человек прислал несколько фотографий дефектов защиты
        if str(await data["state"].get_state()).split(":")[-1] == "depend_defects_photo":
            for info in context.album:
                if info.video:
                    await event.answer(text="Нужны только фото!")
                    return

            await data["state"].update_data(
                depend_defects_photo=[photo.photo[-1].file_id for photo in context.album])

        # обрабатывается ситуация, когда человек прислал несколько фотографий чеков
        if str(await data["state"].get_state()).split(":")[-1] == "receipts_photo":
            for info in context.album:
                if info.video:
                    await event.answer(text="Нужны только фото!")
                    return

            await data["state"].update_data(
                receipts_photo=[photo.photo[-1].file_id for photo in context.album])

        # обрабатывается ситуация, когда человек прислал несколько фотографий льготников
        if str(await data["state"].get_state()).split(":")[-1] == "benefits_photo":
            for info in context.album:
                if info.video:
                    await event.answer(text="Нужны только фото!")
                    return

            await data["state"].update_data(
                benefits_photo=[photo.photo[-1].file_id for photo in context.album])

        return await handler(event, data)
