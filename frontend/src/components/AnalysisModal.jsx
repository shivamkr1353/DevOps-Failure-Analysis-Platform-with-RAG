import { useEffect, useRef } from "react"
import AnalysisPanel from "./AnalysisPanel"

function AnalysisModal({ isOpen, onClose, result, isLoading, error }) {
  const overlayRef = useRef(null)

  // Close on Escape key
  useEffect(() => {
    if (!isOpen) return
    const handler = (e) => {
      if (e.key === "Escape") onClose()
    }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [isOpen, onClose])

  // Prevent body scroll when open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden"
    } else {
      document.body.style.overflow = ""
    }
    return () => { document.body.style.overflow = "" }
  }, [isOpen])

  if (!isOpen) return null

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex justify-end"
      onClick={(e) => { if (e.target === overlayRef.current) onClose() }}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-backdrop-fade" />

      {/* Slide-over panel — flex column so header stays fixed, content scrolls */}
      <div className="relative flex h-full w-full max-w-2xl flex-col animate-slide-in-right bg-[#0d0d14] border-l border-white/[0.08] shadow-2xl">

        {/* Fixed header — never scrolls */}
        <div className="flex-shrink-0 flex items-center justify-between border-b border-white/[0.08] bg-[#0d0d14] px-5 py-3">
          <button
            type="button"
            onClick={onClose}
            className="inline-flex items-center gap-2 rounded-md border border-white/[0.1] bg-white/[0.04] px-3.5 py-2 font-mono text-xs font-medium text-gray-300 transition-all hover:bg-white/[0.08] hover:text-white hover:border-white/[0.2] active:scale-[0.97]"
          >
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Runs
          </button>
          <button
            type="button"
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-full bg-white/[0.06] text-gray-400 transition-colors hover:bg-red-500/20 hover:text-red-400"
            title="Close (Esc)"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Scrollable content area */}
        <div className="flex-1 overflow-y-auto p-5">
          <AnalysisPanel
            result={result}
            isLoading={isLoading}
            error={error}
            loadingMessage="Analyzing GitHub Actions failure"
          />
        </div>

      </div>
    </div>
  )
}

export default AnalysisModal
