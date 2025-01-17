import sys
import os
import zlib
import hashlib

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

def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!", file=sys.stderr)

    command = sys.argv[1]
    if command == "init":
        init()
    elif command == "cat-file":
        cat_file()
    elif command == "hash-object":
        hash_object()
    elif command == "ls-tree":
        ls_tree()
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
