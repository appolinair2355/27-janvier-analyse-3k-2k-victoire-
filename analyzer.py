"""
Analyseur d'écarts entre numéros
"""
from config import CATEGORIES

class GapAnalyzer:
    def __init__(self):
        pass
    
    def analyze_all_categories(self, data):
        """
        Analyse toutes les catégories et calcule les écarts
        """
        results = {}
        
        for category_name, numbers in data['categories'].items():
            gaps, max_gap = self.calculate_gaps(numbers)
            emoji = CATEGORIES[category_name]['emoji']
            
            results[category_name] = {
                'emoji': emoji,
                'numbers': numbers,
                'count': len(numbers),
                'gaps': gaps,
                'max_gap': max_gap
            }
        
        return results
    
    def calculate_gaps(self, numbers):
        """Calcule les écarts entre numéros consécutifs"""
        if len(numbers) < 2:
            return [], 0
        
        gaps = [numbers[i+1] - numbers[i] for i in range(len(numbers)-1)]
        max_gap = max(gaps) if gaps else 0
        return gaps, max_gap
    
    def compare_with_previous(self, current_data, previous_data):
        """
        Compare les écarts actuels avec les précédents
        Retourne les alertes (catégories où le max est identique ou a augmenté)
        """
        if not previous_data or 'gaps' not in previous_data:
            return None
        
        comparison = {}
        prev_gaps = previous_data['gaps']
        
        for category, data in current_data.items():
            if category in prev_gaps:
                prev_max = prev_gaps[category]['max_gap']
                curr_max = data['max_gap']
                
                status = 'same' if curr_max == prev_max else 'increased' if curr_max > prev_max else 'decreased'
                
                comparison[category] = {
                    'previous_max': prev_max,
                    'current_max': curr_max,
                    'status': status
                }
        
        return comparison
        
