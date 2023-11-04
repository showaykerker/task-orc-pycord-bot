import os
import base64
import dotenv
import questionary
import argparse
from cryptography.fernet import Fernet



def encrypt(plain_text):
    key = os.environ.get("ENCRYPT_KEY")

    if not key:
        raise ValueError("No encryption key found. Please run `python encrypt.py -g` to generate a key")

    cipher_suite = Fernet(base64.b64decode(key))
    encrypted_binary = cipher_suite.encrypt(plain_text.encode())
    encoded_encrypted = base64.b64encode(encrypted_binary).decode()

    return encoded_encrypted

def decrypt(cipher_text):
    key = os.environ.get("ENCRYPT_KEY")

    if not key:
        raise ValueError("No encryption key found. Please run `python encrypt.py -g` to generate a key")

    cipher_suite = Fernet(base64.b64decode(key))
    decoded = base64.b64decode(cipher_text)
    decrypted = cipher_suite.decrypt(decoded).decode()
    return decrypted

def gen_key():

    dotenv.load_dotenv()

    binary_key = Fernet.generate_key()
    encoded_key = base64.b64encode(binary_key).decode()

    if os.environ.get("ENCRYPT_KEY"):
        if not questionary.confirm(
                "Key already exists. Do you want to overwrite it?").ask():
            print(f"Key was not overwritten.")
            exit(1)

    with open(".env", "a") as f:
        f.write("# Added by encryption.py\n")
        f.write(f"ENCRYPT_KEY={encoded_key}\n")
        print("Key created.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-g", "--generate", help="Generate a new encryption key", action="store_true")

    args = parser.parse_args()

    if args.generate:
        gen_key()
    else:
        print("No arguments were provided. Use -h or --help for help")