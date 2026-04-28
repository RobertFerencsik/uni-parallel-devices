from collections import Counter
import os
from pathlib import Path
import sys
import warnings
import pyopencl as cl
import numpy as np


def _configure_numba_cuda_paths():
    """
    Configure CUDA toolkit paths for Numba in venv/pip-based installs.
    """
    venv_root = Path(sys.prefix)
    bridge_root = venv_root / "cuda-bridge"
    nvidia_root = venv_root / "Lib" / "site-packages" / "nvidia"
    cuda_nvcc = nvidia_root / "cuda_nvcc"
    cuda_runtime = nvidia_root / "cuda_runtime"
    cuda_nvrtc = nvidia_root / "cuda_nvrtc"

    if "CUDA_PATH" not in os.environ:
        if bridge_root.exists():
            os.environ["CUDA_PATH"] = str(bridge_root)
        elif cuda_nvcc.exists():
            os.environ["CUDA_PATH"] = str(cuda_nvcc)

    for bin_dir in (bridge_root / "bin", bridge_root / "nvvm" / "bin",
                    cuda_nvcc / "bin", cuda_nvcc / "nvvm" / "bin",
                    cuda_runtime / "bin", cuda_nvrtc / "bin"):
        if bin_dir.exists():
            os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")
            if hasattr(os, "add_dll_directory"):
                os.add_dll_directory(str(bin_dir))


_configure_numba_cuda_paths()
from numba import cuda
from numba.core.errors import NumbaPerformanceWarning

warnings.filterwarnings("ignore", category=NumbaPerformanceWarning)



class VigenereCracker:
    _ENG_FREQ_ARRAY = np.array([
        8.12, 1.49, 2.71, 4.32, 12.02, 2.30, 2.03, 5.92, 7.31, 0.10, 0.69, 3.98,
        2.61, 6.95, 7.68, 1.82, 0.11, 6.02, 6.28, 9.10, 2.88, 1.11, 2.09, 0.17,
        2.11, 0.07
    ], dtype=np.float32)
    
    def find_key_length(self, ciphertext, max_length=20):
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

    def find_key_sequential(self, ciphertext, key_lengths):
        """Find key based on key length"""
        keys = []
        for key_length in key_lengths:
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
            keys.append(key)
        
        return keys
    
    def find_key_parallel_opencl(self, ciphertext, key_lengths):
        try:
            platforms = cl.get_platforms()
            devices = []
            for platform in platforms:
                devices.extend(platform.get_devices(device_type=cl.device_type.GPU))
            if not devices:
                raise RuntimeError("No OpenCL GPU device found.")
            context = cl.Context(devices=[devices[0]])
            queue = cl.CommandQueue(context)
        except Exception as exc:
            raise RuntimeError("OpenCL is not available or failed to initialize.") from exc

        text = np.array(
            [ord(c.upper()) - ord('A') for c in ciphertext if c.isalpha()],
            dtype=np.int32
        )
        if text.size == 0:
            return []

        program = cl.Program(
            context,
            """
            __kernel void count_all_shifts(
                __global const int* segment,
                const int n,
                __global unsigned int* counts
            ) {
                int gid = get_global_id(0);
                int shift = gid / n;
                int idx = gid % n;
                if (shift >= 26 || idx >= n) {
                    return;
                }

                int val = segment[idx] - shift;
                if (val < 0) {
                    val += 26;
                }
                atom_inc(&counts[shift * 26 + val]);
            }

            __kernel void score_shifts(
                __global const unsigned int* counts,
                __global const float* expected_freq,
                const int n,
                __global float* scores
            ) {
                int shift = get_global_id(0);
                if (shift >= 26) {
                    return;
                }
                float score = 0.0f;
                for (int letter = 0; letter < 26; letter++) {
                    float freq = ((float)counts[shift * 26 + letter] * 100.0f) / (float)n;
                    float diff = expected_freq[letter] - freq;
                    score += diff < 0.0f ? -diff : diff;
                }
                scores[shift] = score;
            }
            """
        ).build()
        count_kernel = cl.Kernel(program, "count_all_shifts")
        score_kernel = cl.Kernel(program, "score_shifts")
        expected_freq_buf = cl.Buffer(
            context,
            cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
            hostbuf=self._ENG_FREQ_ARRAY
        )

        keys = []

        for key_length in key_lengths:
            key = ''

            for position in range(key_length):
                segment = np.ascontiguousarray(text[position::key_length], dtype=np.int32)
                if segment.size == 0:
                    continue

                mf = cl.mem_flags
                segment_buf = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=segment)
                counts = np.zeros(26 * 26, dtype=np.uint32)
                scores = np.zeros(26, dtype=np.float32)
                counts_buf = cl.Buffer(context, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=counts)
                scores_buf = cl.Buffer(context, mf.WRITE_ONLY, scores.nbytes)

                count_kernel.set_args(segment_buf, np.int32(segment.size), counts_buf)
                cl.enqueue_nd_range_kernel(queue, count_kernel, (segment.size * 26,), None)

                score_kernel.set_args(counts_buf, expected_freq_buf, np.int32(segment.size), scores_buf)
                cl.enqueue_nd_range_kernel(queue, score_kernel, (26,), None)

                cl.enqueue_copy(queue, scores, scores_buf).wait()
                best_shift = int(np.argmin(scores))

                key += chr(best_shift + ord('A'))

            keys.append(key)

        return keys

    def find_key_parallel_cuda(self, ciphertext, key_lengths):
        if not cuda.is_available():
            raise RuntimeError("CUDA is not available. NVIDIA GPU execution is required.")

        text = np.array(
            [ord(c.upper()) - ord('A') for c in ciphertext if c.isalpha()],
            dtype=np.int32
        )
        if text.size == 0:
            return []

        @cuda.jit
        def count_all_shifts_kernel(segment, counts):
            idx = cuda.grid(1)
            n = segment.size
            total = n * 26
            if idx < total:
                shift = idx // n
                pos = idx % n
                val = (segment[pos] - shift + 26) % 26
                cuda.atomic.add(counts, (shift, val), 1)

        @cuda.jit
        def score_shifts_kernel(counts, expected_freq, n, scores):
            shift = cuda.grid(1)
            if shift < 26:
                score = 0.0
                for letter in range(26):
                    freq = (counts[shift, letter] * 100.0) / n
                    diff = expected_freq[letter] - freq
                    if diff < 0:
                        diff = -diff
                    score += diff
                scores[shift] = score

        keys = []
        threads = 256

        for key_length in key_lengths:
            key = ''

            for position in range(key_length):
                segment = np.ascontiguousarray(text[position::key_length], dtype=np.int32)
                if segment.size == 0:
                    continue

                d_segment = cuda.to_device(segment)
                d_counts = cuda.to_device(np.zeros((26, 26), dtype=np.int32))
                d_scores = cuda.device_array(26, dtype=np.float32)
                d_expected = cuda.to_device(self._ENG_FREQ_ARRAY)

                count_blocks = ((segment.size * 26) + threads - 1) // threads
                score_blocks = (26 + threads - 1) // threads

                count_all_shifts_kernel[count_blocks, threads](d_segment, d_counts)
                score_shifts_kernel[score_blocks, threads](
                    d_counts, d_expected, np.float32(segment.size), d_scores
                )

                scores = d_scores.copy_to_host()
                best_shift = int(np.argmin(scores))

                key += chr(best_shift + ord('A'))

            keys.append(key)

        return keys

