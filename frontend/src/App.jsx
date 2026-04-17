import { useState } from "react"
import LogInput from "./components/LogInput"
import ResultCard from "./components/ResultCard"
import { sampleLogs } from "./data/sampleLogs"

const API_BASE_URL = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "")
const ANALYZE_ENDPOINT = API_BASE_URL ? `${API_BASE_URL}/analyze` : "/analyze"

function App() {
  const [logs, setLogs] = useState(sampleLogs[0].logs)
  const [result, setResult] = useState(null)
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const analyzeLogs = async () => {
    if (!logs.trim()) {
      setError("Paste CI/CD logs before running an analysis.")
      setResult(null)
      return
    }

    setIsLoading(true)
    setError("")

    try {
      const response = await fetch(ANALYZE_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ logs })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "The backend could not analyze these logs.")
      }

      setResult(data)
    } catch (requestError) {
      setResult(null)
      setError(requestError.message || "Something went wrong while calling the API.")
    } finally {
      setIsLoading(false)
    }
  }

  const loadExample = (exampleLogs) => {
    setLogs(exampleLogs)
    setResult(null)
    setError("")
  }

  return (
    <main className="min-h-screen px-4 py-10 text-slate-100">
      <div className="mx-auto max-w-7xl">
        <header className="mb-8 text-center">
          <span className="pill">FastAPI + React + OpenAI</span>
          <h1 className="mx-auto mt-4 max-w-4xl text-4xl font-extrabold tracking-tight text-white md:text-6xl">
            Turn noisy DevOps logs into clear failure analysis
          </h1>
          <p className="mx-auto mt-4 max-w-3xl text-base leading-7 text-slate-300 md:text-lg">
            Paste failing CI/CD output, run one analysis request, and get a readable diagnosis with a likely root
            cause, concise summary, and next-step fix suggestion.
          </p>
        </header>

        <div className="grid gap-6 xl:grid-cols-[1.2fr_0.9fr]">
          <LogInput
            logs={logs}
            onLogsChange={setLogs}
            onAnalyze={analyzeLogs}
            isLoading={isLoading}
            examples={sampleLogs}
            onLoadExample={loadExample}
          />
          <ResultCard result={result} isLoading={isLoading} error={error} />
        </div>
      </div>
    </main>
  )
}

export default App
