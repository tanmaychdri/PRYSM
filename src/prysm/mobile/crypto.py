import base64
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


class MobileCrypto:
    """
    Handles cryptographic operations for the secure device link.
    - X25519 for Key Exchange
    - HKDF for Key Derivation
    - AES-GCM for Encrypted Payloads
    """

    @staticmethod
    def generate_keypair() -> tuple[bytes, bytes]:
        """
        Generate a new X25519 keypair.
        Returns (private_key_bytes, public_key_bytes) in raw format.
        """
        private_key = x25519.X25519PrivateKey.generate()
        public_key = private_key.public_key()

        from cryptography.hazmat.primitives import serialization

        priv_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        pub_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
        )
        return priv_bytes, pub_bytes

    @staticmethod
    def derive_shared_secret(
        private_key_bytes: bytes, peer_public_key_bytes: bytes
    ) -> bytes:
        """
        Derive a shared secret using X25519 and HKDF.
        """
        private_key = x25519.X25519PrivateKey.from_private_bytes(private_key_bytes)
        peer_public_key = x25519.X25519PublicKey.from_public_bytes(
            peer_public_key_bytes
        )

        shared_key = private_key.exchange(peer_public_key)

        # Derive a 256-bit AES key
        derived_key = HKDF(
            algorithm=hashes.SHA256(), length=32, salt=None, info=b"prysm-device-link"
        ).derive(shared_key)

        return derived_key

    @staticmethod
    def encrypt_payload(shared_secret: bytes, plaintext: bytes) -> dict:
        """
        Encrypt a payload using AES-GCM.
        Returns a dictionary with base64 encoded nonce and ciphertext.
        """
        aesgcm = AESGCM(shared_secret)
        nonce = os.urandom(12)  # 96-bit nonce
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        return {
            "nonce": base64.b64encode(nonce).decode("utf-8"),
            "ciphertext": base64.b64encode(ciphertext).decode("utf-8"),
        }

    @staticmethod
    def decrypt_payload(
        shared_secret: bytes, nonce_b64: str, ciphertext_b64: str
    ) -> bytes:
        """
        Decrypt a payload using AES-GCM.
        """
        aesgcm = AESGCM(shared_secret)
        nonce = base64.b64decode(nonce_b64)
        ciphertext = base64.b64decode(ciphertext_b64)

        return aesgcm.decrypt(nonce, ciphertext, None)
