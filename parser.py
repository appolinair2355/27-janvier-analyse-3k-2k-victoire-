"""
Parseur de messages Telegram
"""
import re
from config import CATEGORIES

class MessageParser:
    def __init__(self):
        self.required_categories = list(CATEGORIES.keys())
    
    def parse_message(self, text):
        """
        Parse un message complet et extrait toutes les catégories
        Retourne None si toutes les catégories ne sont pas présentes
        """
        if not text or 'STATISTIQUES COMPLÈTES' not in text:
            return None
        
        result = {
            'total_games': self.extract_total_games(text),
            'categories': {}
        }
        
        all_found = True
        for category_name, config in CATEGORIES.items():
            numbers = self.extract_category_numbers(text, category_name, config['patterns'])
            if numbers:
                result['categories'][category_name] = numbers
            else:
                all_found = False
                print(f"⚠️ Catégorie manquante: {category_name}")
        
        if not all_found:
            return None
            
        return result
    
    def extract_total_games(self, text):
        """Extrait le nombre total de jeux"""
        match = re.search(r'Total jeux analysés\s*:\s*(\d+)', text)
        return int(match.group(1)) if match else 0
    
    def extract_category_numbers(self, text, category_name, patterns):
        """
        Extrait les numéros pour une catégorie spécifique
        Gère les deux formats (liste standard et sections décorées)
        """
        lines = text.split('\n')
        numbers = []
        in_section = False
        section_end_patterns = ['━━━━━━━━', '┏━━━━', '┗━━━━', '╔════', '╚════', '']
        
        for line in lines:
            if not in_section:
                for pattern in patterns:
                    if pattern in line:
                        in_section = True
                        break
            else:
                if any(end in line for end in section_end_patterns) and line.strip():
                    if '---' in line or '━━━━' in line:
                        continue
                    break
                
                nums = re.findall(r'#N(\d+)', line)
                numbers.extend([int(n) for n in nums])
        
        return numbers if numbers else None
