import { useRef, useState } from 'react'

const styles = {
  zone: {
    border: '2.5px dashed #ccc',
    borderRadius: 12,
    padding: '48px 32px',
    textAlign: 'center',
    cursor: 'pointer',
    transition: 'all 0.2s',
    background: '#fff',
    position: 'relative',
  },
  zoneActive: {
    borderColor: 'var(--orange)',
    background: 'var(--orange-light)',
  },
  preview: {
    width: '100%',
    maxHeight: 340,
    objectFit: 'contain',
    borderRadius: 8,
    marginBottom: 16,
    border: '1px solid var(--border)',
  },
  icon: {
    fontSize: 48,
    marginBottom: 12,
    display: 'block',
  },
  label: {
    fontSize: 18,
    fontWeight: 600,
    color: 'var(--dark)',
    marginBottom: 6,
  },
  sub: {
    fontSize: 13,
    color: 'var(--muted)',
    marginBottom: 20,
  },
  btn: {
    display: 'inline-block',
    background: 'var(--orange)',
    color: '#fff',
    border: 'none',
    borderRadius: 6,
    padding: '10px 22px',
    fontSize: 14,
    fontWeight: 600,
    letterSpacing: '0.3px',
  },
  changeBtn: {
    background: 'none',
    border: '1.5px solid var(--border)',
    borderRadius: 6,
    padding: '8px 18px',
    fontSize: 13,
    color: 'var(--mid)',
    fontWeight: 500,
  },
}

export default function ImageUploader({ onImageSelected }) {
  const [dragging, setDragging] = useState(false)
  const [preview, setPreview] = useState(null)
  const [fileName, setFileName] = useState('')
  const inputRef = useRef()

  const handleFile = (file) => {
    if (!file) return
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file (JPEG or PNG)')
      return
    }
    const url = URL.createObjectURL(file)
    setPreview(url)
    setFileName(file.name)
    onImageSelected(file)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    handleFile(file)
  }

  const handleInputChange = (e) => {
    handleFile(e.target.files[0])
  }

  return (
    <div
      style={{ ...styles.zone, ...(dragging ? styles.zoneActive : {}) }}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => !preview && inputRef.current.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        style={{ display: 'none' }}
        onChange={handleInputChange}
      />

      {preview ? (
        <>
          <img src={preview} alt="Scorecard preview" style={styles.preview} />
          <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
            <button
              style={styles.changeBtn}
              onClick={(e) => { e.stopPropagation(); inputRef.current.click() }}
            >
              Change image
            </button>
          </div>
          {fileName && (
            <p style={{ ...styles.sub, marginTop: 10, marginBottom: 0 }}>{fileName}</p>
          )}
        </>
      ) : (
        <>
          <span style={styles.icon}>🥏</span>
          <p style={styles.label}>Drop your UDisc scorecard here</p>
          <p style={styles.sub}>JPEG or PNG — screenshot directly from UDisc app</p>
          <button style={styles.btn} onClick={(e) => { e.stopPropagation(); inputRef.current.click() }}>
            Browse files
          </button>
        </>
      )}
    </div>
  )
}
