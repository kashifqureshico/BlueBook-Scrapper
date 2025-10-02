import asyncio
import time
from apify import Actor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException


# Initialize Chrome for Apify container
def init_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-software-rasterizer")
    return webdriver.Chrome(options=chrome_options)


# Collect company links from search results
def collect_company_links(driver, keyword, location, limit=10):
    search_url = f"https://www.thebluebook.com/search.html?region={location}&searchsrc=thebluebook&searchterm={keyword}"
    driver.get(search_url)
    links = []
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.pro-view-link"))
        )
        elements = driver.find_elements(By.CSS_SELECTOR, "a.pro-view-link")
        for el in elements[:limit]:
            links.append(el.get_attribute("href"))
    except TimeoutException:
        print(f"[WARN] No search results found for {keyword} in {location}.")
    return links


# Scrape a single company profile
def scrape_company(driver, url):
    driver.get(url)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#locationsPage-1 h3"))
        )
    except TimeoutException:
        print(f"[WARN] Could not load {url}")
        return None

    try:
        company_name = driver.find_element(By.CSS_SELECTOR, "#locationsPage-1 h3").text
    except NoSuchElementException:
        company_name = ""

    try:
        address = driver.find_element(
            By.CSS_SELECTOR, "#locationsPage-1 div div div div"
        ).text
    except NoSuchElementException:
        address = ""

    try:
        phone_el = driver.find_element(
            By.XPATH,
            '//*[@id="locationsPage-1"]/div/div[1]/div/div[1]/div/div[1]/div[2]/div[1]/a/span',
        )
        phone = phone_el.text if phone_el else ""
    except NoSuchElementException:
        phone = ""

    try:
        website_el = driver.find_element(
            By.XPATH,
            '//*[@id="locationsPage-1"]/div/div[1]/div/div[1]/div/div[1]/div[3]/a',
        )
        website = website_el.get_attribute("href")
    except NoSuchElementException:
        website = ""

    # Collect contacts if present
    contacts = []
    for i in range(1, 8):
        try:
            name = driver.find_element(
                By.XPATH,
                f'//*[@id="keyContactSection"]/div/div[1]/div[{i}]/div/div/div/div/button',
            ).text
            title = driver.find_element(
                By.XPATH,
                f'//*[@id="keyContactSection"]/div/div[1]/div[{i}]/div/div/div/div/div[1]',
            ).text
            try:
                number = driver.find_element(
                    By.XPATH,
                    f'//*[@id="keyContactSection"]/div/div[1]/div[{i}]/div/div/div/div/div[2]/a/span',
                ).text
            except NoSuchElementException:
                number = ""
            contacts.append({"name": name, "title": title, "number": number})
        except NoSuchElementException:
            continue

    return {
        "company_name": company_name,
        "address": address,
        "phone": phone,
        "website": website,
        "contacts": contacts,
        "url": url,
    }


# Main Apify entry
async def main():
    async with Actor:
        # Read actor input
        input_data = await Actor.get_input() or {}
        keyword = input_data.get("keyword", "subcontractors")
        location = input_data.get("location", "New York")
        max_companies = input_data.get("max_companies", 5)

        print(f"[INFO] Starting scrape for '{keyword}' in '{location}', limit={max_companies}")

        driver = init_driver()
        results = []

        try:
            company_links = collect_company_links(driver, keyword, location, limit=max_companies)

            for idx, url in enumerate(company_links, start=1):
                print(f"[INFO] Scraping company {idx}/{len(company_links)}: {url}")
                data = scrape_company(driver, url)
                if data:
                    results.append(data)
                    await Actor.push_data(data)

                # If you want to throttle, uncomment:
                # print("[INFO] Sleeping 15 minutes before next company…")
                # time.sleep(900)

        finally:
            driver.quit()

        print(f"[DONE] Scraped {len(results)} companies.")
