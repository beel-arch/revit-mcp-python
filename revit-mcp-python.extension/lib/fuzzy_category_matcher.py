# -*- coding: UTF-8 -*-
"""
Fuzzy Category Matching for Revit Elements
Provides intelligent Dutch/English category resolution with fuzzy matching
"""

import json
import re
import unicodedata
import os
from Autodesk.Revit.DB import BuiltInCategory

# Import centralized category mapping
try:
    from CategoryMapping import category_mapping
except ImportError:
    # Fallback minimal mapping
    category_mapping = {
        "doors": BuiltInCategory.OST_Doors,
        "furniture": BuiltInCategory.OST_Furniture,
        "walls": BuiltInCategory.OST_Walls
    }


def resolve_category(input_text, min_ratio=0.72):
    """Resolve category with fuzzy matching (main function)
    
    Args:
        input_text (str): User input (Dutch or English)
        min_ratio (float): Minimum similarity ratio for fuzzy match
        
    Returns:
        tuple: (canonical_label, builtin_category, confidence_score)
    """
    resolver = _get_resolver()
    return resolver.resolve_category(input_text, min_ratio)


def get_supported_categories():
    """Get list of all supported category labels"""
    resolver = _get_resolver()
    return resolver.get_supported_categories()


# Global resolver instance
_resolver = None

def _get_resolver():
    """Get singleton resolver instance"""
    global _resolver
    if _resolver is None:
        _resolver = CategoryResolver()
    return _resolver


class CategoryResolver:
    """Category resolver with fuzzy matching"""
    
    def __init__(self):
        self.synonyms = self._load_synonyms()
        self.index = self._build_index()
    
    def _load_synonyms(self):
        """Load Dutch synonyms from JSON"""
        try:
            current_dir = os.path.dirname(__file__)
            synonyms_path = os.path.join(current_dir, 'revit_nl_synonyms.json')
            
            with open(synonyms_path, 'r') as f:
                return json.load(f)
        except:
            # Fallback
            return {
                "Doors": ["deur", "deuren"],
                "Furniture": ["meubilair", "meubels", "kasten", "kast"],
                "Walls": ["wand", "wanden", "muur", "muren"],
                "Casework": ["maatmeubilair", "inbouwkast"]
            }
    
    def _build_index(self):
        """Build search index"""
        index = []
        for label, terms in self.synonyms.items():
            all_terms = list(terms) + [label]
            for term in all_terms:
                normalized = self._normalize(term)
                index.append((normalized, label, term))
        return index
    
    def _normalize(self, text):
        """Normalize text for matching"""
        if not text:
            return u""
        
        if not isinstance(text, unicode):
            text = unicode(text)
        
        text = text.lower()
        text = unicodedata.normalize('NFD', text)
        text = u"".join([c for c in text if not unicodedata.combining(c)])
        text = re.sub(r'[^a-z0-9 ]+', u' ', text)
        text = u" ".join(text.split())
        return text
    
    def _similarity_ratio(self, a, b):
        """Calculate similarity ratio"""
        a_norm = self._normalize(a)
        b_norm = self._normalize(b)
        
        if not a_norm and not b_norm:
            return 1.0
        
        # Simple Levenshtein distance
        if len(a_norm) < len(b_norm):
            a_norm, b_norm = b_norm, a_norm
        
        if len(b_norm) == 0:
            return 0.0
        
        previous = range(len(b_norm) + 1)
        for i, ca in enumerate(a_norm):
            current = [i + 1]
            for j, cb in enumerate(b_norm):
                insertions = previous[j + 1] + 1
                deletions = current[j] + 1
                substitutions = previous[j] + (ca != cb)
                current.append(min(insertions, deletions, substitutions))
            previous = current
        
        distance = previous[-1]
        max_len = float(max(len(a_norm), len(b_norm)))
        return 1.0 - (distance / max_len) if max_len > 0 else 1.0
    
    def resolve_category(self, input_text, min_ratio=0.72):
        """Resolve category"""
        if not input_text or not self.index:
            return (None, None, 0.0)
        
        query = self._normalize(input_text)
        
        # Exact match first
        for term_norm, label, raw_term in self.index:
            if query == term_norm:
                bic = self._get_builtin_category(label)
                return (label, bic, 1.0)
        
        # Fuzzy match
        best_match = (None, None, 0.0)
        for term_norm, label, raw_term in self.index:
            ratio = self._similarity_ratio(query, term_norm)
            if ratio > best_match[2]:
                bic = self._get_builtin_category(label)
                best_match = (label, bic, ratio)
        
        if best_match[2] >= min_ratio:
            return best_match
        
        return (None, None, best_match[2])
    
    def _get_builtin_category(self, canonical_label):
        """Get BuiltInCategory enum using centralized mapping"""
        # CategoryMapping uses exact canonical labels with proper capitalization
        # Direct lookup without case conversion
        return category_mapping.get(canonical_label)
    
    def get_supported_categories(self):
        """Get supported categories"""
        return list(self.synonyms.keys())
