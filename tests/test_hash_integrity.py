import hashlib
import unittest
import unicodedata


class HashIntegrityTests(unittest.TestCase):
    def sha256(self, value: bytes) -> str:
        return hashlib.sha256(value).hexdigest()

    def test_known_sha256_vector(self):
        self.assertEqual(
            self.sha256(b"abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        )

    def test_one_byte_change_changes_fingerprint(self):
        original = b'{"message":"hello"}\n'
        changed = b'{"message":"jello"}\n'
        self.assertNotEqual(self.sha256(original), self.sha256(changed))

    def test_newline_change_changes_fingerprint(self):
        lf = b"line one\nline two\n"
        crlf = b"line one\r\nline two\r\n"
        self.assertNotEqual(self.sha256(lf), self.sha256(crlf))

    def test_trailing_space_changes_fingerprint(self):
        plain = b'{"value":"test"}\n'
        spaced = b'{"value":"test"} \n'
        self.assertNotEqual(self.sha256(plain), self.sha256(spaced))

    def test_unicode_normalization_changes_exact_bytes(self):
        precomposed = unicodedata.normalize("NFC", "cafe\u0301").encode("utf-8")
        decomposed = unicodedata.normalize("NFD", "caf\u00e9").encode("utf-8")
        self.assertNotEqual(precomposed, decomposed)
        self.assertNotEqual(self.sha256(precomposed), self.sha256(decomposed))


if __name__ == "__main__":
    unittest.main()
