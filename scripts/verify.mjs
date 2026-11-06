import { access, lstat, readdir, readFile } from 'node:fs/promises'
import { constants } from 'node:fs'
import { dirname, extname, resolve } from 'node:path'
import { spawnSync } from 'node:child_process'
import assert from 'node:assert/strict'

const root = resolve(import.meta.dirname, '..')
const manifest = JSON.parse(await readFile(resolve(root, 'release.json'), 'utf8'))
assert.deepEqual(Object.keys(manifest).sort(), ['entries', 'kind'], 'invalid theme collection manifest')
assert.equal(manifest.kind, 'theme')
assert(Array.isArray(manifest.entries) && manifest.entries.length > 0, 'missing theme entries')
assert(manifest.entries.every(entry => typeof entry === 'string'), 'invalid theme entries')
assert.equal(new Set(manifest.entries).size, manifest.entries.length, 'duplicate theme entries')
const packageMetadata = JSON.parse(await readFile(resolve(root, 'package.json'), 'utf8'))
for (const entry of manifest.entries) {
  assert(/^themes\/(?:[a-zA-Z0-9_-]+\/)*[a-zA-Z0-9_.-]+\.css$/.test(entry), `invalid theme entry: ${entry}`)
  assert(packageMetadata.files.includes(`src/${entry}`), `entry is not deployed: ${entry}`)
  const path = resolve(root, 'src', entry)
  assert((await lstat(path)).isFile(), `entry must be regular CSS: ${entry}`)
  await access(path, constants.R_OK)
}

async function walk(path) {
  const info = await lstat(path)
  if (info.isSymbolicLink()) throw new Error(`symlink not allowed: ${path}`)
  if (!info.isDirectory()) return [path]

  const found = []
  for (const item of await readdir(path, { withFileTypes: true })) {
    found.push(...await walk(resolve(path, item.name)))
  }
  return found
}

// Scan only Unit-owned source and the metadata that supports this test. Git state,
// dependency installs, and build products are deliberately outside this boundary.
const ownedPaths = [
  resolve(root, 'src'),
  resolve(root, 'scripts'),
  resolve(root, 'package.json'),
  resolve(root, 'release.json'),
  resolve(root, '.github/workflows/release.yml'),
]
const files = (await Promise.all(ownedPaths.map(walk))).flat()
const importPattern = /(?:^|\n)\s*(?:import|export)\s+(?:[^"'`;]*?\sfrom\s+)?["']([^"']+)["']/g
const cssUrlPattern = /url\(\s*(["']?)(.*?)\1\s*\)/gi
const allowedHostRoots = ['/core/', '/util/', '/widgets/']

for (const file of files) {
  if (['.js', '.mjs'].includes(extname(file))) {
    const checked = spawnSync(process.execPath, ['--check', file], { encoding: 'utf8' })
    assert.equal(checked.status, 0, checked.stderr || checked.stdout)
    const source = await readFile(file, 'utf8')
    for (const match of source.matchAll(importPattern)) {
      const specifier = match[1]
      if (specifier.startsWith('.')) {
        const local = resolve(dirname(file), specifier)
        assert(local.startsWith(root + '/'), `local import escapes repository: ${specifier}`)
        await access(local, constants.R_OK)
      } else if (specifier.startsWith('/')) {
        assert(allowedHostRoots.some(prefix => specifier.startsWith(prefix)),
          `undocumented absolute import: ${specifier}`)
      } else {
        assert(specifier.startsWith('node:'), `undeclared package import: ${specifier}`)
      }
    }
  }
  if (extname(file) === '.css') {
    const source = await readFile(file, 'utf8')
    for (const match of source.matchAll(cssUrlPattern)) {
      const reference = match[2]
      if (!reference || /^(?:data:|https?:|#)/i.test(reference)) continue
      const asset = resolve(dirname(file), reference)
      assert(asset.startsWith(root + '/'), `CSS asset escapes repository: ${reference}`)
      await access(asset, constants.R_OK)
    }
  }
}

console.log(`verified ${files.filter(file => ['.js', '.mjs', '.css'].includes(extname(file))).length} source files`)
