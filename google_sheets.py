from model import ArticleModel
from typing import List
import gspread

class GoogleSheets:
    HEADERS = [
        "Company Name",
        "Address",
        "Company Details",
        "Detail Page URL",
        "Source URL",
        "Company Website",
        "Company Email",
        "Category",
        "Facebook",
        "Twitter",
        "Region",
        "Consultant Name",
        "Consultant Email",
        "LinkedIn",
        "Instagram",
        "Performance Score",
        "SEO Score",
        "Status",
        "Updated Number",
        "Updated Email",
        "Pitch",
        "Assigned Email",
        "Agent Email",
    ]

    def __init__(self):
        self.client = gspread.service_account(filename="credentials.json")
        self.sheet = self.client.open('UK Business List').sheet1
        self.ensure_headers()

    def ensure_headers(self):
        headers = self.sheet.row_values(1)
        if headers != self.HEADERS:
            self.sheet.update("A1", [self.HEADERS])

    def get_existing_rows(self):
        rows = self.sheet.get_all_values()
        return rows[1:]  # Skip header

    def get_existing_names(self) -> set:
        existing_rows = self.get_existing_rows()
        # Assuming company name is in the first column
        return set(row[0].strip().lower() for row in existing_rows if row and row[0].strip())

    def save_to_google_sheets(self, articles: List[ArticleModel]):
        try:
            existing_names = self.get_existing_names()
            rows_to_add = []

            for article in articles:
                name = str(article.company_name or "N/A").strip().lower()
                if name in existing_names:
                    continue

                row = [
                    article.company_name,
                    article.address,
                    article.company_details,
                    article.detail_page_url,
                    article.source_url,
                    article.company_website or "",
                    article.company_email or "",
                    article.category or "",
                    article.facebook or "",
                    article.twitter or "",
                    ", ".join(article.region) if isinstance(article.region, list) else article.region,
                    article.consultant_name,
                    article.consultant_email,
                    article.linkedin,
                    article.instagram,
                    article.performance_score,
                    article.seo_score,
                    article.status,
                    article.updated_number,
                    article.updated_email,
                    article.pitch,
                    article.assigned_email,
                    article.agent_email,
                ]

                rows_to_add.append(row)
                existing_names.add(name)

            if rows_to_add:
                self.sheet.append_rows(rows_to_add, value_input_option="USER_ENTERED")
                print(f"✅ Added {len(rows_to_add)} new articles to Google Sheets.")
            else:
                print("⚠️ No new articles to add (all duplicates).")

        except Exception as e:
            print("❌ Google Sheets setup or fetch failed.")
            print(f"Details: {type(e).__name__}: {e}")
