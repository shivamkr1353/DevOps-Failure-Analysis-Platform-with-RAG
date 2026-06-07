import { useState } from "react"

function FailedRunsTable({ runs = [], onAnalyze, analyzingRunId = null }) {
  const PAGE_SIZE = 10
  const [currentPage, setCurrentPage] = useState(1)

  if (runs.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-white/[0.08] p-6 text-center">
        <p className="font-mono text-xs text-emerald-400 font-semibold">✓ No failed runs found</p>
        <p className="mt-1 font-mono text-[11px] text-gray-600">All recent workflow runs completed successfully.</p>
      </div>
    )
  }

  const totalPages = Math.ceil(runs.length / PAGE_SIZE)
  const startIdx = (currentPage - 1) * PAGE_SIZE
  const visibleRuns = runs.slice(startIdx, startIdx + PAGE_SIZE)

  return (
    <div>
      <div className="overflow-hidden rounded-lg border border-white/[0.08]">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-white/[0.08] bg-surface-raised">
                <th className="px-4 py-2.5 font-mono text-[10px] font-semibold text-gray-500 tracking-wider">RUN</th>
                <th className="px-4 py-2.5 font-mono text-[10px] font-semibold text-gray-500 tracking-wider">WORKFLOW</th>
                <th className="hidden px-4 py-2.5 font-mono text-[10px] font-semibold text-gray-500 tracking-wider md:table-cell">BRANCH</th>
                <th className="px-4 py-2.5 font-mono text-[10px] font-semibold text-gray-500 tracking-wider">STATUS</th>
                <th className="hidden px-4 py-2.5 font-mono text-[10px] font-semibold text-gray-500 tracking-wider lg:table-cell">CREATED</th>
                <th className="px-4 py-2.5 font-mono text-[10px] font-semibold text-gray-500 tracking-wider">ACTION</th>
              </tr>
            </thead>
            <tbody>
              {visibleRuns.map((run) => (
                <tr
                  key={run.id}
                  className="border-b border-white/[0.05] transition-colors hover:bg-white/[0.02]"
                >
                  <td className="px-4 py-3">
                    <span className="font-mono text-xs text-gray-400">#{run.run_number || run.id}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm text-gray-300">{run.workflow_name || run.name || "—"}</span>
                  </td>
                  <td className="hidden px-4 py-3 md:table-cell">
                    <span className="font-mono text-xs text-gray-500">
                      {run.head_branch || "—"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center gap-1.5 font-mono text-xs text-red-400">
                      <span className="h-1.5 w-1.5 rounded-full bg-red-400" />
                      {run.conclusion || "failure"}
                    </span>
                  </td>
                  <td className="hidden px-4 py-3 lg:table-cell">
                    <span className="font-mono text-[11px] text-gray-500">
                      {run.created_at ? new Date(run.created_at).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      }) : "—"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      type="button"
                      onClick={() => onAnalyze(run.id)}
                      disabled={analyzingRunId === run.id}
                      className="btn-primary py-1.5 px-3 text-xs"
                    >
                      {analyzingRunId === run.id ? "analyzing..." : "Analyze"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination controls */}
      {totalPages > 1 ? (
        <div className="mt-3 flex items-center justify-between">
          <p className="font-mono text-[11px] text-gray-500">
            Showing {startIdx + 1}–{Math.min(startIdx + PAGE_SIZE, runs.length)} of {runs.length} failed runs
          </p>
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="btn-ghost px-2.5 py-1.5 text-[11px] disabled:opacity-30 disabled:cursor-not-allowed"
            >
              ← Prev
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1)
              .filter((p) => {
                // Show first, last, current, and neighbors
                if (p === 1 || p === totalPages) return true
                if (Math.abs(p - currentPage) <= 1) return true
                return false
              })
              .reduce((acc, p, i, arr) => {
                // Insert ellipsis markers between gaps
                if (i > 0 && p - arr[i - 1] > 1) {
                  acc.push({ type: "ellipsis", key: `e${p}` })
                }
                acc.push({ type: "page", value: p, key: `p${p}` })
                return acc
              }, [])
              .map((item) =>
                item.type === "ellipsis" ? (
                  <span key={item.key} className="font-mono text-[11px] text-gray-600 px-1">…</span>
                ) : (
                  <button
                    key={item.key}
                    type="button"
                    onClick={() => setCurrentPage(item.value)}
                    className={`font-mono text-[11px] px-2.5 py-1.5 rounded-md transition-colors ${
                      currentPage === item.value
                        ? "bg-orange-500/20 text-orange-400 font-bold"
                        : "btn-ghost"
                    }`}
                  >
                    {item.value}
                  </button>
                )
              )}
            <button
              type="button"
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="btn-ghost px-2.5 py-1.5 text-[11px] disabled:opacity-30 disabled:cursor-not-allowed"
            >
              Next →
            </button>
          </div>
        </div>
      ) : null}
    </div>
  )
}

export default FailedRunsTable
