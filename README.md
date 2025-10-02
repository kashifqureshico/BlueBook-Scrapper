# BlueBook Scraper (Apify Actor)

An Apify Actor that scrapes company profile data from [The Blue Book](https://www.thebluebook.com).  
You can provide a **trade/keyword** (e.g. subcontractors, electricians) and a **location** (e.g. New York, Dallas, Florida).  
The actor will search The Blue Book, collect company profile links, and scrape detailed data for each company.

---

## 🚀 Features
- Scrapes company details:
  - Company name
  - Address
  - Phone number(s)
  - Website
  - Industry
  - Company info section
  - Contacts (Name, Title, Phone)
- Accepts **keyword + location** as input
- Collects multiple companies (configurable `max_companies`)
- Outputs data to Apify **Dataset** (downloadable as JSON, CSV, Excel, etc.)
- Uses **Selenium (headless Chrome)** inside Apify’s Python + Selenium base image

---

## 📥 Input

Input is defined in `.actor/input_schema.json`.  
When you run the actor on Apify Console, you’ll see a form with these fields:

| Field          | Type    | Required | Default         | Description                                           |
|----------------|---------|----------|-----------------|-------------------------------------------------------|
| `keyword`      | string  | ✅ yes   | subcontractors  | Trade or service to search for                        |
| `location`     | string  | ✅ yes   | New York        | City/State/Region for the search                      |
| `max_companies`| integer | ❌ no    | 50              | Maximum number of companies to scrape per run         |

**Example Input JSON:**
```json
{
  "keyword": "subcontractors",
  "location": "New York",
  "max_companies": 20
}
