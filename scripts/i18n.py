"""Interface strings (English is the default language of the interface).

The liturgical texts themselves are never translated; only the site's chrome is.
Add a language by adding a column here and a button in templates/_macros.html.
"""

LANGS = ("en", "ru")

STRINGS = {
    "skip": ("Skip to the text", "Перейти к тексту"),
    # library page
    "tagline": (
        "Church Slavonic service books in Unicode. Read them on any screen, copy the text into your own documents, print it, or check it against the printed page.",
        "Церковнославянские богослужебные книги в Юникоде: читайте с любого устройства, копируйте текст в свои документы, печатайте и сверяйте с печатным изданием.",
    ),
    "find_book": ("Find a book", "Найти книгу"),
    "find_placeholder": ("Title, month or year", "Название, месяц или год"),
    "all_books": ("All books", "Все книги"),
    "no_match": ("No book matches. Try a shorter word, or clear the search.", "Ничего не найдено. Попробуйте более короткое слово или очистите поиск."),
    "clear_search": ("Clear search", "Очистить поиск"),
    "books_count": ("{n} books", "Книг: {n}"),
    "read": ("Read", "Читать"),
    "scan": ("Page scans", "Скан издания"),
    "scan_short": ("Scan", "Скан"),
    "contents": ("Contents", "Содержание"),
    "chapters_n": ("{n} sections", "Разделов: {n}"),
    "about_title": ("About this library", "О библиотеке"),
    "about_text": (
        "The texts are typed in Unicode from the printed editions listed with each book and are maintained as open data on GitHub. To paste the text into Word with the correct letters, install the free Ponomar fonts.",
        "Тексты набраны в Юникоде по указанным изданиям и хранятся как открытые данные на GitHub. Чтобы текст правильно отображался в Word после вставки, установите бесплатные шрифты «Пономарь».",
    ),
    "get_fonts": ("Get the fonts", "Скачать шрифты"),
    "source_on_github": ("Texts on GitHub", "Тексты на GitHub"),
    "report_error": ("Report an error", "Сообщить об ошибке"),
    "supported_by": ("Supported by the Slavonic Computing Initiative", "При поддержке Slavonic Computing Initiative"),
    # book page
    "edition": ("Edition", "Издание"),
    "source_note": ("Source", "Источник"),
    "start_reading": ("Start reading", "Начать чтение"),
    "pages_short": ("pp.", "с."),
    "volume": ("Volume", "Том"),
    "library": ("Library", "Библиотека"),
    "no_scan": ("No page scans for this book yet.", "Сканов этого издания пока нет."),
    # reader
    "open_contents": ("Contents and library", "Содержание и библиотека"),
    "close": ("Close", "Закрыть"),
    "this_book": ("This book", "Эта книга"),
    "in_this_section": ("In this section", "В этом разделе"),
    "previous": ("Previous", "Назад"),
    "next": ("Next", "Далее"),
    "reading_settings": ("Reading settings", "Настройки чтения"),
    "text_size": ("Text size", "Размер текста"),
    "smaller": ("Smaller text", "Мельче"),
    "larger": ("Larger text", "Крупнее"),
    "typeface": ("Typeface", "Шрифт"),
    "theme": ("Page color", "Цвет страницы"),
    "theme_light": ("White", "Белый"),
    "theme_sepia": ("Sepia", "Сепия"),
    "theme_dark": ("Dark", "Тёмный"),
    "page_numbers": ("Page numbers", "Номера страниц"),
    "pages_margin": ("In the margin", "На полях"),
    "pages_inline": ("In the text", "В тексте"),
    "pages_hidden": ("Hidden", "Скрыть"),
    "copy": ("Copy", "Копировать"),
    "copy_section": ("Copy this section", "Копировать раздел"),
    "copied": ("Copied. Paste it into Word or another editor.", "Скопировано. Вставьте в Word или другой редактор."),
    "copy_failed": ("Your browser blocked copying. Select the text and press Ctrl+C.", "Браузер запретил копирование. Выделите текст и нажмите Ctrl+C."),
    "print": ("Print", "Печать"),
    "fonts_hint": ("Install the Ponomar fonts to paste text into Word.", "Для вставки в Word установите шрифты «Пономарь»."),
    "page_n": ("Page {l} in the scan", "Страница {l} в скане"),
    "page_plain": ("Page {l}", "Страница {l}"),
    "note": ("Note", "Примечание"),
    # scan viewer
    "scan_of": ("Scan", "Скан"),
    "back_to_text": ("Back to the text", "Вернуться к тексту"),
    "show_in_text": ("Show this page in the text", "Найти страницу в тексте"),
    "open_full": ("Open full screen", "Открыть на весь экран"),
    "download_pdf": ("Download PDF", "Скачать PDF"),
    "viewer_failed": ("The page viewer did not start. You can open the PDF directly instead.", "Просмотрщик страниц не запустился. Можно открыть PDF напрямую."),
    "open_pdf": ("Open the PDF", "Открыть PDF"),
    "scan_missing": ("This book has no page scans yet.", "Для этой книги пока нет сканов."),
    "close_scan": ("Close the scan", "Закрыть скан"),
    "language": ("Language", "Язык"),
}


def table():
    """{"en": {key: str}, "ru": {...}} for the JavaScript side."""
    return {lang: {k: v[i] for k, v in STRINGS.items()} for i, lang in enumerate(LANGS)}
