import os
import re
import json

input_dir = './jsons'
output_file_prefix = 'usernames'
batch_size = 100000

username_pattern = re.compile(r'"username":\s*"([^"]+)"')

def extract_usernames_from_file(file_path):
    usernames = set()
    with open(file_path, 'r', encoding='utf-8') as file:
        try:
            data = file.read()
            matches = username_pattern.findall(data)
            usernames.update(matches)
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    return usernames

def main():
    all_usernames = set()
    file_count = 1
    
    for root, _, files in os.walk(input_dir):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            if file_path.endswith('.json'):
                print(f"Processing {file_path}...")
                usernames = extract_usernames_from_file(file_path)
                all_usernames.update(usernames)
                
                if len(all_usernames) >= batch_size:
                    current_batch = list(all_usernames)[:batch_size]
                    all_usernames = set(list(all_usernames)[batch_size:])
                    
                    output_file = f"{output_file_prefix}_{file_count}.txt"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write("\n".join(current_batch))
                    print(f"Written {len(current_batch)} usernames to {output_file}")
                    
                    file_count += 1

    if all_usernames:
        output_file = f"{output_file_prefix}_{file_count}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(all_usernames))
        print(f"Written {len(all_usernames)} usernames to {output_file}")

if __name__ == "__main__":
    main()
