import sys
import os
import zlib
import hashlib
import time

def init():
    os.mkdir(".git")
    os.mkdir(".git/objects")
    os.mkdir(".git/refs")
    with open (".git/HEAD", "w") as file:
        file.write("ref: refs/heads/main\n")
    print("Initialized git directory")

def cat_file():
    if sys.argv[2] != "-p":
        raise RuntimeError("Missing '-p' flag")
    obj_name = sys.argv[3]
    with open(f".git/objects/{obj_name[:2]}/{obj_name[2:]}", "rb") as file:
        raw = zlib.decompress(file.read())
        header, content = raw.split(b"\0", maxsplit=1)
        print(content.decode(encoding="utf-8"), end="")

def hash_object():
    if sys.argv[2] != "-w":
        raise RuntimeError("Missing '-w' flag")

    file_path = sys.argv[3]

    # 1. Read the file content
    with open(file_path, "rb") as file:
        content = file.read()

    # 2. Create the blob header: "blob <size>\0"
    header = f"blob {len(content)}\0".encode()

    # 3. Combine header + content
    store_data = header + content

    # 4. Compute SHA-1 hash
    sha1_hash = hashlib.sha1(store_data).hexdigest()

    # 5. Prepare the object path
    dir_name = f".git/objects/{sha1_hash[:2]}"
    file_name = sha1_hash[2:]

    # 6. Create directory if it doesn't exist
    os.makedirs(dir_name, exist_ok=True)

    # 7. Compress and write the data
    compressed_data = zlib.compress(store_data)
    with open(f"{dir_name}/{file_name}", "wb") as f:
        f.write(compressed_data)

    # 8. Print the SHA-1 hash
    print(sha1_hash)

def ls_tree():
    if sys.argv[2] != "--name-only":
        raise RuntimeError("Missing '--name-only' flag")

    tree_sha = sys.argv[3]
    object_path = f".git/objects/{tree_sha[:2]}/{tree_sha[2:]}"

    # 1. Read and decompress the tree object
    with open(object_path, "rb") as file:
        raw = zlib.decompress(file.read())

    # 2. Skip the header ("tree <size>\0")
    _, content = raw.split(b"\0", maxsplit=1)

    entries = []

    # 3. Parse each entry: <mode> <name>\0<20-byte SHA>
    i = 0
    while i < len(content):
        # Extract mode (file type) and name
        mode_end = content.find(b" ", i)
        mode = content[i:mode_end].decode()

        name_end = content.find(b"\0", mode_end)
        name = content[mode_end + 1:name_end].decode()

        # Extract the 20-byte SHA (raw bytes)
        sha = content[name_end + 1:name_end + 21]

        entries.append(name)

        # Move to the next entry
        i = name_end + 21

    # 4. Print sorted names
    for name in sorted(entries):
        print(name)

def write_tree(directory="."):
    entries = []

    # 1. Scan directory contents
    for item in sorted(os.listdir(directory)):
        if item == ".git":
            continue  # Skip the .git directory

        path = os.path.join(directory, item)

        # 2. Handle files (create blob objects)
        if os.path.isfile(path):
            with open(path, "rb") as file:
                content = file.read()

            # Create blob: "blob <size>\0<content>"
            blob_header = f"blob {len(content)}\0".encode()
            blob_data = blob_header + content

            # SHA-1 hash and write the blob
            blob_hash = hashlib.sha1(blob_data).hexdigest()
            dir_name = f".git/objects/{blob_hash[:2]}"
            file_name = blob_hash[2:]
            os.makedirs(dir_name, exist_ok=True)

            # Compress and store blob
            compressed_blob = zlib.compress(blob_data)
            with open(f"{dir_name}/{file_name}", "wb") as f:
                f.write(compressed_blob)

            # Add file entry to the tree (mode 100644 for files)
            entry = f"100644 {item}".encode() + b"\0" + bytes.fromhex(blob_hash)
            entries.append(entry)

        # 3. Handle directories (create tree objects recursively)
        elif os.path.isdir(path):
            subtree_hash = write_tree(path)  # Recursive call

            # Add directory entry to the tree (mode 40000 for directories)
            entry = f"40000 {item}".encode() + b"\0" + bytes.fromhex(subtree_hash)
            entries.append(entry)

    # 4. Create the tree object
    tree_data = b"".join(entries)
    tree_header = f"tree {len(tree_data)}\0".encode()
    store_data = tree_header + tree_data

    # 5. Compute SHA-1 hash for the tree object
    tree_hash = hashlib.sha1(store_data).hexdigest()

    # 6. Write the tree object to .git/objects
    dir_name = f".git/objects/{tree_hash[:2]}"
    file_name = tree_hash[2:]
    os.makedirs(dir_name, exist_ok=True)

    compressed_tree = zlib.compress(store_data)
    with open(f"{dir_name}/{file_name}", "wb") as f:
        f.write(compressed_tree)

    # 7. Return the tree SHA-1 hash
    return tree_hash

def commit_tree():
    # 1. Parse arguments
    tree_sha = sys.argv[2]
    parent_sha = None
    message = ""

    # Handle optional parent (-p) and message (-m)
    if "-p" in sys.argv:
        parent_index = sys.argv.index("-p")
        parent_sha = sys.argv[parent_index + 1]

    if "-m" in sys.argv:
        message_index = sys.argv.index("-m")
        message = sys.argv[message_index + 1]

    # Ensure the message ends with a newline
    if not message.endswith("\n"):
        message += "\n"

    # 2. Author/Committer details (hardcoded)
    author = "Your Name <you@example.com>"
    timestamp = int(time.time())
    timezone = time.strftime('%z')

    # 3. Build the commit content
    commit_lines = [
        f"tree {tree_sha}"
    ]

    if parent_sha:
        commit_lines.append(f"parent {parent_sha}")

    commit_lines.append(f"author {author} {timestamp} {timezone}")
    commit_lines.append(f"committer {author} {timestamp} {timezone}")
    commit_lines.append("")  # Empty line before the message
    commit_lines.append(message)

    commit_content = "\n".join(commit_lines).encode()

    # 4. Create the commit header
    header = f"commit {len(commit_content)}\0".encode()
    store_data = header + commit_content

    # 5. Compute SHA-1 hash
    commit_hash = hashlib.sha1(store_data).hexdigest()

    # 6. Write the commit object
    dir_name = f".git/objects/{commit_hash[:2]}"
    file_name = commit_hash[2:]
    os.makedirs(dir_name, exist_ok=True)

    compressed_commit = zlib.compress(store_data)
    with open(f"{dir_name}/{file_name}", "wb") as f:
        f.write(compressed_commit)

    # 7. Print the commit SHA
    print(commit_hash)

def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!\n", file=sys.stderr)

    command = sys.argv[1]
    if command == "init":
        init()
    elif command == "cat-file":
        cat_file()
    elif command == "hash-object":
        hash_object()
    elif command == "ls-tree":
        ls_tree()
    elif command == "write-tree":
        tree_hash = write_tree()
        print(tree_hash)
    elif command == "commit-tree":
        commit_tree()
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
