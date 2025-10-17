'use client'

import { useState } from 'react'

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return

    setLoading(true)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('model_id', 'qwen2-vl-32b')
    formData.append('prompt', 'OCR this image and extract all text.')

    try {
      const res = await fetch('http://localhost:8081/api/ocr', {
        method: 'POST',
        body: formData,
      })
      const data = await res.json()
      setResult(data)
    } catch (error) {
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: '40px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1>📄 OCR Web Interface</h1>
      <p>Advanced optical character recognition with multiple AI models</p>

      <form onSubmit={handleSubmit} style={{ marginTop: '30px' }}>
        <input
          type="file"
          accept="image/*,.pdf"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          style={{ display: 'block', marginBottom: '20px' }}
        />
        <button type="submit" disabled={!file || loading}>
          {loading ? 'Processing...' : 'Process OCR'}
        </button>
      </form>

      {result && (
        <div style={{ marginTop: '30px', background: '#f5f5f5', padding: '20px', borderRadius: '8px' }}>
          <h2>Results:</h2>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}
