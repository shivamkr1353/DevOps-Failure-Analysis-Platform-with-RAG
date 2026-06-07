import { useState } from "react"
import RepoSelector from "./RepoSelector"
import WorkflowStats from "./WorkflowStats"
import FailedRunsTable from "./FailedRunsTable"
import AnalysisModal from "./AnalysisModal"
import ErrorState from "./ErrorState"
import { fetchFailedRuns, analyzeRun } from "../api"

function GitHubAnalysis() {
  const [owner, setOwner] = useState("")
  const [repo, setRepo] = useState("")
  const [runsData, setRunsData] = useState(null)
  const [fetchError, setFetchError] = useState("")
  const [isFetching, setIsFetching] = useState(false)

  const [analysisResult, setAnalysisResult] = useState(null)
  const [analysisError, setAnalysisError] = useState("")
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analyzingRunId, setAnalyzingRunId] = useState(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  const handleFetchRuns = async () => {
    if (!owner.trim() || !repo.trim()) return

    setIsFetching(true)
    setFetchError("")
    setRunsData(null)
    setAnalysisResult(null)
    setAnalysisError("")

    try {
      const data = await fetchFailedRuns(owner.trim(), repo.trim())
      setRunsData(data)
    } catch (err) {
      setFetchError(err.message || "Failed to fetch workflow runs.")
    } finally {
      setIsFetching(false)
    }
  }

  const handleAnalyzeRun = async (runId) => {
    setIsAnalyzing(true)
    setAnalyzingRunId(runId)
    setAnalysisResult(null)
    setAnalysisError("")
    setIsModalOpen(true)

    try {
      const result = await analyzeRun(owner.trim(), repo.trim(), runId)
      setAnalysisResult(result)
    } catch (err) {
      setAnalysisError(err.message || "Failed to analyze workflow run.")
    } finally {
      setIsAnalyzing(false)
      setAnalyzingRunId(null)
    }
  }

  const handleCloseModal = () => {
    if (!isAnalyzing) {
      setIsModalOpen(false)
    }
  }

  return (
    <div className="grid gap-4">
      <RepoSelector
        owner={owner}
        repo={repo}
        onOwnerChange={setOwner}
        onRepoChange={setRepo}
        onFetch={handleFetchRuns}
        isLoading={isFetching}
      />

      {fetchError ? (
        <ErrorState message={fetchError} onRetry={handleFetchRuns} />
      ) : null}

      {runsData ? (
        <div className="grid gap-4">
          <WorkflowStats
            totalRuns={runsData.total_runs}
            failedRuns={runsData.failed_runs}
            successRate={runsData.success_rate}
          />

          <div className="panel p-5">
            <div className="mb-4 flex items-center justify-between">
              <span className="tag">FAILED RUNS</span>
              <span className="font-mono text-[11px] text-gray-500">
                {runsData.runs.length} run{runsData.runs.length !== 1 ? "s" : ""}
              </span>
            </div>
            <FailedRunsTable
              runs={runsData.runs}
              onAnalyze={handleAnalyzeRun}
              analyzingRunId={analyzingRunId}
            />
          </div>
        </div>
      ) : null}

      <AnalysisModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        result={analysisResult}
        isLoading={isAnalyzing}
        error={analysisError}
      />
    </div>
  )
}

export default GitHubAnalysis
