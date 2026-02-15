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
        Mode permissif: accepte si catégories essentielles présentes
        """
        if not text or 'STATISTIQUES COMPLÈTES' not in text:
            print("⚠️ Message ne contient pas 'STATISTIQUES COMPLÈTES'")
            return None
        
        result = {
            'total_games': self.extract_total_games(text),
            'categories': {}
        }
        
        print(f"📊 Total jeux trouvés: {result['total_games']}")
        
        # Compter les catégories trouvées
        found_categories = 0
        missing_categories = []
        
        for category_name, config in CATEGORIES.items():
            numbers = self.extract_category_numbers(text, category_name, config['patterns'])
            if numbers:
                result['categories'][category_name] = numbers
                found_categories += 1
                print(f"✅ {category_name}: {len(numbers)} numéros trouvés")
            else:
                missing_categories.append(category_name)
                print(f"⚠️ Catégorie manquante: {category_name}")
        
        print(f"📈 Résumé: {found_categories}/{len(CATEGORIES)} catégories trouvées")
        
        # Mode permissif: accepter si on a au moins 4 catégories principales
        essential_categories = ['Victoire Joueur', 'Victoire Banquier', 'Pair', 'Impair']
        has_essential = all(cat in result['categories'] for cat in essential_categories)
        
        if not has_essential:
            print(f"❌ Catégories essentielles manquantes")
            return None
        
        # Si on a les essentielles mais pas toutes, on continue quand même
        if found_categories < len(CATEGORIES):
            print(f"⚠️ Mode permissif: {found_categories} catégories acceptées")
            
        return result
    
    def extract_total_games(self, text):
        """Extrait le nombre total de jeux"""
        patterns = [
            r'Total jeux analysés\s*:\s*(\d+)',
            r'Total jeux?\s*:\s*(\d+)',
            r'Total\s*:\s*(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return 0
    
    def extract_category_numbers(self, text, category_name, patterns):
        """
        Extrait les numéros pour une catégorie spécifique
        Gère le format avec "Liste des numéros - CATEGORY"
        """
        lines = text.split('\n')
        numbers = []
        in_section = False
        section_ended = False
        
        for i, line in enumerate(lines):
            if not in_section and not section_ended:
                # Chercher le début de section
                for pattern in patterns:
                    if pattern in line:
                        in_section = True
                        print(f"   🔍 Section trouvée: '{pattern}' à ligne {i}")
                        break
            
            elif in_section:
                # Vérifier si c'est la fin de section
                if 'Liste des numéros' in line and not any(p in line for p in patterns):
                    section_ended = True
                    in_section = False
                    print(f"   🏁 Fin section (nouvelle liste) à ligne {i}")
                    break
                
                # Ligne de séparation = fin
                if any(end in line for end in ['━━━━━━━━', '─' * 10]) and 'numéros' not in line:
                    section_ended = True
                    in_section = False
                    print(f"   🏁 Fin section (séparateur) à ligne {i}")
                    break
                
                # Extraire les numéros de cette ligne
                nums = re.findall(r'#N(\d+)', line)
                if nums:
                    numbers.extend([int(n) for n in nums])
        
        return numbers if numbers else None
        
