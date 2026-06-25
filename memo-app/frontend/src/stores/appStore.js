import { ref } from 'vue'
import { getTags, getBooks } from '../api/index.js'

// Shared reactive caches — fetched once, shared across components
const tags = ref([])
const books = ref([])
let loaded = false

export function useAppStore() {
  async function load() {
    if (loaded) return
    try {
      const [tagRes, bookRes] = await Promise.all([getTags(), getBooks()])
      tags.value = tagRes.data
      books.value = bookRes.data
      loaded = true
    } catch (e) {
      console.error('Failed to load app store', e)
    }
  }

  function invalidate() {
    loaded = false
  }

  return { tags, books, load, invalidate }
}
