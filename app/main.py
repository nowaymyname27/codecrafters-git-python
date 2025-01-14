import sys
import os
import zlib

def init(command):
    os.mkdir(".git")
    os.mkdir(".git/objects")
    os.mkdir(".git/refs")
    with open (".git/HEAD", "w") as f:
        f.write("ref: refs/heads/main\n")
    print("Initialized git directory")

def cat_file():
    obj_name = sys.argv[3]
    with open(f".git/objects/{obj_name[:2]}/{obj_name[2:]}", "rb") as f:
        raw = zlib.decompress(f.read())
        header, content = raw.split(b"\0", maxsplit=1)
        print(content.decode(encoding="utf-8"), end="")

def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!", file=sys.stderr)

    command = sys.argv[1]
    if command == "init":
        init(command)
    elif command == "cat-file" and sys.argv[2] == "-p":
        cat_file()
    else:
        raise RuntimeError(f"Unknown command #{command}")



if __name__ == "__main__":
    main()
