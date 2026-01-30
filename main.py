from simplegmail import Gmail
from pathlib import Path
import sys

ALLOWED_EXT = {".pdf", ".docx"}

print('Введите даты для фильтрации:')
start = input('Дата с (2025/12/31): ')
end = input('Дата до (2025/12/31): ')

q = f"has:attachment after:{start} before:{end}"

if getattr(sys, "frozen", False):
    base_path = Path(sys.executable).parent
else:
    base_path = Path(__file__).parent

client_secret_file = base_path / "client_secret.json"
gmail = Gmail(client_secret_file=str(client_secret_file))
messages = gmail.get_messages(query=q)

save_dir = base_path / "attachments"
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
