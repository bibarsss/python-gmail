from simplegmail import Gmail
from pathlib import Path

ALLOWED_EXT = {".pdf", ".docx"}

print('Введите даты для фильтрации:')
start = input('Дата с (2025/12/31): ')
start = '2025/12/01'
end = input('Дата до (2025/12/31): ')
end = '2026/01/01'

q = f"has:attachment after:{start} before:{end}"

gmail = Gmail()
messages = gmail.get_messages(query=q)

save_dir = Path("attachments")
save_dir.mkdir(exist_ok=True)

for message in messages:
    if message.attachments:
        print(message.sender, '===================' , message.date)
        for attm in message.attachments:
            if Path(attm.filename).suffix.lower() not in ALLOWED_EXT:
                continue

            file_path = save_dir / attm.filename
            counter = 1

            while file_path.exists():
                file_path = save_dir / f"{file_path.stem}_{counter}{file_path.suffix}"
                counter += 1

            print('File: ' + attm.filename)
            attm.save(filepath=str(file_path))
