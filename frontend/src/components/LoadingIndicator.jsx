import React from 'react'

/**
 * Indicateur de chargement
 */
export default function LoadingIndicator({ message = "Recherche en cours..." }) {
  return (
    <div className="flex justify-start mb-4">
      <div className="max-w-3xl rounded-lg px-4 py-3 bg-white border border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
            <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
            <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
          </div>
          <span className="text-gray-600 text-sm">{message}</span>
        </div>
      </div>
    </div>
  )
}
