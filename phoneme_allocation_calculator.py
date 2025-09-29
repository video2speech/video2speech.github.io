#!/usr/bin/env python3
"""
Calculate optimal phoneme allocation for 50 total items while maintaining original proportions
计算在总数为50的情况下保持原始比例的最优音素分配
"""

import math

def calculate_phoneme_allocation():
    """Calculate optimal allocation of 50 items across 39 phonemes."""
    
    # Original phoneme data (frequency, phoneme)
    phoneme_data = [
        (409, "AH"), (369, "T"), (347, "N"), (320, "S"), (266, "L"),
        (264, "IH"), (262, "R"), (215, "D"), (215, "IY"), (205, "K"),
        (187, "EH"), (160, "M"), (158, "P"), (154, "ER"), (117, "Z"),
        (106, "AA"), (106, "B"), (104, "EY"), (101, "F"), (99, "W"),
        (94, "AE"), (86, "AO"), (84, "AY"), (73, "V"), (73, "NG"),
        (65, "OW"), (63, "HH"), (55, "UW"), (53, "G"), (43, "Y"),
        (42, "SH"), (37, "JH"), (36, "CH"), (33, "DH"), (33, "TH"),
        (32, "AW"), (26, "UH"), (8, "OY"), (4, "ZH")
    ]
    
    total_original = sum(freq for freq, _ in phoneme_data)
    target_total = 50
    num_phonemes = len(phoneme_data)
    
    print("=" * 80)
    print("音素分配计算 - PHONEME ALLOCATION CALCULATOR")
    print("=" * 80)
    print(f"原始总频次: {total_original}")
    print(f"目标总数: {target_total}")
    print(f"音素总数: {num_phonemes}")
    print(f"每个音素最少: 1")
    print("")
    
    # Method 1: Direct proportional allocation with minimum 1
    print("方法1: 直接比例分配（每个音素最少1个）")
    print("-" * 50)
    
    # First, allocate 1 to each phoneme
    remaining = target_total - num_phonemes  # 50 - 39 = 11 remaining
    
    # Calculate proportional allocation for remaining items
    allocations_method1 = []
    allocated_extra = 0
    
    for freq, phoneme in phoneme_data:
        # Base allocation of 1
        base_allocation = 1
        
        # Calculate proportional extra allocation
        proportion = freq / total_original
        extra_allocation = round(proportion * remaining)
        
        total_allocation = base_allocation + extra_allocation
        allocations_method1.append((total_allocation, phoneme, freq, proportion))
        allocated_extra += extra_allocation
    
    # Adjust if total doesn't match exactly
    current_total = sum(alloc for alloc, _, _, _ in allocations_method1)
    adjustment_needed = target_total - current_total
    
    print(f"初始分配总数: {current_total}")
    print(f"需要调整: {adjustment_needed}")
    
    # Apply adjustment to highest frequency phonemes
    if adjustment_needed != 0:
        # Sort by frequency for adjustment
        sorted_for_adjustment = sorted(allocations_method1, key=lambda x: x[2], reverse=True)
        
        # Apply adjustments
        adjusted_allocations = []
        adjustments_made = 0
        
        for i, (alloc, phoneme, freq, prop) in enumerate(sorted_for_adjustment):
            if adjustments_made < abs(adjustment_needed):
                if adjustment_needed > 0:
                    new_alloc = alloc + 1
                    adjustments_made += 1
                else:
                    if alloc > 1:  # Don't go below minimum of 1
                        new_alloc = alloc - 1
                        adjustments_made += 1
                    else:
                        new_alloc = alloc
            else:
                new_alloc = alloc
            
            adjusted_allocations.append((new_alloc, phoneme, freq, prop))
        
        # Sort back to original order
        allocations_method1 = sorted(adjusted_allocations, key=lambda x: x[2], reverse=True)
    
    # Display results
    print("\n最终分配结果:")
    print("排名  音素   分配数量  原始频次  原始比例%  新比例%")
    print("-" * 60)
    
    total_check = 0
    for i, (alloc, phoneme, freq, prop) in enumerate(allocations_method1, 1):
        new_prop = (alloc / target_total) * 100
        orig_prop = prop * 100
        total_check += alloc
        print(f"{i:2d}. /{phoneme:3s}/: {alloc:2d}    {freq:4d}     {orig_prop:5.1f}%     {new_prop:5.1f}%")
    
    print("-" * 60)
    print(f"总计: {total_check}")
    
    # Calculate deviation
    total_deviation = 0
    for alloc, phoneme, freq, prop in allocations_method1:
        original_prop = prop * 100
        new_prop = (alloc / target_total) * 100
        deviation = abs(original_prop - new_prop)
        total_deviation += deviation
    
    average_deviation = total_deviation / num_phonemes
    
    print(f"\n统计信息:")
    print(f"平均偏差: {average_deviation:.2f}%")
    print(f"最大分配: {max(alloc for alloc, _, _, _ in allocations_method1)}")
    print(f"最小分配: {min(alloc for alloc, _, _, _ in allocations_method1)}")
    
    # Generate summary for easy copying
    print("\n" + "=" * 80)
    print("简洁分配结果 (便于复制):")
    print("=" * 80)
    
    for i, (alloc, phoneme, freq, prop) in enumerate(allocations_method1, 1):
        print(f"{i:2d}. /{phoneme}/: {alloc}")
    
    return allocations_method1

if __name__ == "__main__":
    allocations = calculate_phoneme_allocation()


