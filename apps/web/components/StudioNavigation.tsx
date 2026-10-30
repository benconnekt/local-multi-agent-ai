'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Code2, ChartCandlestick, FlaskConical, Clapperboard } from 'lucide-react';

const studios = [
  { href: '/', title: 'Engineering', Icon: Code2 },
  { href: '/trading', title: 'Forex', Icon: ChartCandlestick },
  { href: '/trading/lab', title: 'Strategy Lab', Icon: FlaskConical },
  { href: '/audio-video', title: 'Audio to Video', Icon: Clapperboard },
];
export default function StudioNavigation() {
  const pathname = usePathname();
  return <nav aria-label="Studio navigation" className="studio-navigation">
    <span className="studio-navigation-brand">LOCAL AGENT STUDIO</span>
    <div className="studio-navigation-links">{studios.map(({href,title,Icon}) => <Link
      key={href} href={href} aria-current={pathname === href ? 'page' : undefined}
      className={pathname === href ? 'studio-navigation-link active' : 'studio-navigation-link'}>
      <Icon size={16} aria-hidden="true" />{title}
    </Link>)}</div>
    <span className="studio-navigation-status">Local workspace · Research only</span>
  </nav>;
}
