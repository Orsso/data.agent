import type { Metadata } from 'next'
import localFont from 'next/font/local'

import 'streamdown/styles.css'
import './globals.css'

const everett = localFont({
  src: [
    { path: './fonts/TWKEverett-Light.ttf', weight: '300', style: 'normal' },
    { path: './fonts/TWKEverett-LightItalic.ttf', weight: '300', style: 'italic' },
    { path: './fonts/TWKEverett-Regular.ttf', weight: '400', style: 'normal' },
    { path: './fonts/TWKEverett-RegularItalic.ttf', weight: '400', style: 'italic' },
    { path: './fonts/TWKEverett-Medium.ttf', weight: '500', style: 'normal' },
    { path: './fonts/TWKEverett-Bold.ttf', weight: '700', style: 'normal' },
  ],
  variable: '--font-everett',
})
const geistMono = localFont({
  src: './fonts/GeistMonoVF.woff',
  variable: '--font-geist-mono',
  weight: '100 900',
})

export const metadata: Metadata = {
  title: 'data.agent',
  description: 'Natural language data analysis',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={`${everett.variable} ${geistMono.variable} antialiased`}>
        {children}
      </body>
    </html>
  )
}
