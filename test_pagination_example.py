#!/usr/bin/env python3
"""Example demonstrating file pagination with the new tools"""

# Create a large test file
with open("large_test_file.txt", "w") as f:
    for i in range(1, 2001):
        f.write(f"Line {i}: This is a test line to demonstrate pagination functionality\n")

print("Created large_test_file.txt with 2000 lines")
print("\nTo read this file with pagination, Claude can use:")
print("1. read_file with path='large_test_file.txt' - reads first 500 lines")
print("2. read_file with path='large_test_file.txt', start_line=501 - reads next 500 lines")
print("3. Continue with start_line=1001, 1501, etc.")
print("\nThis ensures the output always fits within API token limits!") 