"use client";

import Link from 'next/link';
import { BookOpenCheck } from 'lucide-react';

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center">
        <nav className="flex items-center space-x-4 lg:space-x-6">
            <Link href="/" className="mr-6 flex items-center space-x-2">
                <BookOpenCheck className="h-6 w-6" />
                <span className="font-bold sm:inline-block">File Converter</span>
            </Link>
        </nav>
      </div>
    </header>
  );
}
