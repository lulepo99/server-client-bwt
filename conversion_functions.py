import numpy as np
from collections import defaultdict, deque


# Functions for BWT transformation

def calculate_ranks(suffix_array, k, ranks):
    """
    Function to support the build_suffix_array function. It returns the next_ranks array with the ranks  
    of the suffixes recalculated based on the first k characters.
    """

    # Create the array of rank tuples. Each tuple represents a suffix and contains the suffix current rank (startin at position i) and 
    # its rank k positions ahead, allowing to restart the string if its end is reached.
    suffix_ranks = np.array([(ranks[i], ranks[(i + k) % len(ranks)]) for i in suffix_array], dtype=[('rank1', int), ('rank2', int)])

    # Sort the suffixes based on the tuples in suffix_ranks with a stable kind to preserve the relative order 
    # of suffix indices with equal tuples.
    sorted_indices = np.argsort(suffix_ranks, order=['rank1', 'rank2'], kind='mergesort')

    # Create the next_ranks array for storing the updated ranks.
    next_ranks = np.zeros(len(ranks), dtype=int)

    # The loop iterates through the sorted suffix indices, starting from the second one (the first has rank = 0), and compares each suffix tuple
    # with the previous one to increment the rank by 1 if they differ. Otherwise, assign the same rank as the previous suffix.
    for i in range(1, len(ranks)):
        if suffix_ranks[sorted_indices[i]] != suffix_ranks[sorted_indices[i - 1]]:
            next_ranks[suffix_array[sorted_indices[i]]] = next_ranks[suffix_array[sorted_indices[i - 1]]] + 1
        else:
            next_ranks[suffix_array[sorted_indices[i]]] = next_ranks[suffix_array[sorted_indices[i - 1]]]

    return next_ranks


def build_suffix_array(seq):
    """
    Function to build and return the suffix array for the received sequence.
    """

    # Convert to a numpy array
    seq_array = np.array(list(seq))

    # Create the initial suffix array sorting the starting indices of the suffixes of "seq" based on lexicographic order. 
    # "mergesort" is used to maintain the correct relative order in case of suffixes with the same rank.
    suffix_array = np.argsort(seq_array, kind='mergesort')
    
    # Initialize the ranks array. 
    ranks = np.zeros(len(seq), dtype=int)
    
    # The loop iterates through the sorted suffix indices, starting from the second one (the first has rank = 0), and compares each suffix tuple
    # with the previous one to increment the rank by 1 if they differ. Otherwise, assign the same rank as the previous suffix.
    #  In this part, we are assigning the same initial rank to the suffixes that start with the same character.
    for i in range(1, len(seq)):
        if seq_array[suffix_array[i]] != seq_array[suffix_array[i - 1]]:
            ranks[suffix_array[i]] = ranks[suffix_array[i - 1]] + 1
        else:
            ranks[suffix_array[i]] = ranks[suffix_array[i - 1]]
    

    # In each iteration, compare the suffixes using their ranks through the calculate_ranks function. 
    k = 1
    while k < len(seq):
        
        # Create the array of rank tuples. Each tuple represents a suffix and contains the suffix current rank and its rank k positions ahead.
        suffix_ranks = np.array([(ranks[i], ranks[(i + k) % len(seq)]) for i in suffix_array], dtype=[('rank1', int), ('rank2', int)])

        # Sort the rank tuples ("mergesort" as before).
        sorted_indices = np.argsort(suffix_ranks, order=['rank1', 'rank2'], kind='mergesort')

        # Reorder the suffix array based on the new indices.
        suffix_array = suffix_array[sorted_indices]
        
        # Update the ranks based on the new sorted suffix array using the calculate_ranks function.
        ranks = calculate_ranks(suffix_array, k, ranks)
        
        # Double k to compare larger portions of the suffixes in the next iteration. 
        k *= 2

        # Stop the cycle early if all the suffixes have distinct ranks (optimization)
        if ranks[suffix_array[-1]] == len(seq) - 1:
            break

    return suffix_array


def burrows_wheeler_conversion(seq):
    """
    Function to convert and return the received sequence in the BWT format using the suffix array.
    """

    # Append the character "$" to the string to mark the end. This symbol is lexicographically smaller
    # than all the other characters. 
    seq += "$"

    # Build the suffix array of the sequence using the build_suffix_array function.
    suffix_array = build_suffix_array(seq)

    # Convert to a numpy array.
    seq_array = np.array(list(seq))

    # Create the BWT result to store the result of the conversion based on the suffix array. 
    # For each index i in the suffix array, append the character at i-1 in the original sequence.
    bwt_result = ''.join(seq_array[(i - 1) % len(seq)] for i in suffix_array)

    # Join into a single string and return the final BWT.
    return bwt_result




# Functions for BWT reversion

def map_last_to_first(bwt):
    """
    Function that implements LF mapping:
        - Takes the bwt string (last column) as input.
        - Constructs the first column (the bwt string sorted lexicographically).
        - Determines the rank of each character in the last column.
        - Calculates the corresponding position of the character in the first column.
        - Returns the final array with the indexes.
    """
    
    # Convert to a numpy array.
    bwt_array = np.array(list(bwt))  

    # Sort the bwt string lexicographically to create the first column.
    first_col = np.sort(bwt_array)

    # Create an array to store the indices mapping from the last column to the first column.
    last_to_first = np.zeros(len(bwt), dtype=int)

    # Dictionary to store the first occurrence of each character present in the sorted first column.
    first = {}
    for i, char in enumerate(first_col):
        if char not in first:
            first[char] = i

    # Dictionary to store how many times each character is encountered (the rank).
    char_counts = defaultdict(int)  
    
    # For each character in the last column, determine its index in the first column by summing the index of its first occurrence in the first column  
    # with its rank (the number of occurrences so far in the last column). Then, store it in the last_to_first array.
    for i, char in enumerate(bwt_array):
        first_col_index = first[char] + char_counts[char]      # Find the index in the first column.
        last_to_first[i] = first_col_index      # Store the index.
        char_counts[char] += 1      # Increment the count for the found character.

    return last_to_first


def revert_burrows_wheeler(bwt):
    """
    Function to reverse the bwt string and return the original sequence.
    """
    # This line calls the map_last_to_first function to store the positions of the characters present
    # in the bwt string mapped in the sorted bwt string (first column).
    last_to_first = map_last_to_first(bwt)

    # Convert to a numpy array.
    bwt_array = np.array(list(bwt))
    
    # Get the index of the terminator character.
    idx = np.where(bwt_array == '$')[0][0]

    # Variable to store the reconstructed sequence. A deque is used to more efficiently prepend 
    # the characters.
    original_seq = deque()

    # The loop iterates for the length of the bwt string, prepending the characters to "original_seq" 
    # in reverse order using the last_to_first mapping.    
    for _ in range(len(bwt)):
        char = bwt_array[idx]      # Get the character at index "idx" in the bwt string
        original_seq.appendleft(char)      # Append the character to the front of "original_seq".
        idx = last_to_first[idx]      # Update idx 

    # Join into a single string and return the original sequence without the terminator character
    return ''.join(original_seq)[:-1]


