import type {Metadata} from 'next';
import './globals.css';
import {Toaster} from '@/components/ui/toaster';
import {Navbar} from '@/components/navbar';

export const metadata: Metadata = {
  title: 'File Converter',
  description: 'Decrypt files.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="true" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="font-body antialiased">
        <Navbar />
        <main className="flex min-h-[calc(100vh-4rem)] w-full flex-col items-center justify-center bg-background p-4">
          {children}
        </main>
        <Toaster />
      </body>
    </html>
  );
}
