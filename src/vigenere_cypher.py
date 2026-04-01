import re

class VigenereCypher:
    def __init__(self, key):
        self.key = key

    @staticmethod
    def _remove_non_alpha(text):
        return re.sub(r'[^A-Za-z]', '', text).upper()

    def encrypt(self, plaintext):
        plaintext = self._remove_non_alpha(plaintext)
        ciphertext = []
        key_length = len(self.key)

        for i, char in enumerate(plaintext):
            # convert letters to numbers 0-25
            p_val = ord(char) - ord('A')
            k_val = ord(self.key[i % key_length]) - ord('A')
            c_val = (p_val + k_val) % 26
            ciphertext.append(chr(c_val + ord('A')))

        return ''.join(ciphertext)

    def decrypt(self, ciphertext):
        ciphertext = self._remove_non_alpha(ciphertext)
        plaintext = []
        key_length = len(self.key)

        for i, char in enumerate(ciphertext):
            c_val = ord(char) - ord('A')
            k_val = ord(self.key[i % key_length]) - ord('A')
            p_val = (c_val - k_val) % 26
            plaintext.append(chr(p_val + ord('A')))

        return ''.join(plaintext)

    def print_key_plaintext_ciphertext(self, plaintext, ciphertext):
        key_repeated = (self.key * ((len(plaintext) // len(self.key)) + 1))[:len(plaintext)]
        print(f"Key:       {key_repeated}")
        print(f"Plaintext: {plaintext}")
        print(f"Ciphertext:{ciphertext}")