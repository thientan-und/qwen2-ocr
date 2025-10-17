export const metadata = {
  title: 'OCR Web Interface',
  description: 'Advanced optical character recognition with multiple AI models',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
