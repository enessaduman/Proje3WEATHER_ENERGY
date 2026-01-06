"""
Playwright & Scrapy automation to scrape Electricity Generation data
from the EPIAS Transparency Platform and save it in JSON format.
"""

import os
import json
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from scrapy import Selector


def main():
    """
    Main processing function. Launches the browser, logs in,
    scrapes the table data, and saves it to a file.
    """
    load_dotenv()

    # Variable names preserved as requested.
    username = os.getenv("EPIAS_USERNAME")
    password = os.getenv("EPIAS_PASSWORD")

    table_data = []
    next_button_visibility = True

    with sync_playwright() as p:
        # slow_mo is great for visualizing the process during debugging.
        browser = p.chromium.launch(headless=True, slow_mo=750)
        context = browser.new_context()
        page = context.new_page()

        # Going to the URL
        page.goto("https://giris.epias.com.tr/cas/login?service=https://seffaflik.epias.com.tr")

        # Filling the requirements for login
        page.fill("#username", username)
        page.fill("#password", password)
        print("Logining DONE!")
        # Login Button Execution
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        # Hover to the sidebar, go down to the table page link
        page.locator(".narrow-container").hover()
        page.locator("span.item-title").filter(has_text="ELEKTRİK").first.click()
        page.locator("span.item-title").filter(has_text="ELEKTRİK ÜRETİM").first.click()
        page.locator("span.item-title").filter(has_text="Gerçekleşen Üretim").first.click()
        page.locator("span.item-title").filter(has_text="Gerçek Zamanlı Üretim").first.click()
        print("Table found!")
        # Adjust the date interval
        page.fill("input[name='startDate']", "15.08.2025")
        page.fill("input[name='endDate']", "15.11.2025")

        # Bringing the table
        page.get_by_role("button", name="Sorgula").click()
        page.wait_for_selector("div.epuitable-body-section")
        # Table expand
        # nth(-1) is the correct usage to select the last element.
        page.locator("div[class='react-select__control css-13cymwt-control']").nth(-1).click()
        print("Table loaded, SCRAPING IS STARTED!")
        #A loading status bar
        loading_bar=["-"]*20
        status=0
        current_bar=0
        print("     Loading Bar")
        # NOW WE HAVE THE TABLE!
        while next_button_visibility:
            # Feeding Playwright content to Scrapy Selector
            selector = Selector(text=page.content())
            energy_table = selector.css("div.epuitable-body-section")
            rows_of_table = energy_table.css("div[class*='epuitable-row-item epuitable-row-item']")

            for row in rows_of_table:
                cells = row.css("div[class*='epuitable-cell-item epuitable-cell-item-']")
                cell_content = []

                for cell in cells:
                    cell_content.append(cell.css("span::text").get())

                if len(cell_content) > 0:
                    table_data.append({
                        "Date": cell_content[0],
                        "Hour": cell_content[1],
                        "Total Energy": cell_content[2],
                        "Solar Energy": cell_content[9],
                        "Wind Energy": cell_content[8],
                    })
            if (status % 5) == 0:
                loading_bar[current_bar]="="
                print(f"\r[{"".join(loading_bar)}]     {(current_bar+1)*5}% Completed", end="")
                current_bar += 1
            status=status+1

            next_button = page.locator("div[role='button'][class*='epuitable-pagination-next']")

            # Pagination logic checking the class attribute
            if "disabled" in next_button.get_attribute("class"):
                break

            next_button.click()
            page.wait_for_timeout(150)

    # Specifying encoding is critical for non-ASCII characters.
    loading_bar=["="]*20
    print(f"\r[{"".join(loading_bar)}]     {100}% Completed", end="")
    print("\nWeb Scraping is Completed!")
    with open("energy_data.json", "w", encoding="utf-8") as f:
        json.dump(table_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
