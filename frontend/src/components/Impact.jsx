import React from 'react';
import styles from './Impact.module.css';

const Impact = () => {
  return (
    <section id="impact" className={`${styles.impact} section`}>
      <div className="container">
        <div className={styles.wrapper}>
          <div className={styles.content}>
            <h2 className={styles.title}>Zero Overcrowding. Zero Phone Calls.</h2>
            <p className={styles.description}>
              In the 2017 Las Vegas shooting, one hospital received 200+ patients while another nearby received only 10. 
              Respondr.ai solves this imbalance through autonomous load balancing.
            </p>
            
            <div className={styles.metrics}>
              <div className={styles.metric}>
                <div className={styles.value}>3m <span className={styles.arrow}>→</span> 15s</div>
                <div className={styles.label}>Triage-to-Dispatch Time</div>
              </div>
              <div className={styles.metric}>
                <div className={styles.value}>100%</div>
                <div className={styles.label}>Ghost Capacity Elimination</div>
              </div>
            </div>
          </div>
          
          <div className={styles.quoteCard}>
            <p className={styles.quote}>
              "The Agent handles the logistics, the humans handle the medicine."
            </p>
            <div className={styles.author}>
              <div className={styles.avatar}>R</div>
              <div className={styles.authorInfo}>
                <div className={styles.name}>Respondr.ai Philosophy</div>
                <div className={styles.role}>Core Principle</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Impact;
