import React from 'react';
import { Menu, X, Activity } from 'lucide-react';
import Button from './Button';
import styles from './Navbar.module.css';

const Navbar = () => {
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <nav className={`${styles.navbar} glass`}>
      <div className="container">
        <div className={styles.wrapper}>
          <div className={styles.logo}>
            <div className={styles.iconWrapper}>
              <Activity size={24} color="var(--color-emerald)" />
            </div>
            <span className={styles.brandName}>Respondr.ai</span>
          </div>

          <div className={styles.desktopMenu}>
            <a href="#features" className={styles.link}>Features</a>
            <a href="#how-it-works" className={styles.link}>How it Works</a>
            <a href="#impact" className={styles.link}>Impact</a>
            <Button variant="primary" className={styles.cta}>Get Started</Button>
          </div>

          <button className={styles.mobileToggle} onClick={() => setIsOpen(!isOpen)}>
            {isOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {isOpen && (
        <div className={`${styles.mobileMenu} glass`}>
          <a href="#features" className={styles.mobileLink} onClick={() => setIsOpen(false)}>Features</a>
          <a href="#how-it-works" className={styles.mobileLink} onClick={() => setIsOpen(false)}>How it Works</a>
          <a href="#impact" className={styles.mobileLink} onClick={() => setIsOpen(false)}>Impact</a>
          <Button variant="primary" className={styles.mobileCta}>Get Started</Button>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
