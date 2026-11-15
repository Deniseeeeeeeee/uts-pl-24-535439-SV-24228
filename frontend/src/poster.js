// API tidak menyimpan gambar poster, jadi poster dibuat dari gradien warna.
// Warna dihitung dari judul film, sehingga film yang sama selalu punya warna yang sama.

function hash(text) {
  let h = 0
  for (const ch of String(text || '')) {
    h = (h * 31 + ch.charCodeAt(0)) >>> 0
  }
  return h
}

export function posterStyle(title) {
  const h = hash(title)
  const hue1 = h % 360
  const hue2 = (hue1 + 40 + (h % 80)) % 360
  const angle = 120 + (h % 120)
  return {
    background: `linear-gradient(${angle}deg, hsl(${hue1} 70% 38%), hsl(${hue2} 75% 18%))`,
  }
}

export function initials(title) {
  return String(title || '?')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('')
}
