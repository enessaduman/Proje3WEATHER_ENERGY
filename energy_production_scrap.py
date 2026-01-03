from playwright.sync_api import sync_playwright
from scrapy import Selector
import os
from dotenv import load_dotenv
import json

load_dotenv()
username = os.getenv("EPIAS_USERNAME")
password = os.getenv("EPIAS_PASSWORD")

table_data=[]
next_button_visibility=True
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False,slow_mo=1000)
    context = browser.new_context()
    page = context.new_page()
    #Going to the URL
    page.goto("https://giris.epias.com.tr/cas/login?service=https://seffaflik.epias.com.tr")
    #Filling the requirements for login
    page.fill("#username", username)
    page.fill("#password", password)
    #Login Button Execution
    page.click("button[type='submit']")
    #Hover to the sidebar, go down to the table page link
    page.locator(".narrow-container").hover()
    page.locator("span.item-title").filter(has_text="ELEKTRİK").first.click()
    page.locator("span.item-title").filter(has_text="ELEKTRİK ÜRETİM").first.click()
    page.locator("span.item-title").filter(has_text="Gerçekleşen Üretim").first.click()
    page.locator("span.item-title").filter(has_text="Gerçek Zamanlı Üretim").first.click()
    #Adjsut the date interval
    page.fill("input[name='startDate']","15.08.2025")
    page.fill("input[name='endDate']", "15.11.2025")
    #Bringing the table
    page.get_by_role("button", name="Sorgula").click()
    # table expand
    page.locator("div[class='react-select__control css-13cymwt-control']").nth(-1).click()
    # NOW WE HAVE THE TABLE!
    while next_button_visibility:
        selector = Selector(text=page.content())
        energy_table = selector.css("div.epuitable-body-section")
        rows_of_table = energy_table.css("div[class*='epuitable-row-item epuitable-row-item']")
        for row in rows_of_table:
            cells = row.css("div[class*='epuitable-cell-item epuitable-cell-item-']")
            cell_content=[]
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
        next_button=page.locator("div[role='button'][class*='epuitable-pagination-next']")
        if "disabled" in next_button.get_attribute("class"):
            break
        else:
            next_button.click()
with open("energy_data.json","w") as f:
    json.dump(table_data,f,indent=2,ensure_ascii=False)
