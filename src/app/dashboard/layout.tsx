import Link from 'next/link';
import styles from './dashboard.module.css';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className={styles.dashboardContainer}>
      <aside className={styles.sidebar}>
        <h2 className={styles.sidebarTitle}>Menú</h2>
        <nav className={styles.nav}>
          <Link href="/dashboard" className={styles.navLink}>
            Inicio
          </Link>
          <Link href="/dashboard/becas" className={styles.navLink}>
            Becas
          </Link>
        </nav>
      </aside>
      <main className={styles.mainContent}>
        {children}
      </main>
    </div>
  );
}