import { useState, useEffect } from 'react'
import { listCollections, createCollection as apiCreateCollection } from '../api/client'

export function useCollections() {
  const [collections, setCollections] = useState([])
  const [selectedCollection, setSelectedCollection] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  const loadCollections = async () => {
    setIsLoading(true)
    try {
      const data = await listCollections()
      setCollections(data)
      if (data.length > 0 && !selectedCollection) {
        setSelectedCollection(data[0])
      }
    } catch (error) {
      console.error('Failed to load collections:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const createCollection = async (name, visibility = 'private') => {
    try {
      const newCollection = await apiCreateCollection(name, visibility)
      setCollections((prev) => [...prev, newCollection])
      setSelectedCollection(newCollection)
      return newCollection
    } catch (error) {
      console.error('Failed to create collection:', error)
      throw error
    }
  }

  useEffect(() => {
    loadCollections()
  }, [])

  return {
    collections,
    selectedCollection,
    setSelectedCollection,
    createCollection,
    loadCollections,
    isLoading,
  }
}

