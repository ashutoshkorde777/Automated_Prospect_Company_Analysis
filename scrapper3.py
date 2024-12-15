from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import json
import google.generativeai as genai
import time


API_KEY = "AIzaSyC2CspMqOypevmBq6OK-mDLVWmtj9RrlLw"

genai.configure(api_key="AIzaSyC2CspMqOypevmBq6OK-mDLVWmtj9RrlLw")

model = genai.GenerativeModel("gemini-1.5-flash")



prompt_template = """
Give me the answers to the below questions in a json which will be parsable for the provided text:

row = {{
    "Company Name": company_name,  # The name of the company being evaluated. This refers to the business entity whose details you are gathering.
    "Website URL": website_url,  # A direct link to the company's official website where further information about the company can be found.
    "Relevant": relevant,  # Indicates whether the company’s offerings align with UBL’s products or services. This can be either "Yes" or "No."
    "Category": category,  # The sector or industry classification of the company, such as Food & Beverages (F&B), Pharmaceuticals, Technology, etc.
    "Manufacturer": manufacturer,  # A binary indicator of whether the company is involved in the production or manufacturing of goods ("Yes") or not ("No").
    "Brand": brand,  # A binary indicator of whether the company operates as a recognized brand ("Yes") or not ("No").
    "Distributor": distributor,  # A binary indicator of whether the company acts as a distributor, supplying products from other manufacturers ("Yes") or not ("No").
    "F&B": fnb,  # A binary indicator of whether the company is involved in the Food & Beverages sector ("Yes") or not ("No").
    "Probiotics": probiotics,  # A binary indicator of whether the company is involved in the production, research, or selling of probiotic products ("Yes") or not ("No").
    "Fortification": fortification,  # A binary indicator of whether the company is involved in fortification, which refers to adding nutrients to foods or beverages to enhance their health benefits ("Yes") or not ("No").
    "Gut Health": gut_health,  # A binary indicator of whether the company focuses on products related to improving or maintaining gut health ("Yes") or not ("No").
    "Women's Health": womens_health,  # A binary indicator of whether the company specializes in products focused on improving women’s health ("Yes") or not ("No").
    "Cognitive Health": cognitive_health,  # A binary indicator of whether the company focuses on cognitive health, which includes products that improve brain function or mental clarity ("Yes") or not ("No").
    "Health Focus": health_focus,  # Describes the specific health areas the company is concerned with, such as immune health, digestive health, mental wellness, etc. This provides more detail on the company’s niche.
    "Sales Stage": sales_stage,  # The current phase of engagement with the company in terms of sales, such as "Exploration" (initial discussions), "Consideration" (reviewing options), "Proposal" (formal offer), "Active" (ongoing negotiations), etc.
    "Probiotic Strain Interest": probiotic_strain_interest,  # The specific probiotic strains that the company may be interested in for their products, such as "Bacillus Coagulans Unique IS2," "Lactobacillus Acidophilus," etc.
    "Product Type": product_type,  # The type of products that are relevant to UBL’s offerings in terms of formats, such as Capsules, Tablets, Beverages, Powders, etc.
    "Product Range": product_range,  # The different categories of products the company deals with, such as Dairy, Supplements, Beverages, Snacks, etc.
    "Certifications": certifications,  # The certifications the company holds, which can include ISO (International Organization for Standardization), GMP (Good Manufacturing Practice), WHO (World Health Organization) certifications, etc.
    "Global Reach": global_reach,  # The geographical area the company covers, such as "Global" (operates worldwide), "Regional" (limited to specific regions), or "Local" (operates within a local area).
    "Potential for Collaboration": collaboration_potential,  # An assessment of how well the company’s needs align with UBL’s offerings, categorized as "High," "Medium," or "Low," indicating the likelihood of forming a successful partnership.

}}

Text:
"""


def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver_path = "chromedriver"  
    service = Service(r"C:\Users\Lenovo\Downloads\chromedriver-win64 (1)\chromedriver-win64\chromedriver.exe")
    return webdriver.Chrome(service=service, options=chrome_options)



def extract_text_from_links(driver, base_url):
    try:
        driver.get(base_url)
        WebDriverWait(driver, 20).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        scroll_page(driver)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        combined_text = soup.get_text()

        if not combined_text.strip():
            print(f"No text found on the main page of {base_url}.")

        links = [link['href'] for link in soup.find_all('a', href=True) if link['href'].startswith("http")]
        for link in links[:10]:  
            try:
                driver.get(link)
                WebDriverWait(driver, 20).until(lambda d: d.execute_script('return document.readyState') == 'complete')
                scroll_page(driver)
                link_soup = BeautifulSoup(driver.page_source, "html.parser")
                link_text = link_soup.get_text()
                if link_text.strip():
                    combined_text += "\n" + link_text
                else:
                    print(f"No text found on link {link}")
            except Exception as e:
                print(f"Error accessing {link}: {e}")
        return combined_text
    except Exception as e:
        print(f"Error extracting text from links on {base_url}: {e}")
        return ""

def scroll_page(driver):
    """Scrolls to the bottom of the page incrementally to load lazy-loaded content."""
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
      
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    
        time.sleep(2) 
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height




def fetch_nlp_response(combined_text, model):
    try:
        response = model.generate_content(prompt_template + combined_text)
        
        if response:
            
            print("Response text:", response.text)
            raw_response = response.text.strip()
            
            if raw_response:
                raw_response = raw_response[3:-3].strip()
                raw_response = raw_response[4:].strip()
                while raw_response[0] != '{':
                    raw_response = raw_response[1:].strip()
                while raw_response[-1] != '}':
                    raw_response = raw_response[:-1].strip()
                
            print("raw response:", raw_response)
               
            try:
                response_data = json.loads(raw_response)
                print(response_data)
                return response_data
            except json.JSONDecodeError as decode_error:
                print(f"Error decoding JSON response: {decode_error}")
                print(f"Cleaned response: {raw_response}") 
                return None
        else:
            print("API call returned no response.")
            return None
    except AttributeError as attr_error:
        print(f"Error with model or response object: {attr_error}")
        return None
    except Exception as e:
        print(f"Unexpected error fetching NLP response: {e}")
        return None


def scrape_website(driver, url):
    try:
        print(f"Scraping {url}...")
        combined_text = extract_text_from_links(driver, url)
        if not combined_text.strip():
            print(f"No text extracted from {url}.")
            return {}
        
        
        nlp_response = fetch_nlp_response(combined_text, model)
        
        if not nlp_response:
            print(f"No valid response from NLP API for {url}.")
            return {}

        company_name = nlp_response.get("Company Name", "Unknown")
        website_url = nlp_response.get("Website URL", "Unknown")
        relevant = nlp_response.get("Relevant", "No")
        category = nlp_response.get("Category", "Unknown")
        manufacturer = nlp_response.get("Manufacturer", "No")
        brand = nlp_response.get("Brand", "No")
        distributor = nlp_response.get("Distributor", "No")
        fnb = nlp_response.get("F&B", "No")
        probiotics = nlp_response.get("Probiotics", "No")
        fortification = nlp_response.get("Fortification", "No")
        gut_health = nlp_response.get("Gut Health", "No")
        womens_health = nlp_response.get("Women’s Health", "No")
        cognitive_health = nlp_response.get("Cognitive Health", "No")
        health_focus = nlp_response.get("Health Focus", "Unknown")
        sales_stage = nlp_response.get("Sales Stage", "Unknown")
        probiotic_strain_interest = nlp_response.get("Probiotic Strain Interest", "Unknown")
        product_type = nlp_response.get("Product Type", "Unknown")
        product_range = nlp_response.get("Product Range", "Unknown")
        certifications = nlp_response.get("Certifications", "Unknown")
        global_reach = nlp_response.get("Global Reach", "Unknown")
        collaboration_potential = nlp_response.get("Potential for Collaboration", "Unknown")

        last_updated = datetime.now().strftime("%Y-%m-%d")

        return {
            "Company Name": company_name,
            "Website URL": website_url,
            "Relevant": relevant,
            "Category": category,
            "Manufacturer": manufacturer,
            "Brand": brand,
            "Distributor": distributor,
            "F&B": fnb,
            "Probiotics": probiotics,
            "Fortification": fortification,
            "Gut Health": gut_health,
            "Women’s Health": womens_health,
            "Cognitive Health": cognitive_health,
            "Health Focus": health_focus,
            "Sales Stage": sales_stage,
            "Probiotic Strain Interest": probiotic_strain_interest,
            "Product Type": product_type,
            "Product Range": product_range,
            "Certifications": certifications,
            "Global Reach": global_reach,
            "Potential for Collaboration": collaboration_potential,
            "Last Updated": last_updated
        }

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return {}



def main(websites):
    driver = init_driver()
    data = []
    try:
        for company in websites:
            result = scrape_website(driver, company.get("url"))
            result["Company Name"] = company.get("name")
            if result:
                data.append(result)
    finally:
        driver.quit()

    
    df = pd.DataFrame(data)
    output_file = "company_health_segments_detailed_selenium.xlsx"
    df.to_excel(output_file, index=False)
    print(f"Data saved to {output_file}")



# List of websites to scrape


companies = [
    {"name": "Nestle", "url": "https://www.nestle.com"},
    {"name": "Dr. Reddy's Laboratories", "url": "https://www.drreddys.com"},
    {"name": "Coca", "url": "https://colacompany.com"},
    {"name": "Pfizer", "url": "https://www.pfizer.com"},
    {"name": "PepsiCo", "url": "https://www.pepsico.com"},
    {"name": "Johnson & Johnson", "url": "https://www.jnj.com"},
    {"name": "Danone", "url": "https://www.danone.com"},
    {"name": "Bayer", "url": "https://www.bayer.com"},
    {"name": "General Mills", "url": "https://www.generalmills.com"},
    {"name": "GlaxoSmithKline (GSK)", "url": "https://www.gsk.com"},
    {"name": "Kellogg’s", "url": "https://www.kelloggs.com"},
    {"name": "Merck & Co.", "url": "https://www.merck.com"},
    {"name": "Unilever", "url": "https://www.unilever.com"},
    {"name": "Roche", "url": "https://www.roche.com"},
    {"name": "Nestle Waters", "url": "https://www.nestlewaters.com"},
    {"name": "Sanofi", "url": "https://www.sanofi.com"},
    {"name": "Mondelez International", "url": "https://www.mondelezinternational.com"},
    {"name": "Novartis", "url": "https://www.novartis.com"},
    {"name": "Kraft Heinz", "url": "https://www.kraftheinzcompany.com"},
    {"name": "Eli Lilly and Company", "url": "https://www.lilly.com"},
    {"name": "Tyson Foods", "url": "https://www.tysonfoods.com"},
    {"name": "Teva Pharmaceuticals", "url": "https://www.tevapharm.com"},
    {"name": "Mars, Incorporated", "url": "https://www.mars.com"},
    {"name": "AbbVie", "url": "https://www.abbvie.com"},
    {"name": "Campbell Soup Company", "url": "https://www.campbellsoupcompany.com"},
    {"name": "Amgen", "url": "https://www.amgen.com"},
    {"name": "Conagra Brands", "url": "https://www.conagrabrands.com"},
    {"name": "AstraZeneca", "url": "https://www.astrazeneca.com"},
    {"name": "Molson Coors", "url": "https://www.molsoncoors.com"},
    {"name": "Boehringer Ingelheim", "url": "https://www.boehringeringelheim.com"},
    {"name": "AB InBev", "url": "https://www.abinbev.com"},
    {"name": "BASF", "url": "https://www.basf.com"},
    {"name": "Diageo", "url": "https://www.diageo.com"},
    {"name": "Procter & Gamble (P&G)", "url": "https://www.pg.com"},
    {"name": "Heineken", "url": "https://www.theheinekencompany.com"},
    {"name": "Medtronic", "url": "https://www.medtronic.com"},
    {"name": "McKesson", "url": "https://www.mckesson.com"},
    {"name": "AmerisourceBergen", "url": "https://www.amerisourcebergen.com"},
    {"name": "Cardinal Health", "url": "https://www.cardinalhealth.com"},
    {"name": "Medline Industries", "url": "https://www.medline.com"}
]

# Run the script
if __name__ == "__main__":
    main(companies)
