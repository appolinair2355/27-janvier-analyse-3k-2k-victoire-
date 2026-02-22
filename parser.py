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

        essential_categories = ['Victoire Joueur', 'Victoire Banquier', 'Pair', 'Impair']
        has_essential = all(cat in result['categories'] for cat in essential_categories)

        if not has_essential:
            print(f"❌ Catégories essentielles manquantes")
            return None

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

    def _is_separator(self, line):
        """Ligne de séparation pure (pas de numéros, pas de texte utile)"""
        stripped = line.strip()
        if not stripped:
            return False
        sep_chars = set('━─—-=*│┃ \t')
        return len(stripped) >= 5 and all(c in sep_chars for c in stripped)

    def _is_major_section_boundary(self, line):
        """Délimiteur majeur qui marque la fin d'un bloc (━━━ ou ┏/┗ avec ━━━)"""
        stripped = line.strip()
        if not stripped:
            return False
        heavy = '━'
        if stripped.count(heavy) >= 8:
            return True
        return False

    def extract_category_numbers(self, text, category_name, patterns):
        """
        Extrait les numéros (#NXXXX) pour une catégorie.

        Stratégie :
        1. Pour les catégories avec "Liste des numéros - PATTERN" dans le message,
           on cherche spécifiquement cette ligne d'en-tête, puis on collecte les
           numéros jusqu'à la prochaine section.
        2. Pour 3/2, 3/3, 2/2, 2/3, les numéros apparaissent dans des blocs
           détaillés "La liste des numéros (Chronologique)" qui suivent un header
           contenant le pattern (ex. "Configuration: 3/2").
        """
        lines = text.split('\n')

        # Essayer d'abord la recherche via "Liste des numéros - PATTERN"
        for pattern in patterns:
            key = f'Liste des numéros - {pattern}'
            numbers = self._extract_after_header(lines, key)
            if numbers is not None:
                return numbers if numbers else None

        # Essayer via "Configuration: PATTERN" (blocs paires détaillés)
        for pattern in patterns:
            key = f'Configuration: {pattern}'
            numbers = self._extract_after_config_header(lines, key)
            if numbers is not None:
                return numbers if numbers else None

        # Fallback: recherche directe du pattern dans une ligne d'en-tête de liste
        for pattern in patterns:
            numbers = self._extract_fallback(lines, pattern)
            if numbers:
                return numbers

        return None

    def _extract_after_header(self, lines, header_text):
        """
        Cherche une ligne contenant header_text, puis collecte les #NXXXX
        sur les lignes suivantes jusqu'à la prochaine grande section.
        Ignore les lignes séparateurs (─────, -----, etc.)
        Retourne None si le header n'est pas trouvé, [] si trouvé mais vide.
        """
        in_section = False
        numbers = []

        for i, line in enumerate(lines):
            if not in_section:
                if header_text in line:
                    in_section = True
                    print(f"   🔍 Header trouvé: '{header_text}' à ligne {i}")
                continue

            # On est dans la section
            stripped = line.strip()

            # Ligne vide ou séparateur léger → on continue (fait partie du format)
            if not stripped or self._is_separator(line):
                continue

            # Séparateur majeur ━━━━ → fin du bloc
            if self._is_major_section_boundary(line):
                print(f"   🏁 Fin section (━━━ majeur) à ligne {i}")
                break

            # Nouveau header "Liste des numéros" d'une autre catégorie → fin
            if 'Liste des numéros' in line and header_text not in line:
                print(f"   🏁 Fin section (nouvelle liste) à ligne {i}")
                break

            # Nouveau header de bloc paire (┏━━━) → fin
            if line.strip().startswith('┏') or line.strip().startswith('╔'):
                print(f"   🏁 Fin section (nouveau bloc) à ligne {i}")
                break

            # Extraire les numéros
            nums = re.findall(r'#N(\d+)', line)
            if nums:
                numbers.extend([int(n) for n in nums])

        if in_section:
            return numbers
        return None

    def _extract_after_config_header(self, lines, config_text):
        """
        Pour les blocs paires : cherche "Configuration: X/Y", puis cherche
        "La liste des numéros" dans le même bloc, puis collecte les #N.
        Retourne None si non trouvé.
        """
        found_config = False
        in_list = False
        numbers = []

        for i, line in enumerate(lines):
            if not found_config:
                if config_text in line:
                    found_config = True
                    print(f"   🔍 Config trouvée: '{config_text}' à ligne {i}")
                continue

            if not in_list:
                if 'La liste des numéros' in line or 'liste des numéros' in line.lower():
                    in_list = True
                    print(f"   📋 Début liste numéros à ligne {i}")
                    continue
                # Si on arrive à un nouveau bloc ┏ avant de trouver la liste → abandon
                if line.strip().startswith('┏') or line.strip().startswith('╔'):
                    print(f"   ⚠️ Nouveau bloc avant liste à ligne {i}")
                    break
                continue

            # On est dans la liste de numéros
            stripped = line.strip()

            if not stripped or self._is_separator(line):
                continue

            # Un nouveau bloc commence → fin
            if line.strip().startswith('┏') or line.strip().startswith('╔'):
                print(f"   🏁 Fin liste (nouveau bloc) à ligne {i}")
                break

            if self._is_major_section_boundary(line):
                print(f"   🏁 Fin liste (━━━ majeur) à ligne {i}")
                break

            nums = re.findall(r'#N(\d+)', line)
            if nums:
                numbers.extend([int(n) for n in nums])
            elif re.search(r'\w', stripped) and not any(c in stripped for c in ['#', '─', '━', '-']):
                # Ligne de texte non-numéros → probablement fin de section
                break

        if found_config and in_list:
            return numbers
        return None

    def _extract_fallback(self, lines, pattern):
        """
        Recherche de secours : trouve le pattern dans une ligne puis cherche
        des numéros dans les lignes suivantes (en ignorant séparateurs).
        """
        in_section = False
        numbers = []

        for i, line in enumerate(lines):
            if not in_section:
                if pattern in line and '#N' not in line:
                    in_section = True
                continue

            stripped = line.strip()
            if not stripped or self._is_separator(line):
                continue

            if self._is_major_section_boundary(line):
                break

            if 'Liste des numéros' in line or line.strip().startswith('┏'):
                break

            nums = re.findall(r'#N(\d+)', line)
            if nums:
                numbers.extend([int(n) for n in nums])

        return numbers if numbers else None
