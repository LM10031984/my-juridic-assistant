import { useState, useEffect, useRef } from 'react'
import ChatMessage from './components/ChatMessage'
import ChatInput from './components/ChatInput'
import LoadingIndicator from './components/LoadingIndicator'
import QualifyingQuestions from './components/QualifyingQuestions'
import { askQuestion } from './services/api'
import { loadHistory, addMessage, clearHistory } from './utils/conversationHistory'

function App() {
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [qualifyingData, setQualifyingData] = useState(null)
  const [currentQuestion, setCurrentQuestion] = useState('')
  const [error, setError] = useState(null)
  const messagesEndRef = useRef(null)

  // Charger l'historique au montage
  useEffect(() => {
    const history = loadHistory()
    setMessages(history)
  }, [])

  // Auto-scroll vers le bas
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading, qualifyingData])

  // Gerer l'envoi d'une question
  const handleSendQuestion = async (question) => {
    setError(null)
    setCurrentQuestion(question)

    // Ajouter la question a l'historique
    const updatedMessages = addMessage(messages, 'user', question)
    setMessages(updatedMessages)

    // Appeler l'API
    setIsLoading(true)

    try {
      const response = await askQuestion(question, {
        enable_prequestioning: true
      })

      setIsLoading(false)

      // Si pre-questionnement necessaire
      if (response.needs_qualification) {
        setQualifyingData(response)
      } else {
        // Ajouter la reponse a l'historique
        const assistantMessages = addMessage(
          updatedMessages,
          'assistant',
          response.answer,
          {
            sources: response.sources || [],
            disclaimer: response.disclaimer
          }
        )
        setMessages(assistantMessages)
        setCurrentQuestion('')
      }
    } catch (err) {
      setIsLoading(false)
      setError(err.message)

      // Ajouter un message d'erreur
      const errorMessages = addMessage(
        updatedMessages,
        'assistant',
        `Desole, une erreur est survenue: ${err.message}. Verifiez que le serveur backend est bien demarre.`
      )
      setMessages(errorMessages)
    }
  }

  // Gerer la soumission des reponses de qualification
  const handleQualifyingAnswers = async (answers) => {
    setQualifyingData(null)
    setIsLoading(true)

    try {
      const response = await askQuestion(currentQuestion, {
        enable_prequestioning: true,
        user_answers: answers
      })

      setIsLoading(false)

      // Ajouter la reponse a l'historique
      const updatedMessages = addMessage(
        messages,
        'assistant',
        response.answer,
        {
          sources: response.sources || [],
          disclaimer: response.disclaimer
        }
      )
      setMessages(updatedMessages)
      setCurrentQuestion('')
    } catch (err) {
      setIsLoading(false)
      setError(err.message)

      const errorMessages = addMessage(
        messages,
        'assistant',
        `Desole, une erreur est survenue: ${err.message}`
      )
      setMessages(errorMessages)
    }
  }

  // Effacer l'historique
  const handleClearHistory = () => {
    if (confirm('Voulez-vous vraiment effacer tout l\'historique ?')) {
      clearHistory()
      setMessages([])
      setQualifyingData(null)
      setCurrentQuestion('')
      setError(null)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 flex-shrink-0">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <svg
                className="h-8 w-8 text-primary-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3"
                />
              </svg>
              <h1 className="ml-3 text-2xl font-bold text-gray-900">
                My Juridic Assistant
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="hidden sm:block text-sm text-gray-500">
                Conseil juridique immobilier
              </div>
              {messages.length > 0 && (
                <button
                  onClick={handleClearHistory}
                  className="text-sm text-gray-600 hover:text-gray-900 flex items-center"
                >
                  <svg
                    className="h-4 w-4 mr-1"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                  Effacer
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto px-4 py-6">
          <div className="max-w-4xl mx-auto">
            {/* Welcome Message */}
            {messages.length === 0 && !isLoading && (
              <div className="text-center py-12">
                <svg
                  className="mx-auto h-16 w-16 text-gray-400 mb-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                  />
                </svg>
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                  Bienvenue sur My Juridic Assistant
                </h2>
                <p className="text-gray-600 mb-6">
                  Posez vos questions juridiques en immobilier français
                </p>
                <div className="max-w-2xl mx-auto">
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h3 className="text-sm font-semibold text-gray-900 mb-3">
                      Exemples de questions :
                    </h3>
                    <ul className="text-sm text-gray-600 space-y-2 text-left">
                      <li className="flex items-start">
                        <svg
                          className="h-5 w-5 text-primary-500 mr-2 flex-shrink-0"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                        Quelles sont les charges récupérables en location ?
                      </li>
                      <li className="flex items-start">
                        <svg
                          className="h-5 w-5 text-primary-500 mr-2 flex-shrink-0"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                        Mon propriétaire peut-il augmenter le loyer ?
                      </li>
                      <li className="flex items-start">
                        <svg
                          className="h-5 w-5 text-primary-500 mr-2 flex-shrink-0"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                        Qui paie les travaux de toiture en copropriété ?
                      </li>
                      <li className="flex items-start">
                        <svg
                          className="h-5 w-5 text-primary-500 mr-2 flex-shrink-0"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                        Quels diagnostics sont obligatoires pour une vente ?
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Messages */}
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}

            {/* Loading Indicator */}
            {isLoading && <LoadingIndicator />}

            {/* Qualifying Questions */}
            {qualifyingData && (
              <QualifyingQuestions
                data={qualifyingData}
                onSubmit={handleQualifyingAnswers}
              />
            )}

            {/* Error Message */}
            {error && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-start">
                  <svg
                    className="h-5 w-5 text-red-600 mr-2 flex-shrink-0 mt-0.5"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <div className="text-sm text-red-800">{error}</div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Chat Input */}
        <div className="flex-shrink-0 max-w-4xl mx-auto w-full">
          <ChatInput
            onSend={handleSendQuestion}
            disabled={isLoading || qualifyingData !== null}
            placeholder={
              qualifyingData
                ? "Repondez aux questions ci-dessus pour continuer..."
                : "Posez votre question juridique..."
            }
          />
        </div>
      </main>
    </div>
  )
}

export default App
