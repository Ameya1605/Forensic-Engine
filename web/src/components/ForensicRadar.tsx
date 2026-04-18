'use client'

import React from 'react';
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer
} from 'recharts';

interface ForensicRadarProps {
  data: {
    intent_confidence: number;
    formatting_signal_strength: number;
    lexical_match_score: number;
  }
}

export default function ForensicRadar({ data }: ForensicRadarProps) {
  // Derive heuristic values from actual data instead of hardcoding
  const avgConfidence = Math.round(
    (data.intent_confidence + data.formatting_signal_strength + data.lexical_match_score) / 3
  );
  const structuralComplexity = Math.min(100, Math.round(
    data.formatting_signal_strength * 0.6 + data.lexical_match_score * 0.4
  ));
  const predictability = Math.min(100, Math.round(
    data.intent_confidence * 0.5 + data.formatting_signal_strength * 0.3 + data.lexical_match_score * 0.2
  ));

  const chartData = [
    { subject: 'Intent', A: data.intent_confidence, fullMark: 100 },
    { subject: 'Formatting', A: data.formatting_signal_strength, fullMark: 100 },
    { subject: 'Lexical', A: data.lexical_match_score, fullMark: 100 },
    { subject: 'Structure', A: structuralComplexity, fullMark: 100 },
    { subject: 'Predict.', A: predictability, fullMark: 100 },
  ];

  return (
    <div style={{ width: '100%', height: '280px' }}>
      <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
        <RadarChart cx="50%" cy="50%" outerRadius="75%" data={chartData}>
          <PolarGrid stroke="rgba(255,255,255,0.08)" />
          <PolarAngleAxis 
            dataKey="subject" 
            tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11, fontFamily: 'Inter, sans-serif' }}
          />
          <PolarRadiusAxis 
            angle={30} 
            domain={[0, 100]} 
            tick={false}
            axisLine={false}
          />
          <Radar
            name="Forensic Breakdown"
            dataKey="A"
            stroke="hsl(185, 100%, 50%)"
            fill="hsl(185, 100%, 50%)"
            fillOpacity={0.2}
            strokeWidth={2}
          />
        </RadarChart>
      </ResponsiveContainer>
      <div style={{
        textAlign: 'center',
        fontSize: '0.65rem',
        opacity: 0.4,
        fontFamily: 'var(--font-mono)',
        marginTop: '-0.5rem',
      }}>
        AVG CONFIDENCE: {avgConfidence}%
      </div>
    </div>
  );
}
