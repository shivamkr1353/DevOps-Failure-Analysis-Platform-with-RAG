import { useState } from "react"

function ResultCard({ result, isLoading, error }) {
  const [copiedLabel, setCopiedLabel] = useState("")

  const sections = result
    ? [
        {
          key: "root_cause",
          title: "Root Cause",
          value: result.root_cause,
          accent: "border-rose-500/30 bg-rose-500/10 text-rose-100"
        },
        {
          key: "summary",
          title: "Summary",
          value: result.summary,
          accent: "border-sky-500/30 bg-sky-500/10 text-sky-100"
        },
        {
          key: "fix",
          title: "Fix Suggestion",
          value: result.fix,
          accent: "border-emerald-500/30 bg-emerald-500/10 text-emerald-100"
        }
      ]
    : []

  const copyText = async (label, text) => {
    await navigator.clipboard.writeText(text)
    setCopiedLabel(label)
    window.setTimeout(() => setCopiedLabel(""), 1600)
  }

  return (
    <section className="glass-panel min-h-[520px] p-6 lg:p-8">
      <div className="flex h-full flex-col gap-5">
        <div className="flex items-center justify-between">
          <span className="pill">Analysis Result</span>
          {result ? (
            <button
              type="button"
              onClick={() =>
                copyText(
                  "analysis",
                  `Root Cause:\n${result.root_cause}\n\nSummary:\n${result.summary}\n\nFix:\n${result.fix}`
                )
              }
              className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:bg-white/10"
            >
              {copiedLabel === "analysis" ? "Copied" : "Copy All"}
            </button>
          ) : null}
        </div>

        {isLoading ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-5 rounded-[1.75rem] border border-white/10 bg-white/5 p-8 text-center">
            <div className="flex gap-2">
              <span className="h-3 w-3 animate-bounce rounded-full bg-sky-400 [animation-delay:-0.2s]" />
              <span className="h-3 w-3 animate-bounce rounded-full bg-cyan-300 [animation-delay:-0.1s]" />
              <span className="h-3 w-3 animate-bounce rounded-full bg-rose-300" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Analyzing your pipeline failure</h2>
              <p className="mt-2 text-sm text-slate-400">
                The model is reviewing the cleaned logs and preparing a likely root cause.
              </p>
            </div>
          </div>
        ) : null}

        {!isLoading && error ? (
          <div className="rounded-[1.75rem] border border-rose-500/30 bg-rose-500/10 p-5">
            <h2 className="text-lg font-bold text-rose-100">Analysis failed</h2>
            <p className="mt-2 text-sm leading-6 text-rose-100/80">{error}</p>
          </div>
        ) : null}

        {!isLoading && !error && !result ? (
          <div className="flex flex-1 flex-col justify-between rounded-[1.75rem] border border-white/10 bg-white/5 p-6">
            <div>
              <h2 className="text-2xl font-bold text-white">Ready to inspect CI/CD failures</h2>
              <p className="mt-3 text-sm leading-6 text-slate-400">
                Paste logs on the left or load one of the built-in examples to see the complete flow.
              </p>
            </div>

            <div className="grid gap-4 pt-6">
              <div className="section-card">
                <p className="text-sm font-semibold uppercase tracking-[0.2em] text-rose-300">What you get</p>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  A likely root cause, a quick summary, and a concrete fix suggestion your team can act on.
                </p>
              </div>
              <div className="section-card">
                <p className="text-sm font-semibold uppercase tracking-[0.2em] text-sky-300">Good for</p>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  Build errors, missing packages, Docker issues, rollout failures, and timeout-heavy deployment logs.
                </p>
              </div>
            </div>
          </div>
        ) : null}

        {!isLoading && !error && result ? (
          <div className="grid gap-4">
            {sections.map((section) => (
              <article key={section.key} className={`rounded-[1.5rem] border p-5 ${section.accent}`}>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h2 className="text-lg font-bold">{section.title}</h2>
                    <p className="mt-3 text-sm leading-6 opacity-90">{section.value}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => copyText(section.key, section.value)}
                    className="rounded-full border border-white/20 bg-black/10 px-3 py-1.5 text-xs font-bold uppercase tracking-[0.15em] transition hover:bg-black/20"
                  >
                    {copiedLabel === section.key ? "Copied" : "Copy"}
                  </button>
                </div>
              </article>
            ))}
          </div>
        ) : null}
      </div>
    </section>
  )
}

export default ResultCard
