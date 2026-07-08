High Level Architecture:
                        ┌─────────────────────┐
                        │ AgriWelfare Website │
                        └──────────┬──────────┘
                                │
                                ▼
                        ┌─────────────────────┐
                        │ Scrape News Links   │
                        └──────────┬──────────┘
                                │
                                ▼
                        ┌─────────────────────┐
                        │ Download PDF        │
                        └──────────┬──────────┘
                                │
                                ▼
                        ┌─────────────────────┐
                        │ Extract PDF Text    │
                        └──────────┬──────────┘
                                │
                                ▼
                        ┌─────────────────────┐
                        │ Clean Description   │
                        └──────────┬──────────┘
                                │
                                ▼
                        ┌─────────────────────┐
                        │ Groq LLM Summary    │
                        │ Hindi Title + Short │
                        └──────────┬──────────┘
                                │
                                ▼
                        ┌─────────────────────┐
                        │ Create Document     │
                        └──────────┬──────────┘
                                │
                                ▼
                        ┌─────────────────────┐
                        │ Save MongoDB        │
                        └─────────────────────┘



Scraping Kya Hai?:
    Scraping ka matlab:
            Website ka HTML lena
                ↓
            Usme se zaruri data nikalna
                ↓
            Apne system me store karna


Jaise:
    Website:
        <div class="news">
            PM Kisan Yojana
        </div>

        <div class="news">
            Soil Health Card
        </div>

Tumhe sirf news chahiye.

    Python bolega:

            news = soup.find_all(
                "div",
                class_="news"
            )

    Output:
        PM Kisan Yojana
        Soil Health Card

Yahi scraping hai.


--------------------------------------------------------------------------------------

Step 1: Website Se HTML Lao:
                import requests

                response = requests.get(
                    "https://example.com"
                )

                print(response.text)

        Flow:
            Python
               ↓
            Website
               ↓
              HTML

##

Step 2: HTML Samjho:

    Maan lo output aaya:

                    <html>

                    <h1>Today's News</h1>

                    <p>PM Kisan launched</p>

                    </html>

    Ab Python ko pata nahi ki title kaha hai.
    Isliye BeautifulSoup use karte hain.


##
Step 3: BeautifulSoup:

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

Ab BeautifulSoup HTML ko tree ki tarah samajh leta hai.

        html
        │
        ├── h1
        │     Today's News
        │
        └── p
            PM Kisan launched

##
Step 4: Data Nikalo:

    Title nikalna:
            title = soup.find("h1")
            print(title.text)

        Output:
            Today's New


##
Agriwelfare Wale Code Me Kya Ho Raha Hai?
Website:
    https://agriwelfare.gov.in

Page source me kuch aisa hai:
<div class="news_scroll">   <div class="swiper-slide">      <a href="news1.pdf">         PM Kisan News      </a>   </div></div>
Tumhara scraper bolta hai:
news_section = soup.find(    "div",    class_="news_scroll")
Meaning:
News wala box dhoondo
Fir:
slides = news_section.find_all(    "div",    class_="swiper-slide")
Meaning:
Us box ke andar jitni news hain sab lao

Link Nikalna
a_tag = slide.find("a")
Ye:
<a href="news1.pdf">
ko pakad raha hai.
Fir:
href = a_tag.get("href")
Output:
news1.pdf

PDF Kyu Download Kar Rahe?
Website par news PDF me rakhi hai.

Website   ↓PDF   ↓News Text
To pehle PDF download karni padegi.
requests.get(pdf_url)

PDF Se Text Nikalna
Maan lo PDF me likha hai:
Government launches PM Kisan Scheme.Farmers will benefit.
PyMuPDF use karke:
page.get_text()
Output:
Government launches PM Kisan Scheme.Farmers will benefit.

Fir AI Kyu Use Kiya?
PDF bahut lambi ho sakti hai.
5 Pages10 Pages20 Pages
User itna nahi padhega.
To AI ko bheja:
Iska short summary bana do.
AI return karta hai:
{  "title":"पीएम किसान योजना",  "summary":"सरकार ने किसानों के लिए नई योजना शुरू की।"}

Complete Scraping Flow
Website   ↓HTML Download   ↓BeautifulSoup   ↓News Link Find   ↓PDF Download   ↓PDF Text Extract   ↓AI Summary   ↓MongoDB Save   ↓App Me Show
Ek Line Me
Tumhara code ye kar raha hai:
Government Agriculture Website      ↓News PDF dhoondta hai      ↓PDF download karta hai      ↓Text nikalta hai      ↓AI se Hindi summary banwata hai      ↓MongoDB me save karta hai      ↓App ko data deta hai
Scraping ka golden rule:
1. Website kholo2. HTML dekho3. Data kis tag me hai pata karo4. requests se HTML lao5. BeautifulSoup se tag pakdo6. Data extract karo7. Save karo
Ye 90% scraping projects ka same pattern hota hai.