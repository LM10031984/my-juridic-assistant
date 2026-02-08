import React from 'react'

/**
 * Composant pour afficher un message dans le chat
 */
export default function ChatMessage({ message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-3xl rounded-lg px-4 py-3 ${
          isUser
            ? 'bg-primary-600 text-white'
            : 'bg-white border border-gray-200 text-gray-900'
        }`}
      >
        {/* Message content */}
        <div className="whitespace-pre-wrap">{message.content}</div>

        {/* Sources (pour les reponses de l'assistant) */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="text-sm font-semibold text-gray-700 mb-2">
              Sources juridiques :
            </div>
            <ul className="text-sm text-gray-600 space-y-1">
              {message.sources.map((source, index) => (
                <li key={index} className="flex items-start">
                  <svg
                    className="h-4 w-4 text-primary-500 mt-0.5 mr-2 flex-shrink-0"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span>{source}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Disclaimer (pour les reponses de l'assistant) */}
        {!isUser && message.disclaimer && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-xs text-gray-500 italic">{message.disclaimer}</p>
          </div>
        )}

        {/* Timestamp */}
        {message.timestamp && (
          <div className="mt-2 text-xs opacity-70">
            {new Date(message.timestamp).toLocaleTimeString('fr-FR', {
              hour: '2-digit',
              minute: '2-digit'
            })}
          </div>
        )}
      </div>
    </div>
  )
}
