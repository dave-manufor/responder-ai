import React from 'react';
import { Activity, Layers, Shield, MapPin } from 'lucide-react';
import styles from './Features.module.css';

const features = [
  {
    icon: <Activity size={32} />,
    title: 'Real-Time Triage',
    description: 'Instant classification of injuries (Red/Yellow/Green) using START Protocol analysis on live audio streams.'
  },
  {
    icon: <Layers size={32} />,
    title: 'Bulk Allocation',
    description: 'Distributes single or multiple patients across multiple hospitals instantly, preventing bottlenecks.'
  },
  {
    icon: <Shield size={32} />,
    title: 'Safety Buffer',
    description: 'Algorithmic safeguard that uses only 85% of reported capacity to account for data latency and walk-ins.'
  },
  {
    icon: <MapPin size={32} />,
    title: 'Geo-Locking',
    description: 'Prevents overcrowding by reserving beds in real-time and locking resources transactionally.'
  }
];

const Features = () => {
  return (
    <section id="features" className={`${styles.features} section`}>
      <div className="container">
        <div className={styles.header}>
          <h2 className={styles.title}>Engineered for Crisis Response</h2>
          <p className={styles.subtitle}>
            Moving beyond simple chat to event-driven orchestration. 
            Respondr.ai integrates audio, NLP, and geospatial logic to solve the "Patient Dumping" problem.
          </p>
        </div>

        <div className={styles.grid}>
          {features.map((feature, index) => (
            <div key={index} className={styles.card}>
              <div className={styles.iconWrapper}>
                {feature.icon}
              </div>
              <h3 className={styles.cardTitle}>{feature.title}</h3>
              <p className={styles.cardDescription}>{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;
