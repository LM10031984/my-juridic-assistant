import React, { useState } from 'react'

/**
 * Composant pour afficher et collecter les reponses aux questions de qualification
 */
export default function QualifyingQuestions({ data, onSubmit }) {
  const [answers, setAnswers] = useState({})

  const handleAnswer = (questionId, answer) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }))
  }

  const handleSubmit = () => {
    // Verifier que toutes les questions ont une reponse
    const allAnswered = data.questions.every(q => answers[q.id])

    if (allAnswered) {
      onSubmit(answers)
    }
  }

  const allAnswered = data.questions.every(q => answers[q.id])

  return (
    <div className="max-w-3xl rounded-lg px-6 py-4 bg-blue-50 border border-blue-200 mb-4">
      {/* Header */}
      <div className="flex items-start mb-4">
        <svg
          className="h-6 w-6 text-blue-600 mt-0.5 mr-3 flex-shrink-0"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-1">
            Quelques precisions necessaires
          </h3>
          <p className="text-sm text-gray-600">{data.message}</p>
          <p className="text-xs text-gray-500 mt-1">
            Domaine: <span className="font-medium">{data.domaine}</span>
          </p>
        </div>
      </div>

      {/* Questions */}
      <div className="space-y-4">
        {data.questions.map((question) => (
          <div key={question.id} className="bg-white rounded-lg p-4 border border-gray-200">
            <label className="block text-sm font-medium text-gray-900 mb-3">
              {question.id}. {question.question}
            </label>

            {question.type === 'yes_no' && (
              <div className="flex space-x-3">
                <button
                  type="button"
                  onClick={() => handleAnswer(question.id, 'Oui')}
                  className={`flex-1 px-4 py-2 rounded-lg border transition-colors ${
                    answers[question.id] === 'Oui'
                      ? 'bg-primary-600 text-white border-primary-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  Oui
                </button>
                <button
                  type="button"
                  onClick={() => handleAnswer(question.id, 'Non')}
                  className={`flex-1 px-4 py-2 rounded-lg border transition-colors ${
                    answers[question.id] === 'Non'
                      ? 'bg-primary-600 text-white border-primary-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  Non
                </button>
              </div>
            )}

            {question.type === 'multiple_choice' && (
              <div className="space-y-2">
                {question.choices.map((choice, index) => (
                  <button
                    key={index}
                    type="button"
                    onClick={() => handleAnswer(question.id, choice)}
                    className={`w-full text-left px-4 py-3 rounded-lg border transition-colors ${
                      answers[question.id] === choice
                        ? 'bg-primary-600 text-white border-primary-600'
                        : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center">
                      <div
                        className={`w-4 h-4 rounded-full border-2 mr-3 flex-shrink-0 ${
                          answers[question.id] === choice
                            ? 'border-white bg-white'
                            : 'border-gray-300'
                        }`}
                      >
                        {answers[question.id] === choice && (
                          <div className="w-full h-full rounded-full bg-primary-600"></div>
                        )}
                      </div>
                      <span>{choice}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Submit Button */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!allAnswered}
          className="w-full px-4 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {allAnswered
            ? 'Valider mes reponses'
            : `Repondez aux ${data.questions.length} questions pour continuer`}
        </button>
      </div>
    </div>
  )
}
