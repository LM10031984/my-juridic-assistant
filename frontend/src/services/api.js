/**
 * API Service pour communiquer avec le backend
 */

// Use environment variable for API URL, fallback to /api for local dev
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

/**
 * Poser une question juridique
 * @param {string} question - Question de l'utilisateur
 * @param {object} options - Options (domaine, enable_prequestioning, user_answers)
 * @returns {Promise<object>} Reponse de l'API
 */
export async function askQuestion(question, options = {}) {
  const {
    domaine = null,
    enable_prequestioning = true,
    user_answers = null
  } = options

  const response = await fetch(`${API_BASE_URL}/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question,
      domaine,
      enable_prequestioning,
      user_answers
    })
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Erreur inconnue' }))
    throw new Error(error.detail || 'Erreur lors de la requete')
  }

  return response.json()
}

/**
 * Recuperer la liste des domaines juridiques
 * @returns {Promise<object>} Liste des domaines
 */
export async function getDomains() {
  const response = await fetch(`${API_BASE_URL}/domains`)

  if (!response.ok) {
    throw new Error('Erreur lors de la recuperation des domaines')
  }

  return response.json()
}

/**
 * Verifier le health de l'API
 * @returns {Promise<object>} Status de l'API
 */
export async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/health`)

  if (!response.ok) {
    throw new Error('API non disponible')
  }

  return response.json()
}
