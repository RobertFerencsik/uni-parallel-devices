import time
import matplotlib.pyplot as plt
import random

class Performance:
    def __init__(self, functions, text, possible_lengths, number_of_slices):
        self.functions =  functions
        self.text = text
        #self.text = ''.join(random.sample(text, len(text)))
        self.possible_lengths = possible_lengths
        self.number_of_slices = number_of_slices

    def ellapsed_time_per_function(self):
        results = {}
        for function in self.functions:
            start = time.perf_counter()
            function(self.text, self.possible_lengths)
            end = time.perf_counter()
            results[function.__name__] = end - start
        return results

    def _slice_text(self):
        text = self.text
        number_of_slices = self.number_of_slices
        n = len(text)
        base, rem = divmod(n, number_of_slices)
        slices = []
        i = 0
        for p in range(number_of_slices):
            size = base + (1 if p < rem else 0)
            slices.append(text[i : i + size])
            i += size
        return slices

    def _build_accumulative_slices(self):
        slices = self._slice_text()
        accumulated_slices = []
        accumulator = ""
        for part in slices:
            accumulator += part
            accumulated_slices.append(accumulator)
        return accumulated_slices

    def _build_long_text(self):
        long_text = ""
        for _ in range(30):
            long_text += self.text
        return long_text
            
    def compare_text_length_run_time(self):
        accumulated_slices = self._build_accumulative_slices()
        text_length_results = {}
        for part in accumulated_slices:
            self.text = part
            results = self.ellapsed_time_per_function()
            text_length_results[len(self.text)] = results
        return text_length_results
        
    def visualize_text_length_run_time(self):
        text_length_results = self.compare_text_length_run_time()
        lengths = list(text_length_results.keys())
        names = text_length_results[lengths[0]].keys()
        for name in names:
            times = [text_length_results[L][name] for L in lengths]
            plt.plot(lengths, times, label=name)
        plt.xlabel("Text Length")
        plt.ylabel("Run Time (s)")
        plt.title("Text Length vs Run Time")
        plt.legend()
        plt.show()

    def stress_test_cuda(self):
        long_text = self._build_long_text()
        self.text = long_text
        results = self.ellapsed_time_per_function()
        return results