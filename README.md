# Vigenère Cipher Breaking Sequentially and Using Parallelism

The purpose of this repository is to compare the run time and efficiency of decoding a Vigenère Cipher using CPU and GPU device.

Implements:

- Cypher
- Decypher
- Break
- Evaluation

## History of The Unbreakable Cipher
French diplomat and cryptographer Blaise de Vigenère developed the Vigenère Cipher in the 16 century (circa 1580), which over time become known as 'The Unbreakable Cipher'. Vigenère examined the writings of Leon Alberti (the pioneer),  Johannes Trithemius and Giovanni Porta.

This is a polyalphabetic coding system. Compared to the monoalphabetic ciphers which use a single alphabet that yields the same letter for each specific plaintext letter, polyalphabetic ciphers may substitute multiple letters for the same letter. This makes them more resistant to frequency analysis by flattening the frequency distribution.

The original idea uses a table called Vigenère Square and a keyword. The table consists of 26 shifts of the alphabet, first row represents a cipher alphabet with Caesar shift of 1 and so on. To get the encrypted letter repeat the keyword until the length of the  plaintext without spaces, then match each letter of the key word and plain text based on the position, lastly get the intersection of the two from the table.

![[vigenere_square.png]]

Later Hamilton & Yankosky (2024) discuss an other method, in which letters are associated with numbers: A=0, B=1..., Z=25. The plaintext and key word letters are associated with the corresponding numbers, then adding the numbers in modulo 26. The keyword alphabet corresponding to the result is used to determine the row of the table.

## Cracking The Unbreakable Cipher
Charles Babbage British cryptographer cracked it in 1854, however his technique reached the public only in the 1970's.

The keyword length determines the number of ways a letter from the plain text can be encrypted, this results in multiple encodings for words too. The number of ways of encoding a word corresponds to the length of the keyword too and depends on its position relative to the keyword. Frequent words in a long text are inevitably are repeated in long text which indicates repetition in the keyword. Looking at the space between such repetitions hinted at the length of the keyword. Repetition likely occurs due to enciphering the word with the same part of the key.

This observation is used for the Vigenère attack. First the key length is determined using Kasiski examination and IoC (Index of Coincidence), then the cipher text split into columns of key length, from which key letters are recovered by brute force and best frequency distribution is chosen,  
combining these we get the key (let's assume that the key is an English word)

Two important notes. First a sufficiently long enough key, consisting of random letters eliminates the traces of letter frequency. This is called a Vernam Cipher, the key is called a worm and makes it almost impossible to break. Secondly we are assuming English word keywords, and evaluation is important. After deciphering with the key coherent text are expected.

## Sources
ScienceDirect. (n.d.). Polyalphabetic Cipher. https://www.sciencedirect.com/topics/computer-science/polyalphabetic-cipher#:~:text=In%20subject%20area:%20Computer%20Science,On%20this%20page

The Black Chamber. (n.d.). Vigenère Cipher. https://www.simonsingh.net/The_Black_Chamber/vigenere_cipher.html

Clark, Virginia L., "The Vigenére Cipher Expository Paper" (2006). MAT Exam Expository Papers. 7. https://digitalcommons.unl.edu/mathmidexppap/7

University of Southampton.(n.d.). Five Ways to Crack a Vigenère Cipher https://www.cipherchallenge.org/wp-content/uploads/2020/12/Five-ways-to-crack-a-Vigenere-cipher.pdf

https://github.com/kn0x0x/vigenere-cracker/blob/main/README.md

https://github.com/Freegle1643/Vigenere-cipher-decoder-and-encoder/blob/master/ciphermanipulate.py

## Paralellism

3 methods are written to find the keys for cracking the vigenere cipher. They paralellism happens in the evaluate shifts. Core idea:

For each key candidate key length:

1. Split cipher text into key_length groups by position
2. For each group, try Caesar shifts 0..25
3. Score each shifted group against expected English frequencies
4. Pick the best shift, convert to key letter
5. Combine letters into the key

The loop over `key_lengths`and loop over every key `position` is sequential in the following methods. Paralellism happens inside each segment's shift evaulation.

###find_key_sequential (CPU, no true parallelism)

- Loops through each key_length.
- Loops through each key position.
- Builds chars = ciphertext[i::key_length].
- For every shift in 0..25, decrypts chars and calls _score_text.
- Keeps the shift with lowest score.
- Appends letter to key.

### find_key_parallel_opencl (GPU via OpenCL)

- Initialize OpenCL platform/device/context/queue.
- Convert ciphertext to numeric array 0..25 once.
- Compile two kernels:
    - count_all_shifts
    - score_shifts
- For each key position segment:
    - Send segment to GPU.
    - Launch counting kernel over global size segment.size * 26.
    - Launch scoring kernel over global size 26.
    - Copy back 26 scores and pick argmin.

### find_key_parallel_cuda (GPU via Numba CUDA)

- Check cuda.is_available().
- Convert ciphertext to numeric array.
- Define two CUDA kernels (@cuda.jit):
    - count_all_shifts_kernel
    - score_shifts_kernel
- For each segment:
    - Copy segment and arrays to device.
    - Compute block counts.
    - Launch counting kernel, then scoring kernel.
    - Copy 26 scores back and pick best shift.