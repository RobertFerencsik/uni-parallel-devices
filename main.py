from src.vigenere_cypher import VigenereCypher
from src.vigenere_cracker import VigenereCracker

def main():
    key = input("Provide your key: ")
    cipher = VigenereCypher(key)
    
    try:
        with open("plaintext.txt", "r") as f:
            plaintext = f.read()
    except FileNotFoundError:
        print("plaintext.txt not found. Please create the file with your plaintext.")
        return

    ciphertext = cipher.encrypt(plaintext)
    print(f"Ciphertext: {ciphertext}")
    plaintext = cipher.decrypt(ciphertext)
    print(f"Decrypted plaintext: {plaintext}")

    cracker = VigenereCracker(ciphertext)
    possible_keys = cracker.crack()
    print(f"Possible keys: {possible_keys}")


if __name__ == "__main__":
    main()