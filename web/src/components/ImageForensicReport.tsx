'use client'

import React, { useState } from 'react'
import styles from '../app/page.module.css'
import { ShieldAlert, ShieldCheck, HelpCircle, Cpu, ChevronDown, ChevronUp, Eye, Database, BarChart3, Terminal } from 'lucide-react'
import { motion } from 'framer-motion'
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer
} from 'recharts'

interface ImageForensicReportProps {
  results: {
    analysis: {
      origin_verdict: string
      confidence_score: number
      suspected_generator: string
      detected_anomalies: string[]
      style_markers: string[]
    }
    metadata: {
      has_camera_exif: boolean
      software_tag: string | null
      resolution: string | null
      resolution_ratio_suspicious: boolean
      ai_watermark_detected: boolean
      ai_keywords_in_metadata: string[]
    }
    confidence_metrics: {
      visual_confidence: number
      metadata_confidence: number
      combined_confidence: number
      anatomy_score?: number
      text_score?: number
      texture_score?: number
      lighting_score?: number
      style_score?: number
      watermark_score?: number
    }
    detailed_reasoning: string
    reconstructed_prompt?: string
  }
}

export default function ImageForensicReport({ results }: ImageForensicReportProps) {
  const [reasoningExpanded, setReasoningExpanded] = useState(false)

  const { analysis, metadata, confidence_metrics } = results
  const isAI = analysis.origin_verdict === 'AI_GENERATED'
  const isHuman = analysis.origin_verdict === 'LIKELY_HUMAN'

  const VerdictIcon = isAI ? ShieldAlert : isHuman ? ShieldCheck : HelpCircle

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={styles.imageReportResults}
    >
      {/* Forensic Dimension Radar */}
      {(confidence_metrics.anatomy_score !== undefined || confidence_metrics.texture_score !== undefined) && (
        <div style={{ width: '100%', height: '220px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="70%" data={[
              { subject: 'Anatomy', A: confidence_metrics.anatomy_score || 0, fullMark: 100 },
              { subject: 'Text', A: confidence_metrics.text_score || 0, fullMark: 100 },
              { subject: 'Texture', A: confidence_metrics.texture_score || 0, fullMark: 100 },
              { subject: 'Lighting', A: confidence_metrics.lighting_score || 0, fullMark: 100 },
              { subject: 'Style', A: confidence_metrics.style_score || 0, fullMark: 100 },
              { subject: 'Watermark', A: confidence_metrics.watermark_score || 0, fullMark: 100 },
            ]}>
              <PolarGrid stroke="rgba(255,255,255,0.08)" />
              <PolarAngleAxis
                dataKey="subject"
                tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 10, fontFamily: 'Inter, sans-serif' }}
              />
              <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
              <Radar
                name="Forensic Dimensions"
                dataKey="A"
                stroke="hsl(330, 100%, 50%)"
                fill="hsl(330, 100%, 50%)"
                fillOpacity={0.2}
                strokeWidth={2}
              />
            </RadarChart>
          </ResponsiveContainer>
          <div style={{
            textAlign: 'center', fontSize: '0.6rem', opacity: 0.35,
            fontFamily: 'var(--font-mono)', marginTop: '-0.5rem',
          }}>
            ANOMALY DIMENSIONS (higher = more suspicious)
          </div>
        </div>
      )}

      {/* Verdict Badge */}
      <div className={`${styles.verdictBadge} ${isAI ? styles.verdictAI : isHuman ? styles.verdictHuman : styles.verdictUnknown}`}>
        <VerdictIcon size={20} />
        <span>{analysis.origin_verdict.replace(/_/g, ' ')}</span>
      </div>

      {/* Confidence Gauges */}
      <div className={styles.confidenceSection}>
        <div className={styles.flexCenter} style={{ marginBottom: '0.75rem' }}>
          <BarChart3 size={14} style={{ opacity: 0.5 }} />
          <label style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--secondary)', opacity: 0.8 }}>
            Confidence Breakdown
          </label>
        </div>
        {[
          { label: 'Visual', value: confidence_metrics.visual_confidence, icon: <Eye size={12} /> },
          { label: 'Metadata', value: confidence_metrics.metadata_confidence, icon: <Database size={12} /> },
          { label: 'Combined', value: confidence_metrics.combined_confidence, icon: <BarChart3 size={12} /> },
        ].map((metric) => (
          <div key={metric.label} className={styles.confidenceRow}>
            <div className={styles.confidenceLabel}>
              {metric.icon}
              <span>{metric.label}</span>
            </div>
            <div className={styles.confidenceBarTrack}>
              <motion.div
                className={styles.confidenceBarFill}
                initial={{ width: 0 }}
                animate={{ width: `${metric.value}%` }}
                transition={{ duration: 0.8, ease: 'easeOut' }}
                style={{
                  background: metric.value > 70
                    ? 'linear-gradient(to right, var(--accent), #ff4d6d)'
                    : metric.value > 40
                    ? 'linear-gradient(to right, var(--warning), #fbbf24)'
                    : 'linear-gradient(to right, var(--success), #34d399)'
                }}
              />
            </div>
            <span className={styles.confidenceValue}>{metric.value}%</span>
          </div>
        ))}
      </div>

      {/* Suspected Generator */}
      {analysis.suspected_generator && analysis.suspected_generator !== 'unknown' && (
        <div className={styles.modelBadge}>
          <Cpu size={14} />
          <span>Generator: {analysis.suspected_generator.toUpperCase()}</span>
        </div>
      )}

      {/* Detected Anomalies */}
      {analysis.detected_anomalies?.length > 0 && (
        <div className={styles.anomalySection}>
          <label style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--secondary)', opacity: 0.8 }}>
            Detected Anomalies
          </label>
          <div className={styles.anomalyList}>
            {analysis.detected_anomalies.map((anomaly, i) => (
              <div key={i} className={styles.anomalyItem}>
                <span className={styles.anomalyDot}>⚠</span>
                <span>{anomaly}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Style Markers */}
      {analysis.style_markers?.length > 0 && (
        <div className={styles.fingerprintGroup}>
          <label>Style Markers</label>
          <div className={styles.fingerprintTags}>
            {analysis.style_markers.map((marker, i) => (
              <span key={i} className={styles.tag}>{marker}</span>
            ))}
          </div>
        </div>
      )}

      {/* Metadata Flags */}
      <div className={styles.metadataSection}>
        <label style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--secondary)', opacity: 0.8 }}>
          Metadata Analysis
        </label>
        <div className={styles.metadataGrid}>
          <div className={styles.metadataItem}>
            <span className={styles.metadataKey}>Camera EXIF</span>
            <span className={metadata.has_camera_exif ? styles.metadataTrue : styles.metadataFalse}>
              {metadata.has_camera_exif ? 'Present' : 'Missing'}
            </span>
          </div>
          {metadata.software_tag && (
            <div className={styles.metadataItem}>
              <span className={styles.metadataKey}>Software</span>
              <span className={styles.metadataValue}>{metadata.software_tag}</span>
            </div>
          )}
          {metadata.resolution && (
            <div className={styles.metadataItem}>
              <span className={styles.metadataKey}>Resolution</span>
              <span className={styles.metadataValue}>{metadata.resolution}</span>
            </div>
          )}
          <div className={styles.metadataItem}>
            <span className={styles.metadataKey}>AI Watermark</span>
            <span className={metadata.ai_watermark_detected ? styles.metadataTrue : styles.metadataFalse}>
              {metadata.ai_watermark_detected ? 'Detected' : 'None'}
            </span>
          </div>
        </div>
      </div>

      {/* Detailed Reasoning (expandable) */}
      {results.detailed_reasoning && (
        <div className={styles.reasoningSection}>
          <button
            className={styles.reasoningToggle}
            onClick={() => setReasoningExpanded(!reasoningExpanded)}
          >
            <span>Detailed Reasoning</span>
            {reasoningExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
          {reasoningExpanded && (
            <motion.p
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className={styles.reasoningText}
            >
              {results.detailed_reasoning}
            </motion.p>
          )}
        </div>
      )}
    </motion.div>
  )
}
