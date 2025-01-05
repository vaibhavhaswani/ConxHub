import pandas as pd
from gnews import GNews
from pytrends.request import TrendReq
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tag import pos_tag
from collections import Counter
import re
import logging
from typing import List, Dict
import time

class AutoProductRanker:
    def __init__(self):
        """Initialize the analyzer with required clients and NLTK downloads"""
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize clients with Indian market focus
        self.news = GNews(language='en', country='IN', period='14d', max_results=100)
        self.trends = TrendReq(hl='en-IN', tz=330)  # Indian timezone
        
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            nltk.download('maxent_ne_chunker', quiet=True)
            nltk.download('words', quiet=True)
        except Exception as e:
            self.logger.warning(f"NLTK download error: {str(e)}")

    def get_product_patterns(self, category: str) -> Dict:
        """
        Get regex patterns and brand names for different product categories
        """
        patterns = {
            "bike": {
                "brands": [
                    # Indian Brands
                    "Royal Enfield", "Bajaj", "TVS", "Hero", "Honda", "Yamaha", 
                    "KTM", "Jawa", "Yezdi", "Suzuki",
                    # International Brands
                    "Kawasaki", "Triumph", "BMW", "Ducati", "Harley-Davidson"
                ],
                "patterns": [
                    # Royal Enfield patterns
                    r"Royal Enfield (?:Classic|Bullet|Meteor|Hunter|Himalayan|Continental|Interceptor) \d+(?:\s?(?:X|GT|Scram))?",
                    r"Royal Enfield Super Meteor \d+",
                    # Bajaj patterns
                    r"Bajaj (?:Pulsar|Dominar|Avenger) \d+(?:\s?(?:F|N|NS|RS|Street|Cruise))?",
                    # TVS patterns
                    r"TVS (?:Apache|Jupiter|Ntorq|Ronin|iQube) \d+(?:\s?(?:RTR|RR|Race|Electric))?",
                    # Hero patterns
                    r"Hero (?:Splendor|HF|Passion|Glamour|Xpulse|Xtreme) \d+(?:\s?(?:Plus|Pro|i3s|Sports))?",
                    # Honda patterns
                    r"Honda (?:Activa|Shine|Unicorn|SP|CB|CBR) \d+(?:\s?(?:X|R|F|DLX))?",
                    # Yamaha patterns
                    r"Yamaha (?:MT|R|FZ|FZS|Aerox) \d+(?:\s?(?:V\d|S|FI|ABS))?",
                    # KTM patterns
                    r"KTM (?:Duke|RC|Adventure) \d+(?:\s?(?:R|X))?",
                    # Jawa/Yezdi patterns
                    r"(?:Jawa|Yezdi) (?:Perak|42|Adventure|Scrambler|Roadster)(?: \d+)?",
                    # Suzuki patterns
                    r"Suzuki (?:Access|Burgman|Gixxer|Hayabusa|V-Strom) \d+(?:\s?(?:SF|GT))?",
                    # Other international brands
                    r"Kawasaki (?:Ninja|Z|Versys|Vulcan) \d+(?:\s?(?:R|RR|X))?",
                    r"Triumph (?:Tiger|Street|Rocket|Trident|Speed) \d+(?:\s?(?:GT|R|RS|RR))?",
                    r"BMW [A-Z]\d+(?:\s?(?:RR|GS|XR))?",
                    r"Ducati (?:Monster|Panigale|Multistrada|Scrambler) \d+(?:\s?(?:V\d|S|R))?",
                    r"Harley-Davidson (?:Iron|Street|Pan America|Nightster|Sportster) \d+(?:\s?(?:S|Special))?"
                ],
                "exclude": ["accessory", "cover", "helmet", "service", "spare", "modification"]
            },
            "car": {
                "brands": [
                    # Indian Brands
                    "Tata", "Mahindra", "Maruti Suzuki", 
                    # International Brands in India
                    "Hyundai", "Toyota", "Honda", "Kia", "MG", "Volkswagen", 
                    "Skoda", "Mercedes-Benz", "BMW", "Audi"
                ],
                "patterns": [
                    # Tata patterns
                    r"Tata (?:Nexon|Harrier|Safari|Punch|Altroz|Tiago|Tigor)(?: EV)?(?: \d{4})?(?:\s?(?:Dark|Gold|iCNG))?",
                    # Mahindra patterns
                    r"Mahindra (?:Scorpio|XUV|Thar|Bolero|KUV|Marazzo) \d+(?:\s?(?:N|Z|Classic|Neo))?",
                    r"Mahindra XUV\d+(?:\s?(?:L|e))?",
                    # Maruti Suzuki patterns
                    r"Maruti(?: Suzuki)? (?:Swift|Baleno|Brezza|Dzire|Ertiga|Grand Vitara|Jimny|Fronx)(?: \d{4})?(?:\s?(?:Alpha|Delta|Zeta|CNG))?",
                    # Hyundai patterns
                    r"Hyundai (?:Creta|Venue|i\d+|Verna|Exter|Alcazar|Tucson)(?: \d{4})?(?:\s?(?:Knight|N Line))?",
                    # Toyota patterns
                    r"Toyota (?:Fortuner|Innova|Urban Cruiser|Glanza|Camry|Vellfire)(?: \d{4})?(?:\s?(?:Legender|Hycross|Crysta))?",
                    # Honda patterns
                    r"Honda (?:City|Amaze|Elevate|WR-V|CR-V)(?: \d{4})?(?:\s?(?:e:HEV|ZX|VX))?",
                    # Kia patterns
                    r"Kia (?:Seltos|Sonet|Carens|EV6|Carnival)(?: \d{4})?(?:\s?(?:X|GT))?",
                    # MG patterns
                    r"MG (?:Hector|Astor|Comet|ZS|Gloster)(?: EV)?(?: \d{4})?(?:\s?(?:Plus|Sharp|Savvy))?",
                    # Volkswagen patterns
                    r"Volkswagen (?:Taigun|Virtus|Tiguan)(?: \d{4})?(?:\s?(?:GT|Plus))?",
                    # Skoda patterns
                    r"Skoda (?:Kushaq|Slavia|Kodiaq|Octavia|Superb)(?: \d{4})?(?:\s?(?:Style|L&K))?",
                    # Luxury brands
                    r"Mercedes(?:-Benz)? (?:A-Class|C-Class|E-Class|GLA|GLC|GLE|S-Class)(?: \d{4})?",
                    r"BMW (?:[A-Z]\d|X\d)(?: \d{4})?(?:\s?(?:M Sport|xDrive))?",
                    r"Audi (?:[A-Z]\d|Q\d)(?: \d{4})?(?:\s?(?:Technology|Premium Plus))?"
                ],
                "exclude": ["service", "spare", "accessory", "insurance", "finance", "second hand", "used"]
            }
        }
        
        # Include other categories (smartphone, laptop, drone) unchanged
        patterns.update({
            "smartphone": {
                "brands": ["iPhone", "Samsung", "Google", "OnePlus", "Xiaomi", "Vivo", "Oppo", "Realme", "Nothing"],
                "patterns": [
                    r"iPhone \d+(?:\s?(?:Pro|Plus|Max|Ultra))?",
                    r"Samsung Galaxy (?:S|A|M|F)\d+(?:\s?(?:Plus|Ultra|FE))?",
                    r"OnePlus \d+(?:\s?(?:Pro|R|T))?",
                    r"Xiaomi \d+(?:\s?(?:Pro|X|T|S))?",
                    r"Vivo (?:V|X|Y)\d+(?:\s?(?:Pro|Plus|Max))?",
                    r"Oppo (?:Find|Reno|F|A)\d+(?:\s?(?:Pro|Plus|Max))?",
                    r"Realme \d+(?:\s?(?:Pro|GT|Neo))?",
                    r"Nothing Phone \(\d\)"
                ],
                "exclude": ["case", "cover", "screen protector", "charger"]
            }
        })
        
        return patterns.get(category.lower(), {})

    # Rest of the class methods remain unchanged
    def extract_products_from_text(self, text: str, category: str) -> List[str]:
        """Extract product mentions from text using regex patterns"""
        patterns = self.get_product_patterns(category)
        if not patterns:
            return []
            
        products = []
        for pattern in patterns["patterns"]:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                product = match.group()
                if not any(excl in text.lower() for excl in patterns["exclude"]):
                    products.append(product)
                    
        return products

    def get_top_products(self, category: str, limit: int = 5) -> List[str]:
        """Discover top products in a category from news articles"""
        try:
            search_queries = {
                "car": "new car launch review price India",
                "bike": "new bike motorcycle launch review price India",
                "smartphone": "new smartphone launch review price India",
            }
            
            search_query = search_queries.get(category.lower(), f"new {category} launch review India")
            articles = self.news.get_news(search_query)
            
            product_mentions = []
            for article in articles:
                title_products = self.extract_products_from_text(article['title'], category)
                desc_products = self.extract_products_from_text(article.get('description', ''), category)
                product_mentions.extend(title_products + desc_products)
            
            if product_mentions:
                product_counter = Counter(product_mentions)
                return [product for product, _ in product_counter.most_common(limit)]
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error discovering products: {str(e)}")
            return []

    def get_product_scores(self, category: str, products: List[str]) -> Dict:
        """Get combined scores based on news mentions and trends"""
        scores = {}
        
        try:
            for product in products:
                search_query = f"{product} {category} India"
                news_results = self.news.get_news(search_query)
                scores[product] = len(news_results)
                time.sleep(1)
            
            if len(products) <= 5:
                search_terms = [f"{product} {category} India" for product in products]
                self.trends.build_payload(search_terms)
                trends_data = self.trends.interest_over_time()
                
                if not trends_data.empty:
                    for product in products:
                        search_term = f"{product} {category} India"
                        if search_term in trends_data.columns:
                            trend_score = trends_data[search_term].mean()
                            scores[product] = scores[product] * (1 + trend_score/100)
            
        except Exception as e:
            self.logger.error(f"Error calculating scores: {str(e)}")
        
        return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))




### main function to call
def findtrend(category='bike',limit=5):
    ranker = AutoProductRanker()
    
    categories = ["smartphone", "laptop", "bike", "car", "drone"]
    print("\nAvailable categories:")
    print(", ".join(categories))
    print(f"\nSelected Category: {category}")
    # category = input("\nEnter product category: ").strip().lower()
    if category not in categories:
        print(f"Invalid category. Please choose from: {', '.join(categories)}")
        return
        
    limit = max(2, min(10, limit))
    print(f"Number of top products to show: {limit}")
    
    print(f"\nDiscovering top {category} models in Indian market...")
    top_products = ranker.get_top_products(category, limit)
    
    if not top_products:
        print(f"No {category} models found. Please try again later.")
        return
    
    print("\nAnalyzing popularity and trends...")
    product_scores = ranker.get_product_scores(category, top_products)
    
    print(f"\nTop {len(product_scores)} {category} models in India:")
    print("-" * 50)
    for i, (product, score) in enumerate(product_scores.items(), 1):
        print(f"{i}. {product}")
    return product_scores