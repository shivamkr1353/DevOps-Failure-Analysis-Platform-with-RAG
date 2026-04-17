function LogInput({ logs, onLogsChange, onAnalyze, isLoading, examples, onLoadExample }) {
  return (
    <section className="glass-panel p-6 lg:p-8">
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-3">
          <span className="pill">Input Logs</span>
          <div className="flex flex-wrap gap-3">
            {examples.map((example) => (
              <button
                key={example.id}
                type="button"
                onClick={() => onLoadExample(example.logs)}
                className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:border-rose-400/40 hover:bg-rose-500/10"
              >
                {example.title}
              </button>
            ))}
          </div>
        </div>

        <textarea
          value={logs}
          onChange={(event) => onLogsChange(event.target.value)}
          placeholder="Paste CI/CD logs here..."
          className="min-h-[320px] w-full rounded-[1.5rem] border border-rose-500/20 bg-slate-950/80 px-4 py-4 font-mono text-sm leading-6 text-slate-100 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-400/20"
        />

        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <p className="max-w-xl text-sm text-slate-400">
            The backend keeps high-signal lines like <span className="font-semibold text-rose-300">ERROR</span> and
            <span className="font-semibold text-rose-300"> FAILED</span>, removes common CI noise, and then sends the
            cleaned context to the LLM.
          </p>

          <button
            type="button"
            onClick={onAnalyze}
            disabled={isLoading}
            className="inline-flex items-center justify-center rounded-full bg-gradient-to-r from-sky-500 to-cyan-400 px-6 py-3 text-sm font-bold text-slate-950 shadow-lg shadow-sky-900/20 transition hover:scale-[1.01] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isLoading ? "Analyzing..." : "Analyze Logs"}
          </button>
        </div>
      </div>
    </section>
  )
}

export default LogInput

