from src.vigenere_cypher import VigenereCypher
from src.vigenere_cracker import VigenereCracker
from src.performance import Performance

def main():
    key = input("Provide your key: ")
    cipher = VigenereCypher(key)
    cracker = VigenereCracker()
    perf_find_key_length = Performance(cracker.find_key_length)
    perf_find_key = Performance(cracker.find_key)
    
    try:
        with open("plaintext.txt", "r") as f:
            plaintext = f.read()
    except FileNotFoundError:
        print("plaintext.txt not found. Please create the file with your plaintext.")
        return

    ciphertext = cipher.encrypt(plaintext)
    plaintext = cipher.decrypt(ciphertext)
    cipher.print_key_plaintext_ciphertext(plaintext, ciphertext)

    possible_lengths = perf_find_key_length(ciphertext)
    key_text = {}
    possible_keys = perf_find_key(ciphertext, possible_lengths)
    for key in possible_keys:
        decrypted_text = VigenereCypher(key).decrypt(ciphertext)
        key_text[key] = decrypted_text


if __name__ == "__main__":
    main()