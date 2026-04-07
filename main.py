from flows import run
import sys
from playwright.__main__ import main as playwright_main

if len(sys.argv) > 1 and sys.argv[1] == "install":
    # install Chromium browser
    sys.argv = ["playwright", "install", "chromium"]
    playwright_main()
    print("Playwright Chromium installed successfully!")
    sys.exit()

def main():
    run()

if __name__ == "__main__":
    main()

    input("Готово! Нажмите Enter для выхода...")
