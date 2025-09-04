"use client";

const SALT_SIZE = 16;
const IV_SIZE = 12;
const KEY_LENGTH = 256;
const PBKDF2_ITERATIONS = 100000;

async function deriveKey(
  passphrase: string,
  salt: Uint8Array
): Promise<CryptoKey> {
  const passphraseBuffer = new TextEncoder().encode(passphrase);
  const baseKey = await window.crypto.subtle.importKey(
    "raw",
    passphraseBuffer,
    { name: "PBKDF2" },
    false,
    ["deriveKey"]
  );

  return window.crypto.subtle.deriveKey(
    {
      name: "PBKDF2",
      salt: salt,
      iterations: PBKDF2_ITERATIONS,
      hash: "SHA-256",
    },
    baseKey,
    { name: "AES-GCM", length: KEY_LENGTH },
    true,
    ["encrypt", "decrypt"]
  );
}

export async function encryptFile(
  file: File,
  passphrase: string
): Promise<Blob> {
  const salt = window.crypto.getRandomValues(new Uint8Array(SALT_SIZE));
  const iv = window.crypto.getRandomValues(new Uint8Array(IV_SIZE));

  const key = await deriveKey(passphrase, salt);

  const fileBuffer = await file.arrayBuffer();

  const encryptedContent = await window.crypto.subtle.encrypt(
    {
      name: "AES-GCM",
      iv: iv,
    },
    key,
    fileBuffer
  );

  const encryptedBlob = new Blob([salt, iv, encryptedContent]);
  return encryptedBlob;
}

export async function decryptFile(
  file: File,
  passphrase: string
): Promise<Blob> {
  try {
    const fileBuffer = await file.arrayBuffer();

    const salt = fileBuffer.slice(0, SALT_SIZE);
    const iv = fileBuffer.slice(SALT_SIZE, SALT_SIZE + IV_SIZE);
    const encryptedContent = fileBuffer.slice(SALT_SIZE + IV_SIZE);

    if (salt.byteLength !== SALT_SIZE || iv.byteLength !== IV_SIZE) {
      throw new Error(
        "Invalid file format. The file may not be an encrypted file or it is corrupted."
      );
    }

    const key = await deriveKey(passphrase, new Uint8Array(salt));

    const decryptedContent = await window.crypto.subtle.decrypt(
      {
        name: "AES-GCM",
        iv: new Uint8Array(iv),
      },
      key,
      encryptedContent
    );

    const decryptedBlob = new Blob([decryptedContent], {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });
    return decryptedBlob;
  } catch (error) {
    console.error("Decryption error:", error);
    throw new Error(
      "Decryption failed. Please check your passphrase and ensure the file is not corrupted."
    );
  }
}
