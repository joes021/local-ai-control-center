import type { PropsWithChildren, ReactNode } from "react";

type LayoutProps = PropsWithChildren<{
  title: string;
  subtitle: ReactNode;
  nav?: ReactNode;
}>;

export function Layout({ title, subtitle, nav, children }: LayoutProps) {
  return (
    <div className="app-shell">
      <header className="hero">
        <p className="eyebrow">Ubuntu Desktop GUI Shell</p>
        <h1>{title}</h1>
        <div className="subtitle">{subtitle}</div>
      </header>
      {nav ? <nav className="top-nav">{nav}</nav> : null}
      <main className="content-grid">{children}</main>
    </div>
  );
}
