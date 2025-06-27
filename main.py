from playwright.async_api import async_playwright
from google_sheets import GoogleSheets
from model import ArticleModel
import asyncio

async def scrapper():
    sheets = GoogleSheets()
    existing_names = sheets.get_existing_names() or set()  # Ensure fallback to empty set
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()  # New context for isolation
        page = await context.new_page()
        page.set_default_timeout(60000)

        # Start from homepage
        homepage_url = "https://www.ukbusinesslist.co.uk/"
        print(f"\n🏠 Scraping categories from homepage: {homepage_url}")
        await page.goto(homepage_url)
        await page.wait_for_load_state('networkidle')
        await page.evaluate("window.scrollBy(0, 1200)")
        await page.wait_for_timeout(2000)

        # Extract category links
        category_links = await page.query_selector_all('.categories-boxes-container a.category-small-box')
        category_urls = [await link.get_attribute('href') for link in category_links if await link.get_attribute('href')]
        category_urls = list(dict.fromkeys(category_urls))  # Remove duplicates

        if not category_urls:
            print("⚠️ No categories found on homepage. Exiting.")
            await context.close()
            await browser.close()
            return

        print(f"📋 Found {len(category_urls)} categories: {category_urls}")

        for category_idx, category_url in enumerate(category_urls):
            print(f"\n📌 Processing category {category_idx + 1}: {category_url}")
            next_url = category_url
            page_number = 1

            while next_url:
                print(f"\n📄 Scraping page {page_number} of category: {next_url}")
                await page.goto(next_url)
                await page.wait_for_load_state('networkidle')
                await page.evaluate("window.scrollBy(0, 1200)")
                await page.wait_for_timeout(2000)

                # Get article links
                article_links = await page.query_selector_all('#listeo-listings-container a.listing-item-container')
                article_urls = [await link.get_attribute('href') for link in article_links if await link.get_attribute('href')]

                if not article_urls:
                    print("⚠️ No articles found on this page. Moving to next category.")
                    break

                for idx, url in enumerate(article_urls):
                    print(f"\n{idx + 1}. Visiting article: {url}")
                    article_page = await context.new_page()  # New page for each article
                    try:
                        await article_page.goto(url)
                        await article_page.wait_for_load_state('networkidle')

                        name = address = description = email = website = facebook = twitter = category = region = consultant_name = consultant_email = "N/A"

                        if await article_page.locator("div.listing-titlebar-title h1").is_visible():
                            name = (await article_page.locator("div.listing-titlebar-title h1").text_content()).strip()

                        if await article_page.locator("a.listing-address").is_visible():
                            address = (await article_page.locator("a.listing-address").text_content()).strip()

                        if await article_page.locator("#listing-overview").is_visible():
                            description_raw = await article_page.locator("#listing-overview").text_content()
                            description = description_raw.strip().split("\n")[0].strip() if description_raw else "N/A"

                        if await article_page.locator("ul.contact-links a[href^='mailto:']").count() > 0:
                            email_raw = await article_page.locator("ul.contact-links a[href^='mailto:']").get_attribute("href")
                            email = email_raw.replace("mailto:", "").strip() if email_raw else "N/A"

                        if await article_page.locator("ul.contact-links a[href^='http']").count() > 0:
                            website = (await article_page.locator("ul.contact-links a[href^='http']").get_attribute("href")).strip()

                        categories = await article_page.locator("h3:has-text('Categories') + ul a").all_text_contents()
                        category = ", ".join([c.strip() for c in categories]) or "N/A"
                        print(f"📍 Category: {category}")

                        regions = await article_page.locator("h3:has-text('Regions') + ul a").all_text_contents()
                        region = ", ".join([r.strip() for r in regions]) or "N/A"

                        if await article_page.locator("div.hosted-by-title h4 a").is_visible():
                            consultant_name = (await article_page.locator("div.hosted-by-title h4 a").text_content()).strip()

                        if await article_page.locator("ul.listing-details-sidebar a[href^='mailto:']").count() > 0:
                            consultant_email_raw = await article_page.locator("ul.listing-details-sidebar a[href^='mailto:']").get_attribute("href")
                            consultant_email = consultant_email_raw.replace("mailto:", "").strip() if consultant_email_raw else "N/A"

                        if await article_page.locator("ul.share-buttons a.fb-share").count() > 0:
                            facebook = (await article_page.locator("ul.share-buttons a.fb-share").get_attribute("href")).strip()

                        if await article_page.locator("ul.share-buttons a.twitter-share").count() > 0:
                            twitter = (await article_page.locator("ul.share-buttons a.twitter-share").get_attribute("href")).strip()

                        article = ArticleModel(
                            company_name=name,
                            company_details=description,
                            address=address,
                            detail_page_url=url,
                            source_url=next_url,
                            company_website=website,
                            company_email=email,
                            category=category,
                            facebook=facebook,
                            twitter=twitter,
                            region=region,
                            consultant_name=consultant_name,
                            consultant_email=consultant_email,
                        )

                        print(f"📋 Scraped: {name}")
                        if name not in existing_names:
                            sheets.save_to_google_sheets([article])
                            existing_names.add(name)
                            print(f"✅ Saved: {name}")
                        else:
                            print(f"⚠️ Skipping duplicate: {name}")

                    except Exception as e:
                        print(f"❌ Failed to scrape {url}: {e}")
                    finally:
                        await article_page.close()
                    await page.wait_for_timeout(1000)

                # Pagination within category
                try:
                    next_link = await page.query_selector('.nav-previous a')
                    if next_link:
                        next_url = await next_link.get_attribute("href")
                        print(f"➡️ Paginating to: {next_url}")
                        page_number += 1
                    else:
                        print("✅ Reached last page of category.")
                        next_url = None
                except Exception as e:
                    print(f"❌ Failed to get next page: {e}")
                    next_url = None

        await context.close()
        await browser.close()

asyncio.run(scrapper())