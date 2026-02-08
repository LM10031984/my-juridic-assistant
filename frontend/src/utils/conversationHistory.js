/**
 * Utilitaires pour gerer l'historique de conversation
 */

const STORAGE_KEY = 'juridic_assistant_history'

/**
 * Sauvegarder l'historique dans localStorage
 */
export function saveHistory(messages) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages))
  } catch (error) {
    console.error('Erreur lors de la sauvegarde de l\'historique:', error)
  }
}

/**
 * Charger l'historique depuis localStorage
 */
export function loadHistory() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : []
  } catch (error) {
    console.error('Erreur lors du chargement de l\'historique:', error)
    return []
  }
}

/**
 * Effacer l'historique
 */
export function clearHistory() {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch (error) {
    console.error('Erreur lors de l\'effacement de l\'historique:', error)
  }
}

/**
 * Ajouter un message a l'historique
 */
export function addMessage(messages, role, content, metadata = {}) {
  const newMessage = {
    id: Date.now() + Math.random(),
    role, // 'user' ou 'assistant'
    content,
    timestamp: new Date().toISOString(),
    ...metadata
  }

  const updatedMessages = [...messages, newMessage]
  saveHistory(updatedMessages)

  return updatedMessages
}
