import React from 'react';
import Button from './Button';
import styles from './Hero.module.css';
import { Play, ArrowRight } from 'lucide-react';

const Hero = () => {
  return (
    <section className={styles.hero}>
      <div className={styles.auroraBackground}></div>
      <div className="container">
        <div className={styles.content}>
          <div className={styles.badge}>
            <span className={styles.badgeDot}></span>
            Mass Casualty Triage & Logistics Assistant
          </div>
          
          <h1 className={styles.headline}>
            The Agentic Logic Layer for <span className={styles.highlight}>Mass Casualty Logistics</span>
          </h1>
          
          <p className={styles.subheadline}>
            During a mass casualty event, 911 dispatchers face the 'Fog of War.' 
            Respondr.ai is an autonomous AI agent that listens to live radio streams, 
            triages patients in real-time, and intelligently orchestrates hospital bed allocation to save lives.
          </p>
          
          <div className={styles.actions}>
            <Button variant="primary" className={styles.primaryBtn}>
              Request Demo <ArrowRight size={20} style={{ marginLeft: 8 }} />
            </Button>
            <Button variant="secondary" className={styles.secondaryBtn}>
              <Play size={20} style={{ marginRight: 8 }} /> Watch Video
            </Button>
          </div>

          <div className={styles.stats}>
            <div className={styles.statItem}>
              <span className={styles.statValue}>15s</span>
              <span className={styles.statLabel}>Triage Time</span>
            </div>
            <div className={styles.divider}></div>
            <div className={styles.statItem}>
              <span className={styles.statValue}>0</span>
              <span className={styles.statLabel}>Phone Calls</span>
            </div>
            <div className={styles.divider}></div>
            <div className={styles.statItem}>
              <span className={styles.statValue}>100%</span>
              <span className={styles.statLabel}>Real-time Sync</span>
            </div>
          </div>
        </div>
        
        <div className={styles.visual}>
          {/* Abstract 3D representation or Dashboard Mockup Placeholder */}
          <div className={`${styles.card} glass`}>
            <div className={styles.cardHeader}>
              <div className={styles.liveIndicator}>
                <span className={styles.pulse}></span> LIVE INCIDENT
              </div>
              <span className={styles.time}>14:32:05</span>
            </div>
            <div className={styles.waveform}>
              {[...Array(12)].map((_, i) => (
                <div key={i} className={styles.bar} style={{ animationDelay: `${i * 0.1}s` }}></div>
              ))}
            </div>
            <div className={styles.transcription}>
              "Male patient, 30s, severe arterial bleed from leg, unconscious..."
            </div>
            <div className={styles.triageResult}>
              <div className={styles.triageBadge}>
                START Protocol: <span className={styles.red}>RED (Immediate)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;
