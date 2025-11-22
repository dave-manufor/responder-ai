import React from 'react';
import { Github, Twitter, Linkedin } from 'lucide-react';
import styles from './Footer.module.css';

const Footer = () => {
  return (
    <footer className={styles.footer}>
      <div className="container">
        <div className={styles.top}>
          <div className={styles.brand}>
            <h3 className={styles.logo}>Respondr.ai</h3>
            <p className={styles.tagline}>
              The Agentic Logic Layer for Mass Casualty Logistics.
            </p>
          </div>
          
          <div className={styles.links}>
            <div className={styles.column}>
              <h4 className={styles.columnTitle}>Product</h4>
              <a href="#" className={styles.link}>Features</a>
              <a href="#" className={styles.link}>Technology</a>
              <a href="#" className={styles.link}>Security</a>
            </div>
            <div className={styles.column}>
              <h4 className={styles.columnTitle}>Company</h4>
              <a href="#" className={styles.link}>About</a>
              <a href="#" className={styles.link}>Blog</a>
              <a href="#" className={styles.link}>Careers</a>
            </div>
            <div className={styles.column}>
              <h4 className={styles.columnTitle}>Resources</h4>
              <a href="#" className={styles.link}>Documentation</a>
              <a href="#" className={styles.link}>API Reference</a>
              <a href="#" className={styles.link}>Community</a>
            </div>
          </div>
        </div>
        
        <div className={styles.bottom}>
          <p className={styles.copyright}>© 2025 Respondr.ai. All rights reserved.</p>
          <div className={styles.socials}>
            <a href="#" className={styles.socialLink}><Github size={20} /></a>
            <a href="#" className={styles.socialLink}><Twitter size={20} /></a>
            <a href="#" className={styles.socialLink}><Linkedin size={20} /></a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
