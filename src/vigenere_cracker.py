from collections import Counter

from .vigenere_cypher import VigenereCypher



class VigenereCracker:
    def __init__(self, ciphertext):
        self.ciphertext = ciphertext

    def crack(self):
        possible_lengths = self._find_key_length(self.ciphertext)
        possible_keys = {}
        for lenght in possible_lengths:
            key = self._find_key(self.ciphertext, lenght)
            decrypted_text = VigenereCypher(key).decrypt(self.ciphertext)
            possible_keys[key] = decrypted_text
        return possible_keys
    
    @staticmethod
    def _find_key_length(ciphertext, max_length=20):
        """Find possible key length using Kasiski method"""
        # Find repeating sequences
        counts = {}
        for length in range(3, 12):  # Look for sequences of length 3-11 characters
            for i in range(len(ciphertext) - length):
                seq = ciphertext[i:i+length]
                if ciphertext.count(seq) > 1:
                    distances = []
                    pos = -1
                    while True:
                        pos = ciphertext.find(seq, pos + 1)
                        if pos == -1:
                            break
                        distances.append(pos)
                    
                    for i in range(1, len(distances)):
                        dist = distances[i] - distances[i-1]
                        if dist in counts:
                            counts[dist] += 1
                        else:
                            counts[dist] = 1

        # Find most common factors
        factors = {}
        for dist, count in counts.items():
            for i in range(2, min(dist, max_length + 1)):
                if dist % i == 0:
                    if i in factors:
                        factors[i] += count
                    else:
                        factors[i] = count

        # Sort factors by frequency
        sorted_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)

        return [length for length, _ in sorted_factors[:5]]

    @staticmethod
    def _score_text(ciphertext):
        """Score text based on English letter frequency"""
        # English letter frequency
        eng_freq = {
            'E': 12.02, 'T': 9.10, 'A': 8.12, 'O': 7.68, 'I': 7.31, 'N': 6.95, 'S': 6.28, 'R': 6.02, 'H': 5.92, 'D': 4.32,
            'L': 3.98, 'U': 2.88, 'C': 2.71, 'M': 2.61, 'F': 2.30, 'Y': 2.11, 'W': 2.09, 'G': 2.03, 'P': 1.82, 'B': 1.49,
            'V': 1.11, 'K': 0.69, 'X': 0.17, 'Q': 0.11, 'J': 0.10, 'Z': 0.07
        }
        
        # Count letter occurrences
        letter_count = Counter(c.upper() for c in ciphertext if c.isalpha())
        total_letters = sum(letter_count.values())
        
        if total_letters == 0:
            return float('inf')
        
        # Normalize frequencies
        text_freq = {letter: (count / total_letters) * 100 for letter, count in letter_count.items()}
        
        # Calculate deviation score (lower is better)
        score = 0
        for letter, freq in eng_freq.items():
            score += abs(freq - text_freq.get(letter, 0))
        
        # Check for common English words
        common_words = ['THE', 'AND', 'THAT', 'HAVE', 'FOR', 'NOT', 'WITH', 'YOU', 'THIS', 'BUT']
        word_count = 0
        for word in common_words:
            word_count += ciphertext.upper().count(word)
        
        # Combine frequency score and word count
        return score - (word_count * 5)  # Lower score is better

    def _find_key(self, ciphertext, key_length):
        """Find key based on key length"""
        key = ''
        
        for i in range(key_length):
            # Extract characters at the same key position
            chars = ciphertext[i::key_length]
            
            # Try each possible shift and score
            best_score = float('inf')
            best_shift = None
            
            for shift in range(26):
                # Decrypt segment with this shift
                decrypted = ''.join([chr((ord(c.upper()) - ord('A') - shift) % 26 + ord('A')) for c in chars if c.isalpha()])
                
                # Score the result
                score = self._score_text(decrypted)
                
                if score < best_score:
                    best_score = score
                    best_shift = shift
            
            # Add best shift to key
            key += chr(best_shift + ord('A'))
        
        return key

