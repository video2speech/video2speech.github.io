#!/usr/bin/env python3
"""
Calculate phoneme distribution for 50 total items based on original frequencies
根据原始频率计算音素分布，总数为50
"""

# Original phoneme frequencies from the report
phoneme_data = [
    ("AH", 409, 8.0),
    ("T", 369, 7.2),
    ("N", 347, 6.8),
    ("S", 320, 6.3),
    ("L", 266, 5.2),
    ("IH", 264, 5.2),
    ("R", 262, 5.1),
    ("D", 215, 4.2),
    ("IY", 215, 4.2),
    ("K", 205, 4.0),
    ("EH", 187, 3.7),
    ("M", 160, 3.1),
    ("P", 158, 3.1),
    ("ER", 154, 3.0),
    ("Z", 117, 2.3),
    ("AA", 106, 2.1),
    ("B", 106, 2.1),
    ("EY", 104, 2.0),
    ("F", 101, 2.0),
    ("W", 99, 1.9),
    ("AE", 94, 1.8),
    ("AO", 86, 1.7),
    ("AY", 84, 1.6),
    ("V", 73, 1.4),
    ("NG", 73, 1.4),
    ("OW", 65, 1.3),
    ("HH", 63, 1.2),
    ("UW", 55, 1.1),
    ("G", 53, 1.0),
    ("Y", 43, 0.8),
    ("SH", 42, 0.8),
    ("JH", 37, 0.7),
    ("CH", 36, 0.7),
    ("DH", 33, 0.6),
    ("TH", 33, 0.6),
    ("AW", 32, 0.6),
    ("UH", 26, 0.5),
    ("OY", 8, 0.2),
    ("ZH", 4, 0.1)
]

def calculate_distribution_for_50():
    """Calculate phoneme distribution for total of 50 items."""
    
    total_original = sum(count for _, count, _ in phoneme_data)
    target_total = 50
    
    print("=" * 80)
    print("PHONEME DISTRIBUTION CALCULATION FOR 50 TOTAL ITEMS")
    print("=" * 80)
    print(f"Original total occurrences: {total_original}")
    print(f"Target total: {target_total}")
    print(f"Scale factor: {target_total/total_original:.6f}")
    print("")
    
    # Method 1: Direct proportional scaling with rounding
    print("METHOD 1: Direct Proportional Scaling")
    print("-" * 50)
    
    scaled_values = []
    for phoneme, count, percentage in phoneme_data:
        scaled = (count / total_original) * target_total
        rounded = round(scaled)
        scaled_values.append((phoneme, count, percentage, scaled, rounded))
    
    # Check if sum equals 50, if not adjust
    current_sum = sum(rounded for _, _, _, _, rounded in scaled_values)
    
    print(f"Initial sum after rounding: {current_sum}")
    
    # Adjust to make sum exactly 50
    if current_sum != target_total:
        difference = target_total - current_sum
        print(f"Adjustment needed: {difference}")
        
        # Sort by fractional part to decide which to adjust
        fractional_parts = []
        for i, (phoneme, count, percentage, scaled, rounded) in enumerate(scaled_values):
            fractional_part = scaled - rounded
            fractional_parts.append((i, fractional_part, phoneme, rounded))
        
        # Sort by fractional part (descending for positive difference, ascending for negative)
        if difference > 0:
            fractional_parts.sort(key=lambda x: x[1], reverse=True)
        else:
            fractional_parts.sort(key=lambda x: x[1])
        
        # Adjust the values
        adjusted_values = [rounded for _, _, _, _, rounded in scaled_values]
        
        for j in range(abs(difference)):
            idx = fractional_parts[j][0]
            if difference > 0:
                adjusted_values[idx] += 1
            else:
                if adjusted_values[idx] > 0:  # Don't go below 0
                    adjusted_values[idx] -= 1
        
        # Update scaled_values with adjusted values
        for i in range(len(scaled_values)):
            phoneme, count, percentage, scaled, _ = scaled_values[i]
            scaled_values[i] = (phoneme, count, percentage, scaled, adjusted_values[i])
    
    # Display results
    print("\nFINAL DISTRIBUTION:")
    print("Rank | Phoneme | Original | Original% | Scaled | Assigned | New%")
    print("-" * 70)
    
    total_assigned = 0
    for i, (phoneme, count, percentage, scaled, assigned) in enumerate(scaled_values, 1):
        new_percentage = (assigned / target_total) * 100
        total_assigned += assigned
        print(f"{i:4d} | /{phoneme:3s}/   | {count:8d} | {percentage:7.1f}% | {scaled:6.2f} | {assigned:8d} | {new_percentage:5.1f}%")
    
    print("-" * 70)
    print(f"TOTAL|         | {total_original:8d} | {100.0:7.1f}% |  {target_total:.2f} | {total_assigned:8d} | {100.0:5.1f}%")
    
    # Summary for easy copying
    print("\n" + "=" * 80)
    print("SUMMARY FOR 50 ITEMS (COPY-READY FORMAT):")
    print("=" * 80)
    
    for i, (phoneme, count, percentage, scaled, assigned) in enumerate(scaled_values, 1):
        print(f"/{phoneme}/: {assigned}")
    
    # Verification
    print(f"\nVerification - Total assigned: {sum(assigned for _, _, _, _, assigned in scaled_values)}")
    
    return scaled_values

if __name__ == "__main__":
    result = calculate_distribution_for_50()
