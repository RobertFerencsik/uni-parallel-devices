from src.vigenere_cypher import VigenereCypher

def main():
    key = input("Provide your key: ")
    cipher = VigenereCypher(key)
    plaintext = input("Provide your plaintext: ")
    ciphertext = cipher.encrypt(plaintext)
    print(f"Ciphertext: {ciphertext}")
    plaintext = cipher.decrypt(ciphertext)
    print(f"Decrypted plaintext: {plaintext}")



if __name__ == "__main__":
    main()