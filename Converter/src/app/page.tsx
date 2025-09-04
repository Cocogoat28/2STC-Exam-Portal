"use client";

import React, { useState } from "react";
import * as XLSX from "xlsx";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Download, Trash2 } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const SALT_SIZE = 16;
const IV_SIZE = 12;
const TAG_SIZE = 16;
const PBKDF2_ITERATIONS = 100000;
const KEY_LENGTH = 256;

export default function ConverterLoaderPage(): JSX.Element {
  const [file, setFile] = useState<File | null>(null);
  const [passphrase, setPassphrase] = useState("");
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<any[][] | null>(null);
  const [decryptedBlob, setDecryptedBlob] = useState<Blob | null>(null);
  const { toast } = useToast();

  async function deriveKey(passphrase: string, salt: Uint8Array): Promise<CryptoKey> {
    const passBuf = new TextEncoder().encode(passphrase);
    const baseKey = await window.crypto.subtle.importKey(
      "raw",
      passBuf,
      { name: "PBKDF2" },
      false,
      ["deriveKey"]
    );

    return window.crypto.subtle.deriveKey(
      {
        name: "PBKDF2",
        salt,
        iterations: PBKDF2_ITERATIONS,
        hash: "SHA-256",
      },
      baseKey,
      { name: "AES-GCM", length: KEY_LENGTH },
      false,
      ["decrypt"]
    );
  }

  async function decryptDatFile(buffer: ArrayBuffer, passphrase: string): Promise<Blob> {
    const u8 = new Uint8Array(buffer);
    if (u8.length < SALT_SIZE + IV_SIZE + TAG_SIZE + 1) {
      throw new Error("File too small to contain salt + iv + ciphertext + tag");
    }

    const salt = u8.slice(0, SALT_SIZE);
    const iv = u8.slice(SALT_SIZE, SALT_SIZE + IV_SIZE);
    const ciphertext = u8.slice(SALT_SIZE + IV_SIZE, u8.length - TAG_SIZE);
    const tag = u8.slice(u8.length - TAG_SIZE);

    const key = await deriveKey(passphrase, salt);

    const ctWithTag = new Uint8Array(ciphertext.length + tag.length);
    ctWithTag.set(ciphertext, 0);
    ctWithTag.set(tag, ciphertext.length);

    const decryptedBuffer = await window.crypto.subtle.decrypt(
      { name: "AES-GCM", iv },
      key,
      ctWithTag
    );

    return new Blob([decryptedBuffer], {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });
  }

  async function handleLoad() {
    setPreview(null);
    setDecryptedBlob(null);

    if (!file) {
      toast({ variant: "destructive", title: "Please select a file to load." });
      return;
    }

    if (!passphrase) {
      toast({ variant: "destructive", title: "Please provide a passphrase." });
      return;
    }

    setLoading(true);
    try {
      const buffer = await file.arrayBuffer();
      const decrypted = await decryptDatFile(buffer, passphrase);
      setDecryptedBlob(decrypted);

      const arrayBuffer = await decrypted.arrayBuffer();
      const workbook = XLSX.read(arrayBuffer, { type: "array" });
      const firstSheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[firstSheetName];
      const jsonData: any[][] = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
      
      setPreview(jsonData.slice(0, 10)); // preview first 10 rows
      
      toast({
        title: "Success!",
        description: "File decrypted and preview is available.",
      });

    } catch (err: any) {
      console.error(err);
      toast({
        variant: "destructive",
        title: "Decryption Failed",
        description: err.message || String(err),
      });
    } finally {
      setLoading(false);
    }
  }

  function downloadFile() {
    if (!decryptedBlob) return;
    const a = document.createElement("a");
    a.href = URL.createObjectURL(decryptedBlob);
    a.download = file?.name?.replace(/\.dat$/i, ".xlsx") || "decrypted.xlsx";
    document.body.appendChild(a);
a.click();
document.body.removeChild(a);
    URL.revokeObjectURL(a.href);
  }
  
  function resetAll() {
    setFile(null);
    setPassphrase("");
    setPreview(null);
    setDecryptedBlob(null);
  }

  return (
    <Card className="w-full max-w-4xl">
      <CardHeader>
        <CardTitle>File Converter</CardTitle>
        <CardDescription>
          Select an encrypted <code>.dat</code> file, provide the passphrase, and decrypt it to an Excel file.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
            <div className="space-y-2">
                <Label htmlFor="file-upload">Encrypted File (.dat)</Label>
                <Input
                    id="file-upload"
                    type="file"
                    onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
                    accept=".dat"
                    className="max-w-md"
                />
            </div>

            <div className="space-y-2">
                <Label htmlFor="passphrase">Passphrase / Key</Label>
                <Input
                    id="passphrase"
                    type="password"
                    value={passphrase}
                    onChange={(e) => setPassphrase(e.target.value)}
                    placeholder="Enter passphrase for the file"
                    className="max-w-md"
                />
            </div>

            <div className="flex items-center gap-2">
                <Button onClick={handleLoad} disabled={loading || !file || !passphrase}>
                    {loading ? <Loader2 className="animate-spin mr-2" /> : null}
                    {loading ? "Decrypting..." : "Load & Decrypt"}
                </Button>
                {decryptedBlob && (
                  <>
                    <Button variant="outline" onClick={downloadFile}>
                        <Download className="mr-2" />
                        Download XLSX
                    </Button>
                    <Button variant="ghost" size="icon" onClick={resetAll} title="Reset form">
                        <Trash2 className="h-4 w-4" />
                    </Button>
                  </>
                )}
            </div>
        </div>

        {preview && (
            <div className="mt-6">
                <h3 className="text-lg font-semibold mb-2">Decrypted File Preview (First 10 Rows)</h3>
                <div className="overflow-x-auto border rounded-md">
                    <Table>
                        <TableHeader>
                           {preview[0] && (
                             <TableRow>
                               {preview[0].map((cell: any, j: number) => (
                                 <TableHead key={j}>{String(cell)}</TableHead>
                               ))}
                             </TableRow>
                           )}
                        </TableHeader>
                        <TableBody>
                        {preview.slice(1).map((row, i) => (
                            <TableRow key={i}>
                            {row.map((cell: any, j: number) => (
                                <TableCell key={j}>
                                {String(cell)}
                                </TableCell>
                            ))}
                            </TableRow>
                        ))}
                        </TableBody>
                    </Table>
                </div>
            </div>
        )}
      </CardContent>
    </Card>
  );
}
