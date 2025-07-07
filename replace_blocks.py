#!/usr/bin/env python3
"""
Litematic Block Replacer
Replaces specific blocks in .litematic files while maintaining their placement.
Compatible with Litematica mod.
"""

import os
import gzip
from pathlib import Path
try:
    import nbtlib
    from nbtlib import tag
except ImportError:
    print("Error: nbtlib is required. Install it with: pip install nbtlib")
    exit(1)

def detect_file_format(file_path):
    try:
        with open(file_path, 'rb') as f:
            return 'gzipped' if f.read(2) == b'\x1f\x8b' else 'uncompressed'
    except:
        return 'unknown'

def load_litematic(file_path):
    file_format = detect_file_format(file_path)
    try:
        if file_format == 'gzipped':
            try:
                return nbtlib.File.load(file_path, gzipped=True), file_format
            except:
                with gzip.open(file_path, 'rb') as f:
                    return nbtlib.File.parse(f.read()), file_format
        else:
            try:
                return nbtlib.File.load(file_path), file_format
            except:
                with open(file_path, 'rb') as f:
                    return nbtlib.File.parse(f.read()), file_format
    except Exception:
        return None, None

def save_litematic(nbt_data, file_path, original_format):
    try:
        if original_format == 'gzipped':
            nbt_data.save(file_path, gzipped=True)
        else:
            nbt_data.save(file_path)
        return True
    except Exception:
        try:
            with (gzip.open if original_format == 'gzipped' else open)(file_path, 'wb') as f:
                nbt_data.write(f)
            return True
        except:
            return False

def replace_blocks_in_palette(nbt_data, old_block, new_block):
    replacements = 0
    if 'Regions' not in nbt_data:
        return 0
    for region_name, region_data in nbt_data['Regions'].items():
        palette = region_data.get('BlockStatePalette')
        if not palette:
            continue
        for i, block_state in enumerate(palette):
            if block_state.get('Name', '') == old_block:
                new_block_state = tag.Compound({'Name': tag.String(new_block)})
                if 'Properties' in block_state:
                    new_block_state['Properties'] = block_state['Properties']
                palette[i] = new_block_state
                replacements += 1
                print(f"Replaced in region '{region_name}', index {i}")
    return replacements

def list_blocks(nbt_data):
    blocks = set()
    for region in nbt_data.get('Regions', {}).values():
        for block in region.get('BlockStatePalette', []):
            blocks.add(str(block.get('Name', 'unknown')))
    return sorted(blocks)

def verify_structure(nbt_data):
    keys = ['Version', 'MinecraftDataVersion', 'Metadata', 'Regions']
    for k in keys:
        if k not in nbt_data:
            print(f"Warning: Missing '{k}'")
            return False
    print("✓ Structure OK")
    return True

def get_block_selection(blocks, prompt_text):
    """Get block selection from user - either by number or by typing block name"""
    while True:
        user_input = input(f"\n{prompt_text} (number or block name): ").strip()
        
        # Check if input is a number
        if user_input.isdigit():
            block_num = int(user_input)
            if 1 <= block_num <= len(blocks):
                selected_block = blocks[block_num - 1]
                print(f"Selected: {selected_block}")
                return selected_block
            else:
                print(f"Invalid number. Please enter 1-{len(blocks)}")
                continue
        
        # Handle text input
        if ':' not in user_input:
            user_input = f"minecraft:{user_input}"
        
        if user_input in blocks:
            return user_input
        else:
            print("Block not found. Try again.")

def main():
    print("=== Litematic Block Replacer ===")
    while True:
        file_path = input("Enter path to .litematic file: ").strip()
        file_path = Path(file_path)
        if file_path.exists() and file_path.suffix == '.litematic':
            break
        print("Invalid file. Try again.")

    nbt_data, fmt = load_litematic(file_path)
    if not nbt_data:
        print("Failed to load.")
        return

    verify_structure(nbt_data)
    blocks = list_blocks(nbt_data)
    if not blocks:
        print("No blocks found.")
        return

    print("Found blocks:")
    for i, b in enumerate(blocks, 1):
        print(f"{i:2d}. {b}")

    old_block = get_block_selection(blocks, "Block to replace")
    new_block = input("Replace with: ").strip()
    if ':' not in new_block:
        new_block = f"minecraft:{new_block}"

    if input(f"\nConfirm replace '{old_block}' with '{new_block}'? (y/n): ").lower() != 'y':
        print("Cancelled.")
        return

    replaced = replace_blocks_in_palette(nbt_data, old_block, new_block)
    if replaced == 0:
        print("No replacements made.")
        return

    backup_path = file_path.with_suffix('.litematic.backup')
    try:
        backup_path.write_bytes(file_path.read_bytes())
        print(f"Backup created: {backup_path}")
    except Exception as e:
        print(f"Failed to create backup: {e}")

    if save_litematic(nbt_data, file_path, fmt):
        print(f"File saved: {file_path}")
        test_data, _ = load_litematic(file_path)
        if test_data and verify_structure(test_data):
            print("✓ Verified updated file.")
        else:
            print("⚠ Warning: Structure check failed.")
    else:
        print("Failed to save changes.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.")
    except Exception as e:
        print(f"Unexpected error: {e}")
