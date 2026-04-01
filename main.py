from simplegmail import Gmail
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
import sys
import re
from playwright.__main__ import main as playwright_main

def get_unique_path(path: Path) -> Path:
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent

    counter = 1
    while True:
        new_path = parent / f"{stem}-{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1

try:
    print('1 -> Скачать прикрепленные файлы')
    print('2 -> Скачать файлы из ссылок по типу cloud.mail')
    print('3 -> Установка браузера')
    flow = int(input())
    if flow not in [1, 2, 3]:
        raise Exception()
except Exception as e:
    print('Произошла ошибка')
    input()
    sys.exit(1)

if flow == 3:
    sys.argv = ["playwright", "install", "chromium"]
    print("Playwright Chromium installed successfully!")
    input()
    sys.exit()

ALLOWED_EXT = [".pdf", ".docx", ".zip", ".rar", ".7z"]

print('Введите даты для фильтрации:')
start = input('Дата с (2025/12/31): ')
end = input('Дата до (2025/12/31): ')

if getattr(sys, "frozen", False):
    base_path = Path(sys.executable).parent
else:
    base_path = Path(__file__).parent

client_secret_file = base_path / "client_secret.json"
gmail = Gmail(client_secret_file=str(client_secret_file))

if flow == 1:
    print('Скачиваются прикрепленные файлы...')
    q = f"has:attachment after:{start} before:{end}"

    messages = gmail.get_messages(query=q)

    save_dir = base_path / "attachments"
    save_dir.mkdir(exist_ok=True)

    for message in messages:
        if message.attachments:
            print(f'Отправитель [{message.sender}], дата [{message.date}]')
            for attm in message.attachments:
                if Path(attm.filename).suffix.lower() not in ALLOWED_EXT:
                    continue

                # if markAsRead:
                #     message.mark_as_read()

                # file path before checking uniqueness
                file_path = save_dir / attm.filename

                # ✅ get a unique path if file already exists
                file_path = get_unique_path(file_path)

                print('File: ' + attm.filename)
                attm.save(filepath=str(file_path))

if flow == 2:
    print('Скачиваются файлы из ссылок (cloud.mail)...')

    q = f"has:attachment after:{start} before:{end}"

    save_dir = base_path / "downloads_from_links"
    save_dir.mkdir(exist_ok=True)

    messages = gmail.get_messages(query=q, include_spam_trash=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        page = browser.new_page()

        for message in messages:
            if not message.plain:
                continue

            if 'cloud.mail.ru/stock' in message.plain:
                links = re.findall(r'https://cloud\.mail\.ru/stock/[^\s]+', message.plain)
                if len(links) == 0:
                    continue

                clean_links = [link.strip().rstrip(').,]') for link in links]
                for clean_link in clean_links:
                    try:
                        print("Opening:", clean_link)

                        response = page.goto(clean_link, wait_until="domcontentloaded", timeout=15000)

                        # ❗ check HTTP response
                        if response is None or response.status >= 400:
                            print("Bad response:", response.status if response else None)
                            continue

                        # ❗ ensure we are still on Mail.ru
                        if "cloud.mail.ru" not in page.url:
                            print("Redirected to unexpected page:", page.url)
                            continue

                        # ❗ try to find download button
                        try:
                            page.wait_for_selector('[data-qa-id="download"]', timeout=7000)
                        except PlaywrightTimeoutError:
                            # maybe expired or invalid link
                            content = page.content()

                            if "Файл удалён" in content or "not found" in content.lower():
                                print("Link expired or file deleted")
                            else:
                                print("Download button not found (unknown page structure)")

                            continue

                        # ✅ download
                        with page.expect_download() as download_info:
                            page.locator('[data-qa-id="download"]').click()

                        download = download_info.value

                        original_path = save_dir / download.suggested_filename
                        file_path = get_unique_path(original_path)

                        download.save_as(str(file_path))

                        print("Saved to:", file_path)

                    except PlaywrightTimeoutError:
                        print("Timeout while opening:", clean_link)
                        continue

                    except Exception as e:
                        print("Unexpected error:", str(e))
                        continue

        browser.close()
