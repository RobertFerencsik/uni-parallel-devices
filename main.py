from src.vigenere_cypher import VigenereCypher
from src.vigenere_cracker import VigenereCracker
from src.performance import Performance

def main():
    key = input("Provide your key: ")
    cipher = VigenereCypher(key)
    cracker = VigenereCracker()
    try:
        with open("plaintext.txt", "r", encoding="latin-1") as f:
            plaintext = "".join(
                c for c in f.read()
                if "A" <= c <= "Z" or "a" <= c <= "z"
            )
            
    except FileNotFoundError:
        print("plaintext.txt not found. Please create the file with your plaintext.")
        return

    ciphertext = cipher.encrypt(plaintext)

    possible_lengths = cracker.find_key_length(ciphertext)

    functions = [cracker.find_key_sequential, cracker.find_key_parallel_opencl, cracker.find_key_parallel_cuda]
    performance = Performance(functions, ciphertext, possible_lengths, number_of_slices=10)
    performance.visualize_text_length_run_time()

    key_text = {}
    possible_keys = cracker.find_key_sequential(ciphertext, possible_lengths)
    for key in possible_keys:
        decrypted_text = VigenereCypher(key).decrypt(ciphertext)
        key_text[key] = decrypted_text


if __name__ == "__main__":
    main()