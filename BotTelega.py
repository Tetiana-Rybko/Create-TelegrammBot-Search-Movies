import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    filters,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler
)

from con_db import DatabaseManager
from s_movies import FilmSearch
from s_history import SearchHistory


load_dotenv()


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
READ_HOST = os.getenv("READ_HOST")
READ_USER = os.getenv("READ_USER")
READ_PASSWORD = os.getenv("READ_PASSWORD")
READ_DATABASE = os.getenv("READ_DATABASE")


db_manager = DatabaseManager(
    host=READ_HOST,
    user=READ_USER,
    password=READ_PASSWORD,
    database=READ_DATABASE
)
film_search = FilmSearch(db_manager)
history = SearchHistory()


SEARCH_KEYWORD, SEARCH_GENRE_YEAR = range(2)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Получена команда /start")
    await update.message.reply_text(
        "Добро пожаловать в бота для поиска фильмов!\n"
        "Доступные команды:\n"
        "/search_keyword – поиск по ключевому слову\n"
        "/search_genre_year – поиск по жанру и году\n"
        "/popular – вывод популярных запросов\n"
        "/cancel – отмена текущей операции"
    )

async def search_keyword_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Получена команда /search_keyword")
    await update.message.reply_text("Введите ключевое слово для поиска фильмов:")
    return SEARCH_KEYWORD

async def search_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyword = update.message.text
    logger.info(f"Поиск по ключевому слову: {keyword}")
    history.save_query(f"keyword: {keyword}")
    results = film_search.search_by_keyword(keyword)
    if results:
        response = "\n".join([f"{film['title']} ({film['release_year']})" for film in results])
    else:
        response = "Фильмы не найдены."
    await update.message.reply_text(response)
    return ConversationHandler.END

async def search_genre_year_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Получена команда /search_genre_year")
    await update.message.reply_text("Введите жанр и год через запятую (например, Action, 2006):")
    return SEARCH_GENRE_YEAR

async def search_genre_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        genre, year = [x.strip() for x in text.split(",")]
        logger.info(f"Поиск по жанру: {genre}, год: {year}")
    except Exception as e:
        logger.error(f"Ошибка при разборе жанра и года: {e}")
        await update.message.reply_text("Неверный формат. Пожалуйста, используйте формат: Жанр, Год")
        return SEARCH_GENRE_YEAR

    history.save_query(f"genre: {genre}, year: {year}")
    results = film_search.search_by_genre_and_year(genre, year)
    if results:
        response = "\n".join([f"{film['title']} ({film['release_year']}), жанр: {film['category']}" for film in results])
    else:
        response = "Фильмы не найдены."
    await update.message.reply_text(response)
    return ConversationHandler.END

async def popular_queries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Получена команда /popular")
    popular = history.get_popular_queries()
    if popular:
        response = "\n".join([f"{row[0]} – {row[1]} раз(а)" for row in popular])
    else:
        response = "История запросов пуста."
    await update.message.reply_text(response)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Получена команда /cancel")
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()


    conv_handler_keyword = ConversationHandler(
        entry_points=[CommandHandler('search_keyword', search_keyword_command)],
        states={
            SEARCH_KEYWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_keyword)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    conv_handler_genre_year = ConversationHandler(
        entry_points=[CommandHandler('search_genre_year', search_genre_year_command)],
        states={
            SEARCH_GENRE_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_genre_year)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )


    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler_keyword)
    application.add_handler(conv_handler_genre_year)
    application.add_handler(CommandHandler("popular", popular_queries))
    application.add_handler(CommandHandler("cancel", cancel))

    application.run_polling()

    db_manager.close()
    history.close()

if __name__ == '__main__':
    main()
