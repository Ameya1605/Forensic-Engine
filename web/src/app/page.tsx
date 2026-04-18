'use client'

import { useState } from 'react'
import styles from './page.module.css'
import ForensicRadar from '@/components/ForensicRadar'
import ImageDropZone from '@/components/ImageDropZone'
import ImageForensicReport from '@/components/ImageForensicReport'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Loader2, FileText, Clipboard, Activity, Shield, Cpu, AlertTriangle, ImageIcon } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type AnalysisMode = 'text' | 'image'

export default function Home() {
  const [mode, setMode] = useState<AnalysisMode>('text')
  const [inputText, setInputText] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [results, setResults] = useState<any>(null)
  const [imageResults, setImageResults] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    if (results?.reconstructed_prompt) {
      navigator.clipboard.writeText(results.reconstructed_prompt)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleModeSwitch = (newMode: AnalysisMode) => {
    if (isAnalyzing) return
    setMode(newMode)
    setError(null)
    // Don't clear results so user can switch back and see them
  }

  const handleAnalyze = async () => {
    if (!inputText.trim()) return
    setIsAnalyzing(true)
    setResults(null)
    setError(null)
    
    try {
      const response = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: inputText }),
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || `Analysis failed (${response.status})`)
      }
      
      const data = await response.json()
      setResults(data)
    } catch (err: any) {
      console.error('Forensic Analysis failed:', err)
      const message = err.message?.includes('fetch')
        ? 'Cannot connect to the Forensic Backend. Ensure it is running on port 8000.'
        : err.message || 'Analysis failed unexpectedly.'
      setError(message)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleImageAnalyze = async (file: File) => {
    setIsAnalyzing(true)
    setImageResults(null)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${API_URL}/analyze/image`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || `Image analysis failed (${response.status})`)
      }

      const data = await response.json()
      setImageResults(data)
    } catch (err: any) {
      console.error('Image Forensic Analysis failed:', err)
      const message = err.message?.includes('fetch')
        ? 'Cannot connect to the Forensic Backend. Ensure it is running on port 8000.'
        : err.message || 'Image analysis failed unexpectedly.'
      setError(message)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const wordCount = inputText.trim().split(/\s+/).filter(Boolean).length
  const activeResults = mode === 'text' ? results : imageResults

  return (
    <main className={styles.container}>
      <header className={styles.header}>
        <div className={styles.logoWrapper}>
          <div className={styles.scannerIcon}></div>
          <h1 className="neon-text">PREE <span className={styles.tagline}>FORENSIC ENGINE</span></h1>
        </div>
        <div className={styles.statusPanel}>
          <div className={styles.statusItem}>
            <span className={styles.dot}></span>
            SYSTEM: ONLINE
          </div>
          <div className={styles.statusItem}>
            <span className={styles.dotPulse}></span>
            MODELS: LOADED
          </div>
        </div>
      </header>

      {/* Tab Switcher */}
      <div className={styles.tabSwitcher}>
        <button
          className={`${styles.tabButton} ${mode === 'text' ? styles.tabButtonActive : ''}`}
          onClick={() => handleModeSwitch('text')}
          disabled={isAnalyzing}
        >
          <FileText size={16} />
          <span>TEXT ANALYSIS</span>
        </button>
        <button
          className={`${styles.tabButton} ${mode === 'image' ? styles.tabButtonActive : ''}`}
          onClick={() => handleModeSwitch('image')}
          disabled={isAnalyzing}
        >
          <ImageIcon size={16} />
          <span>IMAGE ANALYSIS</span>
        </button>
      </div>

      <section className={styles.forensicView}>
        <div className={`${styles.terminalGroup} glass`}>
          <div className={styles.terminalHeader}>
            <div className={styles.flexCenter}>
              {mode === 'text' ? (
                <>
                  <FileText size={14} className={styles.iconDim} />
                  <span className={styles.terminalTitle}>SUSPECTED_TEXT_INPUT.TXT</span>
                </>
              ) : (
                <>
                  <ImageIcon size={14} className={styles.iconDim} />
                  <span className={styles.terminalTitle}>SUSPECTED_IMAGE_INPUT</span>
                </>
              )}
            </div>
            <div className={styles.terminalControls}>
              <span className={styles.dotControl}></span>
              <span className={styles.dotControl}></span>
              <span className={styles.dotControl}></span>
            </div>
          </div>

          <AnimatePresence mode="wait">
            {mode === 'text' ? (
              <motion.div
                key="text-input"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.2 }}
              >
                <textarea 
                  id="forensic-input"
                  className={styles.terminalInput}
                  placeholder="Paste AI-generated text here for forensic breakdown..."
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                />
                <div className={styles.terminalFooter}>
                  <span className={styles.wordCount}>{wordCount} words</span>
                  <button 
                    id="analyze-button"
                    className={`${styles.analyzeButton} neon-border`}
                    onClick={handleAnalyze}
                    disabled={isAnalyzing || !inputText.trim()}
                  >
                    {isAnalyzing ? (
                      <>
                        <Loader2 className={styles.spin} size={16} />
                        <span>SCANNING...</span>
                      </>
                    ) : (
                      <>
                        <Search size={16} />
                        <span>RUN FORENSIC SCAN</span>
                      </>
                    )}
                  </button>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="image-input"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
                className={styles.imageInputArea}
              >
                <ImageDropZone onAnalyze={handleImageAnalyze} isAnalyzing={isAnalyzing} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <aside className={`${styles.analysisSidebar} glass`}>
          <div className={styles.sidebarHeader}>
            <div className={styles.flexCenter}>
              <Activity size={16} className={styles.iconMargin} />
              <h3>FORENSIC REPORT</h3>
            </div>
          </div>
          <div className={styles.sidebarContent}>
            <AnimatePresence mode="wait">
              {error ? (
                <motion.div 
                  key="error"
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                  className={styles.errorState}
                >
                  <AlertTriangle size={32} />
                  <p>{error}</p>
                  <button className={styles.retryButton} onClick={mode === 'text' ? handleAnalyze : undefined}>Retry</button>
                </motion.div>
              ) : !activeResults && !isAnalyzing ? (
                <motion.div 
                  key="empty"
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                  className={styles.emptyState}
                >
                  <Shield size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
                  <p>{mode === 'text' ? 'Awaiting input for analysis...' : 'Drop an image to analyze...'}</p>
                </motion.div>
              ) : isAnalyzing ? (
                <motion.div 
                  key="loading"
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                  className={styles.loadingState}
                >
                  <div className={styles.scanLine}></div>
                  <p className={styles.loadingPulse}>
                    {mode === 'text' ? 'Analyzing lexical fingerprints...' : 'Analyzing visual artifacts...'}
                  </p>
                  <div className={styles.loadingSteps}>
                    {mode === 'text' ? (
                      <>
                        <div className={styles.step}>✓ Lexical analysis</div>
                        <div className={styles.stepActive}>⟳ Parameter estimation...</div>
                        <div className={styles.stepPending}>○ Model attribution</div>
                        <div className={styles.stepPending}>○ Prompt reconstruction</div>
                      </>
                    ) : (
                      <>
                        <div className={styles.step}>✓ Metadata extraction</div>
                        <div className={styles.stepActive}>⟳ Visual artifact scan...</div>
                        <div className={styles.stepPending}>○ Generator attribution</div>
                        <div className={styles.stepPending}>○ Origin determination</div>
                      </>
                    )}
                  </div>
                </motion.div>
              ) : mode === 'text' && results ? (
                <motion.div 
                  key="text-results"
                  initial={{ opacity: 0, scale: 0.95 }} 
                  animate={{ opacity: 1, scale: 1 }}
                  className={styles.reportResults}
                >
                  <ForensicRadar data={{
                    intent_confidence: results?.confidence_metrics?.intent_confidence || 0,
                    formatting_signal_strength: results?.confidence_metrics?.formatting_signal_strength || 0,
                    lexical_match_score: results?.confidence_metrics?.lexical_match_score || 0
                  }} />

                  {results?.analysis?.suspected_model && results.analysis.suspected_model !== 'unknown' && (
                    <div className={styles.modelBadge}>
                      <Cpu size={14} />
                      <span>Suspected: {results.analysis.suspected_model.toUpperCase()}</span>
                    </div>
                  )}

                  <div className={styles.resultItem}>
                    <label>Primary Intent</label>
                    <span className={styles.intentLabel}>{results?.analysis?.primary_intent}</span>
                  </div>
                  
                  <div className={styles.progressLabel}>
                    <label>Temperature Estimate</label>
                    <span className={styles.progressValue}>{results?.analysis?.temperature_estimate}</span>
                  </div>
                  <div className={styles.progressContainer}>
                    <motion.div 
                      className={styles.progressBar} 
                      initial={{ width: 0 }}
                      animate={{ width: `${(results?.analysis?.temperature_estimate || 0) * 100}%` }}
                    ></motion.div>
                  </div>
                  
                  <div className={styles.fingerprintGroup}>
                    <label>Detected AI Fingerprints</label>
                    <div className={styles.fingerprintTags}>
                      {results?.analysis?.ai_fingerprints?.slice(0, 6).map((f: string, i: number) => (
                        <span key={i} className={styles.tag}>{f}</span>
                      ))}
                    </div>
                  </div>
                </motion.div>
              ) : mode === 'image' && imageResults ? (
                <ImageForensicReport key="image-results" results={imageResults} />
              ) : null}
            </AnimatePresence>
          </div>
        </aside>
      </section>

      {mode === 'text' && results && (
        <motion.section 
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className={`${styles.promptRecovery} glass`}
        >
          <div className={styles.recoveryHeader}>
            <h2 className="neon-text">PROMPT RECONSTRUCTION</h2>
            <button id="copy-prompt" className={styles.copyButton} onClick={handleCopy}>
              {copied ? (
                <>
                  <span className={styles.dot}></span>
                  <span style={{ color: 'var(--success)' }}>COPIED!</span>
                </>
              ) : (
                <>
                  <Clipboard size={14} />
                  <span>COPY TO CLIPBOARD</span>
                </>
              )}
            </button>
          </div>
          <pre className={styles.recoveredPrompt}>
            {results.reconstructed_prompt}
          </pre>
        </motion.section>
      )}

      {mode === 'image' && imageResults && (
        <motion.section
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className={`${styles.promptRecovery} glass`}
        >
          {imageResults.reconstructed_prompt && imageResults.reconstructed_prompt !== 'N/A' && (
            <>
              <div className={styles.recoveryHeader}>
                <h2 className="neon-text">PROMPT RECONSTRUCTION</h2>
                <button id="copy-image-prompt" className={styles.copyButton} onClick={() => {
                  navigator.clipboard.writeText(imageResults.reconstructed_prompt)
                  setCopied(true)
                  setTimeout(() => setCopied(false), 2000)
                }}>
                  {copied ? (
                    <>
                      <span className={styles.dot}></span>
                      <span style={{ color: 'var(--success)' }}>COPIED!</span>
                    </>
                  ) : (
                    <>
                      <Clipboard size={14} />
                      <span>COPY TO CLIPBOARD</span>
                    </>
                  )}
                </button>
              </div>
              <pre className={styles.recoveredPrompt}>
                {imageResults.reconstructed_prompt}
              </pre>
            </>
          )}

          {imageResults.detailed_reasoning && (
            <>
              <div className={styles.recoveryHeader} style={{ marginTop: imageResults.reconstructed_prompt && imageResults.reconstructed_prompt !== 'N/A' ? '1.5rem' : 0 }}>
                <h2 className="neon-text" style={{ fontSize: '1rem' }}>FORENSIC REASONING</h2>
              </div>
              <pre className={styles.recoveredPrompt} style={{ borderLeftColor: 'var(--secondary)' }}>
                {imageResults.detailed_reasoning}
              </pre>
            </>
          )}
        </motion.section>
      )}

    </main>
  )
}
