from src.vigenere_cypher import VigenereCypher
from src.vigenere_cracker import VigenereCracker
from src.performance import Performance

def main():
    key = input("Provide your key: ")
    cipher = VigenereCypher(key)
    cracker = VigenereCracker()
    perf_find_key_seq = Performance(cracker.find_key_sequential)
    perf_find_key_opencl = Performance(cracker.find_key_parallel_opencl)
    perf_find_key_cuda = Performance(cracker.find_key_parallel_cuda)
    
    try:
        with open("plaintext.txt", "r", encoding="utf-8") as f:
            plaintext = f.read()
    except FileNotFoundError:
        print("plaintext.txt not found. Please create the file with your plaintext.")
        return

    ciphertext = cipher.encrypt(plaintext)
    plaintext = cipher.decrypt(ciphertext)
    #cipher.print_key_plaintext_ciphertext(plaintext, ciphertext)

    possible_lengths = cracker.find_key_length(ciphertext)
    key_text = {}
    possible_keys = perf_find_key_seq(ciphertext, possible_lengths)
    possible_keys = perf_find_key_opencl(ciphertext, possible_lengths)
    possible_keys = perf_find_key_cuda(ciphertext, possible_lengths)
    for key in possible_keys:
        decrypted_text = VigenereCypher(key).decrypt(ciphertext)
        key_text[key] = decrypted_text


if __name__ == "__main__":
    main()